#!/usr/bin/env python3
"""
25_song_generate.py  -  Full songs WITH vocals + lyrics (HeartMuLa)

Wraps HeartMuLa (Apache-2.0, github.com/HeartMuLa/heartlib) - an open-source
song foundation model that generates complete songs (vocals + instrumental)
from LYRICS + STYLE TAGS, up to ~6 minutes, multilingual. Apache-2.0 means
true commercial use with no revenue cap (unlike the Stability Community License).

This is the vocals/lyrics path. For INSTRUMENTAL full songs (2-4 min) use:
    python 22_sa3_workflow.py song --model medium --prompt "..." --duration 180 --out song.wav

Setup (see cloud/heartmula_setup.sh):
    git clone https://github.com/HeartMuLa/heartlib && cd heartlib && pip install -e .
    hf download --local-dir ./ckpt HeartMuLa/HeartMuLaGen
    hf download --local-dir ./ckpt/HeartMuLa-oss-3B HeartMuLa/HeartMuLa-oss-3B-happy-new-year
    hf download --local-dir ./ckpt/HeartCodec-oss  HeartMuLa/HeartCodec-oss-20260123

Usage:
    python 25_song_generate.py --heartlib /path/to/heartlib --ckpt /path/to/heartlib/ckpt \
        --lyrics-file my_song.txt --tags "boom bap,hip hop,male vocals,dusty,90 bpm" \
        --duration 3 --out song.mp3
    # or inline lyrics:
    python 25_song_generate.py --heartlib ... --ckpt ... --lyrics-text "[Verse]\nrise and grind..." \
        --tags "trap,dark,808" --out song.mp3

Lyrics use [Intro]/[Verse]/[Chorus]/[Bridge]/[Outro] section tags (see README).
Tags are comma-separated, no spaces between (e.g. piano,happy,romantic).
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heartlib", default=os.environ.get("HEARTLIB_HOME", "./heartlib"),
                    help="Path to the cloned heartlib repo (or set HEARTLIB_HOME)")
    ap.add_argument("--ckpt", help="Path to HeartMuLa ./ckpt dir (default <heartlib>/ckpt)")
    ap.add_argument("--lyrics-file", help="Path to a lyrics .txt (sectioned with [Verse] etc.)")
    ap.add_argument("--lyrics-text", help="Inline lyrics (use \\n for line breaks)")
    ap.add_argument("--tags", required=True, help="Comma-separated style tags, no spaces between")
    ap.add_argument("--duration", type=float, default=3.0, help="Minutes (default 3; max ~6)")
    ap.add_argument("--out", required=True, help="Output audio (.mp3 or .wav)")
    ap.add_argument("--version", default="3B", choices=["3B", "7B"])
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--cfg", type=float, default=1.5)
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--lazy-load", action="store_true",
                    help="Load modules on demand (single-GPU / low VRAM)")
    ap.add_argument("--mula-device", default="cuda")
    ap.add_argument("--codec-device", default="cuda")
    args = ap.parse_args()

    heartlib = Path(args.heartlib)
    run_script = heartlib / "examples" / "run_music_generation.py"
    if not run_script.exists():
        sys.exit(f"HeartMuLa not found at {run_script}. Clone it and pass --heartlib "
                 f"(see cloud/heartmula_setup.sh).")
    ckpt = Path(args.ckpt) if args.ckpt else heartlib / "ckpt"
    if not ckpt.exists():
        sys.exit(f"Checkpoints not found at {ckpt}. Download them (see setup).")

    if not args.lyrics_file and not args.lyrics_text:
        ap.error("Provide --lyrics-file or --lyrics-text.")

    with tempfile.TemporaryDirectory() as tmp:
        lyrics_path = (Path(args.lyrics_file) if args.lyrics_file
                       else Path(tmp) / "lyrics.txt")
        if args.lyrics_text:
            lyrics_path.write_text(args.lyrics_text.replace("\\n", "\n"), encoding="utf-8")
        tags_path = Path(tmp) / "tags.txt"
        tags_path.write_text(args.tags.strip(), encoding="utf-8")

        cmd = [sys.executable, str(run_script),
               f"--model_path={ckpt}",
               "--lyrics", str(lyrics_path),
               "--tags", str(tags_path),
               "--save_path", str(args.out),
               "--max_audio_length_ms", str(int(args.duration * 60 * 1000)),
               "--version", args.version,
               "--temperature", str(args.temperature),
               "--cfg_scale", str(args.cfg),
               "--topk", str(args.topk),
               "--mula_device", args.mula_device,
               "--codec_device", args.codec_device]
        if args.lazy_load:
            cmd += ["--lazy_load", "true"]
        print("Running HeartMuLa:\n  " + " ".join(cmd))
        try:
            subprocess.run(cmd, check=True, cwd=str(heartlib))
        except subprocess.CalledProcessError as e:
            sys.exit(f"HeartMuLa generation failed ({e}). Check GPU memory (try --lazy-load) "
                     f"and that flag names match your heartlib version (python "
                     f"examples/run_music_generation.py --help).")
        print(f"\nSong -> {args.out}")


if __name__ == "__main__":
    main()
