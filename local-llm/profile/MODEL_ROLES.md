# What each local model is for

Renamed 2026-11-26: every tag is named for its **job**, not its vendor. This
file is the spec the proxy's router implements (`route_model` in
`anthropic_proxy.py`); `test_proxy_router.py` is the executable version.

Speeds are **warm** tok/s. Always warm a model before measuring — the first
cold run once reported `srini-vision:2b` at 2.1 tok/s against 129.6 warm, which
would have led to the exact wrong conclusion.

| tag | size | warm | num_ctx | placement | use it for |
|---|---|---|---|---|---|
| `srini-coder:9b` | 6.6 GB | 47 | 32768 | 81% GPU | **The default.** Code, refactors, debugging, planning, anything needing the best reasoning that fits the card at all. |
| `srini-tools:3b` | 2.2 GB | 103 | 65536 | 100% GPU | **Tool calls, structured JSON, and cited answers from retrieval.** The one to trust for external facts. |
| `srini-vision:2b` | 4.3 GB | **132** | 131072 | 100% GPU | **Images and audio** — the only tag that accepts them. Also the fastest, so it is the small/background slot. |
| `srini-draft:4b` | 3.3 GB | 78 | 65536 | 100% GPU | Fast drafts and throwaway edits. Also the training student base. |
| `srini-tools:8b` | 5.3 GB | 48 | 32768 | 74% GPU | Explicit only — see the over-trigger note below. |
| `srini-deep:35b` | 22 GB | — | 32768 | spills | Explicit only. Hard reasoning you are willing to wait minutes for. |
| `srini-bulk:30b` | 25 GB | — | 32768 | spills | Explicit only. 30B MoE, 3B active; slow but solid. |
| `srini-embed` | 274 MB | — | — | — | Embeddings (zimrag reranking). Not a chat model. |

## Which to trust for facts, and why it is not the biggest one

Measured 2026-11-25 against a real MCP retrieval tool, executions counted
server-side:

| model | called the tool | fabricated |
|---|---|---|
| `srini-vision:2b` | 6/6 | **0/10** |
| `srini-tools:3b` | 6/6 | **0/10** |
| `srini-coder:9b` | 3/6 | **2/2 on the ones it skipped** |
| `srini-draft:4b` | 0/3 | 3/3 |

So the 9B is the best *reasoner* and the worst *retriever* — it answers from
memory and invents specifics. On this machine, training 745 facts into a LoRA
gave 19% exact recall, so an uncited specific from any of these is probably
wrong. That is why a factual turn is routed **away** from the daily driver.

The 4B and 9B do call the tool reliably below ~9 kB of request content; past
that the harness's own tool schemas crowd out the directive. The proxy keeps
them capped at 9000 bytes in `ZIM_DIRECTIVE_MODELS` for that reason.

`srini-tools:8b` is excluded from automatic routing despite retrieving
correctly (4/4 factual, no prose-describing, no loops): it *over*-triggers,
running a full retrieval for "write a function that reverses a string" — 297 s
against 27-38 s for the 3b, which correctly stays silent.

## It is a swap, not a mesh

All models cannot be resident. At their baked `num_ctx` the four GPU-capable
tags need **2.0 + 4.5 + 5.2 + 6.9 = 18.6 GB** against **~6.6 GB usable** (8 GB
less the ~1.4 GB desktop compositor) — 2.8× over. Even the two smallest,
`srini-vision:2b` + `srini-tools:3b`, come to 7.2 GB and do not fit. The only
pair that co-resides is vision + draft at 6.5 GB, with nothing left for KV
growth. `OLLAMA_MAX_LOADED_MODELS` is 2.

So switching model means a **cold load**: measured 2026-11-26, 22.2 s for
`srini-tools:3b` (1.8 s warm) and 45.1 s for `srini-coder:9b`. The router is
therefore deliberately reluctant — a wrong swap costs the load *and* a weaker
answer, which is worse than a mildly wrong model. It declines far more often
than it moves.

## What the router actually does

In order, on every `/v1/messages` request:

1. **`@prefix` in the newest user turn** → that model, no questions asked.
   `@coder @code @draft @fast @tools @facts @vision @image @deep @bulk`. This
   is the only way routing reaches `@deep`/`@bulk`, and the prefix is stripped
   before the prompt reaches the model.
2. **An image or audio block anywhere in the conversation** → `srini-vision:2b`.
   Capability, not preference: every other tag silently drops the block and
   answers about nothing, which reads as a hallucination rather than an error.
3. **A short external-fact question with `zim_search` actually on offer** →
   `srini-tools:3b`. All four conditions must hold: the retrieval tool is
   present, the text is ≤400 chars, it matches a fact pattern, and it has **no**
   code signal. "what is this function doing?" matches the fact pattern too, so
   the code check runs first and wins.
4. **Otherwise, stay put.** No retrieval tool, a long body, an imperative
   ("add a dataclass here"), a filename, a traceback, a code fence — all keep
   the turn where it already is.

Two guards sit on top: a route whose target `num_ctx` cannot hold the current
prompt is declined (handing Ollama an oversized prompt is a 400, not an
answer), and any exception inside the router is swallowed so it can never take
the proxy down.

Every decision is logged to `proxy_requests.log` as `ROUTED a -> b (reason)` or
`route declined ...`. Set **`PROXY_NO_ROUTE=1`** to turn the whole thing off.

## Picking by hand

Routing never overrides a deliberate choice of launch model, and the launcher
shorthands still work:

```
cclocal               # srini-coder:9b, the default
cclocal granite3b     # srini-tools:3b
cclocal gemma         # srini-vision:2b
cclocal nemotron      # srini-bulk:30b
```

`/model` mid-session cannot resize the context window — `MAX_CONTEXT_TOKENS` is
read once at launch — so switching to a smaller-window model still 400s. The
proxy rewrites that 400 to name the prompt size, the model's `num_ctx`, and the
fix. Relaunch, or use `--bare`.
