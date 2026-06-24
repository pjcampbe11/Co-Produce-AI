# API keys cheat sheet

All optional and free except where noted. Keys live in **environment variables**,
never in the repo. Windows: `$env:NAME="value"` (this shell) or
`setx NAME "value"` (persistent, new terminal). macOS/Linux: `export NAME=value`.

## Spotify  (playlist_meta.py, genre_playlists.py) — free
1. <https://developer.spotify.com/dashboard> → log in.
2. **Create app**. Name + description = anything. **Redirect URI** = `http://127.0.0.1:8888/callback` (required, unused by Client Credentials).
3. Tick **Web API**, accept terms, **Save**.
4. Open app → **Settings** → copy **Client ID** and **View client secret**.

```
SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
```

## Genius  (genius_lookup.py, playlist_meta.py --samples) — free
1. <https://genius.com/api-clients> → **New API Client**.
2. Fill any app name + URL → **Save**.
3. Click **Generate Access Token** → copy it.

```
GENIUS_TOKEN
```

## YouTube  (genre_playlists.py) — free
1. <https://console.cloud.google.com> → create/select a project.
2. **APIs & Services → Library** → enable **YouTube Data API v3**.
3. **Credentials → Create credentials → API key** → copy.

```
YOUTUBE_API_KEY
```

## Apple Music  (genre_playlists.py) — needs paid Apple Developer
1. Apple Developer account → **Certificates, Identifiers & Profiles → Keys** → create a **MusicKit** key (download the `.p8`).
2. Generate a **developer token** (JWT) signed with that key (ES256, your Team ID + Key ID). See Apple's "Generating Developer Tokens" docs.
3. Without it, the tool just emits an Apple Music search link.

```
APPLE_MUSIC_TOKEN
```

## RunPod  (cloud + serverless client) — account required
- **API key**: console.runpod.io → **Settings → API Keys** (for the Go client `RUNPOD_API_KEY`).
- **S3 keys**: **Settings → S3 API Keys** (separate; for the network volume — see `cloud/connect.md`).

## Stripe  (server/ billing) — account required
- `STRIPE_SECRET_KEY` (dashboard → Developers → API keys), `STRIPE_WEBHOOK_SECRET` (Developers → Webhooks → your endpoint), and `STRIPE_PRICES` (map each price id → plan + credits). See `server/.env.example` and `DEPLOY.md`.

## HuggingFace  (gated model downloads / training) — free
- `hf auth login` with a token from <https://huggingface.co/settings/tokens>; accept each gated model's terms on its model page.
