# SEI Monitor → Aviso no Teams

Automação que verifica periodicamente a tela de **Controle de Processos** do
SEI e manda uma mensagem direta no **Teams** sempre que um processo tiver
uma movimentação nova ainda não avisada — sem repetir aviso de algo que já
foi enviado.

## Como funciona, resumido

1. Um script Python abre (com **Playwright**) a tela de processos do SEI,
   usando uma sessão de navegador já logada.
2. Para cada processo, verifica se ele está marcado como "tem novidade" (o
   mesmo indicador visual que o SEI já mostra na lista).
3. Compara com o estado salvo num banco **SQLite** local. Se um processo
   passou de "sem novidade" para "com novidade", dispara um aviso.
4. O aviso é um POST HTTP para um fluxo do **Power Automate**, que posta a
   mensagem diretamente no chat dela no Teams.
5. Depois que um processo é avisado, ele não é avisado de novo até que
   alguém abra/leia o processo no SEI (limpando a novidade) e uma nova
   movimentação aconteça depois disso.

## 1. Pré-requisitos

- Python 3.10 ou superior
- Acesso de rede da máquina ao SEI e à internet (para falar com o Power
  Automate)

```bash
pip install -r requirements.txt
playwright install chromium
```

No Windows, rode os mesmos comandos no PowerShell ou Prompt de Comando,
com `python` e `pip` no PATH.

## 2. Configuração inicial

```bash
cp config.example.yaml config.yaml
```

Edite `config.yaml` e ajuste pelo menos:

- `sei.url_lista_processos`
- `teams.power_automate_webhook_url` (ver passo 5)
- `teams.destinatario_email`

## 3. Login (sessão persistente)

Como o login é via **gov.br (SSO)**, e pode envolver MFA/biometria, a
automação **não tenta refazer login sozinha a cada execução** — isso seria
frágil e arriscado de disparar bloqueios de segurança. Em vez disso, você
faz login manualmente **uma vez**, e a sessão fica salva localmente:

```bash
python setup_login.py
```

Isso abre um navegador de verdade. Faça o login normalmente até ver a lista
de processos, volte ao terminal e aperte ENTER. A sessão fica salva na pasta
`perfil_navegador/` (configurável).

> Sempre que o `sei_monitor.py` avisar "sessão expirada" no Teams, basta
> rodar `python setup_login.py` de novo.

## 4. Calibrando os seletores (passo importante)

Os seletores em `config.yaml -> seletores` são **placeholders** — a
estrutura HTML do SEI varia conforme a versão/tema da instalação da sua
organização. Para calibrar:

```bash
python debug_inspect.py
```

Isso gera `debug_pagina.html` e `debug_screenshot.png`. Abra o HTML, ache a
tabela de processos e me envie um trecho dela (ou a screenshot) — eu te
ajudo a ajustar os três seletores certinhos para o seu SEI.

## 5. Configurando o Power Automate

Como vocês já têm acesso ao Power Automate, o caminho mais simples é um
fluxo com gatilho HTTP que posta direto no chat pessoal dela via "Bot do
Fluxo" (não dá pra usar mais os webhooks antigos do Teams/Office 365
Connectors — foram desativados pela Microsoft em 2026; o substituto oficial
é justamente um fluxo do Power Automate).

