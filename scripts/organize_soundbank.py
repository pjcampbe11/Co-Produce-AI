#!/usr/bin/env python3
"""
organize_soundbank.py
Turn a messy, untagged soundbank into the labeled tag-folder structure the rest
of the toolkit expects (prepare_dataset.py and beat_builder.py).

Classification = filename keywords first, audio analysis as fallback:
  one-shots (<= 2.5s): kick / 808_bass / snare_clap / hat / perc / fx
  longer files:        drum_loop / melodic_loop / vocal / fx / stem

Every decision is written to review.csv with a confidence score. Low-confidence
files go to _review/ for manual sorting - the report tells you what to listen to.
Files are COPIED by default (originals untouched); use --move to relocate.

Usage:
    python organize_soundbank.py --input messy_bank --output organized --dry-run
    python organize_soundbank.py --input messy_bank --output organized
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Classifies filename-keywords FIRST, audio-analysis only as fallback.
#   - Files below --min-confidence go to _review/ for manual sorting.
#   - COPIES by default (originals safe); --move relocates. --resume re-runs safely.
#   - --ai-tags adds local CLAP zero-shot tags after sorting. .vst3 bundles & junk handled.
# ---------------------------------------------------------------------------
import argparse
import csv
import shutil
import sys
from pathlib import Path

import librosa
import numpy as np
from tqdm import tqdm

SR = 22050  # analysis rate (fast); files are copied untouched
ONESHOT_MAX = 2.5
AUDIO_EXTS = {".wav", ".flac", ".aif", ".aiff", ".mp3", ".ogg", ".m4a"}
# production files worth keeping, routed without analysis
NONAUDIO_MAP = {".mid": "midi", ".midi": "midi", ".rx2": "rex_loops",
                ".fxp": "presets", ".fst": "presets", ".nki": "presets/kontakt",
                ".nkm": "presets/kontakt", ".sf2": "presets/soundfonts"}
JUNK_EXTS = {".asd", ".ds_store", ".ini", ".db", ".url", ".txt", ".pdf", ".jpg", ".png", ".gif", ".html", ".nfo", ".m3u"}

# (category, keywords) - first match wins, order matters
KEYWORD_MAP = [
    ("drums_oneshots/808s",   ("808", "sub bass", "subbass")),
    ("drums_oneshots/kicks",  ("kick", "_bd", " bd ", "bassdrum", "bass drum", "bd_")),
    ("drums_oneshots/snares", ("snare", "_sd", "sd_", "clap", "rimshot", "rim shot")),
    ("drums_oneshots/cymbals", ("china", "splash", "crash", "ride bell")),
    ("drums_oneshots/hats",   ("hat", "hh_", "_hh", "hihat", "hi-hat", "cymbal", "ride", "shaker")),
    ("drums_oneshots/percs",  ("perc", "conga", "bongo", "tom", "cowbell", "tamb", "block", "clave")),
    ("drums_loops",           ("drum loop", "drumloop", "break", "drum_loop", "breakbeat",
                               "amen", "blast beat", "blastbeat", "d-beat", "dbeat", "two step", "two-step")),
    ("melodic_loops/bass",    ("bassline", "bass loop", "bass_loop",
                               "reese", "wobble", "neuro", "growl", "sub drop")),
    ("melodic_loops/riffs",   ("riff", "chug", "palm mute", "palm-mute", "djent", "power chord",
                               "powerchord", "tremolo pick")),
    ("melodic_loops/keys",    ("piano", "keys", "rhodes", "organ", "ep_", "wurli")),
    ("melodic_loops/strings", ("string", "violin", "cello", "orchestra")),
    ("melodic_loops/synth",   ("synth", "pad", "lead", "pluck", "arp")),
    ("melodic_loops/guitar",  ("guitar", "gtr")),
    ("melodic_loops/brass",   ("brass", "horn", "trumpet", "sax", "flute")),
    ("vocals",                ("vocal", "vox", "acapella", "chant", "adlib", "ad-lib")),
    ("fx",                    ("fx", "riser", "sweep", "impact", "whoosh", "scratch", "vinyl stop", "transition")),
]


def quick_duration(path: Path):
    """Header-only duration read (no decode). None if unreadable."""
    try:
        import soundfile as sf
        info = sf.info(str(path))
        return info.frames / info.samplerate
    except Exception:
        return None


def classify_by_name(path: Path):
    hay = str(path).lower().replace("\\", "/")
    for category, keys in KEYWORD_MAP:
        if any(k in hay for k in keys):
            # keyword said one-shot, but commercial packs put "hat"/"kick" in
            # LOOP names too - cheap duration check reroutes long files
            if category.startswith("drums_oneshots/"):
                dur = quick_duration(path)
                if dur is not None and dur > ONESHOT_MAX:
                    loop_cat = ("drums_loops" if any(
                        k in hay for k in ("kick", "snare", "hat", "perc", "drum", "cymbal"))
                        else "melodic_loops/unsorted")
                    return loop_cat, 0.8
            return category, 0.9
    return None, 0.0


def classify_by_audio(path: Path):
    """Heuristic audio classification. Returns (category, confidence)."""
    try:
        y, sr = librosa.load(str(path), sr=SR, mono=True, duration=35.0)
    except Exception:
        return "_review", 0.0
    if y.size == 0 or np.abs(y).max() < 1e-4:
        return "_review", 0.0
    y = y / np.abs(y).max()
    dur = len(y) / sr
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    n_onsets = len(onsets)

    if dur <= ONESHOT_MAX:
        zcr = float(librosa.feature.zero_crossing_rate(y).mean())
        # energy ratio below 150 Hz
        spec = np.abs(librosa.stft(y, n_fft=2048)) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        low_ratio = spec[freqs < 150].sum() / max(spec.sum(), 1e-9)
        if low_ratio > 0.55:
            return ("drums_oneshots/808s" if dur > 1.0 else "drums_oneshots/kicks"), 0.7
        if centroid > 5000 and zcr > 0.15:
            return "drums_oneshots/hats", 0.7
        if 1500 < centroid <= 5000 and dur < 1.2:
            return "drums_oneshots/snares", 0.55
        return "drums_oneshots/percs", 0.4

    # longer material: drum loop vs melodic vs stem
    y_harm, y_perc = librosa.effects.hpss(y)
    perc_ratio = float((y_perc ** 2).sum() / max((y ** 2).sum(), 1e-9))
    if dur > 30:
        return "stems", 0.5
    if perc_ratio > 0.6 and n_onsets / max(dur, 0.1) > 2:
        return "drums_loops", 0.65
    if perc_ratio < 0.45:
        return "melodic_loops/unsorted", 0.6
    return "_review", 0.3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--move", action="store_true", help="Move instead of copy")
    ap.add_argument("--dry-run", action="store_true", help="Classify and report only; touch nothing")
    ap.add_argument("--min-confidence", type=float, default=0.5,
                    help="Below this, file goes to _review/ (default 0.5)")
    ap.add_argument("--resume", action="store_true",
                    help="Skip files whose destination already exists (re-run after interruption)")
    ap.add_argument("--include-nonaudio", action="store_true", default=True,
                    help="Route MIDI/REX/presets into midi/, rex_loops/, presets/ (default on)")
    ap.add_argument("--limit", type=int, default=0, help="Process only first N audio files (sampling)")
    ap.add_argument("--ai-tags", action="store_true",
                    help="After organizing, run CLAP zero-shot tagging (pip install laion-clap). "
                         "Writes <file>.tags.json read by prepare_dataset.py")
    args = ap.parse_args()

    in_root, out_root = Path(args.input), Path(args.output)
    if not in_root.is_dir():
        sys.exit(f"Input not found: {in_root}")
    all_files = sorted(p for p in in_root.rglob("*") if p.is_file())
    files, nonaudio = [], []
    for f in all_files:
        ext = f.suffix.lower()
        if ext in AUDIO_EXTS:
            files.append(f)
        elif ext in NONAUDIO_MAP and args.include_nonaudio:
            nonaudio.append(f)
    if not files and not nonaudio:
        sys.exit("No usable files found.")
    if args.limit:
        files = files[: args.limit]

    rows, counts = [], {}
    for f in nonaudio:
        category = NONAUDIO_MAP[f.suffix.lower()]
        counts[category] = counts.get(category, 0) + 1
        rows.append({"file": str(f), "category": category, "confidence": 1.0, "method": "extension"})
        if not args.dry_run:
            dest_dir = out_root / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f.name
            if args.resume and dest.exists():
                continue
            i = 1
            while dest.exists():
                dest = dest_dir / f"{f.stem}_{i}{f.suffix}"
                i += 1
            (shutil.move if args.move else shutil.copy2)(str(f), str(dest))

    for f in tqdm(files, desc="Classifying"):
        category, conf = classify_by_name(f)
        method = "filename"
        if category is None:
            category, conf = classify_by_audio(f)
            method = "audio"
        if conf < args.min_confidence:
            category = "_review"
        counts[category] = counts.get(category, 0) + 1
        rows.append({"file": str(f), "category": category,
                     "confidence": round(conf, 2), "method": method})
        if not args.dry_run:
            dest_dir = out_root / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f.name
            if args.resume and dest.exists():
                continue
            i = 1
            while dest.exists():  # name collisions in messy banks are common
                dest = dest_dir / f"{f.stem}_{i}{f.suffix}"
                i += 1
            (shutil.move if args.move else shutil.copy2)(str(f), str(dest))

    out_root.mkdir(parents=True, exist_ok=True)
    report = out_root / "review.csv"
    with open(report, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "category", "confidence", "method"])
        w.writeheader()
        w.writerows(rows)

    print(f"\n=== {'DRY RUN - nothing moved' if args.dry_run else 'Done'} ===")
    for cat in sorted(counts):
        print(f"  {cat:32s} {counts[cat]}")
    print(f"\nFull report: {report}")
    print(f"Manually sort everything in {out_root / '_review'} - then add tags.txt files")
    print("with era/texture descriptors (your domain knowledge) before training.")

    if args.ai_tags and not args.dry_run:
        ai_tag(out_root)


TAG_VOCAB = [
    "dusty vinyl texture", "lofi tape warmth", "1990s boom bap", "soulful",
    "dark and eerie", "aggressive", "smooth and mellow", "bright and crisp",
    "distorted", "clean", "punchy transient", "deep sub bass", "808 bass",
    "trap style", "drill style", "jazzy", "orchestral", "electric guitar",
    "acoustic guitar", "piano keys", "synthesizer", "strings", "brass",
    "vocal chop", "drum break", "live drums", "drum machine", "shaker groove",
    "reese bass", "wobble bass", "neuro growl", "metal guitar chugs",
    "rock drums", "ambient pad", "riser sweep fx", "vinyl crackle",
]


def ai_tag(out_root: Path, top_k=3, threshold=0.25, batch=8):
    """CLAP zero-shot tagging: writes <file>.tags.json next to each audio file."""
    import json
    import numpy as np
    try:
        import laion_clap
    except ImportError:
        print("laion-clap not installed - skipping AI tags. pip install laion-clap")
        return
    print("Loading CLAP for zero-shot tagging...")
    model = laion_clap.CLAP_Module(enable_fusion=False)
    model.load_ckpt()
    texts = [f"the sound of {t}" for t in TAG_VOCAB]
    temb = model.get_text_embedding(texts, use_tensor=False)
    temb = temb / np.linalg.norm(temb, axis=1, keepdims=True)
    wavs = [p for p in out_root.rglob("*") if p.suffix.lower() in {".wav", ".flac", ".mp3"}
            and "_review" not in p.parts and "presets" not in p.parts]
    print(f"Tagging {len(wavs)} files...")
    for i in tqdm(range(0, len(wavs), batch), desc="AI tagging"):
        chunk = wavs[i:i + batch]
        try:
            aemb = model.get_audio_embedding_from_filelist([str(p) for p in chunk], use_tensor=False)
        except Exception:
            continue
        aemb = aemb / np.linalg.norm(aemb, axis=1, keepdims=True)
        sims = aemb @ temb.T
        for p_, row in zip(chunk, sims):
            order = np.argsort(-row)[:top_k]
            tags = [TAG_VOCAB[j] for j in order if row[j] >= threshold]
            if tags:
                p_.with_suffix(p_.suffix + ".tags.json").write_text(
                    json.dumps({"tags": tags, "scores": [round(float(row[j]), 3) for j in order]}),
                    encoding="utf-8")


if __name__ == "__main__":
    main()
