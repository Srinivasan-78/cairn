#!/usr/bin/env python3
"""
probe_models.py - Check which local tags are fit for the Claude Code harness.

Three things decide that, and none of them are benchmark scores:

  1. does it answer at all, and how fast (tok/s, and prompt-eval latency, which
     is what a system prompt costs you on every single request)
  2. does it emit a *well-formed tool call* when given a tool - a model that
     fumbles this loops with "Invalid tool parameters" in an agent harness and
     is unusable regardless of how clever it is
  3. does it keep its reasoning out of the answer channel

Usage:
    python bench/probe_models.py
    python bench/probe_models.py --models srini-tools:8b srini-coder:9b
    python bench/probe_models.py --json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.error
import urllib.request

HOST = "http://127.0.0.1:11434"

DEFAULT_MODELS = [
    "srini-coder:9b",
    "srini-draft:4b",
    "srini-tools:8b",
    "srini-tools:3b",
    "srini-vision:2b",
]

# A deliberately unambiguous tool call: one required string argument whose value
# is stated in the prompt. Any model that cannot do this will not survive an
# agent loop.
TOOLS = [{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file from disk and return its contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "start_line": {"type": "integer"},
            },
            "required": ["path"],
        },
    },
}]

TOOL_PROMPT = "Read the file E:/LocalLLM/teacher_pipeline/curriculum.yaml. Use the tool."
SPEED_PROMPT = "In one sentence: how much VRAM can I use for a model on this machine?"


def chat(model: str, prompt: str, *, tools: list | None = None,
         think: bool = False, max_tokens: int = 200, timeout: int = 300) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": think,
        "options": {"num_predict": max_tokens, "temperature": 0.2},
    }
    if tools:
        payload["tools"] = tools
    req = urllib.request.Request(
        f"{HOST}/api/chat", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError) as e:
        return {"error": f"{type(e).__name__}: {e}"}
    data["_wall"] = time.time() - started
    return data


def placement(model: str) -> str:
    """Whether the resident copy is on the GPU or spilled to CPU.

    A model that silently runs on the CPU looks like a bad model - it is just a
    model that did not fit, or whose architecture this Ollama build cannot
    offload. Worth distinguishing before blaming the weights.
    """
    try:
        with urllib.request.urlopen(f"{HOST}/api/ps", timeout=10) as r:
            for m in json.loads(r.read()).get("models", []):
                if m.get("name") == model or m.get("model") == model:
                    total = m.get("size") or 0
                    vram = m.get("size_vram") or 0
                    if not total:
                        return "?"
                    pct = vram / total * 100
                    return "GPU" if pct > 95 else f"{pct:.0f}% GPU"
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        pass
    return "?"


def probe(model: str) -> dict:
    out: dict = {"model": model}

    # Warm up first: the first call pays model load and kernel compilation, and
    # measuring that reports a cold-start penalty as though it were throughput.
    warm = chat(model, "hi", max_tokens=8)
    if "error" in warm:
        out["error"] = warm["error"]
        return out
    out["placement"] = placement(model)

    # --- speed, and what the system prompt costs -----------------------------
    r = chat(model, SPEED_PROMPT, max_tokens=150)
    if "error" in r:
        out["error"] = r["error"]
        return out
    msg = r.get("message", {}) or {}
    eval_count = r.get("eval_count") or 0
    eval_dur = r.get("eval_duration") or 0
    prompt_count = r.get("prompt_eval_count") or 0
    prompt_dur = r.get("prompt_eval_duration") or 0
    out["tok_s"] = round(eval_count / (eval_dur / 1e9), 1) if eval_dur else 0.0
    out["prompt_tokens"] = prompt_count
    out["prompt_eval_s"] = round(prompt_dur / 1e9, 2) if prompt_dur else 0.0
    out["first_answer_s"] = round(out["prompt_eval_s"], 2)
    out["wall_s"] = round(r["_wall"], 1)
    answer = (msg.get("content") or "").strip()
    out["answer_head"] = answer[:90]
    # Reasoning leaking into the answer channel wastes tokens and confuses a
    # harness that expects content to be the answer.
    out["leaks_think"] = "<think>" in answer or "</think>" in answer

    # --- tool calling --------------------------------------------------------
    t = chat(model, TOOL_PROMPT, tools=TOOLS, max_tokens=200)
    if "error" in t:
        out["tool"] = f"ERROR {t['error'][:40]}"
        return out
    tmsg = t.get("message", {}) or {}
    calls = tmsg.get("tool_calls") or []
    if not calls:
        # Some models describe the call in prose instead of emitting one.
        prose = (tmsg.get("content") or "")
        out["tool"] = "prose" if "read_file" in prose else "none"
    else:
        fn = (calls[0].get("function") or {})
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                args = {}
        ok_name = fn.get("name") == "read_file"
        ok_path = isinstance(args, dict) and "path" in args
        no_junk = isinstance(args, dict) and set(args) <= {"path", "start_line"}
        out["tool"] = "ok" if (ok_name and ok_path and no_junk) else "malformed"
        out["tool_args"] = json.dumps(args)[:70] if isinstance(args, dict) else str(args)[:70]
    return out


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        if isinstance(s, io.TextIOWrapper):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass

    p = argparse.ArgumentParser(description="Probe local tags for harness fitness.")
    p.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    rows = []
    for m in args.models:
        print(f"probing {m} ...", file=sys.stderr)
        rows.append(probe(m))

    if args.as_json:
        print(json.dumps(rows, indent=2))
        return 0

    print(f"\n{'model':<22}{'tok/s':>7}{'prompt':>8}{'p-eval':>8}"
          f"{'tools':>10}{'placement':>11}{'think-leak':>12}")
    print("-" * 82)
    for r in rows:
        if "error" in r:
            print(f"{r['model']:<22}  ERROR {r['error'][:40]}")
            continue
        print(f"{r['model']:<22}{r['tok_s']:>7}{r['prompt_tokens']:>8}"
              f"{r['prompt_eval_s']:>7}s{r.get('tool', '?'):>10}"
              f"{r.get('placement', '?'):>11}"
              f"{'YES' if r.get('leaks_think') else 'no':>12}")
    print("\nanswers:")
    for r in rows:
        if "error" not in r:
            print(f"  {r['model']:<22} {r['answer_head']}")
            if r.get("tool_args"):
                print(f"  {'':<22} tool args: {r['tool_args']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
