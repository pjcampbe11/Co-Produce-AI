#!/usr/bin/env bash
# Beat Toolkit - one-shot pod bootstrap.
#
# Clones the repo onto the pod (prefers the network volume at /workspace so it
# persists), installs Python deps, and prints what to run next. Idempotent: if
# the repo already exists it just pulls + reinstalls.
#
# Usage on a fresh pod (paste into the pod's SSH session):
#   curl -fsSL https://raw.githubusercontent.com/pjcampbe11/Beat-Toolkit/main/cloud/pod_bootstrap.sh | bash
# Private-repo clone? Provide a token first (cleared from env after use):
#   GH_TOKEN=ghp_xxx bash pod_bootstrap.sh
# Optional env:
#   WORKDIR=/workspace        where to clone (default: /workspace if writable, else $HOME)
#   GENIUS_TOKEN=...          enables genius_lookup.py later
#   TAG_ENGINE=qwen3-omni     used only by the optional auto-run line below
set -euo pipefail

REPO_HTTPS="https://github.com/pjcampbe11/Beat-Toolkit.git"
WORKDIR="${WORKDIR:-/workspace}"
# Fall back to $HOME if /workspace isn't mounted/writable on this pod.
if ! mkdir -p "$WORKDIR" 2>/dev/null || [ ! -w "$WORKDIR" ]; then
  echo "[bootstrap] $WORKDIR not writable - using \$HOME instead"
  WORKDIR="$HOME"
fi
cd "$WORKDIR"

# Build clone URL (inject token only if the repo is private and a token is given).
CLONE_URL="$REPO_HTTPS"
if [ -n "${GH_TOKEN:-}" ]; then
  CLONE_URL="https://x-access-token:${GH_TOKEN}@github.com/pjcampbe11/Beat-Toolkit.git"
fi

if [ -d Beat-Toolkit/.git ]; then
  echo "[bootstrap] repo exists - pulling latest"
  git -C Beat-Toolkit pull --ff-only || true
else
  echo "[bootstrap] cloning into $WORKDIR/Beat-Toolkit"
  git clone "$CLONE_URL" Beat-Toolkit
fi
unset GH_TOKEN  # don't leave the token in the environment

cd Beat-Toolkit
echo "[bootstrap] installing Python deps"
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

# Keep big model caches on the persistent volume so future pods skip re-downloads.
if [ -d /workspace ] && [ -w /workspace ]; then
  export HF_HOME=/workspace/.cache/huggingface
  export TORCH_HOME=/workspace/.cache/torch
  mkdir -p "$HF_HOME" "$TORCH_HOME"
  echo "[bootstrap] HF_HOME=$HF_HOME  TORCH_HOME=$TORCH_HOME (persisted on the volume)"
fi

cat <<NEXT

[bootstrap] READY in $WORKDIR/Beat-Toolkit
Next steps:
  cd $WORKDIR/Beat-Toolkit/scripts

  # GPU tagging (the heavy engine that won't fit a small local card):
  python auto_tag.py --stems-dir /workspace/raw_beats --source beat --engine ${TAG_ENGINE:-qwen3-omni} --resume

  # then enrich + caption:
  python genius_lookup.py --beats /workspace/raw_beats --resume   # needs GENIUS_TOKEN
  python build_captions.py --beats /workspace/raw_beats

Upload beats first with either:
  (local)  scp -P <PORT> -i <KEY> -r "F:\\RAP_ARCHIVES\\raw_beats" root@<POD_IP>:/workspace/
  (S3)     aws s3 cp ... s3://d39orqnjjh/raw_beats/  (see cloud/connect.md)
NEXT
