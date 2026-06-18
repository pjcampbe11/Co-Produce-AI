# Full Songs (2-4 min) - two options

The sample/beat pipeline makes loops and one-shots. For complete 2-4 minute
songs there are two engines, depending on whether you want vocals.

## A) Instrumental full songs - Stable Audio 3 (you already have it)
SA3 Medium generates up to ~380 s (6+ min). New `song` subcommand:
```bash
python scripts/sa3_workflow.py song --model medium \
  --prompt "boom bap hip hop instrumental, 90 BPM, key of F minor, dusty soul sample, \
intro then verse loop then hook with horns, vinyl crackle" \
  --duration 180 --out song_instr.wav
```
Works with your fine-tuned beat LoRA too: add `--lora F:\lora_beats\....safetensors`.
License: Stability Community License (free commercial < $1M revenue).

## B) Full songs WITH vocals + lyrics - HeartMuLa (song_generate.py)
HeartMuLa is an open song model (Apache-2.0 - true commercial use, no revenue
cap) that turns LYRICS + STYLE TAGS into a complete sung song, multilingual,
up to ~6 min.

Setup (one-time):  bash cloud/heartmula_setup.sh
```bash
python scripts/song_generate.py \
  --heartlib /workspace/heartlib --ckpt /workspace/heartlib/ckpt \
  --lyrics-file prompts/song_lyrics.example.txt \
  --tags "boom bap,hip hop,male vocals,dusty,90 bpm" \
  --duration 3 --out song.mp3 --lazy-load
```
- Lyrics: section tags `[Intro] [Verse] [Chorus] [Bridge] [Outro]` (see the
  example file). Tags: comma-separated, NO spaces between (piano,happy,romantic).
- VRAM: 3B fits ~16-24 GB; `--lazy-load` for a single GPU. Multi-GPU: split with
  `--mula-device cuda:0 --codec-device cuda:1`.
- It shells out to heartlib's run_music_generation.py - if a flag name differs in
  your version, run `python examples/run_music_generation.py --help` and adjust.

## Which to use
- Need an instrumental beat/track to rap or sing over -> A (SA3), and you can
  steer it with your own fine-tuned LoRA so it sounds like your catalog.
- Need a finished song with AI vocals from your written lyrics -> B (HeartMuLa).
- Rights: HeartMuLa's Apache-2.0 is the most permissive; SA3 is free commercial
  under $1M revenue. Either way, lyrics/style you provide should be your own.
