# Brief for a second teaching agent

You are co-authoring training data for a local model. Another agent (Claude Code,
"Agent A") owns the curriculum, grading and training runs. You are **Agent B**:
you produce lesson data to the spec below. Read this whole file before writing
anything — the filters and calibration numbers are not negotiable and most of
them were learned by getting them wrong.

---

## The setup, in one paragraph

A local Qwen3.5-4B is fine-tuned with QLoRA in small increments ("lessons") on
`E:\LocalLLM`. Machine: RTX 4060 Ti with **8 GB VRAM, ~6.6 GB usable** (the
Windows desktop compositor holds ~1.4 GB), Ryzen 7 5700X, 64 GB RAM. Inference
runs on Windows via Ollama; training runs in WSL2 because Unsloth and
bitsandbytes are unreliable on native Windows. The operator's main project is
**repo2graph** — a Python 3.11+ code-graph and MCP server. Its authoritative
checkout is **`E:\Github\repo2graph` (v5.0.0)**; the copy at
`C:\Users\Srini\code\repo2graph` is two major versions stale, so never quote
versions, flags or paths from it.

## Hard constraints — breaking these corrupts shared state

1. **Never run training.** One 8 GB GPU; a second concurrent run OOMs and can
   leave a half-written adapter. Agent A runs `run-lesson.ps1`. You never do.
2. **Never write to** `dataset/*.jsonl`, `adapters/`, or
   `adapters/lesson_ledger.json`. Those are shared state with a fingerprint
   ledger; concurrent writes desynchronise it.
3. **Write exactly one file:** `lessons/lesson_<NNN>_agentb.json`. Pick an NNN
   above 100 so it cannot collide (`lesson_101_agentb.json`, `102`, ...).
   Agent A ingests it.
4. **Never run** `generate_lessons.py ingest` — ingestion mutates the dataset and
   the ledger. Hand over the file; Agent A ingests.
5. If you need a port, do not use **11434** (Ollama) or **11435** (an inference
   proxy and the adapter server both use it).

## The file format

```json
{
  "lesson": 101,
  "author": "agent-b",
  "domain": "Agentic Python tooling for code-intelligence systems",
  "notes": "One paragraph: what this batch targets and why.",
  "examples": [
    {
      "skill": "python_stack",
      "difficulty": "medium",
      "instruction": "The user's question, verbatim as they would ask it.",
      "thinking": "Your reasoning, first person, working the problem. This is trained on - it is not commentary about the answer.",
      "output": "The answer the model should learn to give."
    }
  ]
}
```

## The quality filters your examples must survive

These run on ingest. Anything that fails is silently dropped into
`dataset/rejected.jsonl`, so a batch can shrink without warning.

| rule | value | consequence if you ignore it |
|---|---|---|
| `min_chars` on `output` | **120** | shorter answers are dropped |
| `max_chars` on `output` | **8000** | longer answers are dropped |
| `require_thinking` | true | an example with no `thinking` is dropped — but see the warning below, because the filter only checks *presence* |
| reject refusals | — | never write "I can't help with that" |
| reject placeholders | — | no `TODO`, `...`, "your code here" |
| `max_per_skill_ratio` | **0.40** | no skill may exceed 40% of the batch, or the excess is cut |
| dedupe | MinHash Jaccard **≥ 0.85**, 5-word shingles | near-identical examples collapse to one |
| holdout | **0.20** | 1 in 5 of your examples becomes eval data, unseen in training |

**Known filter flaw, work around it:** a correct bare tool call like
`{"model": "x", "limit": 15}` is ~40 characters and gets dropped by the 120-char
minimum — for `tool_call_format`, the single highest-value skill. Either skip
that skill or write examples where the *correct* answer legitimately includes
prose (for example, a request whose second half the given tools cannot satisfy,
where the right answer is one call plus a statement of what is missing).

## The `thinking` field is trained on — it is not metadata

`train_on_responses_only` computes loss across the whole assistant turn,
**including the think block**. So whatever you put there is what the model learns
"reasoning" looks like. This is the easiest place in the whole spec to go wrong,
because no filter can catch it: `require_thinking` only checks that the field is
non-empty.

Two examples in the first Agent B batch were dropped at ingest for this. Their
`thinking` read:

> "Work through extract_file_ast MCP call. Schema: file_path, max_depth,
> node_types, include_spans. Numbers: 4, 45, 3, 1, 10, 80, 2, 540."

