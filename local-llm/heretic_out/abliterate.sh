#!/usr/bin/env bash
# Abliterate the srini-* lineup: refusal-direction ablation via heretic, exported
# as PEFT LoRA adapters that teacher_pipeline/serve_adapter.py can serve.
#
# Run from WSL:  bash /mnt/e/LocalLLM/heretic_out/abliterate.sh
#
# WHY THESE MODELS AND NOT OTHERS
# heretic needs HF safetensors; it cannot touch Ollama GGUF blobs, so each tag is
# mapped back to its upstream repo. Sizes marked (measured) were loaded at 4-bit
# with device_map={"":0} and torch.cuda.memory_allocated() read off; the rest are
# estimated from Qwen3.5-4B's measured 3.18 GB for 4.7B params.
#
#   tag              repo                            params   4bit VRAM  verdict
#   srini-tools:3b   ibm-granite/granite-4.2-3b        3.7B   3.84 (m)   runs
#   srini-draft:4b   unsloth/Qwen3.5-4B                4.7B   3.18 (m)   DONE already
#   srini-tools:8b   ibm-granite/granite-4.2-8b        8.8B   ~6.3 est   tight, attempted last
#   srini-vision:2b  google/gemma-4-E2B-it             5.1B   6.39 (m)   NO - see below
#   srini-coder:9b   Qwen/Qwen3.5-9B                   9.7B   ~6.6 est   over budget before
#                                                                        activations
#   srini-deep:35b   Qwen3.5-35B (MoE)                  ~35B    ~28 est   not on this card
#   srini-bulk:30b   Nemotron-3.5-Lightning-30B-A3B    32.9B   ~26 est   not on this card
#   srini-embed      nomic-embed-text                     -        -      not a chat model,
#                                                                        has no refusals
#
# gemma-4-E2B is the surprising exclusion, and the per-B estimate is what misled
# me: it allocates 6.39 GB at 4-bit, of which 5.16 GB is EMBEDDINGS. bitsandbytes
# quantizes Linear layers, not embedding tables, and this architecture keeps its
# parameters mostly in per-layer embeddings - so "E2B" costs more VRAM than the
# 9.7B Qwen does. At a 6500MB budget that leaves ~0.1 GB for activations, so
# accelerate put the whole model on CPU and a batch-size-1 probe still had not
# finished after 10 minutes. It would need batch 1 at a ~7.4 GB budget, i.e. a
# ~20x slower search. Excluded on measurement, not on principle.
#
# WHY EVERY MODEL IS SEARCHED TWICE
# heretic's only non-interactive selector is --trial-index, a position in the
# Pareto front, which cannot be known before the search. And a study cannot be
# resumed to export: main.py:406 restores the settings the study was CREATED
# with, discarding the CLI flags, so --trial-index never takes effect on a
# resume. So: search once to learn the front, then re-run with the index. The
# fixed seed makes the second search reproduce the first front exactly.
# shortcut: pays a 2x GPU cost to avoid rewriting settings inside the study
# journal; upgrade if heretic ever gains a rule-based selector.
set -u

VENV="$HOME/heretic-venv"
OUT=/mnt/e/LocalLLM/heretic_out
TRIALS=${TRIALS:-12}          # 12 matches the run that produced the 4B adapter
STARTUP=${STARTUP:-6}
SEED=${SEED:-20261126}

# slug|repo|vram-budget - slug names the output dir, so it records the real
# upstream model. Cheapest/safest model first, so an interrupted job still
# leaves a finished adapter behind.
MODELS=(
  "granite42_3b|ibm-granite/granite-4.2-3b|6500MB"
  "granite42_8b|ibm-granite/granite-4.2-8b|7200MB"
)

source "$VENV/bin/activate" || { echo "no heretic venv at $VENV"; exit 1; }
mkdir -p "$OUT/logs"

python "$OUT/pick_trial.py" --self-check || { echo "selector self-check failed"; exit 1; }

# A resident Ollama model would silently starve these runs - the same way the
# game did during lesson 35 grading, where it dropped to 7 tok/s with no error.
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
if [ -n "${used:-}" ] && [ "$used" -gt 1500 ]; then
  echo "ABORT: ${used} MiB VRAM already in use. Stop Ollama first:"
  echo "  powershell.exe -c \"Get-Process ollama* | Stop-Process -Force\""
  exit 1
