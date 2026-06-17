# Organizing F:\Sound Bank (run on your PC)

Your bank: ~69,000 files / ~33,500 audio (plus 12k presets, 2.4k MIDI, REX,
Kontakt). The organizer runs locally - no cloud AI. The optional AI tagging
stage uses CLAP, a local model (~300 MB download, runs offline).

## One-time setup (PowerShell or cmd)

```bat
cd /d C:\path\to\samplepack-toolkit
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
pip install laion-clap        :: only needed for --ai-tags
```

## Phase 1 - Dry run (30-60 min, touches nothing)

```bat
python scripts\07_organize_soundbank.py --input "F:\Sound Bank" --output "F:\Sound Bank Organized" --dry-run
```
Open `F:\Sound Bank Organized\review.csv` in Excel - sanity-check ~50 rows
across categories. Low-confidence files are headed to `_review\`.

## Phase 2 - The real run

```bat
python scripts\07_organize_soundbank.py --input "F:\Sound Bank" --output "F:\Sound Bank Organized" --resume
```
- COPIES files (originals untouched). Needs free space roughly equal to the
  audio portion of the bank. Add `--move` only if disk is tight and you trust
  the dry run.
- `--resume` makes it safe to Ctrl+C and re-run anytime.
- MIDI -> `midi\`, REX -> `rex_loops\`, synth/Kontakt presets -> `presets\`,
  junk (.asd, artwork, docs) skipped.
- Time: most of your bank has descriptive filenames (fast path, hundreds/sec);
  ambiguous files get audio analysis (~1-2 s each). Expect a few hours.

## Phase 3 - AI tagging (optional but recommended)

```bat
python scripts\07_organize_soundbank.py --input "F:\Sound Bank" --output "F:\Sound Bank Organized" --resume --ai-tags
```
CLAP zero-shot scores every organized file against a 36-term producer
vocabulary (dusty vinyl, 1990s boom bap, reese bass, metal chugs, riser...)
and writes `<file>.tags.json`. `01_prepare_dataset.py` automatically merges
these into training prompts. GPU: ~1-3 h for 33k files; CPU: overnight.

## Phase 4 - Human pass

1. Listen-sort `F:\Sound Bank Organized\_review\` (the report says how many).
2. Drop `tags.txt` descriptors into key folders where your ear knows better
   than the model.

## License caution

This bank is mostly commercial packs (808 Mafia, Big Fish, Beat Butcha...).
Organizing/using them in your own beats: per their licenses, generally fine.
TRAINING a model you sell from: most pack licenses don't grant ML rights -
check per pack before including it in `01_prepare_dataset.py` input. Your
provenance system (21) is only as good as this step.