That is a note-to-self listing the numbers used, not reasoning — and training on
it teaches the model that thinking means reciting figures. Both were in
already-passing skills, so dropping them cost little, but a batch of those would
actively damage the reasoning score (currently the weakest criterion at 0.25
weight).

**What a usable trace looks like:** first person, working the problem in the order
you actually worked it — what the question is really asking, which constraint
binds, what you ruled out and why, the arithmetic as you did it. Aim for **300+
characters** and never below **150**. Agent A's batch averages 1022; yours
averaged 385, which is fine, but the floor matters more than the mean.

## Calibration — the part that was learned the hard way

Earlier batches averaged **837 characters and 5.4 distinct numbers** per answer,
while the eval references average **1335 characters and 7.7 numbers**. The model
faithfully learned to be shorter and less specific than what it is graded
against: numeric agreement fell 0.669 → 0.455 and answer length collapsed to
0.41x. Recalibrating fixed most of it.

**So: every `output` you write should be 1200–1900 characters with at least 8
distinct numbers, and every number must be load-bearing and derived in the
open.** Padding with filler numbers is worse than having few.

The upper bound is deliberately generous. Eval references run from 135 to **2675**
characters (mean 1335), and the measured failure was *undershooting*, not
overshooting — so landing at 1800 is fine and landing at 900 is not. The band
started at 1700 and was widened after Agent A's own batch settled naturally at a
mean of 1622 with several examples near 1900.

## What to teach, and what not to bother teaching

Five graded lessons measured the same pattern every time: training moved **style**
(conciseness +0.5, formatting +0.25) and did **not** move substance (accuracy
negative in all five; exact identifier recall 19%). Facts live in the system
prompt and in retrieval, not in the weights.

**Write examples that teach procedure and shape, carried on correct specifics:**

- how to decide, in what order, with what verification step
- the exact flag, tensor name, config key or signature — never a vague gesture
- showing the arithmetic rather than asserting a number
- naming a failure mode and the control that catches it
- saying plainly when something cannot be done with the tools at hand

**Do not** write examples whose value is "the model should memorise this fact".
That has been measured and does not work.

## Your assigned skills

Agent A takes the three weakest skills — `localllm_ops` (0.423),
`supply_chain` (0.435) and `agentic_planning` (0.442) — because they depend on
the measurement history it holds. **You take:**

Scores below are from the most recent grading run; the pass threshold is **0.70**.

| skill | what it means | current | priority |
|---|---|---|---|
| `python_stack` | Modern Python 3.11+: type hints, `pathlib`, dataclasses, narrow excepts, **explicit `encoding=` on every read** (the default is cp1252 on Windows and this has caused real bugs), docstrings that say *why* | **0.490** | **highest — failing, and the one you own** |
| `static_analysis` | tree-sitter / AST reasoning: node types, traversal, queries, mapping symbols to definitions | **no eval rows** | high — your examples create the eval coverage, so write them carefully |
| `tool_call_format` | Exact tool/MCP call JSON: right name, only declared params, valid JSON, no prose wrapping the call | 0.716 | low — just passed; don't regress it |
| `structured_extraction` | Output matching an exact schema: no extra keys, correct types, stable field order | 0.814 | low — maintain, don't over-invest |

So: weight the batch toward `python_stack` and `static_analysis` (up to the 40%
cap each), with a few of the other two to hold the line.

## House style the examples should model

Answer directly; do not emit `<think>` blocks in the `output`. Show the
arithmetic for any hardware or cost claim. Verify with `make lint`,
`make typecheck`, `make test` (cheapest first) before claiming a change works.
Conventional-commit titles phrased as statements. Never add co-author or
"generated by" trailers to commits. Never claim something works without having
verified it; say plainly when a step failed or was skipped.

## Deliverable

One file, `lessons/lesson_1NN_agentb.json`, with **16–25 examples**, no skill over
40% of the batch, each `output` 1200–1900 characters with ≥8 distinct numbers,
each with a real `thinking` trace. Then tell the operator it is ready — Agent A
ingests, trains and grades it, and reports which skills moved.

Self-check before handing over: valid JSON, every example has all five keys, no
output under 1200 or over 1900 characters, no placeholders, no refusals, and no
two examples that are near-duplicates of each other.