fi
echo "VRAM in use at start: ${used:-unknown} MiB"

run_heretic() {   # run_heretic <repo> <journal-dir> <budget> [extra...]
  local repo="$1" studydir="$2" budget="$3"; shift 3
  heretic \
    --model "$repo" \
    --quantization bnb_4bit \
    --max-memory "{\"0\": \"$budget\", \"cpu\": \"48GB\"}" \
    --offload-outputs-to-cpu \
    --n-trials "$TRIALS" \
    --n-startup-trials "$STARTUP" \
    --seed "$SEED" \
    --max-batch-size 16 \
    --study-checkpoint-dir "$studydir" \
    "$@" < /dev/null
  # No --n-additional-trials: the config rejects 0, and on a restart run heretic
  # never asks for more trials anyway. Phase 1 still ends in an EOFError on the
  # interactive Pareto menu, which is harmless - the study is already written.
}

for entry in "${MODELS[@]}"; do
  IFS='|' read -r slug repo budget <<< "$entry"
  dest="$OUT/${slug}_ara"
  log="$OUT/logs/${slug}.log"
  studydir="$OUT/study_${slug}"

  echo
  echo "================================================================"
  echo "== $slug  <-  $repo   (budget $budget)   $(date +%H:%M:%S)"
  echo "================================================================"

  if [ -f "$dest/adapter_model.safetensors" ]; then
    echo "   already exported -> $dest  (skipping; delete it to redo)"
    continue
  fi

  # Gate: accelerate silently puts a too-large model on CPU rather than failing,
  # and a CPU search never finishes - gemma-4-E2B burned 10 minutes on a single
  # batch-size-1 probe that way. Forcing device_map={"":0} turns that into an
  # immediate, legible OOM.
  echo "-- pre-flight: does $slug fit at 4-bit on the GPU alone?"
  python - "$repo" <<'PY' || { echo "   SKIPPED $slug: does not fit on the GPU"; continue; }
import sys, torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
try:
    m = AutoModelForCausalLM.from_pretrained(
        sys.argv[1], quantization_config=BitsAndBytesConfig(load_in_4bit=True),
        device_map={"": 0}, dtype="auto")
except Exception as e:
    print(f"   does not fit: {type(e).__name__}: {str(e)[:160]}")
    sys.exit(1)
print(f"   fits: {torch.cuda.memory_allocated() / 2**30:.2f} GB allocated")
del m
torch.cuda.empty_cache()
PY

  echo "-- phase 1/2: search $TRIALS trials (log: $log)"
  run_heretic "$repo" "$studydir" "$budget" --checkpoint-action restart > "$log" 2>&1
  journal=$(ls -t "$studydir"/*.jsonl 2>/dev/null | head -1)
  if [ -z "$journal" ]; then
    echo "   SEARCH FAILED - no study written. Last lines:"
    tail -20 "$log"
    continue
  fi

  echo "-- Pareto front:"
  idx=$(python "$OUT/pick_trial.py" "$journal")
  if [ -z "$idx" ]; then
    echo "   SELECTION FAILED for $slug"; continue
  fi

  echo "-- phase 2/2: reproducing the front and exporting index $idx"
  run_heretic "$repo" "$studydir" "$budget" --checkpoint-action restart \
    --trial-index "$idx" \
    --export-strategy adapter \
    --model-action save \
    --save-directory "$dest" >> "$log" 2>&1

  if [ -f "$dest/adapter_model.safetensors" ]; then
    echo "-- OK  $(du -h "$dest/adapter_model.safetensors" | cut -f1)  -> $dest"
  else
    echo "   EXPORT FAILED for $slug. Last lines:"
    tail -20 "$log"
  fi
done

echo
echo "=== done $(date +%H:%M:%S) ==="
for entry in "${MODELS[@]}"; do
  slug="${entry%%|*}"
  f="$OUT/${slug}_ara/adapter_model.safetensors"
  [ -f "$f" ] && echo "  $slug: $(du -h "$f" | cut -f1)" || echo "  $slug: MISSING"
done
