"""
anthropic_proxy.py - Transparent multi-threaded proxy between Claude Code and Ollama.

Features:
1. Intercepts /v1/messages and injects "thinking": {"type": "disabled"} if not present,
   preventing Qwen 3.5 from hanging in runaway reasoning chains.
2. Full Model Alias Resolver for Claude Code's `/model` command:
   - "4b", "haiku", "claude-3-5-haiku", etc. -> "srini-draft:4b"
   - "9b", "sonnet", "opus", "claude-3-5-sonnet", etc. -> "srini-coder:9b"
3. Augments /v1/models with aliases so Claude Code's model discovery finds them.
4. Supports live Server-Sent Events (SSE) streaming with immediate chunk forwarding.
5. Logs all requests to E:\\LocalLLM\\proxy_requests.log for instant diagnostics.
"""

import datetime
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OLLAMA_TARGET = "http://127.0.0.1:11434"
LOG_FILE = r"E:\LocalLLM\proxy_requests.log"
STDERR_LOG_FILE = r"E:\LocalLLM\proxy_stderr.log"
LOG_MAX_BYTES = 2 * 1024 * 1024  # 2 MB, then rotate
# Auto-exit after 30m of no requests (0 disables). Matches OLLAMA_KEEP_ALIVE.
IDLE_TIMEOUT_S = int(os.environ.get("PROXY_IDLE_TIMEOUT", "1800"))
_LAST_ACTIVITY = time.monotonic()
_ACTIVE_REQUESTS = 0
_ACTIVITY_LOCK = threading.Lock()


def _touch_activity(delta: int = 0) -> None:
    global _LAST_ACTIVITY, _ACTIVE_REQUESTS
    with _ACTIVITY_LOCK:
        _LAST_ACTIVITY = time.monotonic()
        _ACTIVE_REQUESTS = max(0, _ACTIVE_REQUESTS + delta)

# Alias targets, overridable from argv so the launcher stays the single source of
# truth for the lineup. Any real Ollama tag bypasses these entirely.
BIG_MODEL = "srini-coder:9b"
SMALL_MODEL = "srini-vision:2b"

# Tool schemas were 72.9% of a measured 26,218-token request (2026-11-25, captured
# straight off the wire). These are harness features a local model cannot use
# productively - cloud task queues, cron, git worktrees, inter-agent messaging,
# design sync - and their schemas alone are ~12.7k tokens, nearly half the prompt.
# Claude Code still offers them; Ollama just never sees them.
#
# The set is FIXED on purpose: Ollama's KV prefix cache only hits when the prefix
# is byte-identical, so a varying filter would cost more than it saves.
# Set PROXY_KEEP_ALL_TOOLS=1 to disable when debugging a tool call.
DROP_TOOLS = frozenset({
    "DesignSync", "Workflow", "ScheduleWakeup", "SendMessage", "ListAgents",
    "CronCreate", "CronDelete", "CronList",
    "EnterWorktree", "ExitWorktree",
    "TaskCreate", "TaskUpdate", "TaskGet", "TaskList", "TaskOutput", "TaskStop",
    "ReportFindings", "WebSearch", "NotebookEdit", "Monitor",
})
KEEP_ALL_TOOLS = os.environ.get("PROXY_KEEP_ALL_TOOLS") == "1"

# Generous because a cold load of a model larger than VRAM is slow, not broken.
UPSTREAM_TIMEOUT = int(os.environ.get("PROXY_UPSTREAM_TIMEOUT", "1800"))

# Reinforce zimrag's tool at the request level, because a baked Modelfile SYSTEM
# block is not reliably delivered: srini-vision:2b's template is literally
# "{{ .Prompt }}" and never renders .System, so its operator profile is dropped.
# Measured 2026-11-25: with only the baked profile gemma never called zim_search;
# with this same text in the request's system field it called it correctly, while
# still skipping it for code generation. Only injected when the tool is present.
ZIM_DIRECTIVE = (
    "You have an mcp__zimrag__zim_search tool over 441 GB of offline Kiwix archives (Wikipedia, "
    "Stack Overflow, devdocs, Arch wiki, libretexts, Gutenberg). For any question of "
    "external fact - documentation, science, history, software behaviour, definitions "
    "- you MUST call mcp__zimrag__zim_search first and answer from the passages it returns. "
    "Do NOT answer such questions from memory. Skip the tool only for code generation "
    "and questions about the current conversation or files.\n"
    # Measured: "what does git reset --hard do" was 0/2 on every model. A question
    # about a command's semantics reads as a coding task, not a lookup, so the
    # trigger list has to name it outright.
    "This includes what a command, flag or API does - 'what does git reset --hard "
    "do', 'what does chmod 755 mean', 'what does Python's dict.setdefault return'. "
    "Looking up documented behaviour is a lookup, not a coding task; only WRITING "
    "code is exempt.\n"
    "Its passages arrive numbered [1], [2], [3]. Every factual claim you take from "
    "them MUST end with that bracketed number, like: mercury boils at 356.73 C [1]. "
    "Never write [n] for a passage no tool returned."
)
# Citation-FORMAT rules deliberately live in the tool result instead (see
# mcp_server.py). Adding them here took srini-vision:2b from 6/6 calling to 2/4, with
# one fabrication - the third time a longer directive measurably hurt compliance.
# The tool result is the last thing read before the answer, is only present when
# retrieval actually happened, and costs nothing in the system prompt.

