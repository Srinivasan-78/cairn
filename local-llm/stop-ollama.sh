#!/usr/bin/env bash
# stop-ollama.sh - Shut down Ollama and anthropic_proxy.py when idle (Linux/WSL/Git Bash).
set -euo pipefail

FORCE=false
if [[ "${1:-}" == "--force" || "${1:-}" == "-f" ]]; then
  FORCE=true
fi

if command -v powershell.exe >/dev/null 2>&1; then
  if [[ "$FORCE" == "true" ]]; then
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\LocalLLM\stop-ollama.ps1' -Force
  else
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\LocalLLM\stop-ollama.ps1'
  fi
fi

if [[ "$FORCE" == "false" ]] && command -v ss >/dev/null 2>&1; then
  if ss -tn state established '( sport = :11434 or sport = :11435 or dport = :11434 or dport = :11435 )' | grep -q ESTAB; then
    echo "Ollama/proxy ports (11434/11435) currently have active connection(s). Re-run with --force." >&2
    exit 1
  fi
fi

pkill -f 'anthropic_proxy\.py' 2>/dev/null || true
pkill -x 'ollama' 2>/dev/null || true
echo "Stopped Ollama and anthropic_proxy (if running)."
