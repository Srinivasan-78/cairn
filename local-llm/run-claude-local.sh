#!/usr/bin/env bash
# run-claude-local.sh - Point Claude Code at your LOCAL model (bash / WSL2 / git-bash).
#
# Intercepts /v1/messages through a lightweight local proxy on port 11435 that injects
# "thinking: disabled", preventing Qwen 3.5 from hanging in 10,000-token runaway reasoning
# chains, and forwarding directly to Ollama on port 11434 with instant SSE streaming.
#
# Usage:
#   ./run-claude-local.sh                      # srini-coder:9b (local)
#   ./run-claude-local.sh 4b                   # srini-draft:4b (student)
#   ./run-claude-local.sh --cloud              # Use cloud Claude instead

set -euo pipefail

# Check if --cloud / --lifeos / --auto-stop flags are passed
USE_CLOUD=false
USE_LIFEOS=false
AUTO_STOP=false
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cloud)     USE_CLOUD=true; shift ;;
    --lifeos)    USE_LIFEOS=true; shift ;;
    --auto-stop) AUTO_STOP=true; shift ;;
    *)           ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

# If NOT using cloud, clear conflicting cloud credentials to prevent interference
if [[ "$USE_CLOUD" == "false" ]]; then
  unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true
else
  # Scrub every local-routing var. Without this, a stale ANTHROPIC_MODEL left in
  # the shell sends a local model name (srini-coder:9b) to api.anthropic.com, which
  # 404s with "model may not exist or you may not have access to it".
  # CLAUDE_CODE_MAX_CONTEXT_TOKENS belongs here too: a leaked local value (8192)
  # would silently cap a cloud session that has 200k available.
  unset ANTHROPIC_BASE_URL ANTHROPIC_MODEL ANTHROPIC_SMALL_FAST_MODEL \
        ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL \
        ANTHROPIC_DEFAULT_HAIKU_MODEL CLAUDE_CODE_MAX_OUTPUT_TOKENS \
        CLAUDE_CODE_MAX_CONTEXT_TOKENS \
        MAX_THINKING_TOKENS ANTHROPIC_THINKING_BUDGET 2>/dev/null || true
fi

MODEL="${MODEL:-srini-coder:9b}"
# srini-vision:2b measures 129.6 tok/s warm (1.7x the 4b) and still emits valid tool
# calls, so it is the better default for the cheap background slot.
SMALL_MODEL="${SMALL_MODEL:-srini-vision:2b}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:11435}"

# Shorthand -> tag. Every tag carries the ~300-token lean operator profile in its
# SYSTEM block. Measured warm 2026-11-24 (bench/probe_models.py): gemma 129.6
# tok/s, granite3b 99.8, 4b 75.8, granite8b 46.7 (TOOL CALLS BROKEN - it
# describes the call in prose instead of emitting one, so it loops in an agent
# harness), 9b 45.0 (best quality that fits the GPU alone). nemotron is a 30B MoE
# with 3B active: 18 GB spills to CPU on an 8 GB card, so it is slow but holds up
# on harder problems.
resolve_model() {
  case "$1" in
    4b)                echo "srini-draft:4b" ;;
    9b)                echo "srini-coder:9b" ;;
    35b)               echo "srini-deep:35b" ;;
    gemma)             echo "srini-vision:2b" ;;
    granite|granite3b) echo "srini-tools:3b" ;;
    granite8b)         echo "srini-tools:8b" ;;
    nemotron|30b)      echo "srini-bulk:30b" ;;
    *)                 echo "$1" ;;
  esac
}

case "${1:-}" in
  4b|9b|35b|gemma|granite|granite3b|granite8b|nemotron|30b)
    MODEL="$(resolve_model "$1")"; shift ;;
esac
MODEL="$(resolve_model "$MODEL")"
SMALL_MODEL="$(resolve_model "$SMALL_MODEL")"

