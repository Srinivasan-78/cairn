# run-claude-local.ps1 - Point Claude Code at your LOCAL model for zero-cost offline work.
#
# Intercepts /v1/messages through a lightweight local proxy on port 11435 that injects
# "thinking: disabled", preventing Qwen 3.5 from hanging in 10,000-token runaway reasoning
# chains, and forwarding directly to Ollama on port 11434 with instant SSE streaming.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-claude-local.ps1
#   powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-claude-local.ps1 -Model 4b
#
# The env vars are scoped to the launched process only - your normal `claude`
# in other terminals keeps using the real Anthropic API.

param(
    # Main model. The 9b is still the quality pick that fits the GPU alone.
    # Shorthand: 9b / 4b / gemma / granite3b / granite8b / nemotron.
    [string]$Model      = 'srini-coder:9b',
    # Small/fast model Claude Code uses for cheap background tasks. srini-vision:2b
    # measures 129.6 tok/s warm - 1.7x the 4b - and still emits valid tool calls,
    # so it is the better default for the jobs this slot actually does.
    [string]$SmallModel = 'srini-vision:2b',
    # BaseUrl points to the local thinking-guard proxy on 11435 (IPv4 127.0.0.1 to match proxy bind).
    [string]$BaseUrl    = 'http://127.0.0.1:11435',
    # Ollama backend URL.
    [string]$OllamaUrl  = 'http://127.0.0.1:11434',
    # Run against the real Anthropic API, scrubbing local routing first.
    [switch]$Cloud,
    # Print what this shell would actually talk to, then exit.
    [switch]$Doctor,
    # Append the full LifeOS constitutional system prompt (~/.claude/LIFEOS/LIFEOS_SYSTEM_PROMPT.md).
    [switch]$LifeOS,
    # Shut down Ollama + proxy ports after this claude session exits (when idle).
    [switch]$AutoStop,
    # Interactively pick a local srini-* model before launching.
    [switch]$Pick,
    # Pass extra args straight through to `claude`.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = 'Stop'

# Shorthand -> tag. Every tag below carries the ~300-token lean operator profile
# baked into its SYSTEM block: enough context that the model stops guessing about
# the hardware ceiling or which repo2graph checkout is real, small enough to cost
# nothing measurable per request (0.02-0.15s of prompt eval).
#
# Measured warm, 2026-11-24, via bench/probe_models.py:
#   gemma      129.6 tok/s   4.3 GB   tools ok   <- fastest; also vision + audio
#   granite3b   99.8 tok/s   2.2 GB   tools ok
#   4b          75.8 tok/s   3.3 GB   tools ok
#   granite8b   46.7 tok/s   5.3 GB   TOOLS BROKEN - describes the call in prose
#                                     instead of emitting one, so it loops in an
#                                     agent harness. Reachable, but not a default.
#   9b          45.0 tok/s   6.6 GB   tools ok   <- best quality on GPU alone
#   nemotron    (30B MoE, 3B active, 18 GB) spills to CPU on an 8 GB card, so it
#               is slow but holds up on harder problems. Deliberate, not a bug.
$ModelAliases = @{
    '4b'        = 'srini-draft:4b'
    '9b'        = 'srini-coder:9b'
    '35b'       = 'srini-deep:35b'
    'gemma'     = 'srini-vision:2b'
    'granite'   = 'srini-tools:3b'
    'granite3b' = 'srini-tools:3b'
    'granite8b' = 'srini-tools:8b'
    'nemotron'  = 'srini-bulk:30b'
    '30b'       = 'srini-bulk:30b'
}
if ($ModelAliases.ContainsKey($Model))      { $Model      = $ModelAliases[$Model] }
if ($ModelAliases.ContainsKey($SmallModel)) { $SmallModel = $ModelAliases[$SmallModel] }

# --- Local-routing env vars, in one place ----------------------------------
$routingVars = @(
    'ANTHROPIC_BASE_URL', 'ANTHROPIC_MODEL', 'ANTHROPIC_SMALL_FAST_MODEL',
    'ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_SONNET_MODEL',
    'ANTHROPIC_DEFAULT_HAIKU_MODEL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS',
    # MAX_CONTEXT_TOKENS belongs here too: a leaked local value would silently
    # cap a cloud session that has 200k available.
    'CLAUDE_CODE_MAX_CONTEXT_TOKENS',
    'MAX_THINKING_TOKENS', 'ANTHROPIC_THINKING_BUDGET'
)

if ($Doctor) {
    Write-Host ''
    Write-Host '  Claude Code routing in THIS shell' -ForegroundColor Cyan
    Write-Host '  ---------------------------------'
    if ($env:ANTHROPIC_BASE_URL) {
        Write-Host "  ANTHROPIC_BASE_URL = $env:ANTHROPIC_BASE_URL   -> LOCAL (proxy)"
    } else {
        Write-Host '  ANTHROPIC_BASE_URL = (unset)                 -> CLOUD'
    }
    $m = if ($env:ANTHROPIC_MODEL) { $env:ANTHROPIC_MODEL } else { '(unset)' }
    Write-Host "  ANTHROPIC_MODEL    = $m"
    Write-Host ''
    # srini-* first: the qwen*-only test silently stopped matching after the
    # 2026-11-26 rename, which is how a dead qwen3.5:9b went unnoticed.
    $localish = 'srini-*', 'qwen*', 'granite*', 'gemma*', 'nemotron*'
    if (-not $env:ANTHROPIC_BASE_URL -and
        ($localish | Where-Object { $env:ANTHROPIC_MODEL -like $_ })) {
        Write-Host '  BROKEN: a local model name is pointed at the cloud API.' -ForegroundColor Red
        Write-Host "  Fix: run 'ccloud' for cloud, or 'cclocal' for local." -ForegroundColor Red
        Write-Host ''
    }
    Write-Host '  Ollama:'
    try {
        $v = Invoke-RestMethod -Uri "$OllamaUrl/api/version" -TimeoutSec 3
        Write-Host "    running - version $($v.version)" -ForegroundColor Green
        $ps = Invoke-RestMethod -Uri "$OllamaUrl/api/ps" -TimeoutSec 3
        if ($ps.models) {
            Write-Host '    loaded in VRAM/RAM:' -ForegroundColor DarkGray
            foreach ($pm in $ps.models) {
                $gb = [math]::Round($pm.size / 1GB, 2)
                $vgb = [math]::Round($pm.size_vram / 1GB, 2)
                Write-Host "      - $($pm.name) ($gb GB total, $vgb GB VRAM)" -ForegroundColor DarkGray
            }
        } else {
            Write-Host '    no models currently loaded in memory' -ForegroundColor DarkGray
        }
    } catch {
        Write-Host '    NOT running (cclocal will start it for you)' -ForegroundColor Yellow
    }
    Write-Host '  Thinking-guard proxy:'
    try {
        $pv = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 2
        Write-Host "    running on $BaseUrl (forwarding to Ollama)" -ForegroundColor Green
    } catch {
        Write-Host "    NOT running on $BaseUrl (will auto-start on cclocal launch)" -ForegroundColor Yellow
    }
    $nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvsmi) {
        $gpuInfo = & $nvsmi.Source --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>$null
        if ($gpuInfo) {
            Write-Host "  GPU: $gpuInfo" -ForegroundColor DarkCyan
        }
    }
    Write-Host ''
    exit 0
}

