#!/usr/bin/env python3
"""Acceptance harness: does a real `claude -p` session, talking to a local
model through anthropic_proxy.py, actually execute mcp__zimrag__zim_search
instead of answering from memory and inventing a "[n]" citation?

Ground truth is server-side only: zimrag/mcp_calls.log gets one line per
real zim_search execution (written by mcp_server.py's _log()). Model text
is never trusted on its own - we delete the log, run one session, and read
the log back.

Usage:
    python zimrag\\test_session.py [--trials N] [--models m1,m2] [--questions 0,2]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # E:\LocalLLM\zimrag
ROOT = HERE.parent                              # E:\LocalLLM  (cwd: .mcp.json is project-scoped)
LOG_FILE = HERE / "mcp_calls.log"

PROXY_ENV = {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:11435",
    "ANTHROPIC_API_KEY": "local",
    "ANTHROPIC_AUTH_TOKEN": "local",
}

DEFAULT_MODELS = ["srini-vision:2b", "srini-tools:3b", "srini-coder:9b"]

# (question, expected substrings (any-of), expect a tool call at all)
QUESTIONS = [
    ("What is the boiling point of mercury in Celsius?", ["356.7"], True),
    ("What is the atomic number of tungsten?", ["74"], True),
    ("In what year was the Treaty of Westphalia signed?", ["1648"], True),
    ("What does the git reset --hard command do to the working tree?",
     ["discard", "overwrit", "reset", "match"], True),
    ("Write a Python function that reverses a string.", [], False),  # control: no retrieval expected
]

CITATION_RE = re.compile(r"\[\d+\]")


def run_session(model: str, question: str, timeout: int = 600) -> dict:
    """Delete the log, run one real claude -p session, read the log back."""
    LOG_FILE.unlink(missing_ok=True)

    env = os.environ.copy()
    env.update(PROXY_ENV)
    env["ANTHROPIC_MODEL"] = model

    cmd = ["claude", "-p", question, "--permission-mode", "bypassPermissions"]
    try:
        proc = subprocess.run(
            cmd, check=False, cwd=str(ROOT), env=env, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        answer = proc.stdout.strip()
        error = proc.stderr.strip() if proc.returncode != 0 else ""
    except subprocess.TimeoutExpired:
        answer, error = "", f"TIMEOUT after {timeout}s"

    log_lines = []
    if LOG_FILE.exists():
        log_lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    tool_called = len(log_lines) > 0

    return {
        "answer": answer,
        "error": error,
        "tool_called": tool_called,
        "log_lines": log_lines,
    }


def evaluate(question: str, expected: list[str], expect_tool: bool, result: dict) -> dict:
    answer = result["answer"]
    has_citation = bool(CITATION_RE.search(answer))
    tool_called = result["tool_called"]
    correct = (not expected) or any(e.lower() in answer.lower() for e in expected)
    fabricated = has_citation and not tool_called  # cited without ever retrieving
    unexpected_call = tool_called and not expect_tool
    return {
        "tool_called": tool_called,
        "has_citation": has_citation,
        "fabricated": fabricated,
        "correct": correct,
        "unexpected_call": unexpected_call,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--models", type=str, default=",".join(DEFAULT_MODELS))
    ap.add_argument("--questions", type=str, default=None,
                     help="comma-separated indices into QUESTIONS, e.g. 0,2,4")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.questions:
        idxs = [int(i) for i in args.questions.split(",")]
        questions = [QUESTIONS[i] for i in idxs]
    else:
        questions = QUESTIONS

    rows = []  # one dict per (model, question, trial)
    for model in models:
        for question, expected, expect_tool in questions:
            for trial in range(args.trials):
                t0 = time.time()
                result = run_session(model, question, timeout=args.timeout)
                dt = time.time() - t0
                ev = evaluate(question, expected, expect_tool, result)
                row = {
                    "model": model, "question": question, "trial": trial,
                    "dt": dt, "expect_tool": expect_tool,
                    **result, **ev,
                }
                rows.append(row)
                tag = "CALLED" if row["tool_called"] else "no-call"
                fab = " FABRICATED" if row["fabricated"] else ""
                unexp = " UNEXPECTED-CALL" if row["unexpected_call"] else ""
                err = f" ERR={row['error']}" if row["error"] else ""
                print(f"[{model}] {question[:50]!r} trial={trial} "
                      f"{tag} cite={row['has_citation']} correct={row['correct']} "
                      f"{dt:.1f}s{fab}{unexp}{err}")

    print_matrix(rows, models, questions)


def print_matrix(rows, models, questions):
    print("\n=== MATRIX (model x question) ===")
    header = f"{'model':<16}{'question':<55}{'called':>8}{'fabricated':>12}{'correct':>9}{'unexp-call':>12}"
    print(header)
    print("-" * len(header))
    for model in models:
        for question, _expected, _expect_tool in questions:
            subset = [r for r in rows if r["model"] == model and r["question"] == question]
            if not subset:
                continue
            n = len(subset)
            called = sum(r["tool_called"] for r in subset)
            fab = sum(r["fabricated"] for r in subset)
            correct = sum(r["correct"] for r in subset)
            unexp = sum(r["unexpected_call"] for r in subset)
            qshort = question[:53]
            print(f"{model:<16}{qshort:<55}{called}/{n:>5}{fab:>9}/{n:<3}{correct}/{n:>5}{unexp:>9}/{n}")


if __name__ == "__main__":
    main()
