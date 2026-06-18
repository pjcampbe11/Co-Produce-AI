# Vocal Removal - `scripts/remove_vocals.py`

One command, one job: remove vocals from a large batch of MP3/WAV files.

Two engines:
- **roformer (default)** - BS-RoFormer via [audio-separator](https://github.com/nomadkaraoke/python-audio-separator).
  Current SOTA (~12.9 dB vocals SDR vs ~9 for htdemucs) - noticeably cleaner
  instrumentals, less vocal bleed.
- **demucs** - [htdemucs](https://github.com/adefossez/demucs) fallback; also
  useful when you want full 4-stem separation.

## Setup (once)

```bash
pip install "audio-separator[gpu]"   # default engine ([cpu] works too, slower)
pip install demucs                   # optional fallback engine
```

- **GPU (NVIDIA):** used automatically if PyTorch sees CUDA — roughly 5-20x
  faster than CPU. CPU works fine, just slower (~1-4 min per song).
- **MP3 input/output** needs ffmpeg available on PATH (`winget install ffmpeg`
  on Windows / `brew install ffmpeg` on macOS / `apt install ffmpeg` on Linux).
- First run downloads the model weights (~300 MB) automatically.

## Usage

```bash
# whole folder (searched recursively), WAV instrumentals out (BS-RoFormer)
python scripts/remove_vocals.py --input songs/ --output instrumentals/

# also keep the isolated vocals (acapellas)
python scripts/remove_vocals.py --input songs/ --output out/ --keep-vocals

# demucs engine, MP3 320k out, 4 CPU jobs
python scripts/remove_vocals.py --input songs/ --output out/ \
    --engine demucs --model htdemucs_ft --mp3 --jobs 4
```

Each input `song.mp3` produces `song_instrumental.wav` (and
`song_vocals.wav` with `--keep-vocals`).

## Behavior

- **Resumable:** files whose output already exists are skipped, so you can
  re-run the same command after an interruption (`--overwrite` forces redo).
- **Large batches:** processes sequentially with a per-file progress log and a
  summary of any failures at the end (exit code 1 if any failed).
- **Quality:** BS-RoFormer is the right default (audited SOTA, June 2026).
  Model weights download automatically on first run. Heavily produced or
  auto-tuned vocals can still leave faint artifacts; for sampling work the
  instrumentals are typically clean enough.
- **Rights note:** separating a recording doesn't change its copyright. Use
  instrumentals from commercial tracks for private practice/reference; only
  feed cleared material into your training set or products.
