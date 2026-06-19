#!/usr/bin/env python3
"""
vocal_guide.py  -  Bridge the toolkit to ACE Studio (or any vocal synth).

ACE Studio turns MIDI + lyrics into sung/rapped vocals, but it's GUI/VST-driven
(no CLI). This script prepares ACE's inputs from a beat: a flow/melody MIDI
aligned to the beat's KEY + BPM + bar grid, plus a syllable-segmented lyric file.
Import the MIDI into ACE Studio, paste the lyrics onto the notes, pick a Rap (or
sung) voice, render, then drop the vocal over the beat in Ableton via ACE Bridge.

Two styles:
  rap   monotone/2-note flow, one note per syllable on a swung 16th grid -
        a rhythmic scaffold to rap against (you'll humanize timing in ACE).
  sung  a simple stepwise topline walking the key's scale - a melody starting point.

BPM/key come from --bpm/--key, or are read from a beat's Deep Listen sidecar
(<beat>.caption.json / .analysis.json) when you pass --beat.

Usage:
    python vocal_guide.py --beat "F:/RAP_ARCHIVES/raw_beats/MyBeat_instrumental.mp3" \
        --lyrics verse.txt --style rap --out guide
    python vocal_guide.py --bpm 90 --key "F minor" --lyrics verse.txt --style sung --out hook
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Builds a flow MIDI aligned to the beat's key+BPM grid + a syllable-segmented lyric file for ACE Studio.
#   - rap = rhythmic monotone scaffold (humanize in ACE); sung = stepwise contour in the key's scale.
#   - ACE can't be driven headlessly - you import the MIDI + paste lyrics in ACE, then ACE Bridge plays it in Ableton.
# ---------------------------------------------------------------------------
import argparse
import json
import re
from pathlib import Path

import mido

PITCH = {"C":0,"C#":1,"DB":1,"D":2,"D#":3,"EB":3,"E":4,"F":5,"F#":6,"GB":6,
         "G":7,"G#":8,"AB":8,"A":9,"A#":10,"BB":10,"B":11}
MAJOR_STEPS = [0,2,4,5,7,9,11]
MINOR_STEPS = [0,2,3,5,7,8,10]


def parse_key(key):
    """'F minor' / 'Fmin' / 'A' -> (tonic_pitch_class, scale_steps)."""
    if not key:
        return 9, MINOR_STEPS  # default A minor
    k = key.strip().lower()
    minor = "min" in k
    m = re.match(r"\s*([a-g][#b]?)", k)
    pc = PITCH.get(m.group(1).upper(), 9) if m else 9
    return pc, (MINOR_STEPS if minor else MAJOR_STEPS)


def count_syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def syllabify_line(line):
    """Return list of syllable-ish tokens (word-level; ACE maps per note)."""
    out = []
    for word in line.split():
        s = count_syllables(word)
        out += ([word] if s <= 1 else
                # crude split into s chunks for note alignment
                [word[i*len(word)//s:(i+1)*len(word)//s] or word for i in range(s)])
    return out


def read_beat_meta(beat_path):
    p = Path(beat_path)
    for ext in (".caption.json", ".analysis.json"):
        for cand in (p.with_suffix(p.suffix + ext), p.with_name(p.stem + ext)):
            if cand.exists():
                d = json.loads(cand.read_text(encoding="utf-8"))
                bpm = d.get("bpm") or d.get("musical", {}).get("bpm")
                key = d.get("key") or d.get("musical", {}).get("key")
                return bpm, key
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beat", help="Beat audio (reads BPM/key from its Deep Listen sidecar)")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--key", help='e.g. "F minor"')
    ap.add_argument("--lyrics", required=True, help="Lyrics .txt (one line per bar-phrase)")
    ap.add_argument("--style", choices=["rap", "sung"], default="rap")
    ap.add_argument("--bars-per-line", type=int, default=1, help="How many bars each lyric line spans")
    ap.add_argument("--out", required=True, help="Output prefix (writes <out>.mid + <out>_lyrics.txt)")
    args = ap.parse_args()

    bpm, key = args.bpm, args.key
    if args.beat:
        b, k = read_beat_meta(args.beat)
        bpm = bpm or b
        key = key or k
    bpm = bpm or 90
    tonic, scale = parse_key(key)
    base = 57 + tonic % 12  # around A3-ish register for vocals
    lyric_lines = [l.strip() for l in Path(args.lyrics).read_text(encoding="utf-8").splitlines()]
    lyric_lines = [l for l in lyric_lines if l and not (l.startswith("[") and l.endswith("]"))]

    tpb = 480
    mid = mido.MidiFile(ticks_per_beat=tpb)
    track = mido.MidiTrack(); mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(int(bpm))))
    step = tpb // 4  # 16th note
    swing = int(step * 0.12)

    out_syllables = []
    t_cursor = 0
    for li, line in enumerate(lyric_lines):
        sylls = syllabify_line(line)
        out_syllables.append(" ".join(sylls))
        if not sylls:
            t_cursor += args.bars_per_line * 16 * step
            continue
        slots = args.bars_per_line * 16
        positions = [round(i * slots / len(sylls)) for i in range(len(sylls))]
        line_start = t_cursor
        last_tick = line_start
        for i, (syl, pos) in enumerate(zip(sylls, positions)):
            on = line_start + pos * step + (swing if pos % 2 else 0)
            dur = max(step, step)  # 16th
            if args.style == "rap":
                note = base if i % 4 != 3 else base + 7  # mostly monotone, lift every 4th
            else:
                deg = scale[(i + (i // len(scale))) % len(scale)]
                note = base + deg
            track.append(mido.Message("note_on", note=note, velocity=90, time=max(0, on - last_tick)))
            track.append(mido.Message("note_off", note=note, velocity=0, time=dur))
            last_tick = on + dur
        t_cursor = line_start + slots * step

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    mid.save(args.out + ".mid")
    Path(args.out + "_lyrics.txt").write_text("\n".join(out_syllables), encoding="utf-8")
    print(f"Wrote {args.out}.mid  ({int(bpm)} BPM, key {key or 'A minor'}, style {args.style})")
    print(f"Wrote {args.out}_lyrics.txt  ({len(lyric_lines)} lines)")
    print("\nIn ACE Studio: New track -> import the .mid -> paste lyrics onto the notes "
          "-> pick a Rap/sung voice -> render. Then in Ableton, ACE Bridge plays it "
          "tempo-synced over your beat.")


if __name__ == "__main__":
    main()
