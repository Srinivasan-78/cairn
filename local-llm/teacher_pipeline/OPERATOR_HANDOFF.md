# Handoff: running the local-model training loop

You are taking over as **Agent A** for `E:\LocalLLM` — you own the curriculum,
ingestion, training, grading and the ledger. A previous agent built this and
measured everything below; the numbers are real measurements from this machine,
not estimates. Read this whole file before running anything that writes.

A companion file, `AGENT_BRIEF.md`, is the spec for a *second* agent that only
authors lesson data. If a second agent is helping, give it that file and keep
ingestion and training to yourself — there is one 8 GB GPU and one dataset.

---

## 1. The machine, and the constraint behind every decision

RTX 4060 Ti, **8 GB VRAM, ~6.6 GB usable** (the Windows desktop compositor holds
~1.4 GB). Ryzen 7 5700X, 64 GB RAM, Windows 11 + WSL2. Work lives on `E:`.

**Inference runs on Windows** via Ollama. **Training runs in WSL2** — Unsloth and
bitsandbytes are unreliable on native Windows. The venv is `~/student-venv` in
the WSL home, never in the project tree (CUDA wheels on the `/mnt/e` DrvFs mount
are slow and break symlinks).

Two separate weight stores, which matters constantly:

| store | size | used for | `ollama pull` touches it? |
|---|---|---|---|
| `E:\LocalLLM\models` | ~32 GB | GGUF, inference | yes |
| `~/.cache/huggingface` (WSL) | ~8.8 GB | safetensors, training base | **no** |

## 2. Current state

