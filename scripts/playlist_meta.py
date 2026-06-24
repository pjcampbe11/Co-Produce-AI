#!/usr/bin/env python3
"""
playlist_meta.py  -  Extract all available metadata from a PUBLIC Spotify playlist
and (optionally) enrich each track with sample/interpolation data.

What it pulls
-------------
  * Playlist: name, owner, description, follower count, track count.
  * Per track: title, artists, album, release date, duration, popularity,
    explicit flag, ISRC, Spotify URL, who added it and WHEN (added_at).
  * Optional audio features (--audio-features): tempo (BPM), key, mode, energy,
    danceability, valence, etc. - great for matching beats to a vibe.
  * Optional sample data (--samples): pulls Genius `song_relationships`
    (samples / interpolations / sampled-in) - the legitimate "who sampled what"
    source. WhoSampled has no free public API (academic/paid only, and it was
    acquired by Spotify in Nov 2025); --whosampled uses a RapidAPI provider if
    you supply RAPIDAPI_KEY (best-effort, third-party).

Auth (free, no user login - these are public-data reads)
--------------------------------------------------------
  Spotify  : create an app at developer.spotify.com -> set
             SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (Client Credentials flow).
  Genius   : GENIUS_TOKEN  (same token genius_lookup.py uses) - only for --samples.
  RapidAPI : RAPIDAPI_KEY  - only for --whosampled.

Examples
--------
  # markdown report to stdout, newest-added first (default sort)
  python playlist_meta.py -pl https://open.spotify.com/playlist/7MNBsBwgsqAsRZkdNE4E5Y

  # full JSON with audio features + sample data, to a file
  python playlist_meta.py --playlist 7MNBsBwgsqAsRZkdNE4E5Y --audio-features --samples \
      --format json --out playlist.json

  # CSV for a spreadsheet
  python playlist_meta.py -pl <url> -f csv -o playlist.csv
"""
import argparse
import base64
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API = "https://api.spotify.com/v1"
GENIUS_API = "https://api.genius.com"

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _req(url, headers=None, data=None, method="GET"):
    """Minimal JSON HTTP with one polite 429 retry. Returns parsed JSON.
    Raises urllib.error.HTTPError (with .read() body) on non-retryable errors."""
    hdr = {"User-Agent": "Co-Produce-AI/1.0 (+https://coproduceai.com)"}
    hdr.update(headers or {})
    r = urllib.request.Request(url, data=data, headers=hdr, method=method)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(int(e.headers.get("Retry-After", "2")) + 1)
                continue
            raise


def playlist_id(arg):
    """Accept a full URL, a spotify: URI, or a bare id; return the bare id."""
    arg = arg.strip().strip('"').strip("'")
    if "open.spotify.com" in arg:
        path = urllib.parse.urlparse(arg).path
        return path.rstrip("/").split("/")[-1]
    if arg.startswith("spotify:playlist:"):
        return arg.split(":")[-1]
    return arg


