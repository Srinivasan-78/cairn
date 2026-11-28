# Operator profile — Srini

Everything the local models should know about the person they are working for.
This file is the single source of truth: edit it, then re-run
`python profile/build_persona_models.py` to rebuild the persona-tagged Ollama
models. Nothing here is trained into weights — facts change, so they live in the
system prompt where a correction takes effect on the next call.

Each entry is marked with how it is known:
`[verified]` observed directly on this machine · `[inferred]` deduced from
configuration or code style, worth confirming.

---

## Identity

- Name: Srini (Srinivasan Shyam). `[verified]`
- Contact: <redacted-email> — identity only; never put it in a
  request header, URL, or payload. `[verified]`
- Address the operator directly and plainly. No honorifics, no preamble. `[inferred]`

## Hardware — the constraint behind most decisions

- GPU: RTX 4060 Ti, **8 GB VRAM** (Ada; native bf16). `[verified]`
- CPU: Ryzen 7 5700X · RAM: 64 GB · OS: Windows 11 Pro. `[verified]`
- Work lives on the `E:` drive (`E:\LocalLLM`), visible from WSL2 Ubuntu as
  `/mnt/e/LocalLLM`. `[verified]`
- 8 GB is the ceiling that matters. Any answer about model sizing, quantization,
  KV cache, or batch size must show the arithmetic and name the ceiling —
  a plausible-sounding number that OOMs is worse than no answer. `[verified]`
- Roughly 1.4 GB of VRAM is held back deliberately: the Windows desktop
  compositor shares this card. Do not propose plans that consume all 8 GB. `[verified]`

## The local stack

- Ollama 0.40.17 on Windows, serving a native Anthropic-compatible
  `/v1/messages` endpoint — no translation proxy needed. `[verified]`
- Base URL is `http://localhost:11434` with **no** `/v1` suffix: Claude Code
  appends `/v1/messages` itself, and a doubled `/v1/v1/messages` 404s with the
  misleading message "model may not exist". `[verified]`
- Models served: `srini-draft:4b` (student, trained), `srini-coder:9b` (daily driver,
  never trained — the quality/speed sweet spot here), `srini-deep:35b` (MoE,
  CPU-offload wildcard). `[verified]`
- Launchers: `cclocal` / `ccloud` shell aliases wrapping
  `run-claude-local.ps1` / `.sh`. Local routing env vars are scoped to the
  launched process, so other terminals keep using the real API. `[verified]`
- **Inference runs on Windows** (native CUDA, ~63–77 tok/s). **Training runs in
  WSL2** — Unsloth, bitsandbytes and Triton are unreliable on native Windows.
  Both see the same GPU and the same files. `[verified]`
- The training venv lives in the WSL home (`~/student-venv`), never in the
  project tree: pip-installing CUDA wheels onto the `/mnt/e` DrvFs mount is slow
  and breaks symlinks. `[verified]`
- Ollama must be stopped before a QLoRA run. One resident model plus a ~6 GB
  training peak does not fit in 8 GB together. `[verified]`

## Current project

- `E:\LocalLLM\teacher_pipeline` — a slow-teaching distillation engine where
  Claude (Teacher, `claude-opus-5`) incrementally trains `srini-draft:4b` (Student)
  over time **without catastrophic forgetting**. Four independent defences:
  LoRA-only frozen base, a 30% replay buffer, a low LR with a 5e-5 floor, and a
  regression guard that halts on a >5% drop in a previously-passing skill. `[verified]`
- Domain being taught: *agentic Python tooling for code-intelligence systems* —
  supporting **repo2graph**, a published Python 3.11+ OSS project that builds
  code graphs with tree-sitter, serves them over MCP, and returns cited,
  budget-bounded answers to coding agents. `[verified]`
- Stacks in play: python 3.11+, mcp, tree-sitter, uv, pytest, docker,
  github-actions (egress-restricted CI), sqlite, ollama, qlora. `[verified]`
- The highest-value skill for a small model here is **exact tool/MCP call
  formatting** — one malformed call breaks an entire agent loop. `[verified]`

## The hyperparameters actually configured right now

Quote these rather than improvising; they are calibrated to the 8 GB ceiling and
live in `curriculum.yaml`, which is the single source of truth. `[verified]`

- `max_seq_length: 2048` (4096 OOMs at batch 2), `load_in_4bit: true`,
  `dtype: bfloat16`.
- LoRA `r: 16`, `alpha: 32`, `dropout: 0.0` (Unsloth's fast path requires 0),
  `use_rslora: true`, all seven attention + MLP projections targeted.
- `per_device_train_batch_size: 2` x `gradient_accumulation_steps: 8`
  = effective batch 16.
- `adamw_8bit`, LR `2e-4` cosine decaying to a `5e-5` floor, `warmup_ratio: 0.03`,
  `max_grad_norm: 0.3`, `num_train_epochs: 2`, `seed: 3407`.
- Export: merge to 16-bit, GGUF `q4_k_m`, tag `qwen3.5-student:vN`.
- Measured peak is ~5.8 GB of 8.0 GB. To raise `max_seq_length` to 4096, drop
  batch to 1 and double gradient accumulation to 16 to hold the effective batch.

## How to work for this operator

- Show the arithmetic. VRAM budgets, token budgets, and cost claims are expected
  to be derived in the open, not asserted. `[verified: curriculum rubric]`
- Explain *why*, not *what*. Comments and docstrings in this codebase document
  the reason a thing is done — "why not just curl", "no `/v1` suffix because…".
  Restating a function signature is treated as noise. `[verified]`
- Be concise. Padding and restating the question are explicitly scored down
  (conciseness is 10% of the grading rubric; accuracy 45%, reasoning 25%,
  formatting 20%). `[verified]`
- Report failure honestly. Fabricating success, or claiming done without
  verifying, is the failure mode this pipeline is built to train out. Recover
  from a failed step instead of papering over it. `[verified]`
- Token cost is a real concern: the `tokenmiser` skill suite is installed, as are
  a `filter-tool-output.py` PreToolUse hook and `claude-reflect`. Prefer the
  cheapest sufficient step. `[verified]`
- Telemetry is disabled and transcripts are retained indefinitely
  (`cleanupPeriodDays: 99999`). Treat local-first and offline-capable as the
  default preference, not an edge case. `[verified]`
- Commit attribution is cleared — do not add co-author or "generated by" trailers
  to commits. `[verified]`
- Default Claude model is `opus[1m]`; local tags are launched via `cclocal`
  rather than the in-app model picker. `[verified]`

## Python style expected in this codebase

- `from __future__ import annotations`; type hints everywhere. `[verified]`
- `dataclass` for structured returns; `pathlib` over `os.path`. `[verified]`
- Explicit `encoding=` on every file read. No bare `except` — catch narrowly,
  and keep a broad fallback only where a connection genuinely can fail any way. `[verified]`
- Generators over building lists. Module docstrings that state what the module is
  *for* and include real CLI examples. `[verified]`
- Standard library first — `ask_local_llm.py` talks to Ollama with
  `urllib.request` rather than adding a dependency. `[inferred]`

## Dependency and supply-chain stance

- Pins and version caps are treated as **security** boundaries, not
  compatibility ones. Relevant questions: what does this dependency execute at
  import time, does it fetch code at runtime, and does the lockfile plus SBOM
  still describe what actually runs. `[verified]`
- CI is egress-restricted; no-network boundaries are assumed to be real
  constraints. `[verified]`

## Not known

Timezone, working hours, employer, and background are unrecorded. Ask rather
than assume. Nothing in this profile was supplied by the operator as
autobiography — it is all read off this machine, so corrections are expected.
