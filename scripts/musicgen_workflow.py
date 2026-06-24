#!/usr/bin/env python3
"""
musicgen_workflow.py  -  Prompt -> instrumental, with optional MELODY conditioning.

MusicGen (Meta AudioCraft, commercial-use-OK) turns a text prompt into an
instrumental loop, and - uniquely among your engines - can be CONDITIONED ON A
MELODY: hum or play an idea and it generates a beat around it. Fills the one real
prompt->beat gap in Co-Produce AI. Runs locally via the `audiocraft` package
(pip install audiocraft); no server needed.

Operator notes (the non-obvious bits):
  - Models: facebook/musicgen-small|medium|large (text) and facebook/musicgen-melody
    (melody-conditioned). Melody only works with the *-melody checkpoint.
  - Melody conditioning uses the chromagram of --melody, not its timbre - so a rough
    hum/piano sketch is enough to steer the harmony/contour.
  - GPU strongly recommended for medium/large; small runs on CPU slowly.

Usage:
    python musicgen_workflow.py --prompt "boom bap, dusty soul, 90 bpm" --duration 12 --count 4 --out gen
    python musicgen_workflow.py --prompt "lofi hip hop, warm rhodes" --melody hum.wav \
        --model facebook/musicgen-melody --out gen
"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="Prompt (+ optional melody) -> instrumental with MusicGen.")
    ap.add_argument("--prompt", required=True, help="text prompt")
    ap.add_argument("--melody", default="", help="optional melody WAV to condition on (needs *-melody model)")
    ap.add_argument("--model", default="facebook/musicgen-medium",
                    help="facebook/musicgen-small|medium|large or facebook/musicgen-melody")
    ap.add_argument("--duration", type=float, default=12.0, help="seconds per clip")
    ap.add_argument("--count", type=int, default=4, help="how many clips")
    ap.add_argument("--out", default="musicgen_out", help="output folder")
    ap.add_argument("--cfg", type=float, default=3.0, help="classifier-free guidance scale")
    args = ap.parse_args()

    try:
        import torch  # noqa
        import torchaudio
        from audiocraft.models import MusicGen
    except Exception as e:
        sys.exit(f"Missing deps: {e}\n  pip install audiocraft torch torchaudio")

    if args.melody and "melody" not in args.model:
        print("[warn] --melody given but model is not a *-melody checkpoint; "
              "switching to facebook/musicgen-melody.", file=sys.stderr)
        args.model = "facebook/musicgen-melody"

    os.makedirs(args.out, exist_ok=True)
    print(f"[musicgen] loading {args.model} ...")
    model = MusicGen.get_pretrained(args.model)
    model.set_generation_params(duration=args.duration, cfg_coef=args.cfg)

    prompts = [args.prompt] * args.count
    if args.melody:
        import torchaudio as ta
        wav, sr = ta.load(args.melody)
        melodies = [wav] * args.count
        outs = model.generate_with_chroma(prompts, melodies, sr)
    else:
        outs = model.generate(prompts)

    sr = model.sample_rate
    import torchaudio as ta
    for i, one in enumerate(outs):
        path = os.path.join(args.out, f"musicgen_{i+1:02d}.wav")
        ta.save(path, one.cpu(), sr)
        print(f"[musicgen] wrote {path}")
    print(f"\n[musicgen] done -> {args.out}")


if __name__ == "__main__":
    main()
