#!/usr/bin/env python3
"""
build_captions.py  -  Fuse Deep Listen reports into canonical training captions.

Joins each beat to its Deep Listen report (by filename, ignoring _instrumental/
_vocals suffixes), distills the full analysis into ONE consistent caption, and
writes it as `<beat>.caption.txt` next to the audio. prepare_dataset.py uses
that verbatim as the training prompt (so the whole pipeline inherits BPM, key,
instrumentation, mood, production, etc. - not just freeform tags).

Caption schema (consistent field order so the model learns vocabulary by position):
  [subgenre/era IF confident, else "hip hop"], [instrumentation], [mood],
  [production/texture], [N BPM], [key of X], [loop|one shot], [your freeform tags]

Subgenre/era only lead the caption when the analysis is confident (score >=
--genre-threshold); otherwise it falls back to plain "hip hop" - never guessed.

Inputs per beat (any that exist): a Deep Listen report (slim `.caption.json`
from deep_listen --for-captions, or the full `.analysis.json`), and an
optional `.tags.json` from auto_tag.

Usage:
    # reports written next to the beats (deep_listen --out = the beats dir):
    python build_captions.py --beats F:/RAP_ARCHIVES/raw_beats
    # reports in a separate (mirrored) folder:
    python build_captions.py --beats F:/RAP_ARCHIVES/raw_beats --reports F:/reports
"""
import argparse
import json
import re
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".ogg", ".m4a"}
# PANNs/AudioSet labels that aren't useful instrument descriptors
PANN_SKIP = {"music", "musical instrument", "speech", "silence", "sound effect",
             "inside, small room", "inside, large room or hall", "echo", "noise",
             "audio", "song", "male singing", "female singing", "singing"}
ERA_RE = re.compile(r"\b(19\d0s|20\d0s|\d0s)\b")


