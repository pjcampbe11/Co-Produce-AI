"""RunPod Serverless handler for Beat Toolkit.

Operator notes
--------------
Wraps the existing toolkit scripts behind a single RunPod Serverless endpoint so
you can call beat generation / tagging / flips over HTTPS with pay-per-request,
scale-to-zero billing (see README section 33).

The contract: RunPod hands every job a dict `event["input"]`. We switch on an
`input["task"]` field and dispatch to the matching script, returning
JSON-serializable output (audio is base64-encoded WAV bytes under "wav_b64").

Local test (no Docker, no cloud):
    pip install runpod
    python serverless/handler.py --test_input '{"input":{"task":"beat","style":"boom_bap","bpm":90}}'
"""
import base64
import os
import subprocess
import sys
import tempfile

import runpod

# Run scripts relative to repo root regardless of where the worker starts.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _wav_b64(path):
    """Read a WAV file off disk and return it base64-encoded for JSON transport."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def handler(event):
    """event['input'] = {"task": "beat"|"tag"|"flip", ...task-specific args}."""
    inp = event.get("input", {}) or {}
    task = inp.get("task", "beat")
    out = tempfile.mkdtemp()

    if task == "beat":                              # beats from your own samples
        wav = os.path.join(out, "beat.wav")
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "beat_builder.py"),
                        "--style", str(inp.get("style", "boom_bap")),
                        "--bpm", str(inp.get("bpm", 90)),
                        "--out", wav], check=True, cwd=REPO)
        return {"wav_b64": _wav_b64(wav), "style": inp.get("style", "boom_bap")}

    if task == "tag":                               # heuristic tagger (no model download)
        sys.path.insert(0, os.path.join(REPO, "scripts"))
        import auto_tag
        tags, cap = auto_tag.caption_heuristic(inp["path"])
        return {"tags": tags, "caption": cap}

    if task == "flip":                              # audio-to-audio derive a new sound
        wav = os.path.join(out, "flip.wav")
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "audio2audio.py"),
                        "--input", inp["path"], "--prompt", inp.get("prompt", ""),
                        "--strength", str(inp.get("strength", 0.6)),
                        "--out", wav], check=True, cwd=REPO)
        return {"wav_b64": _wav_b64(wav)}

    return {"error": f"unknown task '{task}'"}


# RunPod's entrypoint. With no endpoint env it falls into local test mode and
# honors the --test_input CLI flag shown in the docstring above.
runpod.serverless.start({"handler": handler})
