#!/usr/bin/env python3
"""
generate_engine.py  -  One entry point for every Co-Produce AI generation engine.

Instead of remembering which script drives which model, pick an --engine and this
dispatches to the right workflow with a consistent interface. The dashboard, the
SaaS API, and lyric_to_beat.py can all route through here.

Engines
-------
  PROMPT -> beat/instrumental:
    sao        Stable Audio Open 1.0 (full fine-tune)   -> generate.py
    sa3        Stable Audio 3 (LoRA, your-sound)         -> sa3_workflow.py
    ace-step   ACE-Step 1.5 (fast, REST)                 -> ace_step_workflow.py
    musicgen   MusicGen (+ optional --melody)            -> musicgen_workflow.py
  LYRICS -> full song (vocals):
    yue        YuE (lyrics -> 5-min song)                -> yue_workflow.py
    diffrhythm DiffRhythm (fast lyrics -> song)          -> diffrhythm_workflow.py
    heartmula  HeartMuLa (full songs)                    -> song_generate.py

This is a thin, transparent router: it prints and runs the underlying command so
you always see exactly what ran. Engine-specific flags pass through unchanged.

Usage
-----
  python generate_engine.py --engine sa3   --plan prompts/pack_plan.example.json --out generated
  python generate_engine.py --engine musicgen --prompt "boom bap, dusty, 90 bpm" --melody hum.wav --out gen
  python generate_engine.py --engine yue   --yue ~/YuE --lyrics verse.txt --genre "hip hop, 90 bpm" --out songs
  python generate_engine.py --list
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# engine -> (script, kind, one-line description)
ENGINES = {
    "sao":        ("generate.py",            "prompt", "Stable Audio Open 1.0 full fine-tune"),
    "sa3":        ("sa3_workflow.py",        "prompt", "Stable Audio 3 LoRA (your-sound)"),
    "ace-step":   ("ace_step_workflow.py",   "prompt", "ACE-Step 1.5 (fast, REST; also does vocals)"),
    "musicgen":   ("musicgen_workflow.py",   "prompt", "MusicGen (+ melody conditioning)"),
    "yue":        ("yue_workflow.py",        "lyrics", "YuE - lyrics to full song"),
    "diffrhythm": ("diffrhythm_workflow.py", "lyrics", "DiffRhythm - fast lyrics to song"),
    "heartmula":  ("song_generate.py",       "lyrics", "HeartMuLa - full songs w/ vocals"),
}


def main():
    ap = argparse.ArgumentParser(
        description="Unified entry point for all generation engines.",
        epilog="Any flags after --engine are passed through to the underlying workflow.")
    ap.add_argument("--engine", choices=list(ENGINES), help="which engine to run")
    ap.add_argument("--list", action="store_true", help="list engines and exit")
    ap.add_argument("--python", default=sys.executable)
    # parse only our flags; everything else passes through to the sub-script
    args, passthrough = ap.parse_known_args()

    if args.list or not args.engine:
        print("Engines (--engine):")
        for k, (script, kind, desc) in ENGINES.items():
            print(f"  {k:11s} [{kind:6s}] {desc}   ({script})")
        if not args.engine:
            return
        return

    script, kind, _ = ENGINES[args.engine]
    target = SCRIPTS / script
    if not target.exists():
        sys.exit(f"engine script missing: {target}")
    cmd = [args.python, str(target)] + passthrough
    print(f"[generate_engine] {args.engine} ({kind}) -> {script}")
    print("$ " + " ".join(cmd))
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
