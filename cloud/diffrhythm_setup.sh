#!/usr/bin/env bash
# DiffRhythm setup on a GPU pod (open; fast lyrics -> full song).
set -euo pipefail
cd "${WORKDIR:-/workspace}"
git clone https://github.com/ASLP-lab/DiffRhythm.git || true
cd DiffRhythm
pip install -q -r requirements.txt || pip install -q torch torchaudio transformers accelerate einops soundfile librosa
export HF_HOME=/workspace/.cache/huggingface
echo "READY. Generate from Co-Produce AI:"
echo "  python scripts/diffrhythm_workflow.py --diffrhythm $(pwd) --lyrics verse.lrc \\"
echo "    --prompt 'boom bap hip hop, dusty soul, male rap vocal, 90 bpm' --out drafts"
echo "NOTE: DiffRhythm flag names vary by version - check its README; the wrapper probes common ones."
