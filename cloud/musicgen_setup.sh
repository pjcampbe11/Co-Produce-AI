#!/usr/bin/env bash
# MusicGen setup (Meta AudioCraft; commercial-use OK). Prompt + optional melody -> instrumental.
set -euo pipefail
pip install -q audiocraft torch torchaudio
echo "READY (no server needed). Examples:"
echo "  python scripts/musicgen_workflow.py --prompt 'boom bap, dusty soul, 90 bpm' --duration 12 --count 4 --out gen"
echo "  python scripts/musicgen_workflow.py --prompt 'lofi, warm rhodes' --melody hum.wav --model facebook/musicgen-melody --out gen"