def spotify_token(cid, secret):
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    out = _req(SPOTIFY_TOKEN_URL, headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"}, data=body, method="POST")
    return out["access_token"]


def fetch_playlist(token, pid):
    h = {"Authorization": f"Bearer {token}"}
    meta = _req(f"{SPOTIFY_API}/playlists/{pid}"
                "?fields=name,description,followers(total),owner(display_name),external_urls(spotify)", headers=h)
    fields = ("items(added_at,added_by(id),track(name,id,popularity,duration_ms,explicit,"
              "external_ids(isrc),external_urls(spotify),artists(name,id),"
              "album(name,release_date))),next")
    # Spotify deprecated the /tracks alias - use /items (same response shape).
    url = f"{SPOTIFY_API}/playlists/{pid}/items?limit=100&fields={urllib.parse.quote(fields)}"
    items = []
    while url:
        try:
            page = _req(url, headers=h)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                sys.exit(
                    f"\nSpotify returned {e.code} for this playlist's items.\n"
                    "  - Client Credentials can't read Spotify-owned EDITORIAL/ALGORITHMIC playlists\n"
                    "    (only your own / regular public ones). Duplicate it to your account and use that URL.\n"
                    "  - If it IS your public playlist, make sure it's set to public, and that your\n"
                    "    Spotify app has 'Web API' enabled (developer.spotify.com -> your app -> Settings).\n")
            raise
        items += page.get("items", [])
        url = page.get("next")
    return meta, items


def fetch_audio_features(token, track_ids):
    h = {"Authorization": f"Bearer {token}"}
    feats = {}
    for i in range(0, len(track_ids), 100):
        chunk = [t for t in track_ids[i:i + 100] if t]
        if not chunk:
            continue
        try:
            out = _req(f"{SPOTIFY_API}/audio-features?ids={','.join(chunk)}", headers=h)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("[warn] Spotify audio-features is deprecated for apps created after "
                      "2024-11-27 (403) - continuing WITHOUT BPM/key. Remove --audio-features "
                      "to silence this.", file=sys.stderr)
                return {}
            raise
        for f in out.get("audio_features", []) or []:
            if f:
                feats[f["id"]] = f
    return feats


def genius_samples(artist, title, token):
    """Sample relationships from Genius song_relationships."""
    h = {"Authorization": f"Bearer {token}"}
    q = urllib.parse.quote(f"{artist} {title}")
    try:
        hits = _req(f"{GENIUS_API}/search?q={q}", headers=h).get("response", {}).get("hits", [])
        if not hits:
            return {}
        song_id = hits[0]["result"]["id"]
        song = _req(f"{GENIUS_API}/songs/{song_id}?text_format=plain", headers=h)
        rels = song.get("response", {}).get("song", {}).get("song_relationships", [])
        out = {}
        for rel in rels:
            kind = rel.get("relationship_type")
            songs = [f"{s.get('primary_artist',{}).get('name','?')} - {s.get('title','?')}"
                     for s in rel.get("songs", [])]
            if songs:
                out[kind] = songs
        return out
    except Exception as e:
        return {"_error": str(e)}


def whosampled_rapidapi(artist, title, key):
    """Optional best-effort WhoSampled lookup via a RapidAPI provider."""
    host = os.environ.get("WHOSAMPLED_RAPIDAPI_HOST", "whosampled-api.p.rapidapi.com")
    q = urllib.parse.quote(f"{artist} {title}")
    try:
        return _req(f"https://{host}/search?query={q}",
                    headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": host})
    except Exception as e:
        return {"_error": str(e)}


def build_rows(items, feats, args):
    rows = []
    for it in items:
        t = it.get("track") or {}
        if not t:
            continue
        af = feats.get(t.get("id"), {}) if feats else {}
        rows.append({
            "added_at": it.get("added_at", ""),
            "title": t.get("name", ""),
            "artists": ", ".join(a["name"] for a in t.get("artists", [])),
            "album": (t.get("album") or {}).get("name", ""),
            "release_date": (t.get("album") or {}).get("release_date", ""),
            "duration_sec": round((t.get("duration_ms") or 0) / 1000),
            "popularity": t.get("popularity"),
            "explicit": t.get("explicit"),
            "isrc": (t.get("external_ids") or {}).get("isrc", ""),
            "spotify_url": (t.get("external_urls") or {}).get("spotify", ""),
            "track_id": t.get("id", ""),
            **({"bpm": round(af["tempo"]) if af.get("tempo") else None,
                "key": (KEYS[af["key"]] + ("m" if af.get("mode") == 0 else "")) if af.get("key", -1) >= 0 else "",
                "energy": af.get("energy"), "danceability": af.get("danceability"),
                "valence": af.get("valence")} if feats else {}),
        })
    if args.sort == "added":
        rows.sort(key=lambda r: r["added_at"], reverse=True)
    elif args.sort == "popularity":
        rows.sort(key=lambda r: r["popularity"] or 0, reverse=True)
    elif args.sort == "release":
        rows.sort(key=lambda r: r["release_date"], reverse=True)
    elif args.sort == "name":
        rows.sort(key=lambda r: r["title"].lower())
    if args.limit:
        rows = rows[:args.limit]
    return rows


def render_md(meta, rows, with_feats, with_samples):
    o = io.StringIO()
    o.write(f"# {meta.get('name','Playlist')}\n\n")
    if meta.get("description"):
        o.write(f"*{meta['description']}*\n\n")
    o.write(f"- Owner: {meta.get('owner',{}).get('display_name','?')}\n")
    o.write(f"- Followers: {meta.get('followers',{}).get('total','?')}\n")
    o.write(f"- Tracks: {len(rows)}\n")
    o.write(f"- URL: {meta.get('external_urls',{}).get('spotify','')}\n\n")
    cols = ["#", "Added", "Title", "Artists", "Album", "Release", "Len", "Pop"]
    if with_feats:
        cols += ["BPM", "Key"]
    o.write("| " + " | ".join(cols) + " |\n")
    o.write("|" + "|".join(["---"] * len(cols)) + "|\n")
    for i, r in enumerate(rows, 1):
        line = [str(i), (r["added_at"] or "")[:10], r["title"], r["artists"], r["album"],
                r["release_date"], f"{r['duration_sec']}s", str(r["popularity"])]
        if with_feats:
            line += [str(r.get("bpm") or ""), r.get("key") or ""]
        o.write("| " + " | ".join(s.replace("|", "/") for s in line) + " |\n")
    if with_samples:
        o.write("\n## Samples & interpolations\n\n")
        for r in rows:
            s = r.get("samples")
            if s and any(k != "_error" for k in s):
                o.write(f"**{r['title']} - {r['artists']}**\n")
                for kind, lst in s.items():
                    if kind == "_error" or not isinstance(lst, list):
                        continue
                    o.write(f"  - {kind}: " + "; ".join(lst) + "\n")
                o.write("\n")
    return o.getvalue()


def main():
    ap = argparse.ArgumentParser(description="Extract metadata from a public Spotify playlist.")
    ap.add_argument("-pl", "--playlist", required=True, help="Playlist URL, URI, or id")
    ap.add_argument("-f", "--format", choices=["md", "json", "csv"], default="md")
    ap.add_argument("-o", "--out", help="Output file (default: stdout)")
    ap.add_argument("--sort", choices=["added", "popularity", "release", "name"], default="added",
                    help="Report order (default: newest added first)")
    ap.add_argument("--limit", type=int, default=0, help="Only the first N after sorting")
    ap.add_argument("--audio-features", action="store_true", help="Add BPM/key/energy/etc.")
    ap.add_argument("--samples", action="store_true", help="Add Genius sample relationships (needs GENIUS_TOKEN)")
    ap.add_argument("--whosampled", action="store_true", help="Also query WhoSampled via RapidAPI (needs RAPIDAPI_KEY)")
    ap.add_argument("--client-id", default=os.environ.get("SPOTIFY_CLIENT_ID", ""))
    ap.add_argument("--client-secret", default=os.environ.get("SPOTIFY_CLIENT_SECRET", ""))
    args = ap.parse_args()

    if not args.client_id or not args.client_secret:
        sys.exit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (developer.spotify.com -> create app).")

    pid = playlist_id(args.playlist)
    token = spotify_token(args.client_id, args.client_secret)
    meta, items = fetch_playlist(token, pid)
    print(f"[playlist_meta] '{meta.get('name')}' - {len(items)} tracks", file=sys.stderr)

    feats = {}
    if args.audio_features:
        feats = fetch_audio_features(token, [((it.get('track') or {}).get('id')) for it in items])

    rows = build_rows(items, feats, args)

    if args.samples or args.whosampled:
        gtok = os.environ.get("GENIUS_TOKEN", "")
        rkey = os.environ.get("RAPIDAPI_KEY", "")
        for i, r in enumerate(rows, 1):
            print(f"[samples] {i}/{len(rows)} {r['title']}", file=sys.stderr)
            if args.samples and gtok:
                r["samples"] = genius_samples(r["artists"].split(",")[0], r["title"], gtok)
            if args.whosampled and rkey:
                r.setdefault("samples", {})["whosampled"] = whosampled_rapidapi(
                    r["artists"].split(",")[0], r["title"], rkey)
            time.sleep(0.2)

    if args.format == "json":
        text = json.dumps({"playlist": meta, "tracks": rows}, indent=2, ensure_ascii=False)
    elif args.format == "csv":
        buf = io.StringIO()
        flat = [{k: v for k, v in r.items() if k != "samples"} for r in rows]
        w = csv.DictWriter(buf, fieldnames=list(flat[0].keys()) if flat else [])
        w.writeheader(); w.writerows(flat)
        text = buf.getvalue()
    else:
        text = render_md(meta, rows, args.audio_features, args.samples or args.whosampled)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[playlist_meta] wrote {args.out} ({len(rows)} tracks)", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
