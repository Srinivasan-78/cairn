#!/usr/bin/env python3
"""test_commandq.py - do command/flag questions trigger retrieval?

Factual questions ("boiling point of mercury") trigger reliably; questions about
what a command or flag does triggered only ~1/4, because the tool description
listed "factual, reference, or documentation knowledge" and a CLI flag does not
obviously read as any of those. mcp_server.py's description now names command-line
tools, flags and options explicitly. This measures whether that moved the rate.

    python test_commandq.py [model ...]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = r"E:\LocalLLM"
MCP_CFG = r"E:\LocalLLM\.mcp.json"
LOGFILE = r"E:\LocalLLM\zimrag\commandq.log"

QUESTIONS = [
    "What does git reset --hard do?",
    "What does the tar -x flag do?",
    "What does chmod 755 mean?",
    "What does rsync --delete do?",
]


def ran(model: str, prompt: str) -> bool:
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    env = os.environ.copy()
    env.update(ZIM_MCP_LOG=LOGFILE, ANTHROPIC_BASE_URL="http://127.0.0.1:11435",
               ANTHROPIC_API_KEY="local", ANTHROPIC_AUTH_TOKEN="local",
               ANTHROPIC_MODEL=model)
    cmd = [shutil.which("claude") or "claude", "-p", "--bare", "--mcp-config", MCP_CFG,
           "--permission-mode", "bypassPermissions"]
    try:
        subprocess.run(cmd, check=False, cwd=ROOT, env=env, input=prompt,
                       capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        pass
    return os.path.exists(LOGFILE)


def main() -> int:
    for m in sys.argv[1:] or ["srini-draft:4b", "srini-vision:2b"]:
        hits = 0
        for q in QUESTIONS:
            ok = ran(m, q)
            hits += ok
            print(f"  {m:<14} {'CALLED' if ok else 'silent':<7} {q}")
        print(f"  {m:<14} -> {hits}/{len(QUESTIONS)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