def norm_key(name: str) -> str:
    s = name.lower()
    for suf in ("_instrumental", "_vocals", "_(instrumental)", "_(vocals)", ".caption", ".analysis"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s.strip()


def index_reports(reports_dir: Path):
    idx = {}
    for p in reports_dir.rglob("*"):
        if p.name.endswith(".caption.json") or p.name.endswith(".analysis.json"):
            stem = norm_key(p.name[: p.name.rfind(".")] if p.name.endswith(".json") else p.stem)
            # prefer .caption.json over .analysis.json if both exist
            if stem not in idx or p.name.endswith(".caption.json"):
                idx[stem] = p
    return idx


def top_labels(items, thr, n, key="label", score="score"):
    out = []
    for it in items or []:
        if isinstance(it, dict) and it.get(score, 0) >= thr:
            out.append(it[key])
        if len(out) >= n:
            break
    return out


def build_caption(report: dict, freeform: list, args) -> str:
    vibe = report.get("vibe", {}) if isinstance(report.get("vibe"), dict) else {}
    musical = report.get("musical", {}) if isinstance(report.get("musical"), dict) else {}
    # also accept slim flat fields
    bpm = (musical.get("bpm") or report.get("bpm"))
    key = (musical.get("key") or report.get("key"))
    kind = report.get("kind") or musical.get("kind")

    parts = []

    # --- lead: confident subgenre, else "hip hop" ---
    genre = top_labels(vibe.get("genre"), args.genre_threshold, 1)
    lead = genre[0] if genre else "hip hop"
    if "hip hop" not in lead.lower() and "hip-hop" not in lead.lower():
        # keep it anchored to the domain unless the subgenre already implies it
        lead = f"{lead}" if lead.lower() in ("trap", "drill", "boom bap", "lofi",
                                             "lo-fi", "g-funk", "gangsta rap") else lead
    parts.append(lead)

    # --- era: only if confident (from production vocab year labels) ---
    for it in vibe.get("production", []) or []:
        if isinstance(it, dict) and it.get("score", 0) >= args.genre_threshold and ERA_RE.search(it["label"]):
            parts.append(ERA_RE.search(it["label"]).group(0))
            break

    # --- instrumentation: PANNs sound events + CLAP instruments ---
    instruments = []
    for e in (report.get("sound_events", {}) or {}).get("clip_level", []) or []:
        lab = e.get("sound", "").lower()
        if e.get("confidence", 0) >= 0.30 and lab and lab not in PANN_SKIP:
            instruments.append(e["sound"].lower())
    instruments += [x.lower() for x in top_labels(vibe.get("instruments"), args.vibe_threshold, 3)]
    for i in instruments[:4]:
        parts.append(i)

    # --- mood + production texture ---
    parts += top_labels(vibe.get("mood"), args.vibe_threshold, 2)
    for pl in top_labels(vibe.get("production"), args.genre_threshold, 2):
        if not ERA_RE.search(pl):
            parts.append(pl)

    # --- numeric / structural ---
    if bpm:
        parts.append(f"{bpm} BPM")
    if key:
        parts.append(f"key of {key}")
    parts.append("one shot" if kind == "oneshot" else "loop")

    # --- your freeform auto-tags last ---
    parts += [t for t in (freeform or [])]

    # dedupe (case-insensitive), preserve order, cap length
    seen, out = set(), []
    for p in parts:
        p = str(p).strip()
        pl = p.lower()
        if p and pl not in seen:
            seen.add(pl)
            out.append(p)
        if len(out) >= args.max_terms:
            break
    return ", ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True, help="Folder of beat audio files")
    ap.add_argument("--reports", help="Folder of Deep Listen reports (default: next to each beat)")
    ap.add_argument("--genre-threshold", type=float, default=0.35,
                    help="Min confidence to lead with a subgenre/era (else 'hip hop')")
    ap.add_argument("--vibe-threshold", type=float, default=0.25,
                    help="Min confidence for mood/instrument descriptors")
    ap.add_argument("--max-terms", type=int, default=14)
    ap.add_argument("--resume", action="store_true", help="Skip beats that already have .caption.txt")
    ap.add_argument("--dry-run", action="store_true", help="Print captions, write nothing")
    args = ap.parse_args()

    beats_dir = Path(args.beats)
    beats = [p for p in beats_dir.rglob("*") if p.suffix.lower() in AUDIO_EXTS
             and "_vocals" not in p.name.lower()]
    if not beats:
        raise SystemExit("No beat audio found.")
    report_idx = index_reports(Path(args.reports)) if args.reports else None

    ok = skipped = no_report = 0
    for b in sorted(beats):
        cap_path = b.with_suffix(b.suffix + ".caption.txt")
        if args.resume and cap_path.exists():
            skipped += 1
            continue
        # find report
        rp = None
        if report_idx is not None:
            rp = report_idx.get(norm_key(b.stem))
        else:
            for ext in (".caption.json", ".analysis.json"):
                cand = b.with_suffix(b.suffix + ext)
                cand2 = b.with_name(b.stem + ext)
                rp = cand if cand.exists() else (cand2 if cand2.exists() else None)
                if rp:
                    break
        report = {}
        if rp and rp.exists():
            try:
                report = json.loads(rp.read_text(encoding="utf-8"))
            except Exception:
                pass
        else:
            no_report += 1
        # optional freeform tags
        freeform = []
        tj = b.with_suffix(b.suffix + ".tags.json")
        if tj.exists():
            try:
                freeform = json.loads(tj.read_text(encoding="utf-8")).get("tags", [])
            except Exception:
                pass
        caption = build_caption(report, freeform, args)
        if args.dry_run:
            print(f"{b.name}: {caption}")
        else:
            cap_path.write_text(caption, encoding="utf-8")
            ok += 1
            if ok <= 8:
                print(f"{b.name}: {caption}")
    print(f"\n=== {ok} captions written, {skipped} skipped, {no_report} had no report "
          f"(captioned from filename/tags only) ===")
    if not args.dry_run:
        print("Next: prepare_dataset.py will use these .caption.txt verbatim as prompts.")


if __name__ == "__main__":
    main()
