# Guia de Instalação — Windows 11

Siga este guia **uma única vez**. Depois disso, o monitor roda sozinho no
computador, sem precisar abrir nada nem fazer login toda vez.

---

## O que você vai precisar

- Computador com Windows 11 ligado e conectado à internet
- Acesso ao SEI (sei.mj.gov.br) com seu login gov.br
- A URL do webhook do Power Automate (quem configurou vai te passar)

---

## Passo 1 — Instalar o Python

1. Abra o navegador e acesse **https://www.python.org/downloads/**
2. Clique no botão amarelo **"Download Python 3.x.x"**
3. Abra o arquivo baixado
4. **IMPORTANTE:** marque a caixa **"Add Python to PATH"** antes de clicar em Install
5. Clique em **Install Now** e aguarde terminar
6. Feche o instalador

> Se já tiver o Python instalado, pule este passo.

---

## Passo 2 — Copiar os arquivos do monitor

Copie a pasta `sei-teams-monitor` para o seu computador.
Sugestão de local: `C:\Users\SeuNome\Documents\sei-teams-monitor`

---

## Passo 3 — Instalação automática

1. Abra a pasta `sei-teams-monitor` no Windows Explorer
2. Entre na pasta **`scripts`**
3. Clique duas vezes em **`instalar_windows.bat`**

Uma janela preta vai abrir. Ela vai:
- Instalar as dependências automaticamente
- Fazer algumas perguntas de configuração (veja abaixo)
- Abrir o navegador para você fazer o login no SEI
- Registrar a tarefa que vai rodar o monitor a cada 5 minutos

### Perguntas que vão aparecer

**1. E-mail:** Digite seu e-mail corporativo (o mesmo que você usa no Teams)
```
E-mail: viviane.chagas@mj.gov.br
```

**2. URL do SEI:** Abra o SEI em outro navegador, vá até a tela
"Controle de Processos" e copie a URL da barra de endereços.
Cole aqui e pressione ENTER.

**3. Intervalo:** Quantos minutos entre cada verificação. Deixe em branco
para usar o padrão de 5 minutos.

**4. Webhook:** Cole a URL do fluxo Power Automate que vai receber os avisos.

---

## Passo 4 — Fazer o login no SEI

Quando o instalador abrir o navegador:

1. Faça o login normalmente (gov.br) até aparecer a lista de processos
2. Volte para a janela preta do instalador
3. Pressione **ENTER**

O login fica salvo. **Você não precisa fazer isso todo dia.**

---

## Passo 5 — Confirmar que está funcionando

Ao final da instalação, você deve ver algo como:

```
Verificação concluída: XX processo(s) lidos, 0 notificação(ões) enviada(s).
```

Isso significa que o monitor está funcionando. Na **primeira execução** ele
cataloga tudo sem mandar aviso (para não inundar o Teams com processos
antigos). A partir daí, toda vez que um processo ganhar uma movimentação
nova, você receberá uma mensagem no Teams.

---

## Como funciona no dia a dia

**Você não precisa fazer nada.** O monitor roda automaticamente em segundo
plano, a cada 5 minutos, enquanto o computador estiver ligado e você estiver
com a sessão do Windows aberta (pode deixar a tela bloqueada — isso não
atrapalha).

| Situação | O que acontece |
|---|---|
| Computador ligado, sessão aberta | Monitor roda a cada 5 min ✅ |
| Tela bloqueada (Win+L) | Monitor continua rodando ✅ |
| Computador desligado ou reiniciado | Monitor para, volta automaticamente quando você ligar e entrar no Windows ✅ |
| Computador hibernando/dormindo | Monitor para, volta automaticamente quando acordar ✅ |

---

## Manutenção (rara)

### A cada ~3 meses: renovar a sessão

O monitor renova a sessão do SEI automaticamente enquanto a sessão
Microsoft (do Teams/Outlook) estiver válida — o que dura cerca de 90 dias.

Quando essa sessão expirar, você vai receber uma mensagem no próprio
Teams dizendo:

> ⚠️ A automação do SEI perdeu a sessão de login e não conseguiu renovar
> automaticamente. Rode 'python setup_login.py' novamente na máquina.

Quando receber esse aviso, é só:
1. Abrir a pasta `sei-teams-monitor` no Explorer
2. Clicar duas vezes em **`setup_login.py`**
3. Fazer o login no SEI normalmente
4. Pressionar ENTER quando a lista de processos aparecer

Pronto — mais 3 meses sem precisar fazer nada.

### Se reinstalar o Windows ou trocar de computador

Repita o Passo 3 completo (instalação automática).

---

## Onde ficam os registros (log)

Se quiser conferir o que o monitor está fazendo, abra o arquivo:

```
sei-teams-monitor\scripts\run_windows.log
```

Cada linha mostra data, horário e o que aconteceu na última verificação.

---

## Perguntas frequentes

**O Teams não está recebendo os avisos, o que faço?**
Abra `run_windows.log` e veja se há mensagens de erro. Se estiver vazio,
o monitor pode não ter sido instalado corretamente — repita o Passo 3.

**Posso mudar o intervalo de verificação?**
Sim. Abra `config.yaml` com o Bloco de Notas, mude o número em
`intervalo_minutos`, salve, e rode `scripts\install_task_windows.ps1`
novamente (clique direito → Executar com PowerShell).

**Como verifico se a tarefa agendada está ativa?**
Abra o menu Iniciar, pesquise por "Agendador de Tarefas" e procure
pela tarefa **"SEI Monitor - Aviso Teams"** na lista.

**Posso desinstalar?**
Abra o PowerShell e rode:
```powershell
Unregister-ScheduledTask -TaskName "SEI Monitor - Aviso Teams" -Confirm:$false
```
Depois apague a pasta `sei-teams-monitor`.
