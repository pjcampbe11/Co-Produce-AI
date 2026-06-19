#!/usr/bin/env python3
"""
lyric_to_beat.py  -  Turn a (generated) lyric into a beat brief + flow MIDI.

Reads a lyric file, infers its mood + flow density, and proposes a matching beat:
genre, BPM, key, and a generation prompt for your audio model. Also prints the
exact vocal_guide.py command to make the flow MIDI for ACE Studio, and writes a
1-track pack_plan you can feed to sa3_workflow.py / generate.py.

Usage:
    python lyric_to_beat.py --lyrics verses/verse_dark_01.txt --out beat_brief
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Infers a lyric's mood + flow density and maps them to a genre/BPM/key + beat prompt.
#   - Prints the exact sa3_workflow.py and vocal_guide.py commands so the lyric seeds both beat and vocal.
# ---------------------------------------------------------------------------
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lyric_common as L  # noqa: E402

MINOR_KEYS = ["F minor", "C minor", "G minor", "A minor", "D minor", "E minor"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lyrics", required=True)
    ap.add_argument("--genre", default="auto", choices=["auto", "hiphop", "trap", "dnb", "dubstep"])
    ap.add_argument("--out", default="beat_brief")
    args = ap.parse_args()

    text = Path(args.lyrics).read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip() and not L.SECTION_RE.match(l)]
    words = [w for l in lines for w in L.WORD_RE.findall(l.lower())]
    m = L.analyze_lines(lines)
    moods, _ = L.mood_of(words)
    mood = moods[0] if moods else "reflective"
    dens = m["avg_syllables_per_line"]

    genre = args.genre
    if genre == "auto":
        genre = "trap" if mood == "aggressive" else "hiphop"
    # denser flow -> a bit faster; mood nudges it
    bpm = 140 if genre == "trap" else (95 if dens >= 12 else 88)
    key = MINOR_KEYS[len(words) % len(MINOR_KEYS)]  # default minor; deterministic pick
    texture = {"dark": "dark, eerie, dusty", "aggressive": "hard-hitting, gritty",
               "triumphant": "soulful, anthemic", "reflective": "mellow, soulful, vinyl",
               "sad": "melancholic, sparse", "party": "bouncy, energetic",
               "romantic": "warm, smooth"}.get(mood, "soulful, dusty")
    prompt = f"{genre} beat, {mood}, {bpm} BPM, key of {key}, {texture}, instrumental"

    brief = {"genre": genre, "bpm": bpm, "key": key, "mood": mood,
             "flow_syllables_per_line": dens, "beat_prompt": prompt}
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "beat_brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")
    # 1-track pack plan for sa3/generate
    plan = {"pack_name": "LyricBeat", "bpm": bpm,
            "categories": [{"name": "Beat", "count": 3, "seconds": 30, "prompt": prompt}]}
    (out / "pack_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    print(f"Mood: {mood} | flow ~{dens} syl/line -> {genre} @ {bpm} BPM, {key}")
    print(f"Beat prompt: {prompt}\n")
    print("Make the instrumental:")
    print(f'  python sa3_workflow.py song --model medium --duration 60 --out beat.wav --prompt "{prompt}"')
    print("Make the vocal flow MIDI for ACE Studio:")
    print(f'  python vocal_guide.py --bpm {bpm} --key "{key}" --lyrics "{args.lyrics}" --style rap --out flow')
    print(f"\nWrote {out}/beat_brief.json + pack_plan.json")


if __name__ == "__main__":
    main()