if ($Pick) {
    $choices = @(
        @{ Key = '1'; Tag = 'srini-coder:9b';  Desc = '6.6 GB | 32k ctx | 47 tok/s  | Default code & planning' },
        @{ Key = '2'; Tag = 'srini-tools:3b';  Desc = '2.2 GB | 65k ctx | 103 tok/s | Fast tools & zim_search' },
        @{ Key = '3'; Tag = 'srini-vision:2b'; Desc = '4.3 GB | 131k ctx| 132 tok/s | Fastest + vision/audio' },
        @{ Key = '4'; Tag = 'srini-draft:4b';  Desc = '3.3 GB | 65k ctx | 78 tok/s  | Fast drafts & student' },
        @{ Key = '5'; Tag = 'srini-tools:8b';  Desc = '5.3 GB | 32k ctx | 48 tok/s  | Explicit tools' },
        @{ Key = '6'; Tag = 'srini-deep:35b';  Desc = '22 GB  | 32k ctx | CPU spill | Deep reasoning' },
        @{ Key = '7'; Tag = 'srini-bulk:30b';  Desc = '25 GB  | 32k ctx | CPU spill | 30B MoE (3B active)' }
    )
    Write-Host ''
    Write-Host '  Select local model:' -ForegroundColor Cyan
    foreach ($c in $choices) { Write-Host ("  [{0}] {1,-16} {2}" -f $c.Key, $c.Tag, $c.Desc) }
    $sel = Read-Host '  Choice (default 1)'
    $picked = $choices | Where-Object { $_.Key -eq $sel } | Select-Object -First 1
    if ($picked) { $Model = $picked.Tag }
}

