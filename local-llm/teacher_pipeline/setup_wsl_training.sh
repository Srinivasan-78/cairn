#!/usr/bin/env bash
set -euo pipefail
# setup_wsl_training.sh - Build the QLoRA training environment inside WSL2.
#
# Run from Windows:
#   MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/e/LocalLLM/teacher_pipeline/setup_wsl_training.sh
#
# Two deliberate choices:
#
#  1. Python 3.12 via uv, not the system python. Ubuntu 26.04 ships Python
#     3.14.4, which torch and Unsloth do not publish wheels for yet. uv fetches
#     a standalone CPython 3.12 without touching the system interpreter.
#
#  2. The venv lives in $HOME (ext4), not /mnt/e (DrvFs). Thousands of small
#     file writes onto the Windows filesystem are an order of magnitude slower,
#     and pip installing torch is exactly that workload. The *project* stays on
#     /mnt/e so Windows and WSL share one copy of the data and adapters.

set -uo pipefail

VENV="$HOME/student-venv"
PROJECT="/mnt/e/LocalLLM/teacher_pipeline"
PYVER="3.12"

log() { echo ""; echo "=== $* ==="; }

log "1/6  base packages"
# build-essential is not optional: Triton JIT-compiles CUDA kernels at the first
# training step and needs a host C compiler. Without it the run loads the model,
# prints a full plan, then dies at step 0 with "Failed to find C compiler" - and
# a CUDA matmul test still passes beforehand, because that uses prebuilt kernels.
if ! command -v curl >/dev/null 2>&1 || ! command -v gcc >/dev/null 2>&1; then
  sudo apt-get update -qq && sudo apt-get install -y -qq curl ca-certificates build-essential
fi

log "2/6  uv"
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version || { echo "FATAL: uv install failed"; exit 1; }

log "3/6  CPython $PYVER + venv at $VENV"
uv python install "$PYVER" || { echo "FATAL: could not fetch CPython $PYVER"; exit 1; }
uv venv "$VENV" --python "$PYVER" || { echo "FATAL: venv creation failed"; exit 1; }
PY="$VENV/bin/python"
"$PY" --version

log "4/6  torch (CUDA)"
# The driver reports CUDA UMD 13.5, so cu130 is the right target. Fall back
# through older CUDA channels if that index is not published for this Python.
TORCH_OK=0
for CH in cu130 cu128 cu126; do
  echo "--- trying $CH ---"
  if uv pip install --python "$PY" torch --index-url "https://download.pytorch.org/whl/$CH" 2>&1 | tail -4; then
    if "$PY" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
      echo "torch OK on $CH"
      TORCH_OK=1
      break
    else
      echo "$CH installed but CUDA not available; trying next channel"
    fi
  fi
done
if [ "$TORCH_OK" -ne 1 ]; then
  echo "FATAL: no torch build gave a working CUDA runtime."
  "$PY" -c "import torch;print('torch',torch.__version__,'cuda',torch.version.cuda)" 2>&1 || true
  exit 1
fi

log "5/6  unsloth + trl + peft + bitsandbytes"
uv pip install --python "$PY" -r "$PROJECT/requirements-train.txt" 2>&1 | tail -6

log "6/6  verification"
"$PY" - <<'PYEOF'
import importlib, sys
import torch
print(f"python        {sys.version.split()[0]}")
print(f"torch         {torch.__version__}  (cuda {torch.version.cuda})")
print(f"cuda avail    {torch.cuda.is_available()}")
if torch.cuda.is_available():
    p = torch.cuda.get_device_properties(0)
    print(f"gpu           {p.name}")
    print(f"vram          {p.total_memory/1e9:.1f} GB")
    print(f"bf16          {torch.cuda.is_bf16_supported()}")
    free, total = torch.cuda.mem_get_info()
    print(f"free vram     {free/1e9:.1f} GB")
ok = True
for m in ("unsloth", "trl", "peft", "datasets", "bitsandbytes", "transformers", "yaml"):
    try:
        mod = importlib.import_module(m)
        print(f"{m:<13} {getattr(mod,'__version__','ok')}")
    except Exception as e:
        print(f"{m:<13} MISSING ({type(e).__name__})")
        ok = False
# A real 4-bit allocation is the only honest proof bitsandbytes works.
try:
    import bitsandbytes as bnb
    x = torch.randn(256, 256, device="cuda", dtype=torch.bfloat16)
    print("cuda matmul   ok", (x @ x).shape)
except Exception as e:
    print(f"cuda matmul   FAILED: {e}")
    ok = False
print("\nRESULT:", "READY" if ok else "INCOMPLETE")
PYEOF

echo ""
echo "Activate with:  source $VENV/bin/activate"
echo "Then:           cd $PROJECT && python train_student.py --check"
