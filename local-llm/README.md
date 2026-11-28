# Local LLM & Offline Knowledge Tooling

Folded in from `E:\LocalLLM`, this directory contains the local-first LLM runtime, offline ZIM retrieval, distillation pipeline, persona profiles, and benchmarking scripts used alongside Cairn.

## Contents

- `zimrag/` — Zero-index cited Q&A and MCP server over offline Kiwix `.zim` archives (`libzim` Xapian search + query backoff + passage reranking).
- `teacher_pipeline/` — Slow-teaching QLoRA distillation engine (`curriculum.yaml`, `grade_student.py`, `train_student.py`, `serve_adapter.py`, plus `lessons/`, `dataset/`, and `reports/`).
- `profile/` — Operator profile (`USER_PROFILE.md`, `MODEL_ROLES.md`, `PROJECTS.md`, `REPOS.md`) and `build_persona_models.py` for building Ollama `srini-*` tags.
- `bench/` — Model probing and latency/VRAM benchmarking scripts (`probe_models.py`).
- `heretic_out/` — Abliteration scripts, study logs, and adapter configs (binary `.safetensors` weights listed in `WEIGHTS_MANIFEST.md`).
- `zims/MANIFEST.md`, `models/MANIFEST.md`, `teacher_pipeline/adapters/MANIFEST.md` — Inventories of large local binary archives, Ollama models, and LoRA adapters excluded from Git.
- Root scripts — `anthropic_proxy.py`, `ask_local_llm.py`, `run-claude-local.*`, `start-ollama.*`, `stop-ollama.*`, `pull-model.ps1`, `compare-adapters.ps1`, `run-lesson.ps1`, `setup-lifeos-windows.ps1`, and `test_proxy_router.py`.