if ($Cloud) {
    foreach ($v in $routingVars) {
        Remove-Item "Env:\$v" -ErrorAction SilentlyContinue
    }
    Write-Host ''
    Write-Host '  Claude Code -> CLOUD (real Anthropic API)' -ForegroundColor Cyan
    Write-Host ''
    claude @ClaudeArgs
    exit $LASTEXITCODE
}

# --- Make sure Ollama is actually up ---------------------------------------
try {
    $null = Invoke-RestMethod -Uri "$OllamaUrl/api/version" -TimeoutSec 3
} catch {
    Write-Host 'Ollama is not running - starting it...' -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\start-ollama.ps1"
}

# --- Ensure the thinking-guard proxy is running on port 11435 --------------
# Start-Process launches the proxy in its own process tree, so it survives
# PowerShell closing. The proxy has no auto-restart; this block is the only
# thing that brings it back up. We also launch a small watchdog that polls
# every 30s and restarts if it's gone.
$proxyPort = ([uri]$BaseUrl).Port
if ($proxyPort -le 0) { $proxyPort = 11435 }

function Start-Proxy {
    $py = (Get-Command python).Source
    $cmd = "`"$py`" `"$PSScriptRoot\anthropic_proxy.py`" $proxyPort $Model $SmallModel"
    $startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
    $null = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $cmd
        CurrentDirectory = $PSScriptRoot
        ProcessStartupInformation = $startup
    }
    foreach ($i in 1..10) {
        Start-Sleep -Seconds 1
        try { $null = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 1; return $true } catch {}
    }
    try { $null = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 3; return $true }
    catch { return $false }
}

try {
    $null = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 1
} catch {
    Write-Host "Starting Anthropic thinking-guard proxy on ${BaseUrl}..." -ForegroundColor Cyan
    if (-not (Start-Proxy)) {
        Write-Error "thinking-guard proxy did not come up at $BaseUrl`nsee $PSScriptRoot\proxy_stderr.log"
        exit 1
    }
}

# --- Proxy watchdog --------------------------------------------------------
# A background job that checks every 30s and restarts the proxy if it died.
# Scoped to this PowerShell session, so it dies when the terminal closes.
$pyExe = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if ($pyExe) {
    $watchdogBlock = {
        param($BaseUrl, $PyExe, $WorkDir, $ProxyPort, $Model, $SmallModel)
        $ProxyCmd = "`"$PyExe`" `"$WorkDir\anthropic_proxy.py`" $ProxyPort $Model $SmallModel"
        while ($true) {
            Start-Sleep -Seconds 30
            try { $null = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 2 }
            catch {
                try {
                    $startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
                    $null = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
                        CommandLine = $ProxyCmd
                        CurrentDirectory = $WorkDir
                        ProcessStartupInformation = $startup
                    }
                    Start-Sleep -Seconds 2
                } catch {}
            }
        }
    }
    Start-Job -ScriptBlock $watchdogBlock -ArgumentList $BaseUrl, $pyExe, $PSScriptRoot, $proxyPort, $Model, $SmallModel -Name 'ProxyWatchdog' | Out-Null
    Write-Host '  proxy watchdog started (restarts proxy if it dies)' -ForegroundColor DarkGray
}

# --- Make sure the requested model exists locally ---------------------------
$tags = (Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 10).models.name
foreach ($m in @($Model, $SmallModel)) {
    if ($tags -notcontains $m) {
        Write-Error "Model '$m' is not installed in Ollama.`nInstalled: $($tags -join ', ')"
        exit 1
    }
}

# --- Route Claude Code at the proxy endpoint -------------------------------
$env:ANTHROPIC_BASE_URL   = $BaseUrl
$env:ANTHROPIC_AUTH_TOKEN = 'local-no-key-needed'
$env:ANTHROPIC_API_KEY    = 'local-no-key-needed'