# Repeated on the latest user turn, where a small model actually reads it.
#
# Keep this SHORT. Two attempts at a cleverer version made things worse: an
# "otherwise write UNVERIFIED" escape hatch, then the same split into explicit
# (a)/(b) branches, both produced self-contradicting answers - srini-vision:2b cited
# [1] AND appended UNVERIFIED in the same reply, and once claimed "I called
# zim_search" when the server log proved it had not. Small models follow one
# plain rule far better than a conditional. Fabrication is prevented by
# ZIM_DIRECTIVE_MODELS instead: the two allowlisted models measured 0/10 fake
# citations with exactly this simple wording.
ZIM_REMINDER = (
    "[reminder] If answering this needs an external fact, call "
    "mcp__zimrag__zim_search first and cite its numbered passages as [n]. "
    "Only write [n] for a passage a tool actually returned. "
    "Ignore this for coding tasks or questions about this conversation."
)

# Only models measured to ACT on the directive get it. Trials on the real
# question "boiling point of mercury in Celsius" through a full Claude Code
# session (2026-11-25), counting actual zim_search executions in
# zimrag/mcp_calls.log:
#
# 32 sessions, 2 trials per (model, question), tool executions counted in
# zimrag/mcp_calls.log across mercury boiling point / tungsten atomic number /
# Treaty of Westphalia / git reset --hard / a reverse-a-string control:
#
#   srini-vision:2b      6/6 called on factual, 0/10 fabricated   <- best
#   srini-tools:3b   6/6 called on factual, 0/10 fabricated   <- best
#   srini-coder:9b      3/6 called, and 2/2 FABRICATED on mercury <- excluded
#   srini-draft:4b      0/3 called, 3/3 fabricated                <- excluded
#
# Both exclusions are for the same reason: the directive is a net loss on a model
# that will not act on it, because the citation demand only teaches it to fake
# "[1]". srini-coder:9b is the painful one - it is the best-quality model here, but it
# "knows" famous constants and answers from weights while claiming a source.
# Adding an UNVERIFIED escape hatch did not help 4b (still 3/3). Without the
# directive both answer from memory plainly and cite nothing, which is the honest
# failure. For corpus-backed answers from 9b, use ask_zim.py instead: it forces
# retrieval rather than asking, and always cites.
#
# Unmeasured models default to NO directive - a missing citation is recoverable,
# a fabricated one is not. Measure a model before adding it here.
# model prefix -> largest request (bytes) at which that model still ACTS on the
# directive; 0 means no limit. srini-draft:4b is not incapable, it has a context
# ceiling: measured 2026-11-25 on "boiling point of mercury in Celsius",
#
#   prompt  4,070 B (--bare --mcp-config)  -> 2/2 called, correct, cited
#   prompt 46,936 B (trimmed + no skills)  -> 0/2 called
#   prompt 55,639 B (trimmed tools)        -> 0/2 called
#   prompt ~105,000 B (full session)       -> 0/2 called, 2/2 fabricated "[1]"
#
# So a 4B cannot hold the instruction salient against 19k tokens of tool schemas,
# but handles it fine in a bare session. Giving it the directive only below the
# ceiling buys real retrieval in bare sessions without the fabrication that the
# directive causes in big ones. 12000 leaves ~8 KB of conversation growth above
# the known-good 4,070 while staying far below the known-bad 46,936.
# 9000 is measured, not guessed. Binary search, 3 trials per size, tool executions
# counted in the MCP server's own log:
#
#   srini-draft:4b  10,098 B -> 3/3 called | 10,448 B -> 0/3 called
#   srini-coder:9b  10,129 B -> 3/3 called | 10,479 B -> 0/3 called
#
# One shared cliff inside a 350-byte window, identical for both. An earlier guess
# of 12000 sat ABOVE it, so the directive was injected across 10,300-12,000 where
# the model had already stopped acting on it - a no-op. 9000 leaves ~1,100 bytes
# of per-turn margin below the lowest confirmed 3/3 point.
#
# Re-probed 2026-11-25 at 4 trials: 24,098 B -> 0/4, 46,898 B -> 0/4, so the one
# non-monotonic point in the original sweep (46,898 B -> 1/2) was 2-trial noise.
# Measure this ONLY through `claude -p`. Posting a padded request with a single
# tool schema straight to this proxy gives 4/4 calls at 46,898 B - the cliff is
# competition from ~19k tokens of harness tool schemas, not byte count, and bytes
# are merely a good proxy for schema bulk in a real session.
#
# srini-tools:3b is keyed exactly, NOT by a bare "srini-tools" prefix: srini-tools:8b
# retrieves correctly too (4/4 factual, and its reputation for prose-describing
# tool calls did not reproduce) but it OVER-triggers in bare sessions, running a
# full retrieval for "write a function that reverses a string" - 297 s against
# 27-38 s for gemma/granite-3b, which stay correctly silent. The 3b is faster and
# clean, so the 8b gains nothing here and costs minutes on coding turns.
ZIM_DIRECTIVE_MODELS = {"srini-vision": 0, "srini-tools:3b": 0,
                        "srini-draft:4b": 9000, "srini-coder:9b": 9000}

