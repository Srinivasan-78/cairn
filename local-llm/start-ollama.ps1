# start-ollama.ps1 - Launch the Ollama server tuned for an RTX 4060 Ti (8 GB VRAM).
#
# Why this script exists: the Ollama desktop tray app ignores OLLAMA_MODELS and
# stores models on C:. Running `ollama serve` ourselves keeps the store on E: and
# lets us set the flags that make a 9B model fit in 8 GB at 32k context.
#
# Usage:  powershell -ExecutionPolicy Bypass -File E:\LocalLLM\start-ollama.ps1

param(
    # Skip the baked-profile repair check (see the end of this script).
    [switch]$SkipProfileCheck,
    # Shut down Ollama and proxy ports when not in use (delegates to stop-ollama.ps1).
    [switch]$Stop,
    # Force shutdown even if connections are active (only with -Stop).
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if ($Stop) {
    & "$PSScriptRoot\stop-ollama.ps1" -Force:$Force
    exit $LASTEXITCODE
}

$env:OLLAMA_MODELS = 'E:\LocalLLM\models'
$env:OLLAMA_HOST   = '127.0.0.1:11434'

# --- 8 GB VRAM tuning -------------------------------------------------------
# Flash attention cuts KV-cache memory and speeds up prompt processing.
$env:OLLAMA_FLASH_ATTENTION = '1'
# q8_0 KV cache ~halves context memory vs fp16. This is what buys us 32k on a
# 5.7 GB model inside a 7.2 GiB usable budget.
$env:OLLAMA_KV_CACHE_TYPE   = 'q8_0'
# Default context for all models unless a request overrides it.
$env:OLLAMA_CONTEXT_LENGTH  = '32768'
# Two resident models: a chat model plus srini-embed (274 MB) for zimrag's
# query-time rerank. At 1 they evicted each other on every retrieval. The embedder
# is small enough that srini-vision:2b (2.0 GB) or srini-draft:4b (4.5 GB) still fit 8 GB;
# only srini-coder:9b at 32k ctx (6.9 GB) gets tight.
$env:OLLAMA_MAX_LOADED_MODELS = '2'
# Only one parallel request slot to prevent multiple KV-cache allocations from overflowing 8 GB.
$env:OLLAMA_NUM_PARALLEL      = '1'
# Keep weights warm between prompts so we don't pay reload cost each call.
$env:OLLAMA_KEEP_ALIVE      = '30m'
# Ollama's default 5-minute load timeout is not enough for a model larger than
# VRAM: srini-bulk:30b (25 GB against 8 GB) spills ~17 GB to system
# RAM and died with "timed out waiting for llama-server to start" after 339s
# (measured 2026-11-25). Raised so a cold load of the big MoEs can finish.
$env:OLLAMA_LOAD_TIMEOUT    = '20m'

$exe = 'C:\Users\Srini\AppData\Local\Programs\Ollama\ollama.exe'

# If a server is already up, check whether it was started with our tuned env.
# The Ollama desktop tray app auto-starts on login WITHOUT our OLLAMA_MODELS,
# OLLAMA_FLASH_ATTENTION, or OLLAMA_KV_CACHE_TYPE.  If we see an instance
# whose model store is NOT on E:, kill it and start a fresh one below.
try {
    $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 3
    # Check: does the running instance serve models from our store?
    # A quick signal is whether srini-* tags exist - the tray app on C: won't have them.
    $tags = (Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5).models.name
    $hasSrini = $tags | Where-Object { $_ -like 'srini-*' }
    if ($hasSrini) {
        Write-Host 'Ollama already running on 127.0.0.1:11434 (tuned instance)' -ForegroundColor Yellow
        exit 0
    }
    # Running but no srini tags = wrong instance (tray app on C:). Kill it.
    Write-Host 'Ollama is running but has NO srini-* models (likely the tray app on C:). Restarting with tuned config...' -ForegroundColor Red
    $ollamaProcs = Get-Process -Name 'ollama', 'ollama app' -ErrorAction SilentlyContinue
    if ($ollamaProcs) { $ollamaProcs | Stop-Process -Force; Start-Sleep -Seconds 3 }
} catch { }

Write-Host "Starting Ollama (models: $env:OLLAMA_MODELS)" -ForegroundColor Cyan
Start-Process -FilePath $exe -ArgumentList 'serve' -WindowStyle Hidden

# Wait for the API to answer rather than guessing with a fixed sleep.
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $v = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
        Write-Host "Ollama $($v.version) ready on http://127.0.0.1:11434" -ForegroundColor Green

        # Self-heal the baked-in operator profile. `ollama pull` replaces a tag's
        # manifest and silently drops its SYSTEM block, so rather than relying on
        # remembering to rebuild, check on every server start. Costs one
        # `ollama show` per tag and rebuilds only what actually drifted.
        if (-not $SkipProfileCheck) {
            & python 'E:\LocalLLM\profile\build_persona_models.py' --repair 2>&1 |
                Where-Object { $_ -notmatch '^\s+ok\s' } | ForEach-Object {
                    Write-Host "  $_" -ForegroundColor DarkGray
                }
        }
        exit 0
    } catch { }
}

Write-Error 'Ollama did not come up within 30s.'
exit 1
