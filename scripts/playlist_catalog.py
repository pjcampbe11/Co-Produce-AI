#!/usr/bin/env python3
"""
playlist_catalog.py  -  Build a per-song REFERENCE catalog from a playlist JSON.

Reads the output of playlist_meta.py (`--format json`) and, for each track,
queries the Genius API for metadata and the song's Genius **page URL** (where
the lyrics live). Writes one reference file per song into a folder.

IMPORTANT - what this does NOT do
---------------------------------
It does **not** download, scrape, or store song lyrics. The Genius API does not
serve lyric text, and the lyrics of commercial songs are copyrighted - storing
thousands of them (especially in a commercial project) would be infringement.
Each catalog file instead contains metadata + a link to the lyrics on Genius.
To TRAIN a lyric model, use YOUR OWN written lyrics (see lyric_analyze.py).

Usage
-----
  $env:GENIUS_TOKEN = "your_client_access_token"
  python scripts/playlist_catalog.py --json playlist_full.json --out catalog --resume
  python scripts/playlist_catalog.py --json playlist_full.json --out catalog --limit 50
"""
import argparse
import json
import os
import re
import sys
import time

# reuse the matching helpers from genius_lookup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genius_lookup as gl


def _safe_name(artist, title):
    base = f"{artist} - {title}"
    base = re.sub(r"[^A-Za-z0-9 ._-]", "_", base)
    return re.sub(r"\s+", " ", base).strip()[:120]


def main():
    ap = argparse.ArgumentParser(description="Per-song reference catalog from a playlist JSON (metadata + Genius link, no lyrics).")
    ap.add_argument("--json", required=True, help="playlist_meta.py --format json output")
    ap.add_argument("--out", default="catalog", help="output folder for reference files")
    ap.add_argument("--token", default=os.environ.get("GENIUS_TOKEN", ""))
    ap.add_argument("--delay", type=float, default=0.3, help="seconds between Genius calls")
    ap.add_argument("--limit", type=int, default=0, help="process up to N not-yet-done songs")
    ap.add_argument("--resume", action="store_true", help="skip songs already cataloged")
    ap.add_argument("--index-only", action="store_true", help="only (re)write INDEX.md from existing files")
    args = ap.parse_args()

    data = json.load(open(args.json, encoding="utf-8"))
    tracks = data.get("tracks", data if isinstance(data, list) else [])
    os.makedirs(args.out, exist_ok=True)

    if not args.index_only:
        if not args.token:
            sys.exit("No token. Set GENIUS_TOKEN or pass --token (genius.com/api-clients).")
        ok = skipped = failed = 0
        for i, t in enumerate(tracks, 1):
            artist = (t.get("artists", "") or "").split(",")[0].strip()
            title = (t.get("title", "") or "").strip()
            if not title:
                continue
            name = _safe_name(artist or "unknown", title)
            dest = os.path.join(args.out, name + ".json")
            if args.resume and os.path.exists(dest):
                skipped += 1
                continue
            rec = {"title": title, "artists": t.get("artists", ""),
                   "album": t.get("album", ""), "release_date": t.get("release_date", ""),
                   "spotify_url": t.get("spotify_url", ""), "isrc": t.get("isrc", "")}
            try:
                hit = gl.search(args.token, gl.clean_query(f"{artist} {title}"))
                if hit:
                    rec["genius_url"] = hit.get("url", "")
                    rec["genius_title"] = hit.get("full_title", "")
                    det = gl.song_details(args.token, hit["id"])
                    rec["producer"] = ", ".join(p.get("name", "") for p in det.get("producer_artists", []))
                    rec["writers"] = ", ".join(w.get("name", "") for w in det.get("writer_artists", []))
                    rec["featured"] = ", ".join(f.get("name", "") for f in det.get("featured_artists", []))
                    rd = det.get("release_date_for_display") or det.get("release_date", "")
                    if rd:
                        rec["release_date"] = rd
                    # label (from custom_performances when present)
                    for perf in det.get("custom_performances", []):
                        if "label" in (perf.get("label", "") or "").lower():
                            rec["label"] = ", ".join(a.get("name", "") for a in perf.get("artists", []))
                    # sample / interpolation lineage (legitimately API-provided)
                    samples, sampled_in, interps = [], [], []
                    for rel in det.get("song_relationships", []):
                        names = [f"{x.get('primary_artist',{}).get('name','?')} - {x.get('title','?')}"
                                 for x in rel.get("songs", [])]
                        rt = rel.get("relationship_type")
                        if rt == "samples":
                            samples += names
                        elif rt == "sampled_in":
                            sampled_in += names
                        elif rt == "interpolates":
                            interps += names
                    if samples:
                        rec["samples"] = samples
                    if interps:
                        rec["interpolates"] = interps
                    if sampled_in:
                        rec["sampled_in"] = sampled_in
                    rec["lyrics_note"] = "Lyrics are copyrighted - read them at genius_url. Not stored here."
                else:
                    rec["genius_url"] = ""
                    rec["match"] = "no Genius match"
                json.dump(rec, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                print(f"[{i}/{len(tracks)}] {name}")
                ok += 1
                if args.limit and ok >= args.limit:
                    print(f"(reached --limit {args.limit})")
                    break
                time.sleep(args.delay)
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(tracks)}] FAILED {name}: {e}", file=sys.stderr)
        print(f"\n=== {ok} cataloged, {skipped} skipped, {failed} failed ===")

    # rebuild INDEX.md
    files = sorted(f for f in os.listdir(args.out) if f.endswith(".json"))
    lines = [f"# Song catalog ({len(files)} songs)\n",
             "_Metadata + Genius links only. Lyrics are copyrighted and live on Genius._\n",
             "| Song | Album | Year | Producer | Writers | Samples | Lyrics |",
             "|---|---|---|---|---|---|---|"]
    for f in files:
        try:
            r = json.load(open(os.path.join(args.out, f), encoding="utf-8"))
        except Exception:
            continue
        yr = (r.get("release_date", "") or "")[:4]
        link = f"[Genius]({r['genius_url']})" if r.get("genius_url") else "—"
        title = f"{r.get('artists','')} — {r.get('title','')}".replace("|", "/")
        smp = str(len(r.get("samples", [])) + len(r.get("interpolates", []))) if (r.get("samples") or r.get("interpolates")) else "—"
        lines.append(f"| {title} | {r.get('album','').replace('|','/')} | {yr} | "
                     f"{r.get('producer','').replace('|','/')} | {r.get('writers','').replace('|','/')} | {smp} | {link} |")
    open(os.path.join(args.out, "INDEX.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {os.path.join(args.out, 'INDEX.md')} ({len(files)} songs)")


if __name__ == "__main__":
    main()
