# teacher_pipeline — Slow-Teaching Distillation Engine

Claude (Teacher) incrementally trains a local model (Student) over time, without
catastrophic forgetting.

**Calibrated for:** RTX 4060 Ti 8 GB · Ryzen 7 5700X · 64 GB RAM · Win 11 + WSL2

| Role | Model | Where it runs |
|---|---|---|
| Teacher | `claude-opus-5` | this Claude Code session |
| Student (trained + served) | `srini-draft:4b` / `unsloth/Qwen3.5-4B` | Ollama · WSL2 for training |
| Daily driver (never trained) | `srini-coder:9b` | Ollama, Windows |
| Wildcard (MoE, CPU-offload) | `srini-deep:35b` | Ollama, Windows |

## The split that matters

**Inference runs on Windows** (native CUDA, ~63-77 tok/s). **Training runs in WSL2**
(Unsloth/bitsandbytes/Triton are unreliable on native Windows). Both see the same
GPU and the same files via `/mnt/e/LocalLLM`.

## The loop

```
  1. generate   Teacher authors lessons, or harvest real sessions
                   -> quality filter -> dedupe -> dataset/train.jsonl + eval.jsonl
  2. grade      baseline the Student on the unseen eval split
                   -> reports/*.json, weak_skills list
  3. train      QLoRA micro-epoch on new examples + 30% replay of old ones
                   -> adapters/lesson_NN/
  4. export     merge -> GGUF q4_k_m -> `ollama create qwen3.5-student:vN`
  5. re-grade   compare against baseline; halt on regression
                   -> weak skills feed step 1 of the next lesson
```

## Commands

```bash
# --- data ---------------------------------------------------------------
python generate_lessons.py harvest --limit 200     # mine real Claude sessions
python generate_lessons.py ingest --file lessons/lesson_01.json
python generate_lessons.py stats

# --- evaluate (Windows is fine - inference only) -----------------------
python grade_student.py --baseline                 # pre-training baseline
python grade_student.py --model qwen3.5-student:v1 --compare reports/baseline.json

# --- train (WSL2) ------------------------------------------------------
# The venv lives in the WSL home, not the project tree: pip-installing CUDA
# wheels onto the /mnt/e DrvFs mount is slow and breaks symlinks.
wsl -d Ubuntu
source ~/student-venv/bin/activate
cd /mnt/e/LocalLLM/teacher_pipeline
python train_student.py --check                    # verify env + VRAM
python train_student.py --lesson 2 --export

# Stop Ollama first - one resident model plus a ~6 GB QLoRA peak will not fit
# in 8 GB together. Restart it afterwards to serve the new student tag.
```

## How forgetting is prevented

Four independent defences, because any one alone is leaky:

1. **LoRA only** — base weights stay frozen; the original model is never overwritten.
2. **Replay buffer** — `forgetting_guard.replay_ratio: 0.30` mixes 30% previously-trained
   examples into every new batch.
3. **Low LR with a floor** — `2e-4` decaying cosine toward `5e-5`, never to zero, so
   lessons stack gently instead of lurching.
4. **Regression guard** — `grade_student.py --compare` exits non-zero if a
   previously-passing skill drops more than 5%. Roll back the adapter if it fires.

Plus `train_on_responses_only`, so loss is computed on the Teacher's answers and not
on user turns, and `adapters/lesson_ledger.json`, which tracks exactly which
example fingerprints have already been trained on.

## Files

```
curriculum.yaml           domain, skills, rubric, all hyperparameters
generate_lessons.py       harvest/ingest -> filter -> dedupe -> split
grade_student.py          4-axis rubric scoring + regression guard
train_student.py          QLoRA micro-epochs + GGUF export
requirements-train.txt    WSL2 training deps
dataset/                  train.jsonl, eval.jsonl, rejected.jsonl (audit trail)
adapters/                 lesson_NN/ + lesson_ledger.json
gguf/                     merged q4_k_m exports + Modelfiles
reports/                  grading runs; baseline.json
logs/                     training metrics, pull logs
```

## VRAM budget (why the hyperparameters look conservative)

```
4-bit Qwen3.5-4B base            ~2.4 GB
LoRA r=16 params + grads         ~0.1 GB
adamw_8bit optimizer states      ~0.2 GB
activations @ seq 2048 batch 2   ~2.5 GB   (unsloth gradient checkpointing)
CUDA context + fragmentation     ~0.6 GB
---------------------------------------
peak                             ~5.8 GB   of 8.0 GB
```

The remaining ~1.4 GB is deliberate headroom — the Windows desktop compositor
shares this GPU. If you raise `max_seq_length` to 4096, drop
`per_device_train_batch_size` to 1 and double `gradient_accumulation_steps` to hold
the effective batch at 16.
