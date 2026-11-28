"""Empirical sweep to find the request-size ceiling above which qwen3.5
stops calling the zim_search MCP tool. Creates no deps on proxy internals
other than reading its own log files. Windows paths only (per task notes).

Usage: python test_ceiling.py
"""
import os
import shutil
import subprocess
import uuid

ROOT = r"E:\LocalLLM"
LOGFILE = r"E:\LocalLLM\zimrag\ceiling.log"
PROXY_LOG = r"E:\LocalLLM\proxy_requests.log"
MCP_CFG = r"E:\LocalLLM\.mcp.json"
BASE_Q = "What is the boiling point of mercury in Celsius?"

FILLER_UNIT = ("In unrelated background, note that cartography, agronomy, "
               "and lepidoptery are each large fields with centuries of "
               "literature, none of which bears on this question. ")


def build_question(pad_chars):
    if pad_chars <= 0:
        return BASE_Q
    filler = (FILLER_UNIT * (pad_chars // len(FILLER_UNIT) + 1))[:pad_chars]
    return BASE_Q + " [context-padding, ignore: " + filler + "]"


def run_trial(model, pad_chars, trial_idx, timeout=600):
    """Returns dict: called(bool), fabricated(bool), actual_bytes(int|None),
    timed_out(bool), text(str)."""
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    marker = f"MARK {model} pad={pad_chars} trial={trial_idx} {uuid.uuid4().hex[:8]}"
    with open(PROXY_LOG, "a", encoding="utf-8") as f:
        f.write(marker + "\n")

    question = build_question(pad_chars)
    env = os.environ.copy()
    env["ZIM_MCP_LOG"] = LOGFILE
    env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:11435"
    env["ANTHROPIC_API_KEY"] = "local"
    env["ANTHROPIC_AUTH_TOKEN"] = "local"
    env["ANTHROPIC_MODEL"] = model

    # Long questions blow past the Windows/cmd.exe command-line length limit
    # when passed as an argv item, so feed the prompt over stdin instead.
    cmd = [
        shutil.which("claude") or "claude", "-p",
        "--bare", "--mcp-config", MCP_CFG,
        "--permission-mode", "bypassPermissions",
    ]
    timed_out = False
    text = ""
    try:
        proc = subprocess.run(
            cmd, check=False, cwd=ROOT, env=env, input=question, capture_output=True,
            text=True, timeout=timeout,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as e:
        timed_out = True
        text = (e.stdout or "") if isinstance(e.stdout, str) else ""

    called = os.path.exists(LOGFILE)

    actual_bytes = None
    try:
        with open(PROXY_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        start = None
        for i, line in enumerate(lines):
            if marker in line:
                start = i
                break
        if start is not None:
            for line in lines[start + 1:]:
                if "length=" in line:
                    actual_bytes = int(line.split("length=")[1].split()[0].rstrip(","))
                    break
    except (OSError, ValueError, IndexError):
        pass

    fabricated = ("[1]" in text) or ("[1 " in text)

    dump_dir = r"E:\LocalLLM\zimrag\ceiling_dumps"
    os.makedirs(dump_dir, exist_ok=True)
    safe_model = model.replace(":", "_")
    with open(os.path.join(dump_dir, f"{safe_model}_pad{pad_chars}_t{trial_idx}.txt"),
              "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "called": called,
        "fabricated": fabricated,
        "actual_bytes": actual_bytes,
        "timed_out": timed_out,
        "text_snippet": text[:400],
    }


def sweep(model, pad_sizes, n_trials=3):
    results = {}
    for pad in pad_sizes:
        trials = []
        for t in range(n_trials):
            r = run_trial(model, pad, t)
            trials.append(r)
            print(f"[{model} pad={pad} trial={t}] called={r['called']} "
                  f"bytes={r['actual_bytes']} fabricated={r['fabricated']} "
                  f"timeout={r['timed_out']}")
        results[pad] = trials
    return results


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    model = args[0] if args else "srini-draft:4b"
    rest = args[1:]
    n_trials = 3
    if rest and rest[0].startswith("t="):
        n_trials = int(rest[0][2:])
        rest = rest[1:]
    pads = [int(x) for x in rest] if rest else [0]
    sweep(model, pads, n_trials=n_trials)
