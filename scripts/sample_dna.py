#!/usr/bin/env python3
"""
sample_dna.py  -  Turn a catalog's SAMPLE LINEAGE into ORIGINAL beat prompts.

Reads the per-song reference files made by playlist_catalog.py (which record each
track's samples/interpolations as Genius metadata) and distills the *sampling
tradition* of the catalog - which source artists/eras get flipped - into NEW,
original generation prompts you can feed to the generators.

It NEVER copies the sampled works. It uses only factual credits (who sampled
what) to infer a vibe, then writes original text prompts like "dusty 70s soul
chop, warm Rhodes, vinyl crackle, boom-bap drums" - music you create fresh in
that lineage. That's the legal, creative core of Co-Produce AI.

Usage
-----
  python scripts/sample_dna.py --catalog catalog --report
  python scripts/sample_dna.py --catalog catalog --pack-name "Crate DNA Vol 1" \
      --bpm 90 --key "F minor" --out prompts/sample_dna.json
  # then generate from it:
  python scripts/sa3_workflow.py plan --plan prompts/sample_dna.json --out generated
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Uses ONLY factual sample credits (who sampled what) from the catalog to infer a vibe,
#   - then emits ORIGINAL generation prompts in that tradition - it never reproduces the
#   - sampled works. --flips/--flip-input can also drive audio2audio.py to render fresh
#   - chops from YOUR source audio in the detected era's texture.
#   - Targets Python 3.11; pure-Python, deps via requirements.txt.
# ---------------------------------------------------------------------------
import argparse
import json
import os
import re
import sys
from collections import Counter

# Texture palettes by era - used to craft ORIGINAL prompts (no copyrighted refs).
ERA_VIBES = {
    "1960s": "warm 60s soul/gospel chop, tape saturation, live drums, vinyl crackle",
    "1970s": "dusty 70s soul/funk chop, Rhodes and horns, breakbeat drums, vinyl crackle",
    "1980s": "80s boogie/synth-funk chop, analog keys, punchy drums",
    "1990s": "90s soul/jazz loop, filtered chords, swung boom-bap drums, sampled feel",
    "2000s": "2000s soul-sample bounce, chipmunk-soul pitch, knocking drums",
    "modern": "modern soul-sample trap, lush pads, 808 sub, crisp hats",
}


# Chop techniques layered onto the era vibe to suggest FRESH flips (original output).
CHOP_MOVES = [
    "chopped and re-looped", "pitched-up chipmunk-soul", "half-time and filtered",
    "time-stretched and warped", "reversed-tail swell", "vinyl-crackle one-bar loop",
    "sliced into stabs", "low-passed and dusty",
]


def _decade(date_str):
    m = re.search(r"(19|20)\d{2}", date_str or "")
    if not m:
        return None
    y = int(m.group(0))
    return f"{(y//10)*10}s" if y < 2010 else "modern"


def load_catalog(folder):
    recs = []
    for f in os.listdir(folder):
        if f.endswith(".json"):
            try:
                recs.append(json.load(open(os.path.join(folder, f), encoding="utf-8")))
            except Exception:
                pass
    return recs


def analyze(recs):
    sampled_artists = Counter()
    decades = Counter()
    producers = Counter()
    total_samples = 0
    for r in recs:
        for s in (r.get("samples", []) + r.get("interpolates", [])):
            total_samples += 1
            artist = s.split(" - ")[0].strip()
            if artist and artist != "?":
                sampled_artists[artist] += 1
        d = _decade(r.get("release_date", ""))
        if d:
            decades[d] += 1
        for p in (r.get("producer", "") or "").split(","):
            p = p.strip()
            if p:
                producers[p] += 1
    return {"sampled_artists": sampled_artists, "decades": decades,
            "producers": producers, "total_samples": total_samples,
            "songs": len(recs)}


def build_plan(stats, args):
    # dominant era drives the texture palette (fallback: 1990s boom bap)
    era = (stats["decades"].most_common(1)[0][0] if stats["decades"] else "1990s")
    vibe = ERA_VIBES.get(era, ERA_VIBES["1990s"])
    bpm, key = args.bpm, args.key
    keyp = f", key of {key}" if key else ""
    return {
        "pack_name": args.pack_name,
        "bpm": bpm,
        "_derived_from": {
            "songs": stats["songs"], "sample_refs": stats["total_samples"],
            "dominant_era": era,
            "top_sampled_sources": [a for a, _ in stats["sampled_artists"].most_common(10)],
            "note": "Original prompts inspired by the catalog's sampling tradition. "
                    "No copyrighted audio or lyrics are used or reproduced."},
        "categories": [
            {"name": "MelodicLoops", "count": 25, "seconds": 16.0,
             "prompt": f"hip hop, melodic loops, {vibe}, {bpm} BPM{keyp}, original sample-style chop"},
            {"name": "DrumLoops", "count": 25, "seconds": 8.0,
             "prompt": f"hip hop, drum loops, {bpm} BPM, dusty break, swung groove, vinyl texture"},
            {"name": "Bass", "count": 15, "seconds": 4.0,
             "prompt": f"hip hop, bass loops, {bpm} BPM{keyp}, round upright/sub bass, sampled feel"},
            {"name": "Kicks", "count": 30, "seconds": 1.5,
             "prompt": "hip hop, drums oneshots, kicks, punchy boom bap kick, dusty vinyl texture"},
            {"name": "Snares", "count": 30, "seconds": 1.5,
             "prompt": "hip hop, drums oneshots, snares, cracking boom bap snare, dusty vinyl texture"},
            {"name": "Stems", "count": 10, "seconds": 30.0,
             "prompt": f"hip hop, full instrumental, {vibe}, {bpm} BPM{keyp}, soulful sampled beat with drums and bass"},
        ],
    }


def build_flip_prompts(stats, args):
    """N original flip prompts in the catalog's dominant-era texture."""
    era = (stats["decades"].most_common(1)[0][0] if stats["decades"] else "1990s")
    vibe = ERA_VIBES.get(era, ERA_VIBES["1990s"])
    keyp = f", key of {args.key}" if args.key else ""
    out = []
    for i in range(args.flips):
        move = CHOP_MOVES[i % len(CHOP_MOVES)]
        out.append({
            "name": f"flip_{i+1:02d}_{move.split()[0]}",
            "prompt": f"hip hop sample flip, {vibe}, {move}, {args.bpm} BPM{keyp}, original chop",
            "strength": args.strength,
        })
    return out, era