if [[ "$USE_CLOUD" == "false" ]]; then
  # Auto-start Ollama if not running
  if ! curl -sf --max-time 3 "${OLLAMA_URL}/api/version" >/dev/null; then
    echo "Ollama is not running - starting it..." >&2
    if command -v powershell.exe >/dev/null 2>&1; then
      powershell.exe -ExecutionPolicy Bypass -File 'E:\LocalLLM\start-ollama.ps1' || true
    elif [ -f "/mnt/e/LocalLLM/start-ollama.sh" ]; then
      bash /mnt/e/LocalLLM/start-ollama.sh || true
    else
      (ollama serve >/dev/null 2>&1 &) || true
      for _ in $(seq 30); do
        curl -sf --max-time 2 "${OLLAMA_URL}/api/version" >/dev/null && break
        sleep 1
      done
    fi
  fi

  if ! curl -sf --max-time 3 "${OLLAMA_URL}/api/version" >/dev/null; then
    echo "ERROR: could not reach an Ollama server at ${OLLAMA_URL}" >&2
    exit 1
  fi

  # Auto-start thinking-guard proxy on 11435 if not running. Start-Process detaches
  # it from this console: a plain `&` background job is reaped when `exec claude`
  # below replaces this shell, which silently killed the proxy mid-session.
  if ! curl -sf --max-time 1 "${PROXY_URL}/api/version" >/dev/null; then
    PROXY_PORT="${PROXY_URL##*:}"
    PROXY_PORT="${PROXY_PORT%%/*}"
    [[ "$PROXY_PORT" =~ ^[0-9]+$ ]] || PROXY_PORT=11435
    echo "Starting Anthropic thinking-guard proxy on ${PROXY_URL}..." >&2
    if command -v powershell.exe >/dev/null 2>&1; then
      powershell.exe -NoProfile -Command "\$py=(Get-Command python).Source; \$s=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0}; \$null=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=\"\`\"\$py\`\" \`\"E:\LocalLLM\anthropic_proxy.py\`\" ${PROXY_PORT} ${MODEL} ${SMALL_MODEL}\";CurrentDirectory='E:\LocalLLM';ProcessStartupInformation=\$s}" >/dev/null 2>&1 || true
    else
      (setsid python3 /e/LocalLLM/anthropic_proxy.py "$PROXY_PORT" "$MODEL" "$SMALL_MODEL" >>/e/LocalLLM/proxy_stderr.log 2>&1 &) || true
    fi
    for _ in $(seq 10); do
      curl -sf --max-time 1 "${PROXY_URL}/api/version" >/dev/null && break
      sleep 1
    done
  fi

  if ! curl -sf --max-time 3 "${PROXY_URL}/api/version" >/dev/null; then
    echo "ERROR: thinking-guard proxy did not come up at ${PROXY_URL}" >&2
    echo "       see E:\\LocalLLM\\proxy_stderr.log" >&2
    exit 1
  fi
fi

if [[ "$USE_CLOUD" == "false" ]]; then
  installed=$(curl -sf --max-time 10 "${OLLAMA_URL}/api/tags" \
    | python3 -c 'import json,sys; print(" ".join(m["name"] for m in json.load(sys.stdin).get("models",[])))')

  for m in "$MODEL" "$SMALL_MODEL"; do
    case " $installed " in
      *" $m "*) ;;
      *) echo "ERROR: model '$m' not installed in Ollama. Run: ollama pull $m" >&2
         echo "Installed: $installed" >&2; exit 1 ;;
    esac
  done

  # Route Claude Code through thinking-guard proxy on 11435
  export ANTHROPIC_BASE_URL="${PROXY_URL}"
  export ANTHROPIC_AUTH_TOKEN="local-no-key-needed"
  export ANTHROPIC_API_KEY="local-no-key-needed"

  export ANTHROPIC_MODEL="$MODEL"
  export ANTHROPIC_SMALL_FAST_MODEL="$SMALL_MODEL"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="$MODEL"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="$MODEL"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="$SMALL_MODEL"
fi

export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_TELEMETRY=1
export DISABLE_ERROR_REPORTING=1

if [[ "$USE_CLOUD" == "false" ]]; then
  export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
  if [[ -d "/mnt/e/LocalLLM/models" ]]; then
    export OLLAMA_MODELS="${OLLAMA_MODELS:-/mnt/e/LocalLLM/models}"
  elif [[ -d "/e/LocalLLM/models" ]]; then
    export OLLAMA_MODELS="${OLLAMA_MODELS:-E:\\LocalLLM\\models}"
  fi
  # Ollama hard-rejects any prompt past the model's num_ctx with a 400, so read the
  # real number rather than trusting a constant: 65536 here against a num_ctx of
  # 8192 had Claude Code building prompts 8x too big. Measured 2026-11-25 on the
  # 8 GB card: 8192 is the largest num_ctx for srini-coder:9b that stays 100% GPU
  # (10240 already spills 13% to CPU), so raising it costs speed, not just VRAM.
  # `|| true` is load-bearing: pipefail would otherwise abort the script here
  # instead of letting the fallback below run.
  NUM_CTX="$(ollama show --modelfile "$MODEL" 2>/dev/null \
    | awk '/^PARAMETER[[:space:]]+num_ctx/ {print $3; exit}' || true)"
  if [[ ! "$NUM_CTX" =~ ^[0-9]+$ ]]; then
    echo "WARNING: could not read num_ctx for ${MODEL}; assuming 8192" >&2
    NUM_CTX=8192
  fi

  # Output shares the window with input, so it cannot be the whole window.
  OUT_RESERVE=2048
  if (( OUT_RESERVE * 2 > NUM_CTX )); then OUT_RESERVE=$(( NUM_CTX / 4 )); fi
  export CLAUDE_CODE_MAX_OUTPUT_TOKENS="$OUT_RESERVE"
  export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$NUM_CTX"
  if (( NUM_CTX >= 65536 )); then
    export SLASH_COMMAND_TOOL_CHAR_BUDGET=16000
  else
    export SLASH_COMMAND_TOOL_CHAR_BUDGET=4000
  fi
