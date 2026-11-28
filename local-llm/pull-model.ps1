# pull-model.ps1 - `ollama pull`, adopt it onto the srini tag, restore the profile.
#
# Tags are named for what they are FOR (srini-coder:9b), not for the upstream
# model, and the upstream names were removed on 2026-11-26. You still have to
# pull by the upstream name - the registry only knows qwen3.5:9b - so a refresh
# is three steps, and this script is the only thing that remembers all three:
#
#   1. ollama pull qwen3.5:9b          <- upstream name, re-added by the pull
#   2. ollama cp qwen3.5:9b srini-coder:9b   <- adopt it onto the tag you use
#   3. rebuild the SYSTEM block         <- a pull/cp carries no profile with it
#
# Skip step 2 and you quietly keep running the OLD weights under srini-coder:9b
# while a freshly pulled qwen3.5:9b sits unused beside it. Skip step 3 and the
# model still answers, it just no longer knows the hardware ceiling or which
# repo2graph checkout is authoritative, and nothing says so.
#
# Usage:
#   powershell -File E:\LocalLLM\pull-model.ps1 qwen3.5:9b
#   powershell -File E:\LocalLLM\pull-model.ps1 gemma4:e2b-it-qat granite4.2:3b
#   powershell -File E:\LocalLLM\pull-model.ps1 -All        # refresh every tag

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Tags,
    # Re-pull every tag the profile builder knows about.
    [switch]$All
)

$ErrorActionPreference = 'Stop'
$env:OLLAMA_MODELS = 'E:\LocalLLM\models'
$env:OLLAMA_HOST   = '127.0.0.1:11434'
$builder = 'E:\LocalLLM\profile\build_persona_models.py'

# Upstream registry name -> srini tag, sourced from build_persona_models.py.
$Adopt = @{}
$adoptJson = & python $builder --print-adopt | ConvertFrom-Json
$adoptJson.PSObject.Properties | ForEach-Object { $Adopt[$_.Name] = $_.Value }

if ($All) {
    # qwen3.5:35b was once missing here while the builder knew it, so -All
    # skipped a tag it claims to refresh. Driving off $Adopt keeps them in step.
    $Tags = $Adopt.Keys
}
if (-not $Tags) {
    Write-Error 'Name at least one tag, or pass -All.'
    exit 2
}

$failed = @()
foreach ($t in $Tags) {
    Write-Host "pulling $t" -ForegroundColor Cyan
    & ollama pull $t
    if ($LASTEXITCODE -ne 0) { $failed += $t; continue }

    # Adopt the freshly pulled weights onto the tag everything else calls.
    # Without this the pull is invisible to every caller in the repo.
    $dest = $Adopt[$t]
    if ($dest) {
        Write-Host "  adopting $t -> $dest" -ForegroundColor DarkCyan
        & ollama cp $t $dest
        if ($LASTEXITCODE -ne 0) { $failed += "$t (cp to $dest)" }
    } else {
        Write-Warning "  $t has no srini tag in `$Adopt - pulled but not adopted."
    }
}

# Rebuild only what drifted. --repair reads each tag's current SYSTEM block and
# compares it against the profile, so this is a no-op when nothing changed.
Write-Host 'restoring profiles' -ForegroundColor Cyan
& python $builder --repair

if ($failed) {
    Write-Warning ("failed to pull: " + ($failed -join ', '))
    exit 1
}
exit 0