def run_flips(prompts, args):
    """Drive audio2audio.py once per flip prompt on --flip-input (subprocess)."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    a2a = os.path.join(here, "audio2audio.py")
    model_args = []
    if args.model_config and args.ckpt:
        model_args = ["--model-config", args.model_config, "--ckpt", args.ckpt]
    elif args.pretrained:
        model_args = ["--pretrained", args.pretrained]
    for fp in prompts:
        cmd = [sys.executable, a2a, "--input", args.flip_input, "--prompt", fp["prompt"],
               "--strength", str(fp["strength"]), "--variations", str(args.variations),
               "--out", os.path.join(args.out_dir, fp["name"])] + model_args
        print("$ " + " ".join(cmd))
        subprocess.run(cmd, check=False)


def main():
    ap = argparse.ArgumentParser(description="Distill catalog sample lineage into original beat prompts.")
    ap.add_argument("--catalog", default="catalog", help="folder of playlist_catalog.py JSON files")
    ap.add_argument("--pack-name", default="Crate DNA Vol 1")
    ap.add_argument("--bpm", type=int, default=90)
    ap.add_argument("--key", default="")
    ap.add_argument("--out", help="write a pack-plan JSON here (feeds generate.py / sa3_workflow.py)")
    ap.add_argument("--report", action="store_true", help="print the lineage summary")
    # --- flip seeding (audio2audio) ---
    ap.add_argument("--flips", type=int, default=0, help="generate N era-textured flip prompts")
    ap.add_argument("--flips-out", default="prompts/sample_dna_flips.json", help="where to write the flip prompts")
    ap.add_argument("--flip-input", help="a source WAV - if set, runs audio2audio.py for each flip prompt")
    ap.add_argument("--strength", type=float, default=0.55, help="audio2audio strength 0-1")
    ap.add_argument("--variations", type=int, default=2, help="audio2audio variations per flip")
    ap.add_argument("--out-dir", default="flips", help="output dir for generated flips")
    ap.add_argument("--pretrained", default="stabilityai/stable-audio-open-1.0", help="HF model for flips")
    ap.add_argument("--model-config", default="", help="your model_config.json (with --ckpt)")
    ap.add_argument("--ckpt", default="", help="your ckpt (with --model-config)")
    args = ap.parse_args()

    if not os.path.isdir(args.catalog):
        sys.exit(f"No catalog folder '{args.catalog}'. Run playlist_catalog.py first.")
    recs = load_catalog(args.catalog)
    if not recs:
        sys.exit(f"No .json files in '{args.catalog}'.")
    stats = analyze(recs)

    if args.report or not args.out:
        print(f"Catalog: {stats['songs']} songs, {stats['total_samples']} sample/interpolation refs")
        print("Dominant eras:", ", ".join(f"{d}:{n}" for d, n in stats["decades"].most_common(5)) or "n/a")
        print("Most-sampled sources:", ", ".join(f"{a}({n})" for a, n in stats["sampled_artists"].most_common(10)) or "n/a")
        print("Top producers:", ", ".join(f"{p}({n})" for p, n in stats["producers"].most_common(10)) or "n/a")

    if args.out:
        plan = build_plan(stats, args)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(plan, open(args.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"\nwrote pack plan -> {args.out}  (generate with: "
              f"python scripts/sa3_workflow.py plan --plan {args.out} --out generated)")

    if args.flips:
        flips, era = build_flip_prompts(stats, args)
        os.makedirs(os.path.dirname(args.flips_out) or ".", exist_ok=True)
        json.dump({"era": era, "flips": flips}, open(args.flips_out, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"\nwrote {len(flips)} flip prompts ({era} texture) -> {args.flips_out}")
        if args.flip_input:
            os.makedirs(args.out_dir, exist_ok=True)
            run_flips(flips, args)
        else:
            print("  add --flip-input <source.wav> to render these as audio2audio flips, e.g.:")
            print(f"  python scripts/sample_dna.py --catalog {args.catalog} --flips {args.flips} "
                  f"--flip-input mychop.wav --out-dir flips")


if __name__ == "__main__":
    main()
