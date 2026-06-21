"""
Assistente de configuração inicial do SEI Monitor.

Faz perguntas simples e gera o config.yaml automaticamente.
Execute antes de rodar setup_login.py pela primeira vez,
ou sempre que quiser reconfigurar o monitor.

Uso:
    python setup_wizard.py
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Erro: PyYAML não instalado. Execute primeiro:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

CONFIG_FILE = Path("config.yaml")

# Seletores calibrados para SEI/MJ v5 — funcionam para todas as unidades do MJ.
# Se a sua instalação do SEI for de outro órgão com versão diferente, ajuste aqui
# ou rode debug_inspect.py para calibrar.
SELETORES_PADRAO = {
    "linha_processo": "tr.infraTrClara",
    "numero_processo": "a.processoVisualizado",
    "indicador_novidade": "img[src*='exclamacao.svg']",
}


def ler(prompt: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    while True:
        valor = input(f"{prompt}{sufixo}: ").strip()
        if valor:
            return valor
        if padrao:
            return padrao
        print("  (campo obrigatório)")


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def validar_url_sei(url: str) -> bool:
    return "sei" in url.lower() and "controlador.php" in url.lower()


def limpar_url_sei(url: str) -> str:
    """Remove fragmento # e parâmetros de sessão (inicializando, infra_hash)."""
    url = url.split("#")[0].strip()
    # Remove parâmetros voláteis que o SEI gera por sessão
    params_remover = ["inicializando", "infra_hash", "acao_origem", "acao_retorno"]
    partes = url.split("?", 1)
    if len(partes) == 1:
        return url
    base, qs = partes
    pares = [p for p in qs.split("&") if p.split("=")[0] not in params_remover]
    return base + "?" + "&".join(pares)


def main():
    print()
    print("=" * 60)
    print("  SEI Monitor → Teams  |  Assistente de Configuração")
    print("=" * 60)
    print()

    if CONFIG_FILE.exists():
        resp = input("config.yaml já existe. Sobrescrever? [s/N] ").strip().lower()
        if resp not in ("s", "sim", "y", "yes"):
            print("Configuração cancelada. config.yaml não foi alterado.")
            return
        print()

    # --- E-mail do destinatário ---
    print("1. E-MAIL DO DESTINATÁRIO")
    print("   Quem deve receber os avisos no Teams?")
    print("   (use o mesmo e-mail da conta Microsoft 365 da pessoa)")
    print()
    while True:
        email = ler("   E-mail")
        if validar_email(email):
            break
        print("   Formato inválido. Use algo como: nome@orgao.gov.br")
    print()

    # --- URL do SEI ---
    print("2. URL DA TELA DE PROCESSOS DO SEI")
    print("   Abra o SEI no navegador, entre na tela 'Controle de Processos'")
    print("   e copie a URL completa da barra de endereços.")
    print()
    while True:
        url_raw = ler("   URL")
        if validar_url_sei(url_raw):
            break
        print("   URL não parece ser do SEI (deve conter 'sei' e 'controlador.php').")
    url_sei = limpar_url_sei(url_raw)
    print(f"   URL limpa: {url_sei}")
    print()

    # --- Intervalo ---
    print("3. INTERVALO DE VERIFICAÇÃO (em minutos)")
    print("   Com que frequência o monitor deve checar o SEI?")
    print("   Recomendado: 5 minutos. Não use menos de 2.")
    print()
    while True:
        intervalo_str = ler("   Intervalo", "5")
        try:
            intervalo = int(intervalo_str)
            if intervalo >= 2:
                break
            print("   Use no mínimo 2 minutos para não sobrecarregar o SEI.")
        except ValueError:
            print("   Digite um número inteiro.")
    print()

    # --- Webhook (opcional neste momento) ---
    print("4. WEBHOOK DO POWER AUTOMATE  (opcional agora)")
    print("   Cole a URL HTTP POST do fluxo Power Automate.")
    print("   Se ainda não tiver, deixe em branco — edite config.yaml depois.")
    print()
    webhook = input("   Webhook URL: ").strip()
    if not webhook:
        webhook = "CONFIGURAR"
        print("   Deixado em branco — lembre-se de preencher em config.yaml antes de usar.")
    print()

    # --- Gera config.yaml ---
    config = {
        "sei": {
            "url_lista_processos": url_sei,
            "perfil_navegador": "./perfil_navegador",
        },
        "monitoramento": {
            "intervalo_minutos": intervalo,
            "headless": True,
        },
        "teams": {
            "power_automate_webhook_url": webhook,
            "destinatario_email": email,
        },
        "banco": {
            "caminho": "./estado_processos.db",
        },
        "seletores": SELETORES_PADRAO,
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print()
    print("=" * 60)
    print("  config.yaml gerado com sucesso!")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print()
    print("  1. Faça login no SEI para salvar a sessão:")
    print("       python setup_login.py")
    print()
    if webhook == "CONFIGURAR":
        print("  2. Preencha 'power_automate_webhook_url' em config.yaml")
        print("     com a URL do seu fluxo Power Automate.")
        print()
        print("  3. Teste uma verificação:")
        print("       python sei_monitor.py")
    else:
        print("  2. Teste uma verificação:")
        print("       python sei_monitor.py")
    print()


if __name__ == "__main__":
    main()
