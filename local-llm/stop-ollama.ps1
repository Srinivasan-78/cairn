# stop-ollama.ps1 - Shut down Ollama, its runner processes, and the local proxy (ports 11434/11435).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\stop-ollama.ps1
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\stop-ollama.ps1 -Force
#   ollama-stop [-Force]   (via PowerShell profile)

param(
    # Shut down even if an active connection is open on 11434/11435.
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$targetPorts = @(11434, 11435)

if (-not $Force) {
    $active = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        Where-Object { $targetPorts -contains $_.LocalPort -or $targetPorts -contains $_.RemotePort }
    if ($active) {
        $portsBusy = ($active | Select-Object -ExpandProperty LocalPort -Unique) -join ', '
        Write-Host "Ollama/proxy ports ($portsBusy) currently have active connection(s) in use." -ForegroundColor Yellow
        Write-Host 'Close active sessions or re-run with -Force to shut down anyway.' -ForegroundColor Yellow
        exit 1
    }
}

$stopped = @()

# Stop anthropic_proxy.py (port 11435)
$proxyProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'anthropic_proxy\.py' }
foreach ($p in $proxyProcs) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    $stopped += "anthropic_proxy.py (PID $($p.ProcessId), port 11435)"
}

# Stop Ollama server, tray app, and any llama runner processes (port 11434 + runner ports)
$ollamaNames = @('ollama', 'ollama app', 'ollama_llama_server')
foreach ($name in $ollamaNames) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        $stopped += "$($p.ProcessName) (PID $($p.Id))"
    }
}

# Wait briefly and verify 11434/11435 are no longer listening
Start-Sleep -Milliseconds 500
$stillListening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $targetPorts -contains $_.LocalPort }

if ($stillListening) {
    $left = ($stillListening | Select-Object -ExpandProperty LocalPort -Unique) -join ', '
    Write-Warning "Port(s) still listening: $left"
    exit 1
}

if ($stopped.Count -eq 0) {
    Write-Host 'No Ollama or proxy processes were running.' -ForegroundColor DarkGray
} else {
    Write-Host 'Stopped:' -ForegroundColor Green
    $stopped | ForEach-Object { Write-Host "  - $_" -ForegroundColor Green }
}
exit 0