fi

EXTRA=()
if [[ "$USE_CLOUD" == "true" ]]; then
  cat <<EOF

  Claude Code -> CLOUD (claude.ai)
  Using your normal Claude API credentials

EOF
else
  cat <<EOF

  Claude Code -> LOCAL model (via thinking-guard proxy)
  endpoint : ${ANTHROPIC_BASE_URL} -> ${OLLAMA_URL}
  model    : ${MODEL}   (small: ${SMALL_MODEL})
  context  : ${NUM_CTX} tokens (${OUT_RESERVE} reserved for the reply)
  cost     : \$0.00 - nothing leaves this machine

EOF

  # A full session's system prompt measured 130-155 KB (~32-39k tokens) on
  # 2026-11-25, which no 8k window can hold. --bare drops the skill/plugin
  # listing and is the difference between working and a 400 on the first turn.
  if (( NUM_CTX < 16384 )) && [[ " $* " != *" --bare "* ]]; then
    echo "  NOTE: small ${NUM_CTX}-token window - auto-enabling --bare so the prompt fits." >&2
    echo "" >&2
    EXTRA+=(--bare)
  fi
fi

# zimrag's MCP server lives in E:\LocalLLM\.mcp.json, which Claude Code only
# picks up when that happens to be the working directory - so `cclocal` from any
# other repo silently lost the offline corpus. Naming the file explicitly fixes
# that from anywhere; without --strict-mcp-config it ADDS to whatever MCP config
# the project already has rather than replacing it. It also re-adds the corpus
# under --bare, which otherwise strips every MCP server: --bare plus this is the
# cheap combination, a ~1k-token prompt that can still search 441 GB.
ZIM_MCP=""
ZIM_MCP_ARG=""
if [[ -f "/e/LocalLLM/.mcp.json" ]]; then
  ZIM_MCP="/e/LocalLLM/.mcp.json"
  ZIM_MCP_ARG='E:\LocalLLM\.mcp.json'
elif [[ -f "/mnt/e/LocalLLM/.mcp.json" ]]; then
  ZIM_MCP="/mnt/e/LocalLLM/.mcp.json"
  ZIM_MCP_ARG="/mnt/e/LocalLLM/.mcp.json"
fi
if [[ "$USE_CLOUD" == "false" && -n "$ZIM_MCP" ]] \
   && [[ " $* " != *" --mcp-config "* && " $* " != *" --strict-mcp-config "* ]]; then
  EXTRA+=(--mcp-config "$ZIM_MCP_ARG")
fi

if [[ "$USE_LIFEOS" == "true" ]]; then
  LIFEOS_PROMPT="${USERPROFILE:-$HOME}/.claude/LIFEOS/LIFEOS_SYSTEM_PROMPT.md"
  if [[ ! -f "$LIFEOS_PROMPT" && -f "/mnt/c/Users/${USER}/.claude/LIFEOS/LIFEOS_SYSTEM_PROMPT.md" ]]; then
    LIFEOS_PROMPT="/mnt/c/Users/${USER}/.claude/LIFEOS/LIFEOS_SYSTEM_PROMPT.md"
  fi
  if [[ -f "$LIFEOS_PROMPT" ]]; then
    EXTRA+=(--append-system-prompt-file "$LIFEOS_PROMPT")
  else
    echo "WARNING: LifeOS system prompt not found at $LIFEOS_PROMPT" >&2
  fi
fi

if [[ "$AUTO_STOP" == "true" ]]; then
  claude ${EXTRA[@]+"${EXTRA[@]}"} "$@"
  rc=$?
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\LocalLLM\stop-ollama.ps1' || true
  elif [[ -f "/mnt/e/LocalLLM/stop-ollama.sh" ]]; then
    bash /mnt/e/LocalLLM/stop-ollama.sh || true
  fi
  exit $rc
fi

exec claude ${EXTRA[@]+"${EXTRA[@]}"} "$@"
