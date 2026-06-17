# yt-dlp Commands

## Playlist -> WAV (resumable)

```powershell
# items 102-500 (resume a partial pull; index in filenames starts at 102)
.\yt-dlp.exe --playlist-start 102 --playlist-end 500 -x --audio-format wav --download-archive done.txt -o '%(playlist_index)s - %(title)s.%(ext)s' 'https://www.youtube.com/playlist?list=PLb3DZrKKAtMo'

# whole playlist from item 102 onward (this list has 3392 items) - drop --playlist-end
.\yt-dlp.exe --playlist-start 102 -x --audio-format wav --download-archive done.txt -o '%(playlist_index)s - %(title)s.%(ext)s' 'https://www.youtube.com/playlist?list=PLb3DZrKKAtMo'
```

What the flags do:
- `--playlist-start 102 --playlist-end 500` - items 102-500 of the playlist
- `-x --audio-format wav` - extract audio, convert to WAV (needs ffmpeg on PATH)
- `--download-archive done.txt` - records finished IDs; re-run to RESUME / skip done
- `-o '%(playlist_index)s - %(title)s.%(ext)s'` - names files "001 - Title.wav"

### Notes
- Save to another drive: add `-P "F:\Downloads"` (or set the path in `-o`).
- WAV from YouTube is upsampled lossy audio (source is ~128-160k AAC/Opus).
  Fine as a reference/listening library; for training data prefer true WAV/FLAC.
  `23_deep_listen.py` flags this via its lossy-upsample spectral check.
- Update first if extraction fails: `.\yt-dlp.exe -U`
- Rights: downloading copyrighted tracks is for personal/reference use; do NOT
  feed these into a model you sell from (see provenance + license notes).
