"""
Configuração inicial de login.

Abre um navegador VISÍVEL para você fazer login no gov.br/SEI manualmente.
Ao final, salva o estado do browser em browser_state.json (cookies + storage)
para ser reutilizado pelo sei_monitor.py sem precisar abrir/fechar o browser
a cada verificação.

Rode este script novamente sempre que o sei_monitor.py avisar que a sessão
expirou.

Uso:
    python setup_login.py
"""
import json
import sys
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

STATE_FILE = "browser_state.json"


def carregar_config(caminho="config.yaml") -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = carregar_config()
    perfil_dir = Path(config["sei"]["perfil_navegador"]).resolve()
    perfil_dir.mkdir(parents=True, exist_ok=True)
    url = config["sei"]["url_lista_processos"]

    print(f"Perfil do navegador: {perfil_dir}")
    print("Abrindo navegador. Faça o login normalmente (gov.br) até a tela")
    print("de Controle de Processos do SEI ficar visível.\n")

    with sync_playwright() as p:
        contexto = p.chromium.launch_persistent_context(
            str(perfil_dir),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        pagina = contexto.new_page()
        pagina.goto(url)

        input(">>> Depois de concluir o login e ver a lista de processos, volte aqui e pressione ENTER... ")

        # Salva o estado completo do browser (cookies + localStorage + sessionStorage)
        contexto.storage_state(path=STATE_FILE)
        print(f"\nEstado do browser salvo em {STATE_FILE}.")

        contexto.close()

    print("Sessão salva com sucesso.")
    print("Agora rode 'python sei_monitor.py' para testar uma verificação.")


if __name__ == "__main__":
    sys.exit(main())
