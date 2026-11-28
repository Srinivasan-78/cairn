#!/usr/bin/env python3
"""Self-check for anthropic_proxy's purpose router. No Ollama needed.

    python test_proxy_router.py

The router decides which model answers, and a wrong decision costs a 22-45 s
cold load plus a weaker answer, so the cases that must NOT route matter as much
as the ones that must.
"""

import anthropic_proxy as p

INSTALLED = frozenset({
    "srini-coder:9b", "srini-draft:4b", "srini-deep:35b",
    "srini-tools:3b", "srini-tools:8b", "srini-vision:2b", "srini-bulk:30b",
})
CODER = "srini-coder:9b"
ZIM = [{"name": "mcp__zimrag__zim_search"}]


def req(text, tools=None, image=False, role="user"):
    content = [{"type": "text", "text": text}]
    if image:
        content.insert(0, {"type": "image", "source": {"type": "base64", "data": "x"}})
    body = {"messages": [{"role": role, "content": content}]}
    if tools:
        body["tools"] = tools
    return body


def pick(body, current=CODER):
    return p._pick(current, body, INSTALLED)


fails: list[str] = []


def check(label, got, want):
    if got != want:
        fails.append(f"{label}: got {got!r}, want {want!r}")


# --- capability: only vision takes image/audio -----------------------------
tag, why, _ = pick(req("what is in this picture?", image=True))
check("image routes to vision", tag, "srini-vision:2b")

# An image while already on vision must not thrash back and forth.
tag, why, _ = pick(req("and this one?", image=True), current="srini-vision:2b")
check("image already on vision stays", (tag, why), ("srini-vision:2b", ""))

# --- external-fact questions ----------------------------------------------
tag, why, _ = pick(req("what is a mutex?", tools=ZIM))
check("fact + zim routes to tools:3b", tag, "srini-tools:3b")

tag, why, _ = pick(req("who was Ada Lovelace?", tools=ZIM))
check("fact phrasing 2", tag, "srini-tools:3b")

# Retrieval not on offer -> routing buys nothing, the 3b would just guess.
tag, why, _ = pick(req("what is a mutex?"))
check("fact without zim stays", (tag, why), (CODER, ""))

# A coding turn that happens to start with "what is" is NOT a lookup.
tag, why, _ = pick(req("what is this function doing?\n```py\ndef f(): pass\n```", tools=ZIM))
check("code fence beats fact marker", (tag, why), (CODER, ""))

tag, why, _ = pick(req("what is the traceback telling me?", tools=ZIM))
check("traceback stays on coder", (tag, why), (CODER, ""))

tag, why, _ = pick(req("what does resolve_model do in anthropic_proxy.py?", tools=ZIM))
check("a .py filename stays on coder", (tag, why), (CODER, ""))

# A long body is a working session, not a lookup.
tag, why, _ = pick(req("what is a mutex? " + "context " * 100, tools=ZIM))
check("long body stays", (tag, why), (CODER, ""))

# Not a question at all.
tag, why, _ = pick(req("add a dataclass here", tools=ZIM))
check("imperative stays", (tag, why), (CODER, ""))

# --- explicit @prefix -----------------------------------------------------
tag, why, explicit = pick(req("@tools what is a semaphore?"))
check("@tools routes", (tag, explicit), ("srini-tools:3b", True))

tag, why, explicit = pick(req("@deep plan this migration"))
check("@deep reaches a never-auto model", (tag, explicit), ("srini-deep:35b", True))

# Never-auto models must be unreachable without the prefix.
for never in p.ROUTE_NEVER_AUTO:
    assert never not in (
        pick(req("what is a mutex?", tools=ZIM))[0],
        pick(req("what is in this?", image=True))[0],
    ), f"{never} was reachable automatically"

# The prefix addresses the router and must not survive into the prompt.
body = req("@tools what is a semaphore?")
p._strip_route_prefix(body, "@tools")
check("prefix stripped", body["messages"][0]["content"][0]["text"],
      "what is a semaphore?")

body = {"messages": [{"role": "user", "content": "@vision describe it"}]}
p._strip_route_prefix(body, "@vision")
check("prefix stripped from str content", body["messages"][0]["content"], "describe it")

