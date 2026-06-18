#!/usr/bin/env python3
"""
lyric_analyze.py  -  Profile YOUR lyric style from a folder of .txt files.

Ingests your lyrics, splits into sections (verses/hooks via [Verse]/[Hook]
headers, else blank-line stanzas), and measures: syllables-per-line (flow
density), end-rhyme rate, multisyllabic tendency, vocabulary richness, recurring
themes, and mood mix. Writes:
  - style_profile.json : aggregate stats + a human-readable style summary
  - corpus.jsonl       : cleaned sections (used as few-shot examples by the generator)

Usage:
    python lyric_analyze.py --input "F:/Lyrics" --out lyric_model
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lyric_common as L  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Folder of .txt lyric files")
    ap.add_argument("--out", default="lyric_model", help="Output folder")
    args = ap.parse_args()

    files = sorted(Path(args.input).rglob("*.txt"))
    if not files:
        sys.exit("No .txt files found.")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    corpus, all_words = [], []
    syl_acc, rhyme_acc, ttr_acc = [], [], []
    type_counts = Counter()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for stype, lines in L.split_sections(text):
            if len(lines) < 2:
                continue
            m = L.analyze_lines(lines)
            words = [w for l in lines for w in L.WORD_RE.findall(l.lower())]
            all_words += words
            syl_acc.append(m["avg_syllables_per_line"])
            rhyme_acc.append(m["end_rhyme_rate"])
            ttr_acc.append(m["type_token_ratio"])
            type_counts[stype] += 1
            corpus.append({"type": stype, "lines": lines, "source": f.name, **m})

    if not corpus:
        sys.exit("No usable sections found.")
    avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0
    moods, mood_counts = L.mood_of(all_words)
    themes = L.top_themes(all_words, 20)
    dens = avg(syl_acc)
    flow = "dense/fast" if dens >= 12 else "moderate" if dens >= 8 else "spacious/laid-back"
    rr = avg(rhyme_acc)
    rhyme_desc = "heavy end-rhyme" if rr >= 0.5 else "moderate rhyme" if rr >= 0.25 else "loose/internal-leaning rhyme"

    summary = (f"{flow} flow (~{dens} syllables/line), {rhyme_desc} "
               f"(end-rhyme rate {rr}); vocabulary richness {avg(ttr_acc)}; "
               f"dominant moods: {', '.join(moods) or 'varied'}; "
               f"recurring themes: {', '.join(themes[:10])}.")

    profile = {
        "sections_analyzed": len(corpus),
        "section_types": dict(type_counts),
        "avg_syllables_per_line": dens,
        "flow": flow,
        "avg_end_rhyme_rate": rr,
        "rhyme_style": rhyme_desc,
        "avg_type_token_ratio": avg(ttr_acc),
        "dominant_moods": moods,
        "mood_counts": mood_counts,
        "themes": themes,
        "style_summary": summary,
    }
    (out / "style_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    with open(out / "corpus.jsonl", "w", encoding="utf-8") as fh:
        for c in corpus:
            fh.write(json.dumps(c) + "\n")
    print(f"Analyzed {len(corpus)} sections from {len(files)} files.")
    print("STYLE SUMMARY:\n  " + summary)
    print(f"\nWrote {out}/style_profile.json and {out}/corpus.jsonl")


if __name__ == "__main__":
    main()
