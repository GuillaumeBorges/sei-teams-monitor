@echo off
REM Executado automaticamente pelo instalador apos copiar os arquivos

cd /d "%~dp0"

echo.
echo =====================================================================
echo   SEI Monitor CGTEC  ^|  Finalizando instalacao...
echo =====================================================================
echo.

REM --- Detecta Python ---
python --version >nul 2>&1
if errorlevel 1 (
    set PYTHON=py -3
) else (
    set PYTHON=python
)

REM --- Instala dependencias ---
echo [1/3] Instalando dependencias Python...
%PYTHON% -m pip install --upgrade pip -q
%PYTHON% -m pip install -r requirements.txt -q
echo Dependencias instaladas.
echo.

REM --- Instala Chromium ---
echo [2/3] Instalando navegador Chromium (pode demorar alguns minutos)...
%PYTHON% -m playwright install chromium
echo Chromium instalado.
echo.

REM --- Login no SEI ---
echo [3/3] Abrindo navegador para login no SEI...
echo.
echo Um navegador sera aberto. Faca o login com sua conta gov.br ate ver
echo a lista de processos do SEI, depois volte aqui e pressione ENTER.
echo.
pause
%PYTHON% setup_login.py
echo.

REM --- Teste de verificacao ---
echo =====================================================================
echo   Testando primeira verificacao no SEI...
echo =====================================================================
echo.
%PYTHON% sei_monitor.py
echo.

REM --- Tarefa agendada ---
echo =====================================================================
echo   Instalando tarefa automatica no Windows (a cada 5 minutos)...
echo =====================================================================
PowerShell -ExecutionPolicy Bypass -File "%~dp0scripts\install_task_windows.ps1"
echo.

echo =====================================================================
echo   Instalacao concluida com sucesso!
echo   O monitor esta ativo e vai avisar no Teams automaticamente.
echo =====================================================================
echo.
pause
