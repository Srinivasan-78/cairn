#!/usr/bin/env python3
"""
train_student.py - Incremental QLoRA fine-tuning for the Student, on 8 GB VRAM.

Designed for repeated small runs ("micro-epochs") rather than one big job: each
lesson batch stacks onto the previous adapter, with a replay buffer of older
examples mixed in so the Student does not forget what it already learned.

RUN THIS IN WSL2, not native Windows. Unsloth/bitsandbytes/Triton on Windows is
fragile; the Linux stack inside WSL2 is the supported path and sees the same GPU.

Setup (once, inside WSL2 Ubuntu):
    cd /mnt/e/LocalLLM/teacher_pipeline
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements-train.txt

Usage:
    python train_student.py --check                  # verify env + VRAM, no training
    python train_student.py --dry-run                # build dataset, print plan, stop
    python train_student.py --lesson 1               # train micro-epoch 1
    python train_student.py --lesson 2 --export      # train, then merge -> GGUF -> Ollama

Memory plan on an RTX 4060 Ti 8 GB (measured headroom, not theory):
    4-bit Qwen3.5-4B base weights        ~2.4 GB
    LoRA r=16 params + grads             ~0.1 GB
    8-bit optimizer states               ~0.2 GB
    activations @ seq 2048, batch 2,
      with unsloth gradient checkpointing ~2.5 GB
    CUDA context + fragmentation         ~0.6 GB
    ------------------------------------------------
    peak                                 ~5.8 GB   (leaves ~1.4 GB for the desktop)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CURRICULUM = HERE / "curriculum.yaml"
DATASET = HERE / "dataset"
ADAPTERS = HERE / "adapters"
GGUF = HERE / "gguf"
LOGS = HERE / "logs"


def load_cfg() -> dict:
    import yaml
    return yaml.safe_load(CURRICULUM.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Environment check
# ---------------------------------------------------------------------------
def check_env(cfg: dict) -> bool:
    print("Environment check\n" + "-" * 50)
    ok = True

    print(f"  python           {sys.version.split()[0]}")
    if sys.platform == "win32":
        print("  !! running on native Windows - Unsloth/bitsandbytes are unreliable here.")
        print("     Use WSL2:  wsl -d Ubuntu  then  cd /mnt/e/LocalLLM/teacher_pipeline")
        ok = False
    else:
        print(f"  platform         {sys.platform}")

    try:
        import torch
        print(f"  torch            {torch.__version__}")
        if not torch.cuda.is_available():
            print("  !! torch.cuda.is_available() == False - this is a CPU-only build.")
            print("     Install a CUDA build, e.g.:")
            print("       pip install torch --index-url https://download.pytorch.org/whl/cu130")
            ok = False
        else:
            props = torch.cuda.get_device_properties(0)
            total = props.total_memory / 1e9
            free = torch.cuda.mem_get_info()[0] / 1e9
            print(f"  gpu              {props.name}")
            print(f"  vram             {total:.1f} GB total, {free:.1f} GB free")
            print(f"  bf16             {torch.cuda.is_bf16_supported()}")
            need = 6.2
            if free < need:
                print(f"  !! only {free:.1f} GB free; need ~{need} GB. Close GPU apps "
                      f"(browsers are the usual culprit).")
                ok = False
    except ImportError:
        print("  !! torch not installed")
        ok = False

    # Triton JIT-compiles CUDA kernels at the first training step, which needs a
    # host C compiler. Without one the run loads the model, prints a full plan,
    # then dies at step 0 - so check it here, before paying for the model load.
    cc = os.environ.get("CC") or shutil.which("gcc") or shutil.which("cc")
    if cc:
        print(f"  c compiler       {cc}")
    else:
        print("  !! no C compiler found (gcc/cc) - Triton cannot build kernels.")
        print("     Install it:  sudo apt-get update && sudo apt-get install -y build-essential")
        ok = False

    for mod, hint in (("unsloth", "pip install unsloth"),
                      ("trl", "pip install trl"),
                      ("peft", "pip install peft"),
                      ("datasets", "pip install datasets"),
                      ("bitsandbytes", "pip install bitsandbytes")):
        try:
            m = __import__(mod)
            print(f"  {mod:<16} {getattr(m, '__version__', 'ok')}")
        except ImportError:
            print(f"  !! {mod} missing  ->  {hint}")
            ok = False

    tr = DATASET / "train.jsonl"
    if tr.exists():
        with tr.open(encoding="utf-8") as f:
            n = sum(1 for _ in f)
    else:
        n = 0
    print(f"  train.jsonl      {n} example(s)")
    if n < 10:
        print("  !! fewer than 10 examples; generate more lessons first.")
        ok = False

    print("-" * 50)
    print("READY" if ok else "NOT READY - fix the items marked !!")
    return ok


# ---------------------------------------------------------------------------
# Dataset assembly with replay (anti-forgetting)
# ---------------------------------------------------------------------------
def balanced_sample(rows: list[dict], n: int, cap_ratio: float) -> list[dict]:
    """Sample n rows, letting no single skill exceed cap_ratio of the result.

    The accumulated corpus is ~52% code_facts - one-line lookups whose CoT only
    says "answer with the path and nothing else". A uniform replay sample
    therefore spends half of every lesson re-teaching terseness, which is why
    34 lessons moved formatting and conciseness but not accuracy or reasoning.
    quality_filters.max_per_skill_ratio already states this intent for
    generation; this applies the same cap to replay.
    """
    by_skill: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_skill[r.get("meta", {}).get("skill", "?")].append(r)

    cap = max(1, int(n * cap_ratio))
    kept: list[dict] = []
    overflow: list[dict] = []
    for rs in by_skill.values():
        random.shuffle(rs)
        kept.extend(rs[:cap])
        overflow.extend(rs[cap:])

    random.shuffle(kept)
    if len(kept) < n:  # not enough distinct skills to fill n under the cap
        random.shuffle(overflow)
        kept.extend(overflow[: n - len(kept)])
    return kept[:n]


def build_dataset(cfg: dict, lesson: int):
    """New examples for this lesson + a replay sample of older ones.

    Replay is the main defence against catastrophic forgetting: without it,
    training only on the newest batch drags the adapter toward the new skill
    and degrades everything learned before.
    """
    from datasets import Dataset

    path = DATASET / "train.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        sys.exit("train.jsonl is empty.")

    ledger = ADAPTERS / "lesson_ledger.json"
    seen: set[str] = set()
    if ledger.exists():
        seen = set(json.loads(ledger.read_text(encoding="utf-8")).get("trained_fingerprints", []))

    def fp(r: dict) -> str:
        return r.get("meta", {}).get("fingerprint", "")

    def has_cot(r: dict) -> bool:
        """A target with no CoT is low-signal - quality_filters.require_thinking.

        Harvested transcripts slip past that filter because Claude Code does not
        persist thinking text, so lesson 35 added 113 trace-free rows. Replaying
        them teaches answer shape with no derivation behind it.
        """
        for msg in r.get("messages", []):
            if msg.get("role") == "assistant":
                return "<think" in (msg.get("content") or "")
        return False

    new_rows = [r for r in rows if fp(r) not in seen]
    old_rows = [r for r in rows if fp(r) in seen and has_cot(r)]

    replay_ratio = cfg["training"]["forgetting_guard"]["replay_ratio"]
    random.seed(cfg["training"]["optim"]["seed"])

    if not new_rows:
        print("  no unseen examples; retraining on the full set.")
        batch = rows
    else:
        n_replay = min(len(old_rows), int(len(new_rows) * replay_ratio / max(1e-9, 1 - replay_ratio)))
        cap_ratio = cfg["generation"]["quality_filters"]["max_per_skill_ratio"]
        replayed = balanced_sample(old_rows, n_replay, cap_ratio) if n_replay else []
        batch = new_rows + replayed
        print(f"  {len(new_rows)} new + {len(replayed)} replayed = {len(batch)} example(s)")
        mix: dict[str, int] = defaultdict(int)
        for r in batch:
            mix[r.get("meta", {}).get("skill", "?")] += 1
        print("  batch mix: " + ", ".join(
            f"{s} {c} ({c / len(batch):.0%})" for s, c in sorted(mix.items(), key=lambda x: -x[1])))

    random.shuffle(batch)
    return Dataset.from_list([{"messages": r["messages"]} for r in batch]), batch


def base_revision(cfg: dict) -> str | None:
    """The Hugging Face commit the training base is currently resolved to.

    A LoRA is a delta against *specific* weights, so an adapter is only
    meaningful against the revision it trained on. If the base is re-uploaded
    upstream and the cache refreshes, every adapter still loads - the shapes
    match - and quality degrades silently. Recording the revision is what makes
    that detectable instead of mysterious.
    """
    repo = cfg["meta"].get("student_hf_repo", "")
    if "/" not in repo:
        return None
    cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    if not cache:
        home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
        cache = str(Path(home) / "hub")
    ref = (Path(cache) / f"models--{repo.replace('/', '--')}" / "refs" / "main")
    try:
        return ref.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def verify_base(cfg: dict) -> bool:
    """Compare each trained lesson's recorded base against the current cache."""
    ledger_path = ADAPTERS / "lesson_ledger.json"
    if not ledger_path.exists():
        print("no ledger yet - nothing to verify")
        return True

    now = base_revision(cfg)
    repo = cfg["meta"].get("student_hf_repo", "?")
    print(f"base repo         {repo}")
    print(f"cache revision    {now or '(not cached)'}")

    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    lessons = data.get("lessons", [])
    unknown = [l for l in lessons if not l.get("base_revision")]
    mismatched = [l for l in lessons
                  if l.get("base_revision") and l["base_revision"] != now]

    print(f"lessons recorded  {len(lessons)}")
    if unknown:
        print(f"  {len(unknown)} trained before revisions were recorded "
              f"(lesson {', '.join(str(l['lesson']) for l in unknown[:8])}"
              f"{'...' if len(unknown) > 8 else ''}) - provenance unknown, not "
              f"necessarily wrong")
    if mismatched:
        print(f"\n  !! {len(mismatched)} lesson(s) trained against a DIFFERENT base:")
        for l in mismatched:
            print(f"       lesson {l['lesson']:>2}  {l['base_revision'][:12]} "
                  f"!= {(now or '?')[:12]}")
        print("     Those adapters will still load - the shapes match - but "
              "their deltas no longer correspond to these weights.")
        print("     Retrain them, or restore the recorded revision with:")
        print(f"       huggingface-cli download {repo} --revision <sha>")
        return False
    if not unknown:
        print("\nall lessons match the cached base revision")
    return True


