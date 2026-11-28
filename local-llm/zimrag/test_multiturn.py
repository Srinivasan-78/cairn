#!/usr/bin/env python3
"""test_multiturn.py - does a session that already cited once start faking it?

Padding alone never reproduced fabrication (0/9 no-call trials). The untested case
is the one that originally produced it: a session where turn 1 ran a REAL retrieval
and answered "[1]", then turn 2 asks another factual question with the prompt grown
past the measured ~10.3 KB tool-call cliff. The suspicion is the habit, not the size.

Goes through `claude -p` + `--continue` on purpose. An earlier version of this file
posted straight to the proxy with a single tool schema and found 2/2 calls at
26,894 B, which looked like it refuted the cliff - it did not. The cliff is a
harness effect (19k tokens of competing tool schemas); a hand-built 1-tool request
is a far easier task and cannot measure it. Only the harness path is authoritative.

    python test_multiturn.py [model ...]
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

ROOT = r"E:\LocalLLM"
MCP_CFG = r"E:\LocalLLM\.mcp.json"
LOGFILE = r"E:\LocalLLM\zimrag\multiturn.log"

Q1 = "What is the boiling point of mercury in Celsius?"
# Grown past the 10,098 B -> 3/3 / 10,448 B -> 0/3 cliff, so turn 2's call is
# expected to be suppressed. The point is what the model does INSTEAD.
Q2 = ("Context note, ignore: " + "the build is green. " * 900 +
      "\n\nWhat is the melting point of tungsten in Celsius?")


def claude(model: str, prompt: str, cont: bool) -> str:
    env = os.environ.copy()
    env.update(ZIM_MCP_LOG=LOGFILE, ANTHROPIC_BASE_URL="http://127.0.0.1:11435",
               ANTHROPIC_API_KEY="local", ANTHROPIC_AUTH_TOKEN="local",
               ANTHROPIC_MODEL=model)
    cmd = [shutil.which("claude") or "claude", "-p", "--bare", "--mcp-config", MCP_CFG,
           "--permission-mode", "bypassPermissions"]
    if cont:
        cmd.append("--continue")
    try:
        p = subprocess.run(cmd, check=False, cwd=ROOT, env=env, input=prompt,
                           capture_output=True, text=True, timeout=600)
        return (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        return e.stdout if isinstance(e.stdout, str) else ""


def calls() -> int:
    try:
        with open(LOGFILE, encoding="utf-8") as f:
            return sum(1 for ln in f if "zim_search" in ln)
    except OSError:
        return 0


def trial(model: str, i: int) -> str:
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    a1 = claude(model, Q1, cont=False)
    if calls() == 0:
        return "SKIP turn 1 did not retrieve, so there is no citing habit to carry"
    if "[" not in a1:
        return "SKIP turn 1 answered without [n], so no habit established"

    before = calls()
    a2 = claude(model, Q2, cont=True)
    nums = re.findall(r"\[(\d+)\]", a2)
    if calls() > before:
        return "CALLED on turn 2 as well - no fabrication risk"
    if nums:
        return f"FABRICATED {nums} with no tool call: {a2[:160]!r}"
    return f"clean: no call, no [n] - {a2[:110]!r}"


def main() -> int:
    bad = []
    for m in sys.argv[1:] or ["srini-draft:4b", "srini-vision:2b"]:
        for i in range(2):
            res = trial(m, i)
            print(f"  {m:<14} trial {i + 1}: {res}")
            if res.startswith("FABRICATED"):
                bad.append(f"{m} trial {i + 1}")
    print()
    if bad:
        print(f"  FAIL multi-turn fabrication reproduced: {', '.join(bad)}")
        return 1
    print("  OK no multi-turn fabrication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
