#!/usr/bin/env python3
"""
diffrhythm_workflow.py  -  Fast full-song generation from lyrics with DiffRhythm.

DiffRhythm (github.com/ASLP-lab/DiffRhythm) is an open latent-diffusion song
generator (non-autoregressive) that makes full-length tracks with synchronized
vocals + instrumental in seconds - the fast path for drafts/auditions before
committing GPU time to YuE or HeartMuLa. Takes a style prompt + timestamped
lyrics (LRC) or a plain lyrics file.

Thin CLI wrapper around DiffRhythm's infer script. Point it at your checkout
(see cloud/diffrhythm_setup.sh).

Operator notes (the non-obvious bits):
  - Style can be a TEXT prompt or a reference audio clip; we pass text by default.
  - Lyrics are best as .lrc (timestamped) for tight sync; a plain .txt also works.
  - Much lighter/faster than YuE - good for iterating, then re-render the keeper in YuE.

Usage:
    python diffrhythm_workflow.py --diffrhythm ~/DiffRhythm --lyrics verse.lrc \
        --prompt "boom bap hip hop, dusty soul sample, male rap vocal, 90 bpm" --out drafts
"""
import argparse
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description="Lyrics -> fast full song with DiffRhythm (open).")
    ap.add_argument("--diffrhythm", required=True, help="path to your DiffRhythm repo checkout")
    ap.add_argument("--lyrics", required=True, help="lyrics .lrc (timestamped) or .txt")
    ap.add_argument("--prompt", required=True, help="style/text prompt")
    ap.add_argument("--ref-audio", default="", help="optional reference audio for style instead of text")
    ap.add_argument("--out", default="drafts", help="output folder")
    ap.add_argument("--chunked", action="store_true", help="chunked decoding (lower VRAM)")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--install", action="store_true", help="auto-install missing deps (pip/git) then run")
    ap.add_argument("--skip-check", action="store_true", help="skip the engine readiness preflight")
    args = ap.parse_args()

    if not args.skip_check:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import engine_doctor
        if not engine_doctor.preflight('diffrhythm', install=args.install, diffrhythm=args.diffrhythm):
            sys.exit("[diffrhythm] deps not ready. Re-run with --install to auto-fix, "
                     "or see cloud/diffrhythm_setup.sh. (--skip-check to bypass.)")

    dr = os.path.abspath(os.path.expanduser(args.diffrhythm))
    # DiffRhythm's entry script has moved across versions; probe common locations.
    infer = next((p for p in (os.path.join(dr, "infer", "infer.py"),
                              os.path.join(dr, "scripts", "infer.py"),
                              os.path.join(dr, "infer.py")) if os.path.exists(p)), None)
    if not infer:
        sys.exit(f"DiffRhythm infer script not found under {dr}. See cloud/diffrhythm_setup.sh.")
    os.makedirs(args.out, exist_ok=True)

    cmd = [args.python, infer,
           "--lrc-path", os.path.abspath(os.path.expanduser(args.lyrics)),
           "--output-dir", os.path.abspath(args.out)]
    if args.ref_audio:
        cmd += ["--ref-audio-path", os.path.abspath(os.path.expanduser(args.ref_audio))]
    else:
        cmd += ["--ref-prompt", args.prompt]
    if args.chunked:
        cmd += ["--chunked"]
    print("$ " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=dr).returncode
    if rc == 0:
        print(f"\n[diffrhythm] done -> {args.out}")
    else:
        sys.exit(f"[diffrhythm] inference exited with code {rc} "
                 "(flag names vary by version - check its README and adjust this wrapper).")


if __name__ == "__main__":
    main()
