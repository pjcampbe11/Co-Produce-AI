#!/usr/bin/env python3
"""
genius_lookup.py  -  Enrich beats with Genius metadata (producer/album/year).

Matches each audio file in a folder to a Genius song by cleaning its filename
into a search query, takes the best hit, and writes a `<file>.genius.json`
sidecar with artist, title, producers, album, release date, and the Genius URL.
Pure metadata - the Genius API does NOT return lyrics, and this never scrapes
them.

Setup:
    1. Make a client at https://genius.com/api-clients -> "Generate Access Token"
    2. Put it in an env var (don't hard-code it):
         PowerShell:  $env:GENIUS_TOKEN = "your_client_access_token"
         bash:        export GENIUS_TOKEN=your_client_access_token
    pip install requests

Usage:
    python genius_lookup.py --beats "F:/RAP_ARCHIVES/raw_beats" --resume
    # only instrumentals are matched; *_vocals files are skipped.
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Filename -> search query: strips track numbers, _instrumental, [ids], '(OFFICIAL VIDEO)'/'Prod. By' noise.
#   - Deliberately leaves bare 2-digit leading numbers (so '50 Cent'/'21 Savage' survive); Genius fuzzy-search copes.
#   - match_score + low_confidence flag let you spot-check; token read from GENIUS_TOKEN env (never hard-code).
#   - Metadata only - the Genius API does not return lyrics and this never scrapes them.
# ---------------------------------------------------------------------------
import argparse
import difflib
import json
import os
import re
import sys
import time
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".ogg", ".m4a"}
NOISE = re.compile(
    r"\b(official\s+(music\s+)?video|official\s+audio|lyric(s)?\s*video|lyrics|"
    r"audio|visualizer|explicit|clean|hd|4k|prod\.?\s*by[^)]*|produced\s*by[^)]*)\b",
    re.IGNORECASE)


def clean_query(stem: str) -> str:
    s = stem
    for suf in ("_instrumental", "_vocals", "_(instrumental)", "_(vocals)"):
        if s.lower().endswith(suf):
            s = s[: -len(suf)]
    s = re.sub(r"\[[^\]]*\]", " ", s)          # [youtube_id]
    s = re.sub(r"\([^)]*\)", lambda m: "" if NOISE.search(m.group(0)) else m.group(0), s)
    s = re.sub(r"^\s*\d{1,3}\s*[-.\)]\s*", "", s)  # leading "002 - " / "01." / "1)"
    s = NOISE.sub(" ", s)
    s = s.replace("_", " ")
    s = re.sub(r"\s{2,}", " ", s).strip(" -_.")
    return s


def search(token, query):
    import requests
    r = requests.get("https://api.genius.com/search",
                     params={"q": query},
                     headers={"Authorization": f"Bearer {token}"}, timeout=20)
    r.raise_for_status()
    hits = r.json().get("response", {}).get("hits", [])
    return hits[0]["result"] if hits else None


def song_details(token, song_id):
    import requests
    r = requests.get(f"https://api.genius.com/songs/{song_id}",
                     headers={"Authorization": f"Bearer {token}"}, timeout=20)
    r.raise_for_status()
    return r.json().get("response", {}).get("song", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True, help="Folder of beats to enrich")
    ap.add_argument("--token", default=os.environ.get("GENIUS_TOKEN", ""),
                    help="Genius client access token (or set GENIUS_TOKEN)")
    ap.add_argument("--min-score", type=float, default=0.5,
                    help="Title-similarity below this is flagged low_confidence")
    ap.add_argument("--delay", type=float, default=0.5, help="Seconds between API calls (be polite)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="Skip files already enriched")
    args = ap.parse_args()
    if not args.token:
        sys.exit("No token. Set GENIUS_TOKEN env var or pass --token (see header).")

    beats = [p for p in Path(args.beats).rglob("*")
             if p.suffix.lower() in AUDIO_EXTS and "_vocals" not in p.name.lower()]
    if args.limit:
        beats = beats[: args.limit]
    if not beats:
        sys.exit("No beat audio found.")

    ok = skipped = nomatch = failed = 0
    for i, b in enumerate(beats, 1):
        sidecar = b.with_suffix(b.suffix + ".genius.json")
        if args.resume and sidecar.exists():
            skipped += 1
            continue
        q = clean_query(b.stem)
        try:
            hit = search(args.token, q)
            time.sleep(args.delay)
            if not hit:
                sidecar.write_text(json.dumps({"query": q, "matched": None}, indent=2), encoding="utf-8")
                nomatch += 1
                print(f"[{i}/{len(beats)}] no match: {q}")
                continue
            score = difflib.SequenceMatcher(None, q.lower(), hit.get("full_title", "").lower()).ratio()
            det = song_details(args.token, hit["id"])
            time.sleep(args.delay)
            rec = {
                "query": q,
                "matched": hit.get("full_title"),
                "match_score": round(score, 3),
                "low_confidence": score < args.min_score,
                "title": hit.get("title"),
                "primary_artist": (hit.get("primary_artist") or {}).get("name"),
                "producers": [p.get("name") for p in det.get("producer_artists", [])],
                "writers": [p.get("name") for p in det.get("writer_artists", [])],
                "featured": [p.get("name") for p in det.get("featured_artists", [])],
                "album": (det.get("album") or {}).get("name"),
                "release_date": det.get("release_date_for_display"),
                "genius_id": hit.get("id"),
                "url": hit.get("url"),
            }
            sidecar.write_text(json.dumps(rec, indent=2), encoding="utf-8")
            ok += 1
            flag = "  (LOW CONF)" if rec["low_confidence"] else ""
            print(f"[{i}/{len(beats)}] {q}  ->  {rec['matched']}{flag}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(beats)}] FAILED {q}: {e}")
            time.sleep(args.delay)
    print(f"\n=== {ok} matched, {nomatch} no-match, {skipped} skipped, {failed} failed ===")
    print("Low-confidence matches are flagged in their sidecars - spot-check those.")


if __name__ == "__main__":
    main()
