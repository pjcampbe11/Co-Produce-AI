#!/usr/bin/env python3
"""
mp3_to_wav.py  -  Batch-convert MP3 (and other compressed audio) to WAV.

Operator notes (the non-obvious bits):
  - This DECODES lossy audio to PCM; it does NOT restore quality MP3 discarded.
    Use it for DAW/toolkit compatibility, not to "upgrade" a lossy file.
  - Prefers ffmpeg (exact control over sample rate / bit depth); falls back to
    librosa+soundfile if ffmpeg isn't on PATH.
  - Recursive; --mirror keeps subfolders; --resume skips already-converted files.
  - Also accepts .m4a/.aac/.ogg/.opus/.flac/.aif/.aiff inputs, not just .mp3.

Usage:
    python mp3_to_wav.py --input "F:/RAP_ARCHIVES/mp3" --output "F:/RAP_ARCHIVES/wav" --mirror --resume
    python mp3_to_wav.py --input song.mp3 --output out --sample-rate 44100 --bit-depth 24
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SRC_EXTS = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".aif", ".aiff", ".wma"}
BITFMT = {16: "pcm_s16le", 24: "pcm_s24le", 32: "pcm_s32le"}


def convert_ffmpeg(src, dst, sr, bit):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-c:a", BITFMT.get(bit, "pcm_s16le")]
    if sr:
        cmd += ["-ar", str(sr)]
    cmd.append(str(dst))
    subprocess.run(cmd, check=True)


def convert_librosa(src, dst, sr, bit):
    import librosa
    import soundfile as sf
    y, srr = librosa.load(str(src), sr=(sr or None), mono=False)
    if y.ndim == 1:
        y = y[None, :]
    subtype = {16: "PCM_16", 24: "PCM_24", 32: "PCM_32"}.get(bit, "PCM_16")
    sf.write(str(dst), y.T, srr, subtype=subtype)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="File or folder (searched recursively)")
    ap.add_argument("--output", required=True, help="Output folder")
    ap.add_argument("--sample-rate", type=int, default=0, help="Resample Hz (0 = keep source)")
    ap.add_argument("--bit-depth", type=int, default=16, choices=[16, 24, 32])
    ap.add_argument("--mirror", action="store_true", help="Recreate input subfolders in output")
    ap.add_argument("--resume", action="store_true", help="Skip files whose .wav already exists")
    args = ap.parse_args()

    in_path, out_root = Path(args.input), Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    have_ffmpeg = shutil.which("ffmpeg") is not None
    if not have_ffmpeg:
        print("ffmpeg not found - falling back to librosa (install ffmpeg for speed/accuracy: winget install ffmpeg)")

    files = ([in_path] if in_path.is_file()
             else sorted(p for p in in_path.rglob("*") if p.suffix.lower() in SRC_EXTS))
    if not files:
        sys.exit("No compressed audio files found.")

    ok = skipped = failed = 0
    for i, f in enumerate(files, 1):
        if args.mirror and in_path.is_dir():
            dst = (out_root / f.relative_to(in_path)).with_suffix(".wav")
        else:
            dst = out_root / (f.stem + ".wav")
        if args.resume and dst.exists():
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if have_ffmpeg:
                convert_ffmpeg(f, dst, args.sample_rate, args.bit_depth)
            else:
                convert_librosa(f, dst, args.sample_rate, args.bit_depth)
            ok += 1
            print(f"[{i}/{len(files)}] {f.name} -> {dst.name}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(files)}] FAILED {f.name}: {e}")
    print(f"\n=== {ok} converted, {skipped} skipped, {failed} failed -> {out_root}/ ===")
    print("Note: this is a lossy->PCM decode; it does not recover MP3-discarded quality.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
