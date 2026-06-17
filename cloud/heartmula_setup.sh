#!/usr/bin/env bash
# HeartMuLa setup - full songs with vocals + lyrics (Apache-2.0, commercial OK).
# Needs python 3.10, a CUDA GPU (3B fits ~16-24GB; use --lazy-load on single GPU).
set -euo pipefail
cd /workspace

git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
pip install -e .
pip install -U "huggingface_hub[cli]"

# checkpoints (~ several GB) - go to F:/ai_cache via HF_HOME if you set use_F_drive.ps1
hf download --local-dir ./ckpt HeartMuLa/HeartMuLaGen
hf download --local-dir ./ckpt/HeartMuLa-oss-3B HeartMuLa/HeartMuLa-oss-3B-happy-new-year
hf download --local-dir ./ckpt/HeartCodec-oss  HeartMuLa/HeartCodec-oss-20260123

echo "Ready. Generate a song with vocals:"
cat << 'CMD'
python /workspace/toolkit/scripts/25_song_generate.py \
  --heartlib /workspace/heartlib --ckpt /workspace/heartlib/ckpt \
  --lyrics-file my_song.txt --tags "boom bap,hip hop,male vocals,dusty,90 bpm" \
  --duration 3 --out song.mp3 --lazy-load
CMD
