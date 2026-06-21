@echo off
REM Garante que o script roda a partir da propria pasta, nao importa de onde
REM o Task Scheduler dispare. Aponte a tarefa agendada para ESTE arquivo.
cd /d "%~dp0\.."

python --version >nul 2>&1
if errorlevel 1 (
    py -3 sei_monitor.py >> scripts\run_windows.log 2>&1
) else (
    python sei_monitor.py >> scripts\run_windows.log 2>&1
)
