#!/usr/bin/env bash
# ACE-Step 1.5 setup (MIT-licensed engine). Cloud pod default; runs locally too.
# Min VRAM: ~6 GB (2B turbo, DiT-only) ... 20 GB+ for XL. Models auto-download on first run.
set -euo pipefail
cd /workspace
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5
uv sync
echo "Start the REST API (used by ace_step_workflow.py):"
echo "  ACESTEP_API_HOST=0.0.0.0 uv run acestep-api      # http://<pod>:8001"
echo "Or the Gradio UI (has one-click LoRA training):"
echo "  uv run acestep                                    # http://<pod>:7860"
echo "Then from the toolkit:"
echo "  python /workspace/toolkit/scripts/ace_step_workflow.py generate --plan prompts/pack_plan.example.json --out generated_ace"
