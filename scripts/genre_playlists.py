#!/usr/bin/env python3
"""
genre_playlists.py  -  Find the best playlists for a genre across platforms.

For a given genre (the ones Co-Produce AI works in) this returns curated/most-
relevant **playlists** from:
  * Spotify     - live search via the Web API (Client Credentials; no login).
  * YouTube     - live search via the Data API if YOUTUBE_API_KEY is set,
                  otherwise a ready-to-click YouTube playlist search URL.
  * Apple Music - live search via the Apple Music API if APPLE_MUSIC_TOKEN is
                  set, otherwise an Apple Music playlist search URL.
  * SoundCloud  - SoundCloud's API is closed to new apps, so this emits the
                  genre Charts URL + a "sets" (playlist) search URL.

Great for sourcing reference listening per genre before a pack/training run -
pair the Spotify hits with playlist_meta.py to pull full metadata.

Auth (all optional except Spotify for live Spotify results)
-----------------------------------------------------------
  SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET   developer.spotify.com (free)
  YOUTUBE_API_KEY                             console.cloud.google.com (YouTube Data API v3)
  APPLE_MUSIC_TOKEN                           Apple Developer JWT (MusicKit) - optional

Examples
--------
  python genre_playlists.py -g hiphop
  python genre_playlists.py --genre dnb --limit 8 --format md --out dnb_playlists.md
  python genre_playlists.py -g all --format json --out playlists.json
"""
import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API = "https://api.spotify.com/v1"
YT_API = "https://www.googleapis.com/youtube/v3/search"
APPLE_API = "https://api.music.apple.com/v1/catalog/us/search"