# --- last user turn wins, and assistant turns are not read ----------------
body = {"messages": [
    {"role": "user", "content": "what is a mutex?"},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "now refactor my pytest suite"},
], "tools": ZIM}
check("newest turn decides", pick(body)[:2], (CODER, ""))

text, media = p._user_payload({"messages": [
    {"role": "assistant", "content": [{"type": "image", "source": {}}]}]})
check("image in any turn counts", media, True)

# --- guards ---------------------------------------------------------------
# num_ctx too small for the prompt -> decline rather than hand Ollama a 400.
_real_ctx, _real_installed = p.model_num_ctx, p.installed_models
p.model_num_ctx = lambda tag: 4096
p.installed_models = lambda: INSTALLED
tag, why = p.route_model(CODER, req("what is a mutex?", tools=ZIM), prompt_bytes=400_000)
check("declines a route that would not fit", (tag, why), (CODER, ""))

# Unknown num_ctx (0) must not block a route.
p.model_num_ctx = lambda tag: 0
tag, why = p.route_model(CODER, req("what is a mutex?", tools=ZIM), prompt_bytes=400_000)
check("num_ctx unknown still routes", tag, "srini-tools:3b")

# A router that raises must never take the proxy down with it.
p.installed_models = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
tag, why = p.route_model(CODER, req("what is a mutex?", tools=ZIM), 100)
check("router failure is contained", (tag, why), (CODER, ""))

p.model_num_ctx, p.installed_models = _real_ctx, _real_installed

# Kill switch.
p.NO_ROUTE = True
tag, why = p.route_model(CODER, req("what is in this?", image=True), 100)
check("PROXY_NO_ROUTE disables routing", (tag, why), (CODER, ""))
p.NO_ROUTE = False

# Malformed bodies must not raise.
for junk in ({}, {"messages": None}, {"messages": [None]},
             {"messages": [{"role": "user", "content": None}]},
             {"messages": [{"role": "user", "content": [None]}]}):
    p._user_payload(junk)

# --- proxy guards: cloud-only WebSearch drop + context trimming -----------
check("WebSearch/NotebookEdit/Monitor dropped",
      all(t in p.DROP_TOOLS for t in ("WebSearch", "NotebookEdit", "Monitor")), True)

big_body = {
    "messages": [
        {"role": "user", "content": "first " + "a" * 200},
        {"role": "assistant", "content": "mid1 " + "b" * 2000},
        {"role": "user", "content": "mid2 " + "c" * 2000},
        {"role": "user", "content": "latest " + "d" * 200},
    ]
}
_, trimmed = p.trim_messages_to_ctx(big_body, 400)
check("trim_messages_to_ctx drops middle turns",
      (trimmed, len(big_body["messages"]),
       big_body["messages"][0]["content"].startswith("first"),
       big_body["messages"][-1]["content"].startswith("latest")),
      (2, 2, True, True))

small_body = {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "ok"}]}
_, not_trimmed = p.trim_messages_to_ctx(small_body, 0)
check("trim_messages_to_ctx skips when num_ctx=0", not_trimmed, 0)

single_turn = {"system": "keep " + "x" * 10000, "messages": [{"role": "user", "content": "hi"}]}
trimmed_b, sys_trimmed = p.trim_messages_to_ctx(single_turn, 400)
check("trim_messages_to_ctx trims oversized system on 1-turn", (sys_trimmed > 0, len(trimmed_b) <= 400 * 4), (True, True))

# Detached/hidden Windows launch has sys.stdout = None -> log_event must not raise.
import sys as _sys

_old_out = _sys.stdout
try:
    _sys.stdout = None
    p.log_event("test log_event with stdout=None")
finally:
    _sys.stdout = _old_out

def test_router_and_guards() -> None:
    assert not fails, "Failures:\n" + "\n".join(fails)


if __name__ == "__main__":
    if fails:
        print(f"FAIL {len(fails)} case(s):")
        for f in fails:
            print("  -", f)
        raise SystemExit(1)
    print("ok - router & guards: 27 cases pass")