def log_event(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}\n"
    try:
        # Rotate: once the log exceeds LOG_MAX_BYTES, rename it and start fresh.
        try:
            if os.path.getsize(LOG_FILE) > LOG_MAX_BYTES:
                rotated = LOG_FILE + ".1"
                if os.path.exists(rotated):
                    os.remove(rotated)
                os.rename(LOG_FILE, rotated)
        except OSError:
            pass
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass
    if sys.stdout is not None:
        try:
            sys.stdout.write(entry)
            sys.stdout.flush()
        except (OSError, AttributeError):
            pass


_CACHE_LOCK = threading.Lock()
_tag_cache_at: float = 0.0
_tag_cache_names: frozenset[str] = frozenset()


def installed_models() -> frozenset[str]:
    """Ollama's real tags, cached 60s so a freshly pulled model needs no restart."""
    global _tag_cache_at, _tag_cache_names
    now = time.monotonic()
    with _CACHE_LOCK:
        cached_names = _tag_cache_names
        stale = not cached_names or now - _tag_cache_at > 60
    if stale:
        try:
            with urllib.request.urlopen(f"{OLLAMA_TARGET}/api/tags", timeout=5) as r:
                names = frozenset(m["name"] for m in json.load(r).get("models", []))
            if names:
                with _CACHE_LOCK:
                    _tag_cache_names = names
                    _tag_cache_at = now
                return names
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError) as e:
            log_event(f"WARN could not list Ollama tags, alias mapping only: {e}")
    return cached_names


_ctx_cache: dict[str, int] = {}


def model_num_ctx(tag: str) -> int:
    """num_ctx baked into a tag, cached. Used only to explain a context-length 400."""
    with _CACHE_LOCK:
        if tag in _ctx_cache:
            return _ctx_cache[tag]
    val = 0
    try:
        req = urllib.request.Request(
            f"{OLLAMA_TARGET}/api/show",
            data=json.dumps({"model": tag}).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            for line in (json.load(r).get("parameters") or "").splitlines():
                if line.startswith("num_ctx"):
                    val = int(line.split()[1])
                    break
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError, IndexError):
        pass
    if val > 0:
        with _CACHE_LOCK:
            _ctx_cache[tag] = val
    return val

def resolve_model_name(raw_name: str) -> "str | None":
    """Pass real Ollama tags through untouched; map only Anthropic/shorthand aliases.

    The old version had a hardcoded qwen-only table, so every other model in the
    lineup (gemma, granite, nemotron) was silently served as srini-coder:9b.
    """
    name = (raw_name or "").strip()
    installed = installed_models()

    # The path every cclocal session takes: the launcher exports real tags.
    if name in installed:
        return name
    if name.lower() in installed:
        return name.lower()

    low = name.lower()
    if low in ("4b", "student", "small", "fast") or "haiku" in low:
        return SMALL_MODEL

    # A tag-shaped name we do not have is a real mistake - a /model picker entry
    # for a model that was never pulled. Substituting hides it; None becomes a 404.
    if ":" in low and installed:
        return None
    return BIG_MODEL


