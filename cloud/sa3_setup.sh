#!/usr/bin/env bash
# Stable Audio 3 setup (June 2026 path). LoRA fine-tunes run on a single
# 16-24 GB GPU (RTX 4090 / A10 works) - far cheaper than the SAO full fine-tune.
set -euo pipefail
cd /workspace

# uv + repo
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
git clone https://github.com/Stability-AI/stable-audio-3
cd stable-audio-3
uv sync --extra lora
uv pip install matplotlib   # train_lora imports it (aeiou spectrogram); not in the lock

# --- GPU compatibility --------------------------------------------------------
# Blackwell GPUs (B200 / RTX 50xx, compute sm_100) need a CUDA 12.8 torch build;
# the locked torch only supports up to sm_90 and will refuse the GPU. If you see
# "sm_100 is not compatible", install the cu128 build INTO this venv and run with
# .venv/bin/python (NOT 'uv run', which resyncs and reverts torch):
if .venv/bin/python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
  cap=$(.venv/bin/python -c "import torch;print('.'.join(map(str,torch.cuda.get_device_capability())))" 2>/dev/null || echo "?")
  echo "[sa3] CUDA device capability: $cap"
  if [ "$cap" = "10.0" ] || [ "$cap" = "12.0" ]; then
    echo "[sa3] Blackwell detected -> installing cu128 torch"
    uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
  fi
fi

# Flash Attention 2 (required for Medium) - use a prebuilt wheel matching your
# CUDA/torch/python; browse: github.com/mjun0812/flash-attention-prebuild-wheels
# Example (CUDA 12.6, torch 2.7, py3.10):
# uv pip install https://github.com/mjun0812/flash-attention-prebuild-wheels/releases/download/v0.7.16/flash_attn-2.6.3+cu126torch2.7-cp310-cp310-linux_x86_64.whl
# Then keep it across syncs:  uv sync --inexact

# Accept model licenses on HF first: huggingface.co/stabilityai/stable-audio-3-medium
uv run hf auth login

echo "=== LoRA training (from toolkit dataset) ==="
cat << 'CMD'
# 1. stage data (toolkit dataset -> SA3 format):
uv run python /workspace/toolkit/scripts/sa3_workflow.py prepare \
    --dataset /workspace/dataset --data-dir /workspace/sa3_data
# 2. confirm caption format:  uv run python scripts/train_lora.py --help
# 3. train (use .venv/bin/python so a cu128/Blackwell torch isn't resynced away;
#    note the flag is --save_dir, not --output_dir):
.venv/bin/python scripts/train_lora.py --model medium-base \
    --data_dir /workspace/sa3_data --rank 16 --adapter_type dora-rows \
    --steps 1000 --exclude seconds_total --save_dir /workspace/lora_beats
# 4. generate with it:
uv run python /workspace/toolkit/scripts/sa3_workflow.py plan \
    --model medium-base --lora lora_out/lora_step1000.safetensors \
    --plan /workspace/toolkit/prompts/pack_plan.example.json --out /workspace/generated
CMD