# repo genre -> {search terms, SoundCloud charts genre slug}
GENRES = {
    "hiphop":    {"q": "hip hop",          "sc": "hiphoprap"},
    "boom_bap":  {"q": "boom bap",         "sc": "hiphoprap"},
    "trap":      {"q": "trap",             "sc": "hiphoprap"},
    "drill":     {"q": "drill",            "sc": "hiphoprap"},
    "lofi":      {"q": "lofi hip hop",     "sc": "hiphoprap"},
    "rock":      {"q": "rock",             "sc": "rock"},
    "metal":     {"q": "metal",            "sc": "metal"},
    "rockmetal": {"q": "rock metal",       "sc": "rock"},
    "dubstep":   {"q": "dubstep",          "sc": "dubstep"},
    "dnb":       {"q": "drum and bass",    "sc": "drumbass"},
}


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# ---------- Spotify ----------
def spotify_token(cid, secret):
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(SPOTIFY_TOKEN_URL, data=body, method="POST",
                                 headers={"Authorization": f"Basic {auth}",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def spotify_playlists(token, terms, limit):
    q = urllib.parse.quote(f"{terms} playlist")
    url = f"{SPOTIFY_API}/search?q={q}&type=playlist&limit={min(limit,50)}"
    out = _get(url, headers={"Authorization": f"Bearer {token}"})
    items = (out.get("playlists") or {}).get("items") or []
    res = []
    for p in items:
        if not p:                       # Spotify search can return null entries
            continue
        res.append({"name": p.get("name", ""),
                    "owner": (p.get("owner") or {}).get("display_name", ""),
                    "tracks": (p.get("tracks") or {}).get("total"),
                    "url": (p.get("external_urls") or {}).get("spotify", "")})
        if len(res) >= limit:
            break
    return res


# ---------- YouTube ----------
def youtube_playlists(key, terms, limit):
    q = urllib.parse.quote(f"{terms} playlist")
    url = (f"{YT_API}?part=snippet&type=playlist&maxResults={min(limit,25)}"
           f"&q={q}&key={key}")
    out = _get(url)
    res = []
    for it in out.get("items", []):
        pid = (it.get("id") or {}).get("playlistId")
        sn = it.get("snippet", {})
        if pid:
            res.append({"name": sn.get("title", ""), "owner": sn.get("channelTitle", ""),
                        "url": f"https://www.youtube.com/playlist?list={pid}"})
    return res[:limit]


def youtube_search_url(terms):
    return ("https://www.youtube.com/results?search_query="
            + urllib.parse.quote(f"{terms} playlist") + "&sp=EgIQAw%253D%253D")  # sp filter = playlists


# ---------- Apple Music ----------
def apple_music_playlists(token, terms, limit):
    """Live Apple Music catalog playlist search (needs a developer JWT token)."""
    q = urllib.parse.quote(terms)
    url = f"{APPLE_API}?types=playlists&limit={min(limit,25)}&term={q}"
    out = _get(url, headers={"Authorization": f"Bearer {token}"})
    data = (out.get("results") or {}).get("playlists", {}).get("data", [])
    res = []
    for p in data:
        a = p.get("attributes", {})
        res.append({"name": a.get("name", ""),
                    "owner": a.get("curatorName", ""),
                    "url": a.get("url", "")})
    return res[:limit]


def apple_search_url(terms):
    return "https://music.apple.com/us/search?term=" + urllib.parse.quote(f"{terms} playlist")


# ---------- SoundCloud (no open API -> link out) ----------
def soundcloud_links(terms, sc_slug):
    return {
        "charts": f"https://soundcloud.com/charts/top?genre={sc_slug}&country=US",
        "sets_search": "https://soundcloud.com/search/sets?q=" + urllib.parse.quote(terms),
    }


def gather(genre, args, sp_token, yt_key, am_token):
    cfg = GENRES[genre]
    block = {"genre": genre, "spotify": [], "youtube": [], "youtube_search": None,
             "soundcloud": soundcloud_links(cfg["q"], cfg["sc"])}
    if sp_token:
        try:
            block["spotify"] = spotify_playlists(sp_token, cfg["q"], args.limit)
        except Exception as e:
            block["spotify_error"] = str(e)
    if yt_key:
        try:
            block["youtube"] = youtube_playlists(yt_key, cfg["q"], args.limit)
        except Exception as e:
            block["youtube_error"] = str(e)
    if not block["youtube"]:
        block["youtube_search"] = youtube_search_url(cfg["q"])
    block["apple"], block["apple_search"] = [], None
    if am_token:
        try:
            block["apple"] = apple_music_playlists(am_token, cfg["q"], args.limit)
        except Exception as e:
            block["apple_error"] = str(e)
    if not block["apple"]:
        block["apple_search"] = apple_search_url(cfg["q"])
    return block


def render_md(blocks):
    out = ["# Best playlists by genre\n"]
    for b in blocks:
        out.append(f"## {b['genre']}\n")
        out.append("**Spotify**")
        if b["spotify"]:
            for p in b["spotify"]:
                t = f" ({p['tracks']} tracks)" if p.get("tracks") is not None else ""
                out.append(f"- [{p['name']}]({p['url']}) — {p['owner']}{t}")
        else:
            out.append("- _(set SPOTIFY_CLIENT_ID/SECRET for live results)_")
        out.append("\n**YouTube**")
        if b["youtube"]:
            for p in b["youtube"]:
                out.append(f"- [{p['name']}]({p['url']}) — {p['owner']}")
        else:
            out.append(f"- [Search YouTube playlists]({b['youtube_search']})")
        out.append("\n**Apple Music**")
        if b["apple"]:
            for p in b["apple"]:
                out.append(f"- [{p['name']}]({p['url']}) — {p['owner']}")
        else:
            out.append(f"- [Search Apple Music]({b['apple_search']})")
        out.append("\n**SoundCloud**")
        out.append(f"- [Genre charts]({b['soundcloud']['charts']})")
        out.append(f"- [Playlist (sets) search]({b['soundcloud']['sets_search']})")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Find the best playlists for a genre across platforms.")
    ap.add_argument("-g", "--genre", default="hiphop",
                    help="genre or 'all'. choices: " + ", ".join(GENRES))
    ap.add_argument("--limit", type=int, default=5, help="results per platform")
    ap.add_argument("-f", "--format", choices=["md", "json"], default="md")
    ap.add_argument("-o", "--out", help="output file (default stdout)")
    args = ap.parse_args()

    genres = list(GENRES) if args.genre == "all" else [args.genre]
    for g in genres:
        if g not in GENRES:
            sys.exit(f"unknown genre '{g}'. choices: {', '.join(GENRES)} (or 'all')")

    cid, secret = os.environ.get("SPOTIFY_CLIENT_ID", ""), os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    yt_key = os.environ.get("YOUTUBE_API_KEY", "")
    am_token = os.environ.get("APPLE_MUSIC_TOKEN", "")
    sp_token = ""
    if cid and secret:
        try:
            sp_token = spotify_token(cid, secret)
        except Exception as e:
            print(f"[warn] Spotify auth failed ({e}); skipping live Spotify results", file=sys.stderr)
    else:
        print("[info] no SPOTIFY_CLIENT_ID/SECRET set - Spotify results skipped (YouTube/SoundCloud links still work)", file=sys.stderr)

    blocks = [gather(g, args, sp_token, yt_key, am_token) for g in genres]
    text = json.dumps(blocks, indent=2) if args.format == "json" else render_md(blocks)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"[genre_playlists] wrote {args.out} ({len(blocks)} genre(s))", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
