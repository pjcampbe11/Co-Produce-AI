#!/usr/bin/env bash
# The 4 training runs — one LoRA per sample pack. Run from /workspace/stable-audio-3.
# First: bash /workspace/runpod_pack_kit/make_style_datasets.sh
# Runs are sequential (one GPU). Pick each pack's checkpoint by ear from demos @ steps 1500–3500.
set -uo pipefail
train() { # 1:name 2:data_dir
  echo "═══ training: $1 ═══"
  WANDB_MODE=disabled .venv/bin/python scripts/train_lora.py \
    --model medium-base \
    --data_dir "$2" \
    --rank 16 --lora_alpha 16 --adapter_type dora-rows --dropout 0.05 \
    --exclude seconds_total \
    --duration 30 --batch_size 8 --lr 2e-4 --steps 4000 \
    --base_precision bf16 --seed 42 --num_workers 16 \
    --logger csv \
    --save_dir "/workspace/sweeps/${1}_r16a16_lr2e4" \
    --checkpoint_every 500 --demo_every 250 --log_every 50
}
train boombap /workspace/sa3_boombap
train trap    /workspace/sa3_trap
train drill   /workspace/sa3_drill
train lofi    /workspace/sa3_lofi
