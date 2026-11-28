#!/usr/bin/env bash
# start-ollama.sh - Launch Ollama tuned for RTX 4060 Ti (8 GB VRAM) from Linux/WSL.
set -euo pipefail

export OLLAMA_MODELS="${OLLAMA_MODELS:-/mnt/e/LocalLLM/models}"
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_CONTEXT_LENGTH="32768"
export OLLAMA_MAX_LOADED_MODELS="2"
export OLLAMA_NUM_PARALLEL="1"
export OLLAMA_KEEP_ALIVE="30m"
# Ollama's default load timeout is not enough for large models that spill to CPU.
export OLLAMA_LOAD_TIMEOUT="20m"

if curl -sf --max-time 3 "http://${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
  echo "Ollama is already running on ${OLLAMA_HOST}"
  exit 0
fi

echo "Starting Ollama (models: ${OLLAMA_MODELS})..."
nohup ollama serve > /dev/null 2>&1 &

for _ in $(seq 30); do
  if curl -sf --max-time 2 "http://${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
    echo "Ollama ready on http://${OLLAMA_HOST}"
    exit 0
  fi
  sleep 1
done

echo "ERROR: Ollama did not come up within 30s" >&2
exit 1
