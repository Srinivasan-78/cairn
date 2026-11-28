# setup-lifeos-windows.ps1 - Windows housekeeping for LifeOS + LocalLLM.
#
# 1. Installs `jq` via winget if missing (LifeOS shell hooks use jq).
# 2. Declines macOS-only / optional tools in LifeOS Doctor.ts so `Doctor.ts` stays clean.
# 3. Optionally registers a Windows Scheduled Task (`LocalLLM-IdleReaper`) to
#    run `stop-ollama.ps1` every 30 minutes when Ollama/proxy are idle.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\setup-lifeos-windows.ps1
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\setup-lifeos-windows.ps1 -RegisterIdleReaper

param(
    [switch]$RegisterIdleReaper,
    [switch]$UnregisterIdleReaper
)

$ErrorActionPreference = 'Continue'
$bun = 'C:\Users\Srini\.bun\bin\bun.exe'
$doctor = 'C:\Users\Srini\.claude\LIFEOS\TOOLS\Doctor.ts'

if (-not (Get-Command jq -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host 'Installing jq via winget...' -ForegroundColor Cyan
        winget install --id jqlang.jq --exact --silent --accept-package-agreements --accept-source-agreements
    } else {
        Write-Warning 'jq not found and winget unavailable.'
    }
} else {
    Write-Host 'jq is already installed.' -ForegroundColor Green
}

if ((Test-Path $bun) -and (Test-Path $doctor)) {
    foreach ($tool in @('imagemagick', 'yt-dlp', 'fabric', 'codex', 'interceptor', 'cloudflare')) {
        & $bun $doctor decline $tool 2>$null | Out-Null
    }
    Write-Host 'LifeOS Doctor macOS/optional checks declined.' -ForegroundColor Green
}

$taskName = 'LocalLLM-IdleReaper'
if ($UnregisterIdleReaper) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Unregistered scheduled task: $taskName" -ForegroundColor Yellow
} elseif ($RegisterIdleReaper) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
        -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "E:\LocalLLM\stop-ollama.ps1"'
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) `
        -RepetitionInterval (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force | Out-Null
    Write-Host "Registered scheduled task: $taskName (runs stop-ollama.ps1 every 30m when idle)" -ForegroundColor Green
}
