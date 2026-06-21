"""
Monitor de processos do SEI -> notificação no Teams.

Verifica a tela de Controle de Processos do SEI e envia uma mensagem direta
no Teams (via Power Automate) sempre que um processo tiver uma movimentação
nova que ainda não foi avisada.

Uso:
    python sei_monitor.py            # roda UMA verificação e termina
                                      # (ideal para tarefa agendada/cron, que
                                      # chama o script a cada N minutos)

    python sei_monitor.py --loop     # roda em loop contínuo mantendo o browser
                                      # aberto — a sessão do SEI permanece ativa
                                      # entre verificações, sem exigir novo login.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import db
import teams_notifier

STATE_FILE = "browser_state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sei_monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def carregar_config(caminho="config.yaml") -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parece_tela_de_login_govbr(pagina) -> bool:
    """Detecta tela gov.br SSO — requer interação humana para renovar."""
    url_atual = pagina.url.lower()
    if "sso.acesso.gov.br" in url_atual:
        return True
    try:
        return pagina.get_by_text("Entrar com gov.br", exact=False).count() > 0
    except Exception:
        return False


def parece_tela_de_login_sip(pagina) -> bool:
    """Detecta tela de login SIP — pode ser renovada via Microsoft SSO silencioso."""
    if "sip/login.php" in pagina.url.lower():
        return True
    try:
        # Botão Microsoft no SIP é um <a onclick="acaoLogin(11,'Microsoft')">
        return pagina.locator("a[onclick*='Microsoft']").count() > 0
    except Exception:
        return False


def parece_tela_de_login(pagina) -> bool:
    return parece_tela_de_login_govbr(pagina) or parece_tela_de_login_sip(pagina)


def tentar_relogin_microsoft(pagina) -> bool:
    """
    Clica em 'Entrar com Microsoft' na tela SIP e aguarda o SSO silencioso concluir.
    Funciona enquanto o cookie ESTSAUTHPERSISTENT (Microsoft, ~90 dias) for válido.
    Retorna True se voltou ao SEI com sessão ativa.
    """
    try:
        # Botão "Entrar com Microsoft" no SIP é um <a onclick="acaoLogin(11,'Microsoft')">
        # com imagem dentro — sem texto visível, então buscamos pelo onclick.
        btn = pagina.locator("a[onclick*='Microsoft']")
        if btn.count() == 0:
            logger.warning("Link de login Microsoft não encontrado na página SIP.")
            return False

        logger.info("Tentando renovar sessão automaticamente via Microsoft SSO...")
        btn.first.click()

        # Aguarda o fluxo de redirecionamentos (SIP → Microsoft → SEI) completar
        pagina.wait_for_url("**/sei/controlador.php**", timeout=30000)
        pagina.wait_for_load_state("networkidle", timeout=15000)

        if "sei/controlador.php" in pagina.url.lower() and "sip/login" not in pagina.url.lower():
            logger.info("Sessão renovada automaticamente via Microsoft SSO.")
            return True

        logger.warning("SSO não completou silenciosamente — pode exigir MFA ou login gov.br.")
        return False

    except PlaywrightTimeoutError:
        logger.warning(
            "Timeout aguardando retorno do Microsoft SSO — sessão Microsoft também expirou. "
            "Rode 'python setup_login.py' para renovar."
        )
        return False
    except Exception as exc:
        logger.warning("Erro inesperado na renovação automática de sessão: %s", exc)
        return False


def coletar_processos(pagina, seletores: dict) -> list[dict]:
    """
    Lê a tabela de processos e devolve uma lista de dicts:
        {"numero": "...", "tem_novidade": True/False}
    """
    linhas = pagina.locator(seletores["linha_processo"])
    total = linhas.count()
    resultado = []

    for i in range(total):
        linha = linhas.nth(i)
        try:
            numero = linha.locator(seletores["numero_processo"]).inner_text().strip()
        except Exception:
            continue

        if not numero:
            continue

        tem_novidade = linha.locator(seletores["indicador_novidade"]).count() > 0
        resultado.append({"numero": numero, "tem_novidade": tem_novidade})

    return resultado


def verificar_com_contexto(pagina, config: dict) -> None:
    """Executa uma verificação usando uma página já aberta (contexto reutilizado)."""
    seletores = config["seletores"]
    url = config["sei"]["url_lista_processos"]
    webhook_url = config["teams"]["power_automate_webhook_url"]
    destinatario = config["teams"]["destinatario_email"]
    caminho_db = config["banco"]["caminho"]

    total_processos = 0
    total_notificados = 0

    try:
        pagina.goto(url, timeout=30000)
        pagina.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeoutError:
        logger.warning("Timeout carregando a página do SEI.")

    if parece_tela_de_login_sip(pagina):
        if tentar_relogin_microsoft(pagina):
            # SSO concluído: já estamos na lista de processos — não recarregamos
            # (o SEI rejeita a URL limpa sem infra_hash após nova sessão).
            pass
        else:
            logger.error("Não foi possível renovar a sessão automaticamente.")
            teams_notifier.enviar_alerta_generico(
                webhook_url,
                destinatario,
                "⚠️ A automação do SEI perdeu a sessão de login e não conseguiu renovar "
                "automaticamente (sessão Microsoft expirada). "
                "Rode 'python setup_login.py' novamente na máquina.",
            )
            with db.conectar(caminho_db) as conn:
                db.registrar_execucao(
                    conn, sucesso=False, total_processos=0,
                    total_notificados=0, mensagem="sessão expirada — SSO Microsoft falhou",
                )
            return

    if parece_tela_de_login_govbr(pagina):
        logger.error("Sessão expirada e caiu no login gov.br (requer interação humana).")
        teams_notifier.enviar_alerta_generico(
            webhook_url,
            destinatario,
            "⚠️ A automação do SEI perdeu a sessão de login. "
            "Rode 'python setup_login.py' novamente na máquina.",
        )
        with db.conectar(caminho_db) as conn:
            db.registrar_execucao(
                conn, sucesso=False, total_processos=0,
                total_notificados=0, mensagem="sessão expirada — login gov.br",
            )
        return

    processos = coletar_processos(pagina, seletores)
    total_processos = len(processos)

    if total_processos == 0:
        logger.warning(
            "Nenhum processo encontrado na página. Verifique os seletores em "
            "config.yaml (rode debug_inspect.py para calibrar)."
        )

    with db.conectar(caminho_db) as conn:
        eh_primeira_execucao = db.primeira_carga(conn)
        if eh_primeira_execucao:
            logger.info(
                "Primeira execução: catalogando %d processo(s) sem disparar notificação.",
                total_processos,
            )

        for processo in processos:
            db.upsert_processo(
                conn,
                numero=processo["numero"],
                tem_novidade=processo["tem_novidade"],
                eh_primeira_execucao=eh_primeira_execucao,
            )

        pendentes = db.processos_pendentes_de_notificacao(conn)
        for processo_row in pendentes:
            sucesso = teams_notifier.enviar_alerta_processo(
                webhook_url, destinatario, processo_row["numero"]
            )
            if sucesso:
                db.marcar_como_notificado(conn, processo_row["numero"])
                total_notificados += 1

        db.registrar_execucao(
            conn, sucesso=True, total_processos=total_processos,
            total_notificados=total_notificados, mensagem="",
        )

    logger.info(
        "Verificação concluída: %d processo(s) lidos, %d notificação(ões) enviada(s).",
        total_processos, total_notificados,
    )


def criar_contexto(p, config: dict):
    """Abre o browser e retorna (navegador_ou_None, contexto, pagina)."""
    perfil_dir = config["sei"]["perfil_navegador"]
    headless = config["monitoramento"].get("headless", True)
    _args = ["--disable-blink-features=AutomationControlled"]
    _ignore = ["--enable-automation"]

    _ua = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/148.0.7778.96 Safari/537.36")

    if Path(STATE_FILE).exists():
        # Contexto com estado completo salvo pelo setup_login.py (cookies + storage).
        navegador = p.chromium.launch(headless=headless, args=_args, ignore_default_args=_ignore)
        contexto = navegador.new_context(storage_state=STATE_FILE, user_agent=_ua)
        logger.info("Sessão carregada de %s.", STATE_FILE)
    else:
        navegador = None
        contexto = p.chromium.launch_persistent_context(
            perfil_dir, headless=headless, args=_args, ignore_default_args=_ignore,
            user_agent=_ua,
        )

    pagina = contexto.new_page()
    return navegador, contexto, pagina


def main():
    parser = argparse.ArgumentParser(description="Monitor de processos do SEI -> Teams")
    parser.add_argument(
        "--loop", action="store_true",
        help="roda continuamente com o browser aberto, mantendo a sessão do SEI ativa",
    )
    args = parser.parse_args()

    config = carregar_config()

    with sync_playwright() as p:
        navegador, contexto, pagina = criar_contexto(p, config)

        try:
            verificar_com_contexto(pagina, config)

            if args.loop:
                intervalo = config["monitoramento"]["intervalo_minutos"] * 60
                logger.info(
                    "Loop ativo: verificando a cada %d minuto(s). Browser mantido aberto.",
                    config["monitoramento"]["intervalo_minutos"],
                )
                while True:
                    time.sleep(intervalo)
                    try:
                        verificar_com_contexto(pagina, config)
                    except Exception:
                        logger.exception("Erro inesperado durante a verificação.")
        finally:
            contexto.close()
            if navegador:
                navegador.close()


if __name__ == "__main__":
    sys.exit(main())
