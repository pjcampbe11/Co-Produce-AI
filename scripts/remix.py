#!/usr/bin/env python3
"""
remix.py  -  AI remix: transform a song into another genre, or mash up genres.

Pure remix tool: feed it a finished track (or beat) and it re-imagines it as
hip-hop, rock/metal, dubstep, or drum & bass - or a MASHUP fusing a target
genre with the track's current vibe. Built on audio-to-audio (the model treats
your track as the diffusion init; --strength sets how far it transforms).

Backend: Stable Audio (your fine-tuned ckpt, or --pretrained base). Same engine
as audio2audio.py, wrapped with genre presets so it acts only as a remixer.

    full   -> become the target genre (strength ~0.6)
    mashup -> fuse target with the original (strength ~0.4, hybrid prompt)

Usage:
    python remix.py --pretrained stabilityai/stable-audio-open-1.0 \
        --input song.wav --genre dnb --mode full --variations 3 --out remixes/
    python remix.py --model-config model_config.json --ckpt hiphop_v1.ckpt \
        --input song.wav --genre rockmetal --mode mashup --current "boom bap hip hop" --out remixes/
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sat_common  # noqa: E402

GENRES = {
    "hiphop":    "hip hop remix, boom bap drums, dusty soul samples, vinyl texture, head-nod swing",
    "rockmetal": "rock metal remix, heavy distorted electric guitars, live drum kit, aggressive driving energy",
    "dubstep":   "dubstep remix, halftime 140 BPM feel, heavy wobble bass, gritty growls, big drop",
    "dnb":       "drum and bass remix, 174 BPM, fast chopped breakbeat, rolling reese bass, energetic",
}


def main():
    ap = argparse.ArgumentParser()
    sat_common.add_model_args(ap)
    ap.add_argument("--input", required=True, help="Song/beat to remix")
    ap.add_argument("--genre", required=True, choices=sorted(GENRES))
    ap.add_argument("--mode", choices=["full", "mashup"], default="full")
    ap.add_argument("--current", default="", help="(mashup) the track's current genre, for the fusion prompt")
    ap.add_argument("--strength", type=float, help="Override 0..1 (default full 0.6 / mashup 0.4)")
    ap.add_argument("--variations", type=int, default=3)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sat_common.validate_model_args(ap, args)

    target = GENRES[args.genre]
    if args.mode == "mashup":
        cur = args.current or "the original track"
        prompt = f"{target}, fused with {cur}, hybrid genre mashup, blended"
        strength = args.strength if args.strength is not None else 0.4
    else:
        prompt = target
        strength = args.strength if args.strength is not None else 0.6

    model, cfg, device = sat_common.load_model(args.model_config, args.ckpt, args.pretrained)
    sr = cfg["sample_rate"]
    init = sat_common.load_audio_file(args.input, sr, device)
    n = init.shape[1]
    seconds = min(n / sr, cfg["sample_size"] / sr)
    out_dir = Path(args.out)
    stem = Path(args.input).stem
    print(f"Remix [{args.mode}] -> {args.genre} (strength {strength})")
    print(f"Prompt: {prompt}")
    for v in range(1, args.variations + 1):
        audio, seed = sat_common.generate(model, cfg, prompt, seconds, device,
                                          steps=args.steps, cfg_scale=args.cfg,
                                          init_audio=init, strength=strength)
        name = f"{stem}_{args.genre}_{args.mode}_v{v:02d}_seed{seed}.wav"
        sat_common.save_wav(audio[:, :n], out_dir / name, sr)
        print(f"  {v}/{args.variations} -> {name}")
    print(f"\nDone -> {out_dir}/  (run postprocess.py on keepers)")


if __name__ == "__main__":
    main()
