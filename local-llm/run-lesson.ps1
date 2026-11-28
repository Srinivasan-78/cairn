# run-lesson.ps1 - One command for a full teach/train/grade pass.
#
# Stops Ollama (a resident model plus a ~6 GB QLoRA peak will not fit in 8 GB),
# runs teacher_pipeline/automate_lesson.sh inside WSL2, then brings Ollama back
# up whatever the outcome - so a failed lesson never leaves you without a
# daily driver.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-lesson.ps1
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-lesson.ps1 -Lesson 2
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-lesson.ps1 -Fresh
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-lesson.ps1 -SkipTrain

param(
    [int]$Lesson = 1,
    # Archive the existing adapters and ledger first, so the run starts clean.
    [switch]$Fresh,
    # Grade what is already trained without running a micro-epoch.
    [switch]$SkipTrain,
    # Attempt the GGUF export too. Expected to fail on Ollama 0.40.17 - see
    # the ssm_beta_alpha note in automate_lesson.sh.
    [switch]$Export,
    # Grade against a different eval set, e.g. dataset/code_eval.jsonl for
    # questions about the operator's own code rather than generic skills.
    [string]$EvalFile = '',
    [int]$Limit = 0,
    [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

$script = '/mnt/e/LocalLLM/teacher_pipeline/automate_lesson.sh'
# Not $args - that is an automatic read-only variable in PowerShell.
$shArgs = @("--lesson", $Lesson)
if ($Fresh)     { $shArgs += '--fresh' }
if ($SkipTrain) { $shArgs += '--skip-train' }
if ($Export)    { $shArgs += '--export' }
if ($EvalFile)  { $shArgs += @('--eval-file', $EvalFile) }
if ($Limit -gt 0) { $shArgs += @('--limit', $Limit) }

function Stop-OllamaForTraining {
    $running = [bool](Get-Process -Name 'ollama', 'ollama app' -ErrorAction SilentlyContinue)
    & powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\LocalLLM\stop-ollama.ps1' -Force
    Start-Sleep -Seconds 2
    return $running
}

function Start-OllamaAgain {
    $starter = 'E:\LocalLLM\start-ollama.ps1'
    if (Test-Path $starter) {
        Write-Host 'Restarting Ollama'
        & powershell -ExecutionPolicy Bypass -File $starter
    } else {
        Write-Warning "start-ollama.ps1 not found at $starter - start Ollama yourself."
    }
}

$wasRunning = Stop-OllamaForTraining

try {
    # Make the script executable in case the DrvFs mount dropped the bit, then
    # run it. Its own log lives in teacher_pipeline/logs/.
    wsl -d $Distro -- bash -lc "chmod +x $script; $script $($shArgs -join ' ')"
    $rc = $LASTEXITCODE
} finally {
    # Always restore the server, even on a failed or interrupted run.
    if ($wasRunning) { Start-OllamaAgain }
}

Write-Host ""
if ($rc -eq 0) {
    Write-Host "Lesson $Lesson complete - no regression guard fired." -ForegroundColor Green
} else {
    Write-Host "Lesson $Lesson finished with exit code $rc - check the run log above." -ForegroundColor Yellow
}
exit $rc
