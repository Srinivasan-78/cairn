#!/usr/bin/env bash
set -euo pipefail
# compare_adapters.sh - Grade every trained adapter against base, one rubric, one eval set.
#
# Answers "which lesson actually produced the best model", which per-lesson runs
# cannot: each of those used whatever eval.jsonl looked like that day (15, then
# 19, then 22 rows) and whatever rubric was current, so their deltas are not
# comparable to each other. This re-grades everything now, so every number in
# the table comes from the same prompts and the same scoring code.
#
# Base is graded once: it is the same weights with the adapter disabled, so it
# does not matter which adapter was loaded to produce it.
#
# Stop Ollama first - serve_adapter needs ~3 GB and an 8 GB card will not hold
# both. compare-adapters.ps1 does that for you.
#
# Usage (WSL2):
#   ./compare_adapters.sh                        # all adapters/lesson_*
#   ./compare_adapters.sh lesson_01 lesson_03     # just these

set -uo pipefail

PROJECT="/mnt/e/LocalLLM/teacher_pipeline"
VENV="$HOME/student-venv"
PORT=11436
STAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT/logs"
RUN_LOG="$LOG_DIR/compare_adapters_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

say() { echo ""; echo "=== $* ==="; }
die() { echo "FATAL: $*" >&2; exit 1; }

SERVE_PID=""
cleanup() {
  if [ -n "$SERVE_PID" ] && kill -0 "$SERVE_PID" 2>/dev/null; then
    kill "$SERVE_PID" 2>/dev/null; wait "$SERVE_PID" 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM

[ -d "$VENV" ] || die "no venv at $VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
cd "$PROJECT" || die "cannot cd to $PROJECT"

if [ $# -gt 0 ]; then
  ADAPTERS=("$@")
else
  mapfile -t ADAPTERS < <(cd adapters && ls -d lesson_[0-9]* 2>/dev/null | sort)
fi
[ "${#ADAPTERS[@]}" -gt 0 ] || die "no adapters found under $PROJECT/adapters"

echo "adapters to grade: ${ADAPTERS[*]}"
echo "rubric version:   $(python -c 'import re;print(re.search(r"RUBRIC_VERSION = (\d+)",open("grade_student.py",encoding="utf-8").read()).group(1))')"
echo "eval rows:        $(wc -l < dataset/eval.jsonl)"

export OLLAMA_HOST="127.0.0.1:$PORT"
BASE_DONE=0
BASE_REPORT=""
ADAPTER_REPORTS=()

serve() {   # $1 = adapter dir name, $2 = trained tag
  python serve_adapter.py --adapter "adapters/$1" --port "$PORT" \
    --tag "$2" --base-tag "student:base" > "$LOG_DIR/serve_${1}_${STAMP}.log" 2>&1 &
  SERVE_PID=$!
  for _ in $(seq 1 90); do
    curl -fs -m 3 "http://127.0.0.1:$PORT/api/version" >/dev/null 2>&1 && return 0
    kill -0 "$SERVE_PID" 2>/dev/null || break
    sleep 10
  done
  tail -20 "$LOG_DIR/serve_${1}_${STAMP}.log"
  die "serve_adapter did not come up for $1"
}

for adapter in "${ADAPTERS[@]}"; do
  tag="student:${adapter//lesson_/l}"     # lesson_01 -> student:l01
  say "serving $adapter as $tag"
  serve "$adapter" "$tag"

  if [ "$BASE_DONE" = "0" ]; then
    say "grading BASE once (adapter disabled - identical whichever adapter is loaded)"
    BASE_REPORT="$PROJECT/reports/grade_student-base_${STAMP}.json"
    python grade_student.py --model "student:base" --out "$BASE_REPORT"
    [ -f "$BASE_REPORT" ] || die "no base report written at $BASE_REPORT"
    echo "base report: $BASE_REPORT"
    BASE_DONE=1
  fi

  say "grading $tag"
  REP="$PROJECT/reports/grade_${tag//:/-}_${STAMP}.json"
  python grade_student.py --model "$tag" --out "$REP"
  [ -f "$REP" ] || die "no adapter report written at $REP"
  ADAPTER_REPORTS+=("$REP")
  echo "report: $REP"

  cleanup; SERVE_PID=""
done

say "summary - all rows from the same eval set and the same rubric"
python - "$BASE_REPORT" "${ADAPTER_REPORTS[@]}" <<'PY'
import json, re, statistics, sys
from pathlib import Path

paths = sys.argv[1:]
reps = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
names = ["base"] + [r["model"].split(":")[-1] for r in reps[1:]]

def facts(rep):
    """Mean of the accuracy sub-scores, which say what kind of wrong an answer is."""
    acc = {}
    for key in ("nums", "ids", "recall"):
        vals = []
        for r in rep["results"]:
            m = re.search(rf"{key}=([\d.]+)", str((r.get("notes") or {}).get("accuracy", "")))
            if m:
                vals.append(float(m.group(1)))
        acc[key] = statistics.mean(vals) if vals else float("nan")
    lens = [len(r["student_answer"]) for r in rep["results"] if "student_answer" in r]
    acc["chars"] = statistics.mean(lens) if lens else float("nan")
    return acc

rows = [facts(r) for r in reps]
w = 10
print(f"{'':<22}" + "".join(f"{n:>{w}}" for n in names))
def line(label, vals, fmt="{:>10.3f}"):
    print(f"{label:<22}" + "".join(fmt.format(v) for v in vals))

line("overall", [r["overall_score"] for r in reps])
line("pass_rate", [r["pass_rate"] for r in reps])
print()
for crit in ("accuracy", "reasoning", "formatting", "conciseness"):
    line(crit, [r["by_criterion"].get(crit, float('nan')) for r in reps])
print()
line("  numbers stated", [x["nums"] for x in rows])
line("  identifiers", [x["ids"] for x in rows])
line("  vocab overlap", [x["recall"] for x in rows])
line("  answer chars", [x["chars"] for x in rows], "{:>10.0f}")
print()
skills = sorted({s for r in reps for s in r["by_skill"]})
for s in skills:
    line(s, [r["by_skill"].get(s, float('nan')) for r in reps])

best = max(range(len(reps)), key=lambda i: reps[i]["overall_score"])
print(f"\nbest overall: {names[best]} at {reps[best]['overall_score']:.3f} "
      f"({reps[best]['overall_score'] - reps[0]['overall_score']:+.3f} vs base)")
PY

echo ""
echo "run log: $RUN_LOG"
