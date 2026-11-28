#!/usr/bin/env bash
set -euo pipefail
# automate_lesson.sh - One unattended pass of the teach/train/grade loop.
#
# Runs entirely inside WSL2: environment check, QLoRA micro-epoch, then grading
# of the base and the trained weights back to back through serve_adapter.py.
#
# GGUF export is skipped by default (--export to attempt it anyway): Ollama
# 0.40.17 cannot load any Qwen3.5 GGUF we can currently produce, so the grading
# leg runs against serve_adapter.py instead. Both runs use the same weights and
# the same 4-bit quantization, with the adapter switched off for the base run -
# a cleaner comparison than GGUF-vs-GGUF would have been anyway.
#
# Stop Ollama before calling this: one resident model plus a ~6 GB training peak
# does not fit in 8 GB. run-lesson.ps1 does that for you.
#
# Usage (WSL2):
#   ./automate_lesson.sh                  # lesson 1, stacked on any existing adapter
#   ./automate_lesson.sh --lesson 2
#   ./automate_lesson.sh --fresh          # archive adapters/ + ledger, start clean
#   ./automate_lesson.sh --skip-train     # just grade what is already trained

set -uo pipefail

PROJECT="/mnt/e/LocalLLM/teacher_pipeline"
VENV="$HOME/student-venv"
PORT=11436
LESSON=1
FRESH=0
SKIP_TRAIN=0
DO_EXPORT=0
TRAINED_TAG="student:trained"
BASE_TAG="student:base"
EVAL_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --lesson)     LESSON="$2"; shift 2 ;;
    --fresh)      FRESH=1; shift ;;
    --skip-train) SKIP_TRAIN=1; shift ;;
    --export)     DO_EXPORT=1; shift ;;
    --port)       PORT="$2"; shift 2 ;;
    # Grade against a different eval set - e.g. dataset/code_eval.jsonl, whose
    # questions are about the operator's own code rather than generic skills.
    --eval-file)  EVAL_ARGS+=(--eval-file "$2"); shift 2 ;;
    --limit)      EVAL_ARGS+=(--limit "$2"); shift 2 ;;
    -h|--help)    sed -n '2,20p' "$0"; exit 0 ;;
    *)            echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

LESSON_PAD=$(printf '%02d' "$LESSON")
ADAPTER="$PROJECT/adapters/lesson_${LESSON_PAD}"
STAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT/logs"
RUN_LOG="$LOG_DIR/automate_lesson${LESSON_PAD}_${STAMP}.log"
SERVE_LOG="$LOG_DIR/serve_adapter_${STAMP}.log"

mkdir -p "$LOG_DIR"
# Everything below is teed to the run log, so a background run is inspectable.
exec > >(tee -a "$RUN_LOG") 2>&1

say() { echo ""; echo "=== $* ==="; }
die() { echo "FATAL: $*" >&2; exit 1; }

