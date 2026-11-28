#!/usr/bin/env python3
"""
ask_local_llm.py - Bridge between Claude (the Teacher) and the local model (the Student).

Claude calls this to send prompts to the local Ollama server, inspect the
Student's reasoning, and grade it programmatically. It is also imported as a
module by teacher_pipeline/grade_student.py.

Why not just curl: Qwen3.5 is a hybrid-reasoning model. Ollama returns its
chain-of-thought in a separate `thinking` field, and `num_predict` is shared
between thinking and the final answer - so a small token budget yields an empty
`content`. This wrapper handles that, separates the two channels, and reports
timing so we can see the real cost of each call.

CLI:
    python ask_local_llm.py "What is a LoRA adapter?"
    python ask_local_llm.py --think "Bat and ball cost $1.10..." --max-tokens 2000
    python ask_local_llm.py --model srini-coder:9b --json "Write a Python LRU cache"
    echo "long prompt" | python ask_local_llm.py --stdin --json
    python ask_local_llm.py --persona "How much VRAM can I spend right now?"

Module:
    from ask_local_llm import ask
    r = ask("prompt", model="srini-draft:4b", think=True)
    r.content, r.thinking, r.tokens_per_sec
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

_DEFAULT_MODELS_DIR = Path(r"E:\LocalLLM\models")
if _DEFAULT_MODELS_DIR.exists():
    os.environ.setdefault("OLLAMA_MODELS", str(_DEFAULT_MODELS_DIR))

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
if not OLLAMA_HOST.startswith("http"):
    OLLAMA_HOST = f"http://{OLLAMA_HOST}"

DEFAULT_MODEL = os.environ.get("LOCAL_LLM_MODEL", "srini-draft:4b")

MODEL_ALIASES = {
    "4b": "srini-draft:4b",
    "9b": "srini-coder:9b",
    "35b": "srini-deep:35b",
    "gemma": "srini-vision:2b",
    "granite": "srini-tools:3b",
    "granite3b": "srini-tools:3b",
    "granite8b": "srini-tools:8b",
    "nemotron": "srini-bulk:30b",
    "30b": "srini-bulk:30b",
}


def resolve_model(name: str) -> str:
    """Normalize shorthand model aliases (e.g. '9b', 'gemma', 'nemotron')."""
    cleaned = (name or "").strip()
    return MODEL_ALIASES.get(cleaned.lower(), cleaned)

# In thinking mode the model routinely spends 500-1500 tokens reasoning before
# emitting a single token of answer. Budget for that or `content` comes back "".
DEFAULT_MAX_TOKENS_THINK = 2048
DEFAULT_MAX_TOKENS_PLAIN = 1024


@dataclass
class LocalReply:
    """One response from the Student, with both channels kept separate."""

    content: str
    thinking: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    wall_seconds: float = 0.0
    tokens_per_sec: float = 0.0
    truncated: bool = False
    error: str | None = None
    messages: list = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)


def persona(*, include_lifeos: bool = True) -> str:
    """The operator profile, as a system prompt.

    The tags built by profile/build_persona_models.py already carry this in their
    Modelfile; this is for sending it to one that does not - a freshly exported
    `qwen3.5-student:vN`, say - without rebuilding anything.
    """
    prof_dir = str(Path(__file__).parent / "profile")
    if prof_dir not in sys.path:
        sys.path.insert(0, prof_dir)
    try:
        from build_persona_models import system_block
    except ImportError as e:
        raise SystemExit(f"profile/build_persona_models.py not importable: {e}") from e
    return system_block(include_lifeos=include_lifeos)


def _post(path: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        f"{OLLAMA_HOST}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ask(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    think: bool = False,
    max_tokens: int | None = None,
    temperature: float = 0.6,
    top_p: float = 0.95,
    num_ctx: int | None = None,
    timeout: int = 900,
    history: list | None = None,
) -> LocalReply:
    """Send one prompt to the local model and return both channels separately.

    `think=False` disables the reasoning channel, which is what you want for
    fast deterministic checks. `think=True` exposes the chain-of-thought in
    `.thinking` - that trace is the raw material for distillation.
    """
    if max_tokens is None:
        max_tokens = DEFAULT_MAX_TOKENS_THINK if think else DEFAULT_MAX_TOKENS_PLAIN

    model = resolve_model(model)
    messages = list(history or [])
    if system:
        if messages and messages[0].get("role") == "system":
            messages[0] = {"role": "system", "content": system}
        else:
            messages.insert(0, {"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    options = {
        "num_predict": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    if num_ctx:
        options["num_ctx"] = num_ctx

    payload = {
        "model": model,
        "messages": messages,
        "think": think,
        "stream": False,
        "options": options,
    }

    started = time.time()
    try:
        data = _post("/api/chat", payload, timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        return LocalReply("", "", model, error=f"HTTP {e.code}: {body}",
                          wall_seconds=round(time.time() - started, 2))
    except urllib.error.URLError as e:
        return LocalReply("", "", model,
                          error=f"URLError ({OLLAMA_HOST}): {e.reason} - is Ollama running? Try: ollama-start",
                          wall_seconds=round(time.time() - started, 2))
    except (OSError, json.JSONDecodeError, ValueError) as e:  # connection refused, timeout, ...
        return LocalReply("", "", model, error=f"{type(e).__name__}: {e}",
                          wall_seconds=round(time.time() - started, 2))

    wall = time.time() - started
    msg = data.get("message", {}) or {}
    content = (msg.get("content") or "").strip()
    thinking = (msg.get("thinking") or "").strip()

    eval_count = data.get("eval_count", 0) or 0
    eval_dur = data.get("eval_duration", 0) or 0
    tps = round(eval_count / (eval_dur / 1e9), 1) if eval_dur else 0.0

    # If we hit the ceiling and produced only reasoning, the answer was cut off.
    truncated = eval_count >= max_tokens and not content

    messages.append({"role": "assistant", "content": content})

    return LocalReply(
        content=content,
        thinking=thinking,
        model=data.get("model", model),
        prompt_tokens=data.get("prompt_eval_count", 0) or 0,
        completion_tokens=eval_count,
        wall_seconds=round(wall, 2),
        tokens_per_sec=tps,
        truncated=truncated,
        messages=messages,
    )


def health() -> dict:
    """Server reachability plus which models are available and resident."""
    out = {"host": OLLAMA_HOST, "up": False, "version": None, "models": [], "loaded": []}
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/version", timeout=5) as r:
            out["version"] = json.loads(r.read())["version"]
            out["up"] = True
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=10) as r:
            out["models"] = [m["name"] for m in json.loads(r.read()).get("models", [])]
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/ps", timeout=10) as r:
            out["loaded"] = [
                {"name": m["name"], "size_gb": round(m.get("size", 0) / 1e9, 2),
                 "ctx": m.get("context_length")}
                for m in json.loads(r.read()).get("models", [])
            ]
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def telos_context() -> str:
    """Compact LifeOS TELOS + Projects context from ~/.config/LIFEOS/USER."""
    user_dir = Path.home() / ".config" / "LIFEOS" / "USER"
    parts = []
    for rel in (Path("TELOS") / "PRINCIPAL_TELOS.md", Path("PROJECTS.md")):
        fp = user_dir / rel
        if fp.exists():
            parts.append(fp.read_text(encoding="utf-8", errors="replace").strip())
    return "\n\n".join(parts)


def log_cli_memory(prompt: str, reply: LocalReply) -> None:
    """Append a compact Q&A record to LifeOS USER/MEMORY/local_cli_log.jsonl."""
    mem_dir = Path.home() / ".config" / "LIFEOS" / "USER" / "MEMORY"
    try:
        mem_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": reply.model,
            "prompt": prompt[:500],
            "response": (reply.content or "")[:1000],
            "tokens": reply.completion_tokens,
            "tok_s": reply.tokens_per_sec,
        }
        with (mem_dir / "local_cli_log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> int:
    # The Windows console defaults to cp1252, and these models emit plenty that
    # it cannot encode - the model's own arithmetic ("~=" as U+2248) is enough
    # to crash print() mid-answer. Reconfigure rather than mangle the text.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass

    p = argparse.ArgumentParser(description="Ask the local LLM (Ollama) a question.")
    p.add_argument("prompt", nargs="*", help="Prompt text.")
    p.add_argument("--stdin", action="store_true", help="Read the prompt from stdin.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--system", default=None, help="Optional system prompt.")
    p.add_argument("--persona", action="store_true",
                   help="Prepend the operator profile (profile/USER_PROFILE.md) "
                        "as the system prompt. Unnecessary for the profiled tags, "
                        "which already embed it.")
    p.add_argument("--no-lifeos", action="store_true",
                   help="Omit LifeOS operating contract when using --persona.")
    p.add_argument("--telos", action="store_true",
                   help="Prepend LifeOS PRINCIPAL_TELOS.md + PROJECTS.md context.")
    p.add_argument("--log-memory", action="store_true",
                   help="Append this Q&A turn to LifeOS USER/MEMORY/local_cli_log.jsonl.")
    p.add_argument("--think", action="store_true", help="Enable the reasoning channel.")
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--num-ctx", type=int, default=None)
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Emit the full structured reply (for programmatic grading).")
    p.add_argument("--health", action="store_true", help="Probe the server and exit.")
    args = p.parse_args()

    if args.health:
        print(json.dumps(health(), indent=2))
        return 0

    prompt = sys.stdin.read() if args.stdin else " ".join(args.prompt)
    if not prompt.strip():
        p.error("no prompt given (pass text, or use --stdin)")

    system = args.system
    if args.telos:
        tc = telos_context()
        if tc:
            system = f"{tc}\n\n{system}" if system else tc
    if args.persona:
        p_txt = persona(include_lifeos=not args.no_lifeos)
        system = f"{p_txt}\n\n{system}" if system else p_txt

    r = ask(
        prompt,
        model=args.model,
        system=system,
        think=args.think,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        num_ctx=args.num_ctx,
        timeout=args.timeout,
    )
    if args.log_memory and not r.error:
        log_cli_memory(prompt, r)

    if args.as_json:
        print(r.to_json())
        return 1 if r.error else 0

    if r.error:
        print(f"ERROR: {r.error}", file=sys.stderr)
        return 1
    if r.thinking:
        print(f"--- thinking ({len(r.thinking)} chars) ---\n{r.thinking}\n--- answer ---")
    print(r.content or "(empty - the token budget was spent on reasoning; raise --max-tokens)")
    print(
        f"\n[{r.model} | {r.completion_tokens} tok | {r.tokens_per_sec} tok/s | {r.wall_seconds}s"
        + (" | TRUNCATED" if r.truncated else "") + "]",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
