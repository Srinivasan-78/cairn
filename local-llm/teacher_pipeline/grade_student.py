#!/usr/bin/env python3
"""
grade_student.py - Benchmark the Student against the Teacher's reference answers.

The Teacher (Claude) writes reference outputs into the eval set. This script
replays those prompts against the local model and scores each answer on four
axes from curriculum.yaml's rubric, then logs which skills are weak so the next
lesson batch can target them.

Scoring is deterministic and offline by default - no Teacher API call needed:
  accuracy     content-word overlap with the reference, plus agreement on any
               numeric facts the reference states
  reasoning    did it produce a usable chain-of-thought, and does that CoT
               mention the key concepts the reference reasoning does
  formatting   structural match: code fences, JSON validity, required markers
  conciseness  length ratio against the reference, penalising padding

With --judge, Claude grades the same answers qualitatively instead (pass the
generated report back to Claude and have it fill in the `judge` block).

Usage:
    python grade_student.py                          # grade srini-draft:4b on eval.jsonl
    python grade_student.py --model srini-coder:9b       # baseline a different model
    python grade_student.py --baseline               # tag this run as the pre-training baseline
    python grade_student.py --compare reports/baseline.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pip install pyyaml")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # so we can import ask_local_llm

try:
    from ask_local_llm import ask, health
except ImportError:
    sys.exit("Cannot import ask_local_llm.py - expected at E:\\LocalLLM\\ask_local_llm.py")

CURRICULUM = HERE / "curriculum.yaml"
DATASET = HERE / "dataset"
REPORTS = HERE / "reports"

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "to", "of", "in", "on",
    "for", "with", "is", "are", "was", "were", "be", "been", "it", "this",
    "that", "these", "those", "as", "at", "by", "from", "you", "your", "we",
    "can", "will", "would", "should", "not", "no", "do", "does", "so", "into",
}

THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
CODE_RE = re.compile(r"```(\w+)?\s*(.*?)```", re.DOTALL)
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# Technical tokens that make an answer checkably right or wrong: CLI flags,
# dotted paths, snake_case and CamelCase names - `--no-mtp`, `torch.cuda`,
# `max_seq_length`, `FastLanguageModel`. Getting one of these wrong is a wrong
# answer, which is not true of the prose around them.
IDENT_RE = re.compile(
    r"--[a-z0-9][a-z0-9-]*"                                   # --no-mtp
    r"|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+"   # torch.cuda
    r"|[a-z][a-z0-9]*(?:_[a-z0-9]+)+"                         # max_seq_length
    r"|[A-Z][a-z]+(?:[A-Z][a-z]+)+"                           # FastLanguageModel
)

# Bumped whenever a scoring function changes, so reports written under different
# rubrics are not silently compared. v1 scored accuracy as 0.7 x content-word
# recall; v2 weights numbers and identifiers instead - see score_accuracy.
RUBRIC_VERSION = 2


# ---------------------------------------------------------------------------
# Scoring primitives
# ---------------------------------------------------------------------------
def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z_][a-z0-9_]{2,}", text.lower()) if w not in STOPWORDS}


def identifiers(text: str) -> set[str]:
    """Checkable technical tokens, lowercased for comparison."""
    return {m.group(0).lower() for m in IDENT_RE.finditer(text)}


def split_reference(target: str) -> tuple[str, str]:
    """Separate the Teacher's <think> trace from the final answer."""
    m = THINK_RE.search(target)
    if not m:
        return "", target.strip()
    return m.group(1).strip(), THINK_RE.sub("", target).strip()


def score_accuracy(student: str, ref: str) -> tuple[float, str]:
    """Agreement on the reference's checkable facts: numbers, identifiers, words.

    v2. v1 was `0.7 * content_word_recall + 0.3 * numeric_agreement`, which made
    this axis structurally anti-correlated with score_conciseness: that function
    awards a full 1.0 anywhere from 0.3x to 1.6x the reference length, but a
    brief answer cannot contain 70% of a long reference's vocabulary - so a
    correct, concise answer was scored as inaccurate. Training against it taught
    the model to echo reference phrasing rather than to be right.

    Numbers and identifiers are what make an answer checkable, so they carry the
    weight now and vocabulary overlap is demoted to a tiebreaker.

    Two deliberate choices:

    - A component is weighted only when the reference actually contains it.
      v1 awarded a free numeric score of 1.0 when the reference had no numbers,
      which silently inflated every prose answer.
    - Recall, not F1. A correct answer should state the reference's figures, and
      padding to catch them is not a cheap attack - you cannot stuff numbers or
      identifiers you do not know. Verbosity is bounded by score_conciseness.
    """
    parts: list[tuple[str, float, float]] = []  # (name, weight, score)

    ref_nums = set(NUM_RE.findall(ref))
    if ref_nums:
        hit = len(ref_nums & set(NUM_RE.findall(student))) / len(ref_nums)
        parts.append(("nums", 0.40, hit))

    ref_ids = identifiers(ref)
    if ref_ids:
        hit = len(ref_ids & identifiers(student)) / len(ref_ids)
        parts.append(("ids", 0.40, hit))

    ref_w = content_words(ref)
    if ref_w:
        hit = len(ref_w & content_words(student)) / len(ref_w)
        parts.append(("recall", 0.20, hit))

    if not parts:
        return 1.0, "empty reference"

    total_w = sum(w for _, w, _ in parts)
    score = sum(w * s for _, w, s in parts) / total_w
    return min(1.0, score), " ".join(f"{n}={s:.2f}" for n, _, s in parts)