SERVE_PID=""
cleanup() {
  if [ -n "$SERVE_PID" ] && kill -0 "$SERVE_PID" 2>/dev/null; then
    echo "stopping serve_adapter (pid $SERVE_PID)"
    kill "$SERVE_PID" 2>/dev/null
    wait "$SERVE_PID" 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM

[ -d "$VENV" ] || die "no venv at $VENV - run setup_wsl_training.sh first"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
cd "$PROJECT" || die "cannot cd to $PROJECT"

say "0/5  environment"
python train_student.py --check || die "environment not ready (see the !! lines above)"

if [ "$FRESH" = "1" ]; then
  say "0b   archiving previous adapters"
  # Archive rather than delete: a trained adapter is expensive to reproduce.
  ARCHIVE="$PROJECT/adapters/_archive_${STAMP}"
  mkdir -p "$ARCHIVE"
  for item in "$PROJECT"/adapters/lesson_* "$PROJECT"/adapters/lesson_ledger.json; do
    [ -e "$item" ] && mv "$item" "$ARCHIVE/" && echo "  moved $(basename "$item")"
  done
  echo "  archive: $ARCHIVE"
fi

if [ "$SKIP_TRAIN" = "0" ]; then
  say "1/5  training lesson $LESSON"
  EXPORT_FLAGS=()
  [ "$DO_EXPORT" = "1" ] && EXPORT_FLAGS+=(--export)
  python train_student.py --lesson "$LESSON" ${EXPORT_FLAGS[@]+"${EXPORT_FLAGS[@]}"}
  TRAIN_RC=${PIPESTATUS[0]}
  # Not $? - that would be tee's status from the exec redirect above.
  [ "$TRAIN_RC" = "0" ] || die "training exited $TRAIN_RC"
else
  say "1/5  training skipped (--skip-train)"
fi

say "2/5  verifying the adapter"
if [ ! -f "$ADAPTER/adapter_model.safetensors" ] && [ ! -f "$ADAPTER/adapter_model.bin" ]; then
  die "no adapter weights in $ADAPTER - refusing to grade an untrained model"
fi
ls -la "$ADAPTER" | grep -E "adapter_model|adapter_config" || true

say "3/5  starting serve_adapter on port $PORT"
python serve_adapter.py --adapter "$ADAPTER" --port "$PORT" \
  --tag "$TRAINED_TAG" --base-tag "$BASE_TAG" > "$SERVE_LOG" 2>&1 &
SERVE_PID=$!
echo "pid $SERVE_PID, log $SERVE_LOG"

# The model load takes a while (4-bit quantization of a 4B base), so poll rather
# than sleeping a guessed amount.
READY=0
for i in $(seq 1 90); do
  if curl -fs -m 3 "http://127.0.0.1:$PORT/api/version" >/dev/null 2>&1; then
    READY=1; echo "  up after ${i}0s"; break
  fi
  kill -0 "$SERVE_PID" 2>/dev/null || break
  sleep 10
done
if [ "$READY" != "1" ]; then
  echo "--- serve_adapter log ---"; tail -30 "$SERVE_LOG"
  die "serve_adapter never came up on port $PORT"
fi

export OLLAMA_HOST="127.0.0.1:$PORT"

BASE_REPORT="$PROJECT/reports/grade_${BASE_TAG//:/-}_${STAMP}.json"
TRAINED_REPORT="$PROJECT/reports/grade_${TRAINED_TAG//:/-}_${STAMP}.json"

say "4/5  grading the BASE weights (adapter off)"
python grade_student.py --model "$BASE_TAG" --out "$BASE_REPORT" ${EVAL_ARGS[@]+"${EVAL_ARGS[@]}"}
[ -f "$BASE_REPORT" ] || die "no base report was written at $BASE_REPORT"
echo "base report: $BASE_REPORT"

say "5/5  grading the TRAINED weights (adapter on), compared to base"
python grade_student.py --model "$TRAINED_TAG" --compare "$BASE_REPORT" --out "$TRAINED_REPORT" ${EVAL_ARGS[@]+"${EVAL_ARGS[@]}"}
GRADE_RC=${PIPESTATUS[0]}
[ -f "$TRAINED_REPORT" ] || die "no trained report was written at $TRAINED_REPORT"

say "summary"
python - "$BASE_REPORT" "$TRAINED_REPORT" <<'PY'
import json, sys
from pathlib import Path

base, trained = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])
print(f"  {'':<24} {'base':>8} {'trained':>8} {'delta':>8}")
print(f"  {'overall':<24} {base['overall_score']:>8.3f} "
      f"{trained['overall_score']:>8.3f} "
      f"{trained['overall_score'] - base['overall_score']:>+8.3f}")
print(f"  {'pass_rate':<24} {base['pass_rate']:>8.3f} "
      f"{trained['pass_rate']:>8.3f} {trained['pass_rate'] - base['pass_rate']:>+8.3f}")
print()
for skill in sorted(set(base["by_skill"]) | set(trained["by_skill"])):
    b, t = base["by_skill"].get(skill), trained["by_skill"].get(skill)
    if b is None or t is None:
        continue
    print(f"  {skill:<24} {b:>8.3f} {t:>8.3f} {t - b:>+8.3f}")
print()
for crit in sorted(set(base["by_criterion"]) | set(trained["by_criterion"])):
    b, t = base["by_criterion"].get(crit), trained["by_criterion"].get(crit)
    if b is None or t is None:
        continue
    print(f"  {crit:<24} {b:>8.3f} {t:>8.3f} {t - b:>+8.3f}")
print(f"\n  weak after training: {trained.get('weak_skills')}")
PY

echo ""
echo "run log:       $RUN_LOG"
echo "base report:   $BASE_REPORT"
echo "trained report: $TRAINED_REPORT"
echo ""
if [ "$GRADE_RC" = "0" ]; then
  echo "RESULT: OK - no regression guard fired"
else
  echo "RESULT: grade_student.py exited $GRADE_RC - regression guard fired or a prompt errored"
fi
exit "$GRADE_RC"
