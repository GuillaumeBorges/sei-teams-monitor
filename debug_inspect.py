"""
Ferramenta de apoio para calibrar os seletores CSS usados em sei_monitor.py.

Abre a tela de Controle de Processos usando a sessão já salva (rode
setup_login.py antes, pelo menos uma vez) e gera:

  - debug_pagina.html     -> HTML completo da página (procure a tabela de processos)
  - debug_screenshot.png  -> print de tela inteira

Use esses arquivos para identificar, junto comigo:
  1) O seletor CSS de cada linha da tabela de processos
  2) O seletor do link/texto com o número do processo
  3) O elemento (ícone, classe, atributo) que só aparece quando o processo
     tem movimentação nova / não lida

Depois, ajuste os valores em config.yaml -> seletores.

Uso:
    python debug_inspect.py
"""
import yaml
from playwright.sync_api import sync_playwright


def main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    perfil_dir = config["sei"]["perfil_navegador"]
    url = config["sei"]["url_lista_processos"]
    headless = config["monitoramento"].get("headless", True)

    with sync_playwright() as p:
        contexto = p.chromium.launch_persistent_context(perfil_dir, headless=False)
        pagina = contexto.new_page()
        pagina.goto(url)
        pagina.wait_for_load_state("networkidle")

        print("Frames encontrados na página:")
        for frame in pagina.frames:
            print(f"  - {frame.name or '(sem nome)'}: {frame.url}")

        print("\nVerifique se a lista de processos está visível no navegador.")
        print("Se caiu na tela de login, faça o login agora até ver a lista.")
        input(">>> Quando a lista de processos estiver visível, pressione ENTER para capturar... ")

        pagina.wait_for_load_state("networkidle")

        html = pagina.content()
        with open("debug_pagina.html", "w", encoding="utf-8") as f:
            f.write(html)

        pagina.screenshot(path="debug_screenshot.png", full_page=True)

        print("\nFrames no momento da captura:")
        for frame in pagina.frames:
            print(f"  - {frame.name or '(sem nome)'}: {frame.url}")

        print("\nArquivos gerados: debug_pagina.html e debug_screenshot.png")
        print("Me mande um trecho da tabela de processos do HTML que eu calibro os seletores.")

        contexto.close()


if __name__ == "__main__":
    main()