def pin_current_base(cfg: dict) -> bool:
    """Stamp the cached revision onto ledger entries that have none.

    This *asserts* that the lessons already trained used the revision sitting in
    the cache now - it cannot prove it. Worth doing once so there is a baseline
    to detect drift against, but it is a claim, not a measurement, so the ledger
    records how each revision got there.
    """
    ledger_path = ADAPTERS / "lesson_ledger.json"
    if not ledger_path.exists():
        print("no ledger to pin")
        return False
    rev = base_revision(cfg)
    if not rev:
        print("base not in the local cache - cannot pin")
        return False

    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    pinned = 0
    for entry in data.get("lessons", []):
        if not entry.get("base_revision"):
            entry["base_repo"] = cfg["meta"].get("student_hf_repo")
            entry["base_revision"] = rev
            entry["revision_source"] = "assumed"   # vs recorded at train time
            pinned += 1
    if not pinned:
        print("every lesson already has a revision")
        return True
    ledger_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"pinned {rev[:12]} onto {pinned} lesson(s), marked 'assumed'")
    print("Future lessons record their revision at training time instead.")
    return True


def update_ledger(batch: list[dict], lesson: int, cfg: dict | None = None) -> None:
    ADAPTERS.mkdir(parents=True, exist_ok=True)
    ledger = ADAPTERS / "lesson_ledger.json"
    data = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {
        "trained_fingerprints": [], "lessons": []
    }
    fps = set(data["trained_fingerprints"])
    fps.update(r.get("meta", {}).get("fingerprint", "") for r in batch)
    data["trained_fingerprints"] = sorted(f for f in fps if f)
    entry = {
        "lesson": lesson,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "n_examples": len(batch),
    }
    # Pin the base: without this, a silent upstream re-upload leaves every
    # adapter loadable but subtly wrong, with nothing to compare against.
    if cfg is not None:
        entry["base_repo"] = cfg["meta"].get("student_hf_repo")
        entry["base_revision"] = base_revision(cfg)
    data["lessons"].append(entry)
    ledger.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train(cfg: dict, lesson: int, dry_run: bool, resume: bool) -> Path | None:
    t = cfg["training"]
    lo, opt = t["lora"], t["optim"]

    # Unsloth must be imported before transformers/trl to apply its patches.
    from unsloth import FastLanguageModel, is_bfloat16_supported  # noqa: I001
    from unsloth.chat_templates import train_on_responses_only
    import torch
    from trl import SFTConfig, SFTTrainer

    def _lesson_key(p: Path) -> tuple[int, str]:
        m = re.search(r"lesson_(\d+)", p.parent.name)
        return (int(m.group(1)) if m else -1, p.parent.name)

    out_dir = ADAPTERS / f"lesson_{lesson:02d}"
    prev = sorted(ADAPTERS.glob("lesson_*/adapter_model.safetensors"), key=_lesson_key)
    resume_from = prev[-1].parent if (resume and prev) else None

    print(f"\nLoading {cfg['meta']['student_hf_repo']} in 4-bit "
          f"(seq {t['max_seq_length']})")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(resume_from) if resume_from else cfg["meta"]["student_hf_repo"],
        max_seq_length=t["max_seq_length"],
        dtype=None,                       # let Unsloth pick bf16 on Ada
        load_in_4bit=t["load_in_4bit"],
    )
    if resume_from:
        print(f"  stacked onto previous adapter: {resume_from.name}")
    else:
        model = FastLanguageModel.get_peft_model(
            model,
            r=lo["r"],
            lora_alpha=lo["alpha"],
            lora_dropout=lo["dropout"],
            bias=lo["bias"],
            target_modules=lo["target_modules"],
            use_rslora=lo["use_rslora"],
            use_gradient_checkpointing=lo["use_gradient_checkpointing"],
            random_state=opt["seed"],
        )

    ds, batch_rows = build_dataset(cfg, lesson)

    bs = t["batch"]
    steps_per_epoch = max(1, len(ds) // (bs["per_device_train_batch_size"]
                                         * bs["gradient_accumulation_steps"]))
    total_steps = steps_per_epoch * opt["num_train_epochs"]

    print(f"\nPlan for lesson {lesson}")
    print(f"  examples            {len(ds)}")
    print(f"  effective batch     {bs['per_device_train_batch_size']} x "
          f"{bs['gradient_accumulation_steps']} = "
          f"{bs['per_device_train_batch_size'] * bs['gradient_accumulation_steps']}")
    print(f"  epochs              {opt['num_train_epochs']}")
    print(f"  optimizer steps     ~{total_steps}")
    print(f"  lr                  {opt['learning_rate']} -> {opt['min_learning_rate']} (cosine)")
    print(f"  lora                r={lo['r']} alpha={lo['alpha']} rslora={lo['use_rslora']}")
    print(f"  output              {out_dir}")

    if dry_run:
        print("\n(dry run - no training performed)")
        return None

    LOGS.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cosine decay to a floor rather than to zero: a nonzero final LR keeps the
    # adapter trainable across many small lessons instead of freezing it.
    lr_kwargs = {}
    ratio = opt["min_learning_rate"] / opt["learning_rate"]
    if opt["lr_scheduler_type"] == "cosine":
        try:
            from transformers.trainer_utils import SchedulerType  # noqa: F401
            lr_kwargs = {"lr_scheduler_kwargs": {"num_cycles": 0.4}}
        except ImportError:
            pass
    print(f"  (cosine floor target ~{ratio:.2f}x of peak)")

    sft_cfg = SFTConfig(
        output_dir=str(out_dir),
        per_device_train_batch_size=bs["per_device_train_batch_size"],
        gradient_accumulation_steps=bs["gradient_accumulation_steps"],
        num_train_epochs=opt["num_train_epochs"],
        learning_rate=opt["learning_rate"],
        lr_scheduler_type=opt["lr_scheduler_type"],
        warmup_ratio=opt["warmup_ratio"],
        weight_decay=opt["weight_decay"],
        max_grad_norm=opt["max_grad_norm"],
        optim=opt["optimizer"],
        seed=opt["seed"],
        bf16=is_bfloat16_supported(),
        fp16=not is_bfloat16_supported(),
        logging_steps=1,
        save_steps=t["checkpointing"]["save_steps"],
        save_total_limit=t["checkpointing"]["save_total_limit"],
        max_length=t["max_seq_length"],
        dataset_num_proc=1,            # >1 deadlocks on WSL2
        report_to="none",
        **lr_kwargs,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        args=sft_cfg,
    )

    # Mask the prompt so loss is computed only on the Teacher's answer. Without
    # this the Student also learns to imitate user turns, which wastes capacity.
    if t["forgetting_guard"]["train_on_responses_only"]:
        try:
            trainer = train_on_responses_only(
                trainer,
                instruction_part="<|im_start|>user\n",
                response_part="<|im_start|>assistant\n",
            )
            print("  loss masked to assistant turns only")
        except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as e:
            print(f"  (could not apply response-only masking: {e})")

    before = torch.cuda.max_memory_reserved() / 1e9
    print(f"\nTraining... (VRAM reserved before start: {before:.2f} GB)\n")
    stats = trainer.train()

    peak = torch.cuda.max_memory_reserved() / 1e9
    print(f"\nDone in {stats.metrics['train_runtime']:.0f}s  "
          f"final loss {stats.metrics.get('train_loss', float('nan')):.4f}  "
          f"peak VRAM {peak:.2f} GB")

    model.save_pretrained(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print(f"adapter saved: {out_dir}")

    update_ledger(batch_rows, lesson, cfg)

    (LOGS / f"lesson_{lesson:02d}_metrics.json").write_text(
        json.dumps({"lesson": lesson, "n_examples": len(ds),
                    "peak_vram_gb": round(peak, 2), **stats.metrics}, indent=2),
        encoding="utf-8",
    )
    return out_dir


# ---------------------------------------------------------------------------
# Export: merge -> GGUF -> Ollama
# ---------------------------------------------------------------------------
def export_gguf(cfg: dict, adapter_dir: Path, lesson: int) -> None:
    """Merge the LoRA into 16-bit weights, convert to GGUF, register in Ollama."""
    from unsloth import FastLanguageModel

    exp = cfg["training"]["export"]
    quant = exp["gguf_quant"]
    GGUF.mkdir(parents=True, exist_ok=True)

    print(f"\nMerging adapter and converting to GGUF ({quant})")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(adapter_dir),
        max_seq_length=cfg["training"]["max_seq_length"],
        dtype=None,
        load_in_4bit=False,       # must dequantize to merge cleanly
    )
    target = GGUF / f"student_lesson{lesson:02d}"
    # Unsloth drives llama.cpp's converter + quantizer under the hood.
    model.save_pretrained_gguf(str(target), tokenizer, quantization_method=quant)

    # Unsloth does not write into `target`: it creates a sibling `<target>_gguf/`
    # directory, so search that too or the export looks like it failed when it
    # did not. It also emits a `BF16-mmproj` vision projector next to the
    # quantized weights - and "BF16-mmproj" sorts before "Q4_K_M", so taking
    # produced[0] naively registers the projector as the model. Drop the
    # projector, then prefer the file whose name carries the requested quant.
    candidates = [
        p for p in GGUF.glob(f"student_lesson{lesson:02d}*/**/*.gguf")
    ] + sorted(GGUF.glob(f"student_lesson{lesson:02d}*.gguf"))
    produced = [p for p in candidates if "mmproj" not in p.name.lower()]
    produced.sort(key=lambda p: (quant.lower() not in p.name.lower(), p.name))
    if not produced:
        print("  !! no .gguf produced - check Unsloth's llama.cpp build output above.")
        return
    gguf_path = produced[0]
    size_gb = gguf_path.stat().st_size / 1e9
    print(f"  {gguf_path.name}  {size_gb:.2f} GB")

    base_tag = exp["ollama_tag"]
    # Respect curriculum.yaml's in-place governance: if ollama_tag already has a
    # `:tag` (e.g. srini-draft:4b), update it in-place rather than appending `:vN`.
    tag = base_tag if ":" in base_tag else f"{base_tag}:v{lesson}"
    modelfile = GGUF / f"Modelfile.v{lesson}"
    modelfile.write_text(
        f"FROM {gguf_path.as_posix()}\n"
        f"PARAMETER num_ctx 65536\n"
        f"PARAMETER temperature 0.3\n"
        f"PARAMETER top_p 0.9\n",
        encoding="utf-8",
    )
    print(f"\nRegister it with Ollama:\n  ollama create {tag} -f {modelfile}")
    print("Then restore the operator profile:\n  python ../profile/build_persona_models.py --repair")
    print(f"Then grade it:\n  python grade_student.py --model {tag} "
          f"--compare reports/baseline.json")

    if shutil.which("ollama"):
        try:
            subprocess.run(["ollama", "create", tag, "-f", str(modelfile)], check=True)
            print(f"\nregistered: {tag}")
        except subprocess.CalledProcessError as e:
            print(f"  (ollama create failed: {e}; run the command above manually)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lesson", type=int, default=1, help="Micro-epoch number.")
    p.add_argument("--check", action="store_true", help="Verify the environment and exit.")
    p.add_argument("--pin-current-base", action="store_true",
                   help="One-off: stamp the cached revision onto ledger entries "
                        "that lack one, marked 'assumed'. Establishes a baseline "
                        "for drift detection; it asserts rather than proves.")
    p.add_argument("--verify-base", action="store_true",
                   help="Compare every trained lesson's recorded base revision "
                        "against the cached base, and exit non-zero on a "
                        "mismatch. A mismatch means those adapters' deltas no "
                        "longer match the weights they will be applied to.")
    p.add_argument("--dry-run", action="store_true", help="Build the plan without training.")
    p.add_argument("--export", action="store_true", help="Merge to GGUF and register in Ollama.")
    p.add_argument("--no-resume", action="store_true", help="Start a fresh adapter.")
    args = p.parse_args()

    cfg = load_cfg()

    if args.pin_current_base:
        return 0 if pin_current_base(cfg) else 1

    if args.verify_base:
        return 0 if verify_base(cfg) else 1

    if args.check:
        ok = check_env(cfg)
        # Report base drift here too: it is the one failure that does not stop
        # a run, so the only way it gets noticed is if something says so.
        print()
        verify_base(cfg)
        return 0 if ok else 1

    if args.dry_run:
        # Dataset assembly needs `datasets` but not a GPU.
        ds, _ = build_dataset(cfg, args.lesson)
        t, opt, bs = cfg["training"], cfg["training"]["optim"], cfg["training"]["batch"]
        eff = bs["per_device_train_batch_size"] * bs["gradient_accumulation_steps"]
        print(f"\nLesson {args.lesson}: {len(ds)} examples, effective batch {eff}, "
              f"{opt['num_train_epochs']} epoch(s)")
        print(f"lr {opt['learning_rate']} -> {opt['min_learning_rate']} cosine, "
              f"seq {t['max_seq_length']}, LoRA r={t['lora']['r']}")
        return 0

    resume = cfg["training"]["forgetting_guard"]["resume_from_last_adapter"] and not args.no_resume
    adapter = train(cfg, args.lesson, dry_run=False, resume=resume)

    # Never report success without the artifact. A step-0 crash (a Triton kernel
    # that cannot compile, for instance) can leave the exit status at 0 with an
    # empty adapter directory, which would let a caller chain export and grading
    # onto a model that was never trained.
    weights = ("adapter_model.safetensors", "adapter_model.bin")
    if not adapter or not any((Path(adapter) / w).exists() for w in weights):
        print(f"\n!! no adapter weights in {adapter or '(no output dir)'} - "
              f"training did not complete. Not exporting.", file=sys.stderr)
        return 1

    if args.export:
        export_gguf(cfg, adapter, args.lesson)
    return 0


if __name__ == "__main__":
    sys.exit(main())
