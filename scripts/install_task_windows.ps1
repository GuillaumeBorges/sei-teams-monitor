# =====================================================================
#  SEI Monitor -> Teams  |  Agendamento no Windows Task Scheduler
#  Execute este script no PowerShell como Administrador.
# =====================================================================

$RaizProjeto = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$caminhoBat  = Join-Path $PSScriptRoot "run_windows.bat"
$nomeTarefa  = "SEI Monitor - Aviso Teams"

# --- Le o intervalo de config.yaml ---
$intervaloMinutos = 5  # fallback padrao
try {
    $configYaml = Join-Path $RaizProjeto "config.yaml"
    if (Test-Path $configYaml) {
        foreach ($linha in (Get-Content $configYaml)) {
            if ($linha -match "^\s*intervalo_minutos\s*:\s*(\d+)") {
                $intervaloMinutos = [int]$Matches[1]
                break
            }
        }
    }
} catch {}

Write-Host ""
Write-Host "====================================================="
Write-Host "  SEI Monitor -> Teams  |  Agendamento no Windows"
Write-Host "====================================================="
Write-Host ""
Write-Host "Projeto  : $RaizProjeto"
Write-Host "Script   : $caminhoBat"
Write-Host "Intervalo: $intervaloMinutos minuto(s)"
Write-Host ""

# Remove tarefa anterior se existir
if (Get-ScheduledTask -TaskName $nomeTarefa -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $nomeTarefa -Confirm:$false
    Write-Host "Tarefa anterior removida."
}

$acao = New-ScheduledTaskAction -Execute $caminhoBat

$gatilho = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $intervaloMinutos) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes ([Math]::Max($intervaloMinutos - 1, 2)))

# Roda com a conta do usuario atual (garante acesso ao perfil do navegador)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName  $nomeTarefa `
    -Action    $acao `
    -Trigger   $gatilho `
    -Settings  $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "Tarefa '$nomeTarefa' criada com sucesso."
Write-Host "Verificando a cada $intervaloMinutos minuto(s)."
Write-Host ""
Write-Host "Para remover depois: Unregister-ScheduledTask -TaskName '$nomeTarefa'"
Write-Host ""