def score_reasoning(student_think: str, ref_think: str, student_answer: str) -> tuple[float, str]:
    """Reward a real CoT that covers the reference reasoning's concepts."""
    if not ref_think:
        # Nothing to compare against; credit any visible reasoning.
        return (0.8 if student_think else 0.5), "no reference CoT"
    if not student_think:
        return 0.0, "student produced no CoT"

    ref_w, stu_w = content_words(ref_think), content_words(student_think)
    coverage = len(ref_w & stu_w) / len(ref_w) if ref_w else 0.0

    # A CoT that is pure restatement of the answer is not reasoning.
    answer_w = content_words(student_answer)
    novelty = len(stu_w - answer_w) / len(stu_w) if stu_w else 0.0

    # Multi-step structure (numbered/bulleted steps) is a good proxy for depth.
    steps = len(re.findall(r"(?m)^\s*(?:\d+[.)]|[-*])\s+", student_think))
    structure = min(1.0, steps / 4.0)

    score = 0.55 * coverage + 0.25 * novelty + 0.20 * structure
    return min(1.0, score), f"cov={coverage:.2f} nov={novelty:.2f} steps={steps}"


def score_formatting(student: str, ref: str) -> tuple[float, str]:
    """Structural fidelity: code fences, language tags, JSON validity."""
    checks, notes = [], []

    ref_blocks, stu_blocks = CODE_RE.findall(ref), CODE_RE.findall(student)
    if ref_blocks:
        if not stu_blocks:
            checks.append(0.0)
            notes.append("missing code block")
        else:
            checks.append(1.0)
            ref_langs = {l for l, _ in ref_blocks if l}
            stu_langs = {l for l, _ in stu_blocks if l}
            if ref_langs:
                checks.append(1.0 if ref_langs & stu_langs else 0.3)
                if not ref_langs & stu_langs:
                    notes.append(f"lang tag {ref_langs}!={stu_langs}")
    else:
        # Reference has no code: punish gratuitous code dumps.
        checks.append(0.6 if stu_blocks else 1.0)
        if stu_blocks:
            notes.append("unrequested code block")

    # Every JSON block the Student emits must actually parse - this is the
    # single most important property for tool calling.
    json_blocks = [b for l, b in stu_blocks if (l or "").lower() == "json"]
    for b in json_blocks:
        try:
            json.loads(b)
            checks.append(1.0)
        except json.JSONDecodeError:
            checks.append(0.0)
            notes.append("invalid JSON")

    # Mirror the reference's use of markdown headings / bullets.
    for pat, label in ((r"(?m)^#{1,6}\s", "headings"), (r"(?m)^\s*[-*]\s", "bullets")):
        if re.search(pat, ref):
            checks.append(1.0 if re.search(pat, student) else 0.5)
            if not re.search(pat, student):
                notes.append(f"missing {label}")

    if not checks:
        return 1.0, "no structure required"
    return sum(checks) / len(checks), ", ".join(notes) or "ok"


def score_conciseness(student: str, ref: str) -> tuple[float, str]:
    """Penalise both padding and truncation, relative to the reference."""
    if not ref.strip():
        return 1.0, "empty reference"
    ratio = len(student) / len(ref)
    if ratio < 0.3:
        return max(0.0, ratio / 0.3), f"too short ({ratio:.2f}x)"
    if ratio <= 1.6:
        return 1.0, f"{ratio:.2f}x"
    # Degrade gradually past 1.6x rather than falling off a cliff.
    return max(0.0, 1.0 - (ratio - 1.6) / 2.4), f"padded ({ratio:.2f}x)"


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------
def load_eval(path: Path, limit: int | None) -> list[dict]:
    if not path.exists():
        sys.exit(f"No eval set at {path}. Run generate_lessons.py first.")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        msgs = r.get("messages", [])
        prompt = next((m["content"] for m in msgs if m["role"] == "user"), None)
        target = next((m["content"] for m in msgs if m["role"] == "assistant"), None)
        if not prompt or not target:
            continue
        system = next((m["content"] for m in msgs if m["role"] == "system"), "")
        rows.append({
            "prompt": prompt,
            "target": target,
            "system": system,
            "skill": r.get("meta", {}).get("skill", "general"),
            "difficulty": r.get("meta", {}).get("difficulty", "medium"),
        })
    return rows[:limit] if limit else rows


