#!/usr/bin/env bash
# YuE setup on a GPU pod (Apache-2.0; lyrics -> full song with vocals).
# Needs ~16-24 GB VRAM for the 7B stage-1. Run on /workspace so it persists.
set -euo pipefail
cd "${WORKDIR:-/workspace}"
git clone https://github.com/multimodal-art-projection/YuE.git || true
cd YuE
pip install -q -r requirements.txt || pip install -q torch torchaudio transformers accelerate einops soundfile
# Stage models download on first run from HuggingFace (m-a-p/YuE-*). Route cache to the volume:
export HF_HOME=/workspace/.cache/huggingface
echo "READY. Generate from Co-Produce AI:"
echo "  python scripts/yue_workflow.py --yue $(pwd) --lyrics verse.txt \\"
echo "    --genre 'hip hop, boom bap, male rapper, dusty, 90 bpm' --segments 2 --out songs"