# ---------------------------------------------------------------------------
# Purpose routing - send the question to the model it is actually for
# ---------------------------------------------------------------------------
# Each tag is named for one job; profile/MODEL_ROLES.md is the written spec.
#
# This is a SWAP, not a mesh. At their baked num_ctx the four GPU-capable tags
# need 2.0 + 4.5 + 5.2 + 6.9 = 18.6 GB against ~6.6 GB usable (8 GB less the
# ~1.4 GB desktop compositor), so they cannot be co-resident - 2.8x over. Even
# the two smallest, srini-vision:2b + srini-tools:3b, are 7.2 GB and do not fit;
# the only pair that does is vision + draft at 6.5 GB. OLLAMA_MAX_LOADED_MODELS
# is 2, so a switch is usually a cold load: measured 2026-11-26, 22.2 s for
# srini-tools:3b (1.8 s warm) and 45.1 s for srini-coder:9b.
#
# So routing is deliberately RELUCTANT. It moves only on a signal worth 20-45 s
# and otherwise leaves the turn on whatever is already warm. A wrong swap costs
# both the load AND a weaker answer, which is worse than a mildly wrong model.
NO_ROUTE = os.environ.get("PROXY_NO_ROUTE") == "1"

# Never chosen automatically. srini-deep:35b and srini-bulk:30b spill to system
# RAM and answer in minutes; srini-tools:8b runs a full retrieval even for
# "write a function that reverses a string" (297 s, against 27-38 s for the 3b).
# Ambushing a session with any of these is worse than not routing at all, so
# they are reachable only by an explicit @prefix.
ROUTE_NEVER_AUTO = frozenset({"srini-deep:35b", "srini-bulk:30b", "srini-tools:8b"})

# "@vision what is in this image" - an explicit request beats every heuristic.
ROUTE_PREFIXES = {
    "@coder": "srini-coder:9b", "@code": "srini-coder:9b",
    "@draft": "srini-draft:4b", "@fast": "srini-draft:4b",
    "@tools": "srini-tools:3b", "@facts": "srini-tools:3b",
    "@vision": "srini-vision:2b", "@image": "srini-vision:2b",
    "@deep": "srini-deep:35b", "@bulk": "srini-bulk:30b",
}

# A question about the outside world - what zim_search and srini-tools:3b exist
# for. Measured 2026-11-25: on factual prompts granite-3b and gemma called the
# tool 6/6 with 0/10 fabrications, while the 9b called 3/6 and FABRICATED 2/2.
# Moving a factual turn off the 9b buys correctness, not just speed.
FACT_MARKERS = re.compile(
    r"\b(?:what|who|when|where|which|why)\s+(?:is|are|was|were|did|does|do)\b"
    r"|\b(?:define|definition of|look up|cite|according to|meaning of|"
    r"history of|documentation for)\b",
    re.IGNORECASE)

# Anything that makes this a coding turn, where the 9b earns its size and a swap
# actively hurts. Checked BEFORE the fact markers: "what is this function doing"
# matches both, and it is a code question.
CODE_MARKERS = re.compile(
    r"```|[A-Za-z]:\\\\|\b(?:def|class|import|async|function|refactor|implement|"
    r"debug|traceback|stacktrace|compile|lint|typecheck|pytest|commit|git|"
    r"dockerfile|regex|exception)\b|\.(?:py|ps1|sh|json|ya?ml|ts|js|md|toml)\b",
    re.IGNORECASE)

# A long body is a working session with context, not a lookup. Routing one to a
# 3B both loses that context and pays the load.
ROUTE_MAX_FACT_CHARS = 400


def _user_payload(data: dict) -> "tuple[str, bool]":
    """Text of the LAST user turn, and whether any turn carries image/audio."""
    text, media = "", False
    for m in (data.get("messages") or []):
        if not isinstance(m, dict):
            continue
        content = m.get("content")
        is_user = m.get("role") == "user"
        if isinstance(content, str):
            if is_user:
                text = content
        elif isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                btype = b.get("type")
                if btype in ("image", "audio", "input_audio"):
                    media = True
                elif btype == "text" and is_user:
                    text = b.get("text") or ""
    return text, media