def grade_one(row: dict, cfg: dict, model: str, system: str | None = None) -> dict:
    ev = cfg["eval"]
    w = cfg["rubric"]["weights"]
    ref_think, ref_answer = split_reference(row["target"])

    # A request-level system prompt overrides whatever the Modelfile baked in,
    # which is the only way to compare tags fairly: every `srini-*` tag carries
    # the lean operator profile in its SYSTEM block (measured 1998 chars, ~500
    # tokens), while the student:base / student:trained tags served by
    # serve_adapter.py carry none. Without this, the comparison measures prompts,
    # not weights.
    r = ask(
        row["prompt"],
        model=model,
        system=system or row["system"] or None,
        think=ev["think"],
        max_tokens=ev["max_tokens"],
        temperature=ev["temperature"],
    )
    if r.error:
        return {"skill": row["skill"], "error": r.error, "total": 0.0,
                "prompt": row["prompt"][:160]}

    stu_answer = r.content
    m_think = THINK_RE.search(stu_answer)
    stu_think = r.thinking or (m_think.group(1) if m_think else "")
    stu_answer_clean = THINK_RE.sub("", stu_answer).strip()

    acc, acc_n = score_accuracy(stu_answer_clean, ref_answer)
    rea, rea_n = score_reasoning(stu_think, ref_think, stu_answer_clean)
    fmt, fmt_n = score_formatting(stu_answer_clean, ref_answer)
    con, con_n = score_conciseness(stu_answer_clean, ref_answer)

    total = acc * w["accuracy"] + rea * w["reasoning"] + fmt * w["formatting"] + con * w["conciseness"]

    return {
        "skill": row["skill"],
        "difficulty": row["difficulty"],
        "prompt": row["prompt"][:160],
        "scores": {"accuracy": round(acc, 3), "reasoning": round(rea, 3),
                   "formatting": round(fmt, 3), "conciseness": round(con, 3)},
        "notes": {"accuracy": acc_n, "reasoning": rea_n,
                  "formatting": fmt_n, "conciseness": con_n},
        "total": round(total, 3),
        "passed": total >= cfg["rubric"]["pass_threshold"],
        "truncated": r.truncated,
        "tokens_per_sec": r.tokens_per_sec,
        "student_answer": stu_answer_clean[:2000],
        "student_thinking": stu_think[:1500],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default=None, help="Ollama tag to grade (default: curriculum student_model).")
    p.add_argument("--system-file", type=Path, default=None,
                   help="Send this file as the system prompt on every request, "
                        "overriding any SYSTEM baked into the tag. Use it to "
                        "compare models under identical context.")
    p.add_argument("--eval-file", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--baseline", action="store_true",
                   help="Also write reports/baseline.json for later comparison.")
    p.add_argument("--compare", type=Path, default=None,
                   help="Diff against a previous report; flags regressions.")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    cfg = yaml.safe_load(CURRICULUM.read_text(encoding="utf-8"))
    model = args.model or cfg["meta"]["student_model"]

    h = health()
    if not h["up"]:
        sys.exit(f"Ollama is not reachable at {h['host']}: {h.get('error')}\n"
                 f"Start it: powershell -ExecutionPolicy Bypass -File E:\\LocalLLM\\start-ollama.ps1")
    if model not in h["models"]:
        sys.exit(f"Model '{model}' not installed. Have: {h['models']}")

    eval_path = args.eval_file or (DATASET / "eval.jsonl")
    rows = load_eval(eval_path, args.limit or cfg["eval"]["n_eval_prompts"])
    if not rows:
        sys.exit(f"{eval_path} has no usable rows.")

    system_prompt = None
    if args.system_file:
        system_prompt = args.system_file.read_text(encoding="utf-8")
        print(f"  system prompt: {args.system_file.name} ({len(system_prompt)} "
              f"chars) - overrides whatever the tag bakes in")

    print(f"Grading {model} on {len(rows)} prompt(s) from {eval_path.name}\n")
    started = time.time()
    results = []
    for i, row in enumerate(rows, 1):
        print(f"  [{i:>3}/{len(rows)}] {row['skill']:<24} ", end="", flush=True)
        res = grade_one(row, cfg, model, system=system_prompt)
        results.append(res)
        if "error" in res:
            print(f"ERROR {res['error'][:60]}")
        else:
            flag = "PASS" if res["passed"] else "FAIL"
            print(f"{res['total']:.3f} {flag}  ({res['tokens_per_sec']} tok/s)")

    scored = [r for r in results if "error" not in r]
    if not scored:
        sys.exit("Every prompt errored - nothing to report.")

    overall = statistics.mean(r["total"] for r in scored)
    by_crit = {
        c: round(statistics.mean(r["scores"][c] for r in scored), 3)
        for c in ("accuracy", "reasoning", "formatting", "conciseness")
    }
    by_skill: dict[str, list[float]] = defaultdict(list)
    for r in scored:
        by_skill[r["skill"]].append(r["total"])
    skill_avg = {k: round(statistics.mean(v), 3) for k, v in sorted(by_skill.items())}

    thresh = cfg["rubric"]["pass_threshold"]
    weak = sorted([k for k, v in skill_avg.items() if v < thresh], key=lambda k: skill_avg[k])

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model": model,
        "rubric_version": RUBRIC_VERSION,
        "eval_file": str(eval_path),
        "n_prompts": len(rows),
        "n_errors": len(results) - len(scored),
        "overall_score": round(overall, 3),
        "pass_rate": round(sum(1 for r in scored if r["passed"]) / len(scored), 3),
        "by_criterion": by_crit,
        "by_skill": skill_avg,
        "weak_skills": weak,
        "mean_tokens_per_sec": round(statistics.mean(r["tokens_per_sec"] for r in scored), 1),
        "wall_seconds": round(time.time() - started, 1),
        "results": results,
    }

    print("\n" + "=" * 62)
    print(f"  {model}  overall {overall:.3f}   pass rate {report['pass_rate']:.0%}")
    print("=" * 62)
    for c, v in by_crit.items():
        bar = "#" * int(v * 30)
        print(f"  {c:<13} {v:.3f}  {bar}")
    print("\n  by skill:")
    for k, v in skill_avg.items():
        print(f"    {'WEAK' if v < thresh else '  ok'}  {k:<28} {v:.3f}")
    if weak:
        print(f"\n  -> target next lesson batch at: {', '.join(weak)}")
    print(f"\n  {report['mean_tokens_per_sec']} tok/s mean, {report['wall_seconds']}s total")

    out = args.out or REPORTS / f"grade_{model.replace(':', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  report: {out}")
    if args.baseline:
        bl = REPORTS / "baseline.json"
        bl.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  baseline: {bl}")

    # --- regression guard: catch catastrophic forgetting --------------------
    if args.compare:
        if not args.compare.exists():
            print(f"\n  (no comparison file at {args.compare})")
            return 0
        prev = json.loads(args.compare.read_text(encoding="utf-8"))
        # A score is only meaningful against another score from the same rubric.
        # v1 reports have no version key at all, so treat a missing one as v1.
        prev_rv = prev.get("rubric_version", 1)
        if prev_rv != RUBRIC_VERSION:
            print(f"\n  !! {args.compare.name} was scored under rubric v{prev_rv}, "
                  f"this run is v{RUBRIC_VERSION} - the delta below is not meaningful.")
            print("     Re-grade the other model under the current rubric to compare.")
        guard = cfg["eval"]["regression_guard"]
        delta = overall - prev["overall_score"]
        print(f"\n  vs {args.compare.name}: {prev['overall_score']:.3f} -> {overall:.3f} "
              f"({delta:+.3f})")
        regressed = []
        for skill, prev_v in prev.get("by_skill", {}).items():
            now_v = skill_avg.get(skill)
            if now_v is None:
                continue
            drop = prev_v - now_v
            if prev_v >= thresh and drop > guard["max_drop"]:
                regressed.append((skill, prev_v, now_v, drop))
        if regressed:
            print(f"\n  !! REGRESSION on {len(regressed)} previously-passing skill(s):")
            for s, pv, nv, d in regressed:
                print(f"       {s:<28} {pv:.3f} -> {nv:.3f}  (-{d:.3f})")
            print("     Likely catastrophic forgetting. Lower the learning rate,")
            print("     raise forgetting_guard.replay_ratio, or roll back the adapter.")
            if guard.get("enabled"):
                return 2
        else:
            print("  no regression on previously-passing skills.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