1. Acesse [make.powerautomate.com](https://make.powerautomate.com)
2. **Criar** → **Fluxo de nuvem instantâneo**
3. Nome sugerido: `SEI - Aviso de Processo`
4. Gatilho: **"Quando uma solicitação HTTP for recebida"** (conector
   *Solicitação*)
5. Em "Esquema do corpo da solicitação JSON", cole:

   ```json
   {
       "type": "object",
       "properties": {
           "destinatario": { "type": "string" },
           "processo": { "type": "string" },
           "mensagem": { "type": "string" },
           "link": { "type": "string" }
       }
   }
   ```

6. Adicione uma nova etapa → conector **Microsoft Teams** → ação
   **"Publicar mensagem em um bate-papo ou canal"**
7. **Postar como**: Bot do Fluxo
8. **Postar em**: Bate-papo com o Bot do Fluxo
9. No campo de destinatário, use conteúdo dinâmico → `destinatario`
10. Na mensagem, combine os campos dinâmicos `mensagem` e `processo`
11. Salve. Copie a **URL HTTP POST** gerada na etapa do gatilho.
12. Cole essa URL em `config.yaml -> teams.power_automate_webhook_url`

**Importante:** em alguns tenants, o Bot do Fluxo só pode mandar mensagem
proativa para alguém que já interagiu com ele antes pelo menos uma vez. Se
o teste falhar silenciosamente, peça pra ela abrir o Teams, procurar por
"Power Automate" / "Flow bot" no chat e mandar um "oi" — depois teste de
novo.

Teste manual antes de plugar na automação (Linux/Mac/WSL com curl, ou
PowerShell):

```bash
curl -X POST "SUA_URL_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"destinatario":"secretaria@orgao.gov.br","processo":"00000.000000/2026-00","mensagem":"Teste de notificação","link":""}'
```

## 6. Testando a verificação

```bash
python sei_monitor.py
```

Confira o `sei_monitor.log` gerado. Na primeira execução, todos os
processos são catalogados **sem** disparar aviso (pra não inundar o Teams
avisando de tudo que já estava parado antes da automação existir). A partir
da segunda execução, só dispara aviso quando há mudança de fato.

## 7. Agendando

A automação não precisa (nem deve) ficar como um processo Python rodando
para sempre — é mais simples e resiliente rodar como tarefa agendada a cada
N minutos.

### Windows (máquina dela)

**Opção A — automática:** abra o PowerShell **como Administrador**, vá até
a pasta `scripts/` do projeto e rode:

```powershell
.\install_task_windows.ps1
```

**Opção B — manual (Agendador de Tarefas):**

1. Abra o "Agendador de Tarefas" do Windows
2. "Criar Tarefa..." → nome: `SEI Monitor`
3. Aba "Disparadores" → Novo → "Diariamente", repetir a cada 5 minutos
   indefinidamente (ajuste conforme `intervalo_minutos`)
4. Aba "Ações" → Novo → Programa/script: caminho completo para
   `scripts\run_windows.bat`
5. Aba "Condições": desmarque "Iniciar a tarefa somente se o computador
   estiver com energia AC" se for notebook
6. Salvar

### Linux (sua máquina)

```bash
chmod +x scripts/run_linux.sh
crontab -e
```

Adicione a linha (ajuste o caminho):

```
*/5 * * * * /caminho/completo/para/sei-teams-monitor/scripts/run_linux.sh
```

## 8. Observações importantes

- **Não compartilhe credenciais**: a automação roda usando a sessão de
  navegador da própria pessoa (login dela, sessão dela). Mantenha a pasta
  `perfil_navegador/` privada — ela contém cookies de sessão válidos.
- **Intervalo de 5 minutos é conservador** o suficiente para não parecer
  comportamento abusivo ao SEI/gov.br. Evite intervalos muito agressivos
  (ex.: a cada 30 segundos).
- **Processos sigilosos/restritos**: a automação só envia o *número* do
  processo no aviso, nunca conteúdo do processo — mas se isso for um
  problema de governança de dados na sua organização (dado trafegando por
  Power Automate/Microsoft 365), vale alinhar com quem cuida de
  compliance/LGPD antes de colocar em produção.
- **Se o SEI tiver paginação** na lista de processos (várias páginas), o
  script atual só lê a página carregada — me avisa que adapto para
  percorrer todas as páginas.

## Estrutura do projeto

```
sei-teams-monitor/
├── config.example.yaml      # copie para config.yaml e ajuste
├── requirements.txt
├── setup_login.py           # login único / sempre que a sessão expirar
├── debug_inspect.py         # ajuda a calibrar os seletores CSS
├── sei_monitor.py           # script principal (chamado pela tarefa agendada)
├── db.py                    # estado local (SQLite)
├── teams_notifier.py        # envio HTTP para o Power Automate
└── scripts/
    ├── run_windows.bat
    ├── install_task_windows.ps1
    └── run_linux.sh
```