def _strip_route_prefix(data: dict, prefix: str) -> None:
    """Drop a leading "@tools" from the last user turn, in place.

    It addresses the router, not the model - and a 3B asked to answer
    "@tools what is a mutex" may well answer about the token.
    """
    for m in reversed(data.get("messages") or []):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        content = m.get("content")
        if isinstance(content, str) and content.lstrip().lower().startswith(prefix):
            m["content"] = content.lstrip()[len(prefix):].lstrip()
            return
        if isinstance(content, list):
            for b in content:
                if (isinstance(b, dict) and b.get("type") == "text"
                        and (b.get("text") or "").lstrip().lower().startswith(prefix)):
                    b["text"] = b["text"].lstrip()[len(prefix):].lstrip()
                    return
        return      # only ever the newest user turn


def _pick(current: str, data: dict, installed: frozenset) -> "tuple[str, str, bool]":
    """(tag, reason, was_explicit). Returns `current` unchanged when unsure."""
    text, media = _user_payload(data)
    stay = (current, "", False)

    def usable(tag):
        return tag in installed and tag != current

    # 1. Explicit @prefix. The only route to the never-auto models.
    head = text.lstrip().lower()
    for pre, tag in ROUTE_PREFIXES.items():
        if head.startswith(pre):
            return (tag, f"explicit {pre}", True) if usable(tag) else stay

    # 2. Capability, not preference: srini-vision:2b is the only tag that accepts
    #    image or audio. Any other model drops the block and answers about
    #    nothing at all, which reads as a hallucination rather than an error.
    if media and usable("srini-vision:2b"):
        return "srini-vision:2b", "image/audio input", False

    # 3. External-fact question with retrieval actually on offer.
    tool_names = {t.get("name") for t in (data.get("tools") or [])
                  if isinstance(t, dict)}
    if (any(n and n.endswith("zim_search") for n in tool_names)
            and text and len(text) <= ROUTE_MAX_FACT_CHARS
            and not CODE_MARKERS.search(text)
            and FACT_MARKERS.search(text)
            and usable("srini-tools:3b")):
        return "srini-tools:3b", "external-fact question", False

    return stay


def route_model(current: str, data: dict, prompt_bytes: int) -> "tuple[str, str]":
    """Refine an already-resolved tag to the one this request is for.

    Returns (tag, reason); reason is "" when nothing moved. Never raises - a
    router that 500s the proxy is worse than one that declines to route.
    """
    if NO_ROUTE or not current:
        return current, ""
    try:
        tag, reason, explicit = _pick(current, data, installed_models())
        if tag == current or not reason:
            return current, ""
        if not explicit and tag in ROUTE_NEVER_AUTO:
            return current, ""
        # A route into a smaller window is a 400, not an answer. num_ctx is 0
        # when /api/show could not be read, in which case do not second-guess it.
        nc = model_num_ctx(tag)
        need = prompt_bytes // 4 + 512          # 512 = room for the reply
        if nc and need > nc:
            log_event(f"route declined {current} -> {tag} ({reason}): prompt "
                      f"~{need} tok exceeds its num_ctx {nc}")
            return current, ""
        if explicit:
            _strip_route_prefix(data, reason.split(" ", 1)[1])
        return tag, reason
    except Exception as e:  # noqa: BLE001 - router failure must never crash proxy
        log_event(f"WARN router failed, keeping {current}: {e}")
        return current, ""


