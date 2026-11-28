# compare-adapters.ps1 - Re-grade every trained adapter against base, one rubric.
#
# Stops Ollama (serve_adapter needs ~3 GB and an 8 GB card will not hold both),
# runs teacher_pipeline/compare_adapters.sh in WSL2, then restores Ollama in a
# finally block so a failed comparison never leaves you without a daily driver.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\compare-adapters.ps1
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\compare-adapters.ps1 -Adapters lesson_01,lesson_03

param(
    # Specific adapter directory names; omit for all adapters/lesson_*.
    [string[]]$Adapters = @(),
    [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

$script = '/mnt/e/LocalLLM/teacher_pipeline/compare_adapters.sh'
$shArgs = if ($Adapters.Count) { $Adapters -join ' ' } else { '' }

function Stop-OllamaForGrading {
    $running = [bool](Get-Process -Name 'ollama', 'ollama app' -ErrorAction SilentlyContinue)
    & powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\LocalLLM\stop-ollama.ps1' -Force
    Start-Sleep -Seconds 2
    return $running
}

$wasRunning = Stop-OllamaForGrading

try {
    wsl -d $Distro -- bash -lc "chmod +x $script; $script $shArgs"
    $rc = $LASTEXITCODE
} finally {
    if ($wasRunning) {
        Write-Host 'Restarting Ollama'
        & powershell -ExecutionPolicy Bypass -File 'E:\LocalLLM\start-ollama.ps1'
    }
}

exit $rc
