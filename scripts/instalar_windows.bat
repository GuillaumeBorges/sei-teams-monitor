@echo off
REM =====================================================================
REM  SEI Monitor -> Teams  |  Instalacao no Windows (rode uma unica vez)
REM =====================================================================
REM  Pre-requisito: Python 3.10 ou superior instalado.
REM  Download: https://www.python.org/downloads/
REM  Marque "Add Python to PATH" durante a instalacao.
REM =====================================================================

cd /d "%~dp0\.."

echo.
echo =====================================================================
echo   SEI Monitor -^> Teams  ^|  Instalacao no Windows
echo =====================================================================
echo.

REM --- Verifica Python ---
python --version >nul 2>&1
if errorlevel 1 (
    py -3 --version >nul 2>&1
    if errorlevel 1 (
        echo ERRO: Python nao encontrado.
        echo Instale em https://www.python.org/downloads/
        echo Marque "Add Python to PATH" durante a instalacao.
        pause
        exit /b 1
    )
    set PYTHON=py -3
) else (
    set PYTHON=python
)

echo Python encontrado:
%PYTHON% --version
echo.

REM --- Instala dependencias ---
echo [1/3] Instalando dependencias Python...
%PYTHON% -m pip install --upgrade pip -q
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias. Verifique a conexao com a internet.
    pause
    exit /b 1
)
echo.

REM --- Instala Chromium ---
echo [2/3] Instalando navegador Chromium (Playwright)...
%PYTHON% -m playwright install chromium
if errorlevel 1 (
    echo ERRO ao instalar o Chromium.
    pause
    exit /b 1
)
echo.

REM --- Wizard de configuracao ---
echo [3/3] Configurando o monitor...
echo.
%PYTHON% setup_wizard.py
if errorlevel 1 (
    pause
    exit /b 1
)

REM --- Login ---
echo.
echo =====================================================================
echo   Proximo passo: Login no SEI
echo =====================================================================
echo.
echo Um navegador sera aberto. Faca o login normalmente (gov.br) ate ver
echo a lista de processos, depois volte aqui e pressione ENTER.
echo.
pause
%PYTHON% setup_login.py
if errorlevel 1 (
    echo ERRO no login. Tente rodar 'python setup_login.py' manualmente.
    pause
    exit /b 1
)

REM --- Teste ---
echo.
echo =====================================================================
echo   Testando uma verificacao...
echo =====================================================================
echo.
%PYTHON% sei_monitor.py
echo.

REM --- Agendamento ---
echo =====================================================================
echo   Deseja agendar a verificacao automatica no Windows?
echo   (necessario rodar o PowerShell como Administrador)
echo =====================================================================
echo.
set /p AGENDAR="Abrir o PowerShell como Admin e instalar a tarefa agendada? [s/N] "
if /i "%AGENDAR%"=="s" (
    PowerShell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File ""%~dp0install_task_windows.ps1""' -Verb RunAs"
)

echo.
echo Instalacao concluida! Verifique o Teams para confirmar se o aviso chegou.
echo.
pause