$env:ANTHROPIC_MODEL                  = $Model
$env:ANTHROPIC_SMALL_FAST_MODEL       = $SmallModel
$env:ANTHROPIC_DEFAULT_OPUS_MODEL     = $Model
$env:ANTHROPIC_DEFAULT_SONNET_MODEL   = $Model
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL    = $SmallModel

$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'
$env:DISABLE_TELEMETRY        = '1'
$env:DISABLE_ERROR_REPORTING  = '1'
# Ollama hard-rejects any prompt past the model's num_ctx with a 400, so read the
# real number rather than trusting a constant: 65536 here against a num_ctx of
# 8192 had Claude Code building prompts 8x too big. Measured 2026-11-25 on the
# 8 GB card: 8192 is the largest num_ctx for srini-coder:9b that stays 100% GPU
# (10240 already spills 13% to CPU), so raising it costs speed, not just VRAM.
$numCtx = 0
$ctxLine = (& ollama show --modelfile $Model 2>$null |
            Select-String -Pattern '^PARAMETER\s+num_ctx\s+(\d+)' | Select-Object -First 1)
if ($ctxLine) { $numCtx = [int]$ctxLine.Matches[0].Groups[1].Value }
if ($numCtx -le 0) {
    Write-Warning "could not read num_ctx for $Model; assuming 8192"
    $numCtx = 8192
}
# Scale skill-listing char budget to the model's context window: 65k/131k models
# (3b/4b/2b) can keep a richer listing without overflowing.
$env:SLASH_COMMAND_TOOL_CHAR_BUDGET = if ($numCtx -ge 65536) { '16000' } else { '4000' }

# Output shares the window with input, so it cannot be the whole window.
$outReserve = 2048
if ($outReserve * 2 -gt $numCtx) { $outReserve = [int]($numCtx / 4) }
$env:CLAUDE_CODE_MAX_OUTPUT_TOKENS  = "$outReserve"
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = "$numCtx"

Write-Host ''
Write-Host '  Claude Code -> LOCAL model (via thinking-guard proxy)' -ForegroundColor Green
Write-Host "  endpoint : $BaseUrl -> $OllamaUrl"
Write-Host "  model    : $Model   (small: $SmallModel)"
Write-Host "  context  : $numCtx tokens ($outReserve reserved for the reply)"
Write-Host '  cost     : $0.00 - nothing leaves this machine' -ForegroundColor Green
Write-Host ''

# A full session's system prompt measured 130-155 KB (~32-39k tokens) on
# 2026-11-25, which no 8k window can hold. --bare drops the skill/plugin listing
# and is the difference between working and a 400 on the first turn.
if ($numCtx -lt 16384 -and $ClaudeArgs -notcontains '--bare') {
    Write-Host "  NOTE: small $numCtx-token window - auto-enabling --bare so the prompt fits." -ForegroundColor Yellow
    Write-Host ''
    $ClaudeArgs = @('--bare') + $ClaudeArgs
}

# zimrag's MCP server lives in E:\LocalLLM\.mcp.json, which Claude Code only picks
# up when that is the working directory, so cclocal from another repo silently lost
# the offline corpus. Naming it explicitly works from anywhere, and without
# --strict-mcp-config it ADDS to the project's own MCP config instead of replacing
# it. It also re-adds the corpus under --bare, which otherwise strips every MCP
# server - --bare plus this is a ~1k-token prompt that can still search 441 GB.
$zimMcp = Join-Path $PSScriptRoot '.mcp.json'
if ((Test-Path $zimMcp) -and
    ($ClaudeArgs -notcontains '--mcp-config') -and
    ($ClaudeArgs -notcontains '--strict-mcp-config')) {
    $ClaudeArgs = @('--mcp-config', $zimMcp) + $ClaudeArgs
}

if ($LifeOS) {
    $lifeosPrompt = Join-Path $env:USERPROFILE '.claude\LIFEOS\LIFEOS_SYSTEM_PROMPT.md'
    if (Test-Path $lifeosPrompt) {
        $ClaudeArgs = @('--append-system-prompt-file', $lifeosPrompt) + $ClaudeArgs
    } else {
        Write-Warning "LifeOS system prompt not found at $lifeosPrompt"
    }
}

try {
    claude @ClaudeArgs
} finally {
    Get-Job -Name 'ProxyWatchdog' -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue
    if ($AutoStop -and (Test-Path "$PSScriptRoot\stop-ollama.ps1")) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\stop-ollama.ps1"
    }
}