- **Lessons trained:** 1–17. Adapters in `adapters/lesson_NN/`, ~3.8 GB total.
- **Dataset:** 943 train rows, 70 eval rows, `dataset/rejected.jsonl` as audit trail.
- **Base:** `unsloth/Qwen3.5-4B` at revision `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.
- **Ledger:** `adapters/lesson_ledger.json` — trained fingerprints plus, per lesson,
  `base_repo` / `base_revision`. Lessons 1–15 are marked `revision_source: "assumed"`
  because they were back-filled; 16 onward are recorded at training time.
- **Skill scores** before lesson 17 (pass threshold **0.70**):
  `localllm_ops` 0.423 · `supply_chain` 0.435 · `agentic_planning` 0.442 ·
  `python_stack` 0.490 · `tool_call_format` 0.716 · `structured_extraction` 0.814 ·
  `static_analysis` had **no eval coverage** until lesson 17 added 1 row.

## 3. The loop, as one command

```powershell
powershell -ExecutionPolicy Bypass -File E:\LocalLLM\run-lesson.ps1 -Lesson 18
```

Flags: `-Fresh` (archive adapters + ledger first), `-SkipTrain` (grade only),
`-EvalFile dataset/code_eval.jsonl`, `-Limit 40`, `-Export` (expected to fail —
see §6).

It does: env check → stop Ollama → QLoRA micro-epoch in WSL2 → verify the adapter
file exists → start `serve_adapter.py` → grade base (adapter off) → grade trained
(adapter on, compared to base) → print a delta table → restart Ollama in a
`finally`. Logs to `logs/automate_lessonNN_<stamp>.log`.

Cost per lesson, measured: **44–365 s**, peak **4.6–5.4 GB** VRAM. Adapters are
cheap; **the dataset is the asset.** Back up `dataset/*.jsonl` and the ledger.

## 4. Adding a lesson

```powershell
# 1. author a batch to the spec in AGENT_BRIEF.md -> lessons/lesson_NNN.json
# 2. back up before mutating shared state
copy E:\LocalLLM\teacher_pipeline\dataset\train.jsonl ...\train.jsonl.bak
# 3. ingest (filters, dedupes, splits 20% into eval)
python generate_lessons.py ingest --file lessons/lesson_018.json
# 4. train + grade
powershell -File E:\LocalLLM\run-lesson.ps1 -Lesson 18 -Limit 40
```

Ingest is the only thing that may write `dataset/` and the ledger. Never run two
of them concurrently, and never run two trainings at all.

## 5. Reading the results honestly

The rubric (`curriculum.yaml`): accuracy **0.45**, reasoning **0.25**, formatting
**0.20**, conciseness **0.10**; pass at **0.70**. `score_accuracy` is **rubric v2**
— numbers 40%, identifiers 40%, vocabulary 20%, each counted only when the
reference contains it. Reports carry `rubric_version`, and `--compare` refuses to
compare across versions.

**The headline score can rise while the model gets worse.** This happened: overall
**+0.064** while numeric agreement fell **0.669 → 0.455** and answer length
collapsed to **0.41x**. Style axes carry 0.55 of the weight against accuracy's
0.45. So always check the components, not the total:

```powershell
# per-result accuracy sub-scores live in reports/*.json under notes.accuracy
# as "nums=0.42 ids=0.19 recall=0.28"
```

**Pre-register thresholds before a run**, not after:
numeric agreement > **0.55**, answer length within **0.8–1.4x** of reference,
conciseness > **0.80**, no previously-passing skill down more than **5%**.

## 6. The hard-won gotchas — each of these cost real time

1. **`$?` after a pipeline is the last command's status.** `python x | tee log`
   then `$?` gives tee's. Use `${PIPESTATUS[0]}` immediately. A step-0 crash
   reported `EXIT=0` for a day because of this.
2. **Always warm up before benchmarking a model.** Cold, srini-vision:2b measured
   **2.1 tok/s**; warm, **129.6**. A factor of 62. `bench/probe_models.py` does
   it correctly and also reports GPU placement and tool-call validity.
3. **`srini-tools:8b` cannot be used in an agent harness.** It describes tool calls
   in prose instead of emitting them, reproducibly. Probably Ollama's template for
   that architecture, so retest after an upgrade.
4. **`ollama pull <tag>` silently drops the baked SYSTEM profile.**
   `start-ollama.ps1` now self-heals via
   `profile/build_persona_models.py --repair`; `pull-model.ps1` wraps pull+repair.
   `--verify` exits non-zero if any tag is stale or missing.
5. **GGUF export cannot be served by this Ollama.** Current llama.cpp merges the
   SSM projections into `blk.N.ssm_beta_alpha.weight`; Ollama 0.40.17 wants
   separate `ssm_beta`/`ssm_alpha`. Affects every quant and both converters. That
   is why grading goes through `serve_adapter.py` (transformers) instead.
6. **Port 11435 is contested** — `serve_adapter.py` and the local inference proxy
   both default to it. Pass `--port` if both must run.
7. **`Path.write_text()` on Windows converts LF to CRLF**, which makes a `.sh`
   unrunnable (`env: bash\r: No such file or directory`). Write bytes, or pass
   `newline="\n"`.
8. **Quality filters drop work silently** into `dataset/rejected.jsonl`. One
   harvest kept **9 of 40**. The `min_chars: 120` floor systematically rejects
   correct bare tool calls (~40 chars) — the highest-value skill. Read the yield.
9. **`thinking` is trained on.** `train_on_responses_only` computes loss over the
   think block, so a stub there teaches stub reasoning. Two Agent B examples were
   dropped for having number-inventory "traces".
10. **Base drift is silent.** A new revision of the same base keeps shapes valid,
    so adapters load and degrade quietly. `python train_student.py --verify-base`
    checks; it is also folded into `--check`.
11. **Transformers 5.x `apply_chat_template` returns a str** even with
    `return_tensors="pt"`, and Qwen3.5 hands back a *vision processor*, not a
    tokenizer — use `processor.tokenizer`. Its chat template also **pre-opens**
    the think block, so output is `reasoning … </think> answer` with no opening
    tag; matching balanced tags yields an empty reasoning channel.

## 7. What is settled, and what to stop re-litigating

**Training moves style, not knowledge — at this data scale.** Five lessons, same
result each time: conciseness +0.5, formatting +0.25, accuracy negative.

**But that claim was once over-stated, so be precise.** When data was harvested
from the actual target material instead of authored — 745 examples, 94 optimizer
steps instead of 3–8 — recall *did* move: fully-correct answers **7% → 17%**,
reverse-lookup **57% → 66%**. Still only **19%** exact identifier recall overall,
so the model answers confidently wrong on specifics. Useful for "where is X
defined" (66%); useless for signatures and test contents (0%).

**So: facts belong in the prompt and in retrieval, not the weights.**
- `profile/` bakes a **304-token** lean operator profile into each tag's SYSTEM
  block (`--full` for the ~1.5k version). Prompt eval 0.02–0.15 s.
- `zimrag/` answers from offline Kiwix archives with citations, no index build.
- repo2graph's own MCP server is the right source for code questions.

## 8. The biggest untapped data source

`generate_lessons.py harvest` mines `~/.claude/projects/**/*.jsonl` — **185
transcript files, 240 MB** of real sessions. Barely used. It needs fixing first:
a harvest of 40 kept 9 (**25 rejected as too long**), and **0 of 9 carried a
reasoning trace** despite the transcripts containing them. Fix the `max_chars`
ceiling for this source, preserve the `thinking` blocks, and map turns onto real
curriculum skills instead of one `harvested_session` bucket. That turns the
operator's genuine working history into training data at zero generation cost,
and unlike authored lessons it reflects what they actually do.

## 9. Do not

- run two trainings at once (one 8 GB GPU; OOM leaves a half-written adapter)
- write `dataset/` or the ledger from two processes
- trust an aggregate score without checking its components
- author examples whose value is "memorise this fact" — measured, does not work
- claim a run succeeded without checking the artifact; exit codes lie here
- re-pull a model tag without repairing the profile afterwards