def trim_messages_to_ctx(data: dict, nc: int, body: bytes | None = None) -> tuple[bytes, int]:
    """Drop oldest middle messages (and trim oversized system text if needed) to fit ``nc``."""
    if body is None:
        body = json.dumps(data).encode("utf-8")
    budget_bytes = int(nc * 0.85) * 4
    if not nc or len(body) <= budget_bytes:
        return body, 0
    msgs = data.get("messages")
    dropped = 0
    if isinstance(msgs, list) and len(msgs) > 2:
        while len(msgs) > 2 and len(body) > budget_bytes:
            msgs.pop(1)
            dropped += 1
            body = json.dumps(data).encode("utf-8")
    # If still over budget on a 1-2 turn prompt (e.g. /LifeOS), trim oversized system text.
    if len(body) > budget_bytes and "system" in data:
        over = len(body) - budget_bytes + 512
        sys_val = data["system"]
        if isinstance(sys_val, str) and len(sys_val) > 512:
            keep = max(512, len(sys_val) - over)
            data["system"] = sys_val[:keep] + "\n...[trimmed to fit num_ctx]"
            dropped += 1
            body = json.dumps(data).encode("utf-8")
        elif isinstance(sys_val, list):
            for blk in reversed(sys_val):
                if isinstance(blk, dict) and isinstance(blk.get("text"), str) and len(blk["text"]) > 1024:
                    cut = min(over, len(blk["text"]) - 512)
                    blk["text"] = blk["text"][: len(blk["text"]) - cut] + "\n...[trimmed]"
                    over -= cut
                    dropped += 1
                    if over <= 0:
                        break
            body = json.dumps(data).encode("utf-8")
    return body, dropped


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            try:
                content_length = max(0, int(self.headers.get("Content-Length", 0)))
            except ValueError:
                content_length = 0
            body = self.rfile.read(content_length)

            if self.path.startswith("/v1/messages/count_tokens"):
                resp_data = json.dumps({"input_tokens": max(1, len(body) // 4)}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(resp_data)
                self.wfile.flush()
                log_event(f"POST {self.path} -> 200 (local estimate {len(body) // 4} tok)")
                return
            req_model = ""
            resolved_model = ""

            if self.path.startswith("/v1/messages"):
                try:
                    data = json.loads(body.decode("utf-8"))
                    req_model = data.get("model", "")
                    
                    # 1. Strip runaway thinking loop. Forced, not just defaulted: an
                    # explicit enable is the exact case that hangs Qwen 3.5, and a
                    # thinking budget cannot fit an 8k window anyway.
                    # `or {}` guards an explicit null, which would otherwise raise and
                    # fall through to forwarding the body with thinking still on.
                    if (data.get("thinking") or {}).get("type") == "enabled":
                        log_event("overriding thinking=enabled -> disabled")
                    data["thinking"] = {"type": "disabled"}
                        
                    # 2. Resolve model name
                    resolved_model = resolve_model_name(req_model)
                    if resolved_model is None:
                        log_event(f"POST {self.path} -> 404 model not installed: {req_model}")
                        err = json.dumps({"type": "error", "error": {
                            "type": "not_found_error",
                            "message": f"model '{req_model}' is not installed in Ollama. "
                                       f"Run: ollama pull {req_model}"}}).encode("utf-8")
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(err)))
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self.wfile.write(err)
                        self.wfile.flush()
                        return
                    data["model"] = resolved_model

                    # 2b. Route to the model this question is actually for. Runs
                    # before the tool and directive steps below, because both key
                    # off the final model. See route_model: it declines far more
                    # often than it moves, since a switch is a 22-45 s cold load.
                    routed, why = route_model(resolved_model, data, content_length)
                    if why:
                        log_event(f"ROUTED {resolved_model} -> {routed} ({why})")
                        resolved_model = routed
                        data["model"] = routed

                    # 3. Drop tool schemas a local model cannot use (see DROP_TOOLS).
                    if not KEEP_ALL_TOOLS and isinstance(data.get("tools"), list):
                        kept = [t for t in data["tools"]
                                if t.get("name") not in DROP_TOOLS]
                        if len(kept) != len(data["tools"]):
                            saved = len(json.dumps(data["tools"])) - len(json.dumps(kept))
                            dropped = len(data["tools"]) - len(kept)
                            data["tools"] = kept
                            log_event(f"dropped {dropped} unusable tools, "
                                      f"~{saved // 4} tokens saved")

                    # 4. If zimrag's tool is on offer, make sure the model is told to
                    # use it (see ZIM_DIRECTIVE). Appended, never replacing, so the
                    # client's own system prompt survives.
                    tool_names = {t.get("name") for t in (data.get("tools") or [])
                                  if isinstance(t, dict)}
                    caps = [cap for pre, cap in ZIM_DIRECTIVE_MODELS.items()
                            if pre in resolved_model]
                    if (any(n and n.endswith("zim_search") for n in tool_names)
                            and caps
                            and (max(caps) == 0 or content_length <= max(caps))):
                        sysf = data.get("system")
                        if isinstance(sysf, str):
                            if "zim_search" not in sysf:
                                data["system"] = sysf + "\n\n" + ZIM_DIRECTIVE
                        elif isinstance(sysf, list):
                            if not any("zim_search" in (b.get("text") or "")
                                       for b in sysf if isinstance(b, dict)):
                                sysf.append({"type": "text", "text": ZIM_DIRECTIVE})
                        else:
                            data["system"] = ZIM_DIRECTIVE

                        # A system-block directive alone is not enough in a real
                        # session: Claude Code's own prompt is ~26k tokens and 45
                        # tool schemas, and a 4B model buried the instruction -
                        # it answered mercury's boiling point from memory and
                        # invented a "[1]" with no tool call at all. Small models
                        # weight the most recent turn far more heavily, so repeat
                        # it there. Appended as its own block so the user's text
                        # is never rewritten.
                        msgs = data.get("messages")
                        if isinstance(msgs, list):
                            for m in reversed(msgs):
                                if m.get("role") != "user":
                                    continue
                                c = m.get("content")
                                if isinstance(c, str):
                                    m["content"] = [{"type": "text", "text": c},
                                                    {"type": "text", "text": ZIM_REMINDER}]
                                elif isinstance(c, list) and not any(
                                        b.get("text") == ZIM_REMINDER
                                        for b in c if isinstance(b, dict)):
                                    c.append({"type": "text", "text": ZIM_REMINDER})
                                break
                        log_event("zim_search offered -> directive + turn reminder")

                    nc = model_num_ctx(resolved_model)
                    body, dropped_msgs = trim_messages_to_ctx(data, nc)
                    if dropped_msgs:
                        log_event(f"trimmed {dropped_msgs} old message(s) to fit num_ctx={nc}")
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    log_event(f"POST {self.path} -> 400 invalid JSON: {e}")
                    err = json.dumps({"type": "error", "error": {
                        "type": "invalid_request_error",
                        "message": f"Invalid JSON request body: {e}"}}).encode("utf-8")
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(err)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(err)
                    self.wfile.flush()
                    return

            # Flag substitutions loudly: a silent rewrite hid the gemma/granite bug.
            note = " ALIASED" if resolved_model and req_model != resolved_model else ""
            log_event(f"POST {self.path} length={content_length} model={req_model}->{resolved_model}{note}")

            headers = {}
            for k, v in self.headers.items():
                # transfer-encoding must go too: we always send a fixed Content-Length,
                # and forwarding a stale "chunked" alongside it is malformed.
                if k.lower() not in ("host", "content-length", "connection",
                                     "accept-encoding", "transfer-encoding"):
                    headers[k] = v
            headers["Content-Length"] = str(len(body))
            headers["Host"] = "127.0.0.1:11434"

            req = urllib.request.Request(
                f"{OLLAMA_TARGET}{self.path}",
                data=body,
                headers=headers,
                method="POST"
            )

            try:
                _touch_activity(+1)
                t0 = time.monotonic()
                # 300s was not enough: nemotron is 25 GB against 8 GB of VRAM, so a
                # cold load spills ~17 GB to RAM and the first token can take many
                # minutes. The proxy gave up before Ollama had finished loading.
                with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    is_sse = "text/event-stream" in content_type

                    self.send_response(resp.status)
                    for k, v in resp.headers.items():
                        if k.lower() not in ("transfer-encoding", "content-length", "connection"):
                            self.send_header(k, v)
                    
                    if is_sse:
                        self.send_header("Connection", "close")
                        self.end_headers()
                        in_tok = out_tok = 0
                        while True:
                            line = resp.readline()
                            if not line:
                                break
                            if line.startswith(b"data: "):
                                try:
                                    ev = json.loads(line[6:])
                                    u = ev.get("usage") or (ev.get("message") or {}).get("usage")
                                    if isinstance(u, dict):
                                        in_tok = u.get("input_tokens", in_tok) or in_tok
                                        out_tok = u.get("output_tokens", out_tok) or out_tok
                                except (json.JSONDecodeError, TypeError, ValueError):
                                    pass
                            self.wfile.write(line)
                            self.wfile.flush()
                        dt = max(0.01, time.monotonic() - t0)
                        tok_info = f" in={in_tok} out={out_tok} ({out_tok / dt:.1f} tok/s, {dt:.1f}s)" if out_tok else f" ({dt:.1f}s)"
                        log_event(f"POST {self.path} -> 200 SSE stream completed{tok_info}")
                    else:
                        resp_data = resp.read()
                        self.send_header("Content-Length", str(len(resp_data)))
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self.wfile.write(resp_data)
                        self.wfile.flush()
                        dt = max(0.01, time.monotonic() - t0)
                        log_event(f"POST {self.path} -> {resp.status} length={len(resp_data)} ({dt:.1f}s)")

            except urllib.error.HTTPError as e:
                err_data = e.read()
                # Ollama's context-length 400 says nothing about which number is
                # wrong. /model switches the model but cannot update
                # CLAUDE_CODE_MAX_CONTEXT_TOKENS, which is read once at launch, so
                # this fires exactly when the new model's window is smaller.
                if e.code == 400 and b"context length" in err_data:
                    nc = model_num_ctx(resolved_model)
                    err_data = json.dumps({"type": "error", "error": {
                        "type": "invalid_request_error",
                        "message": (
                            f"prompt is ~{len(body) // 4} tokens but {resolved_model} "
                            f"has num_ctx={nc or 'unknown'}. /model cannot resize the "
                            f"window mid-session (CLAUDE_CODE_MAX_CONTEXT_TOKENS is set "
                            f"at launch), so relaunch with `cclocal {resolved_model}`, "
                            f"or use `cclocal --bare` which cuts the system prompt from "
                            f"~25.6k tokens to ~1k.")}}).encode("utf-8")
                log_event(f"POST {self.path} -> HTTPError {e.code}: {err_data.decode('utf-8', errors='replace')}")
                self.send_response(e.code)
                for k, v in e.headers.items():
                    if k.lower() not in ("transfer-encoding", "content-length", "connection"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(err_data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(err_data)
                self.wfile.flush()
            finally:
                _touch_activity(-1)

        except Exception as e:  # noqa: BLE001 - top-level HTTP handler boundary
            log_event(f"POST {self.path} -> Exception: {e}")
            try:
                self.send_response(500)
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            except OSError:
                pass

    def do_GET(self):
        try:
            req = urllib.request.Request(f"{OLLAMA_TARGET}{self.path}", method="GET")
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read()
                
                # If /v1/models is requested, augment with aliases
                if self.path.startswith("/v1/models"):
                    try:
                        data = json.loads(resp_data.decode("utf-8"))
                        if isinstance(data, dict) and "data" in data:
                            existing = {m.get("id") for m in data["data"]}
                            for alias in ("4b", "9b", "haiku", "sonnet", "opus"):
                                if alias not in existing:
                                    data["data"].append({
                                        "id": alias,
                                        "object": "model",
                                        "created": 1795537894,
                                        "owned_by": "local"
                                    })
                            resp_data = json.dumps(data).encode("utf-8")
                    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                        pass

                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "content-length", "connection"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(resp_data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(resp_data)
                self.wfile.flush()
                log_event(f"GET {self.path} -> {resp.status}")
        except Exception as e:  # noqa: BLE001 - top-level HTTP handler boundary
            log_event(f"GET {self.path} -> Exception: {e}")
            try:
                self.send_response(500)
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            except OSError:
                pass

    def log_message(self, format, *args):
        pass

class Proxy(ThreadingHTTPServer):
    # Windows SO_REUSEADDR lets a second proxy bind a port the first still holds,
    # so two would race on 11435 and requests would land on either one.
    allow_reuse_address = False

def _idle_watchdog(server: Proxy, timeout_s: int) -> None:
    if timeout_s <= 0:
        return
    while True:
        time.sleep(min(30, max(1, timeout_s)))
        with _ACTIVITY_LOCK:
            idle_for = time.monotonic() - _LAST_ACTIVITY
            busy = _ACTIVE_REQUESTS > 0
        if not busy and idle_for >= timeout_s:
            log_event(f"Idle timeout ({timeout_s}s) reached; shutting down proxy")
            server.shutdown()
            return


def _install_stderr_logger() -> None:
    def _hook(exc_type, exc_val, exc_tb):
        import traceback
        msg = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        try:
            with open(STDERR_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}]\n{msg}\n")
        except OSError:
            pass
        log_event(f"UNHANDLED {exc_type.__name__}: {exc_val}")
    sys.excepthook = _hook


def run(port=11435):
    _install_stderr_logger()
    _touch_activity(0)
    log_event(f"Starting anthropic_proxy on port {port} -> {OLLAMA_TARGET} "
              f"(big={BIG_MODEL}, small={SMALL_MODEL}, idle_timeout={IDLE_TIMEOUT_S}s)")
    try:
        server = Proxy(("127.0.0.1", port), ProxyHandler)
    except OSError as e:
        log_event(f"FATAL cannot bind 127.0.0.1:{port} - already in use? {e}")
        sys.exit(1)
    if IDLE_TIMEOUT_S > 0:
        t = threading.Thread(target=_idle_watchdog, args=(server, IDLE_TIMEOUT_S), daemon=True)
        t.start()
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11435
    if len(sys.argv) > 2:
        BIG_MODEL = sys.argv[2]
    if len(sys.argv) > 3:
        SMALL_MODEL = sys.argv[3]
    run(port)
