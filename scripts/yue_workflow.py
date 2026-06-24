#!/usr/bin/env python3
"""
yue_workflow.py  -  Generate full songs (vocals + instrumental) from LYRICS with YuE.

YuE (github.com/multimodal-art-projection/YuE) is an Apache-2.0 open foundation
model - the closest open alternative to Suno for lyric-driven songs. It turns a
genre/style tag line + lyrics into a coherent multi-minute track with sung/rapped
vocals. Commercial use is permitted (Apache-2.0). Pairs perfectly with your own
lyrics (lyric_generate.py) for a finished track in your flow.

This is a thin CLI wrapper around YuE's `infer.py`. You point it at your local
YuE checkout + downloaded stage-1/stage-2 checkpoints (see cloud/yue_setup.sh).

Operator notes (the non-obvious bits):
  - YuE wants TWO files: a genre/tags line and the lyrics, split into [verse]/[chorus] sections.
  - Stage models: an EN/ZH stage-1 (e.g. YuE-s1-7B-anneal-en-cot) + stage-2 upsampler.
  - GPU heavy: ~16-24 GB VRAM for the 7B; use a pod (cloud/yue_setup.sh). CPU is not viable.
  - We write the two temp input files, then call YuE's inference/infer.py with your args.

Usage:
    python yue_workflow.py --yue ~/YuE --lyrics verse.txt \
        --genre "hip hop, boom bap, male rapper, dusty, vinyl, 90 bpm" \
        --stage1 m-a-p/YuE-s1-7B-anneal-en-cot --stage2 m-a-p/YuE-s2-1B-general \
        --segments 2 --out songs
"""
import argparse
import os
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser(description="Lyrics -> full song with YuE (Apache-2.0).")
    ap.add_argument("--yue", required=True, help="path to your YuE repo checkout")
    ap.add_argument("--lyrics", required=True, help="lyrics .txt with [verse]/[chorus] tags")
    ap.add_argument("--genre", required=True, help="genre/style tag line, e.g. 'hip hop, boom bap, male rapper, 90 bpm'")
    ap.add_argument("--stage1", default="m-a-p/YuE-s1-7B-anneal-en-cot", help="stage-1 model id/path")
    ap.add_argument("--stage2", default="m-a-p/YuE-s2-1B-general", help="stage-2 (upsampler) model id/path")
    ap.add_argument("--segments", type=int, default=2, help="number of segments to run (length)")
    ap.add_argument("--max-tokens", type=int, default=3000, help="max new tokens for stage-1")
    ap.add_argument("--out", default="songs", help="output folder")
    ap.add_argument("--python", default=sys.executable, help="python to run YuE with")
    ap.add_argument("--install", action="store_true", help="auto-install missing deps (pip/git) then run")
    ap.add_argument("--skip-check", action="store_true", help="skip the engine readiness preflight")
    args = ap.parse_args()

    if not args.skip_check:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import engine_doctor
        if not engine_doctor.preflight('yue', install=args.install, yue=args.yue):
            sys.exit("[yue] deps not ready. Re-run with --install to auto-fix, "
                     "or see cloud/yue_setup.sh. (--skip-check to bypass.)")

    yue = os.path.abspath(os.path.expanduser(args.yue))
    infer = os.path.join(yue, "inference", "infer.py")
    if not os.path.exists(infer):
        sys.exit(f"YuE infer.py not found at {infer}. Clone YuE first (see cloud/yue_setup.sh).")
    os.makedirs(args.out, exist_ok=True)

    # YuE reads genre + lyrics from files; write temp copies so callers can pass inline text too.
    tmp = tempfile.mkdtemp()
    genre_f = os.path.join(tmp, "genre.txt")
    open(genre_f, "w", encoding="utf-8").write(args.genre.strip() + "\n")
    lyrics_src = os.path.abspath(os.path.expanduser(args.lyrics))

    cmd = [args.python, infer,
           "--stage1_model", args.stage1,
           "--stage2_model", args.stage2,
           "--genre_txt", genre_f,
           "--lyrics_txt", lyrics_src,
           "--run_n_segments", str(args.segments),
           "--stage2_batch_size", "4",
           "--output_dir", os.path.abspath(args.out),
           "--max_new_tokens", str(args.max_tokens)]
    print("$ " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=os.path.join(yue, "inference")).returncode
    if rc == 0:
        print(f"\n[yue] done -> {args.out}")
    else:
        sys.exit(f"[yue] inference exited with code {rc}")


if __name__ == "__main__":
    main()
