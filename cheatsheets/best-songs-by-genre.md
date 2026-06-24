# Best songs by genre — playlist finder

Find top reference **playlists** per genre across Spotify, YouTube, and
SoundCloud, then mine them for ideas (pair with `playlist_meta.py` to pull full
metadata). Powered by `scripts/genre_playlists.py`.

## Use it

```bash
# one genre (markdown to stdout)
python scripts/genre_playlists.py -g hiphop

# all genres, more results each, to a file
python scripts/genre_playlists.py -g all --limit 8 --format md --out playlists.md

# JSON for tooling
python scripts/genre_playlists.py -g dnb --format json --out dnb.json
```

Genres: `hiphop`, `boom_bap`, `trap`, `drill`, `lofi`, `rock`, `metal`,
`rockmetal`, `dubstep`, `dnb`, or `all`.

## What you get per genre

| Source | How it works |
| --- | --- |
| **Spotify** | live Web API search (set `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET`) — names, owners, track counts, URLs |
| **YouTube** | live Data API search if `YOUTUBE_API_KEY` is set; otherwise a ready-to-click playlist search link |
| **SoundCloud** | genre **Charts** URL + a "sets" (playlist) search URL (SoundCloud's API is closed to new apps) |

It degrades gracefully: with **no keys at all** you still get working YouTube and
SoundCloud links; add the Spotify keys for live, ranked Spotify playlists.

## Keys (free)

- Spotify: create an app at developer.spotify.com → copy Client ID/Secret (Client Credentials flow, no user login).
- YouTube: console.cloud.google.com → enable "YouTube Data API v3" → make an API key.

```powershell
$env:SPOTIFY_CLIENT_ID="xxx"; $env:SPOTIFY_CLIENT_SECRET="yyy"; $env:YOUTUBE_API_KEY="zzz"
```

## Quick links (no setup)

SoundCloud genre charts:

- Hip-hop/Rap — https://soundcloud.com/charts/top?genre=hiphoprap&country=US
- Rock — https://soundcloud.com/charts/top?genre=rock&country=US
- Metal — https://soundcloud.com/charts/top?genre=metal&country=US
- Dubstep — https://soundcloud.com/charts/top?genre=dubstep&country=US
- Drum & Bass — https://soundcloud.com/charts/top?genre=drumbass&country=US

YouTube playlist searches: append `+playlist` to a genre query, e.g.
<https://www.youtube.com/results?search_query=boom+bap+playlist&sp=EgIQAw%253D%253D>
(the `sp=` filter restricts results to playlists).

> Use these for **reference listening / inspiration**. Don't train a model you
> sell on copyrighted tracks — see the provenance + license notes (README §6).
