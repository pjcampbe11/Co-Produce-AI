# Getting true WAV / lossless source (or as close as possible)

You cannot un-compress a lossy file. mp3/AAC/Opus permanently discard data;
converting to WAV adds nothing. "True source" = go back to a lossless origin.

## Best legal sources (own/cleared - matters for a commercial model)

1. **Rip your own CDs** - Exact Audio Copy (EAC) or dBpoweramp -> WAV/FLAC.
   True 44.1 kHz / 16-bit redbook lossless. You own the disc.
2. **Buy WAV/FLAC downloads**:
   - Bandcamp - WAV & FLAC, huge indie/hip-hop catalog, supports artists.
   - Beatport / Juno - WAV & AIFF, best for electronic/dnb/dubstep.
   - Qobuz, HDtracks, 7digital - hi-res FLAC (often 24-bit).
3. **Record vinyl yourself** - analog capture into a decent ADC. Not "lossless"
   in the digital sense but a genuine high-quality source, and the dusty/warm
   character is exactly the boom-bap aesthetic. You control the chain.
4. **Cleared-sample services** - Tracklib (licensed original recordings to
   sample, in WAV), Splice (WAV one-shots/loops, rights to use). Best for a
   model you sell from - provenance is clean.
5. **Stems / project files** - official stem releases, your own sessions, or
   producer packs already in WAV.

## Streaming "lossless" tiers (legal to listen, NOT to rip for training)

Apple Music Lossless (ALAC), Tidal (FLAC), Amazon Music HD, Qobuz all stream
lossless - but they're DRM/ToS-protected; ripping them for a dataset is a
rights problem. Use them to decide what to then BUY in WAV.

## If you're stuck with YouTube only

There is no lossless on YouTube - max is ~128-160 kbps AAC/Opus. Grab the best
available stream (don't transcode to a "higher" bitrate, that's fake):
    yt-dlp -f bestaudio --extract-audio --audio-format flac URL
FLAC here just losslessly stores lossy audio - still lossy origin, but no
*further* loss. Treat these as reference/stylistic only, not pristine training.

## Verify what you actually have

- Your own tool: 23_deep_listen.py reports `rolloff95_hz` + a lossy-upsample
  note. Lossless music shows energy up to ~20-22 kHz; lossy shows a hard shelf
  around 16-20 kHz.
- Spek (free, spek.cc) - visual spectrogram; a flat cliff = lossy, full-to-top
  = likely lossless.
- ffprobe - shows codec/bitrate of the real stream:
      ffprobe -hide_banner -show_streams input.wav

## Practical recommendation for your beat model

For a *stylistic* boom-bap/lofi model the YouTube set is fine (the aesthetic is
already gritty). For a *pristine, sellable* model: build a smaller core of
true-WAV material - rip your CD collection, buy Bandcamp WAVs of the records
you'd sample, and/or record vinyl - then fine-tune (or continue-train) on that.
Quality of source > quantity here; 300-500 true-WAV beats can beat 1,500 lossy.
