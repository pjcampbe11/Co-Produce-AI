# Sample chopper — 5 examples per producer

Every command produces **5 variations**, each with a master, slice one-shots,
`pattern.mid`, a cue-marked master, and `mpc/` + `ableton/` import folders.
Examples 1–2 are pure DSP (no AI); 3–5 use the optional AI flags
(`--stems` = separate + chop the melodic layer, `--reimagine` = audio2audio flip).
Swap the `--input` for your own (rights-cleared) sample.

## **********
_off-quantize micro-chops, swung, slight pitch drift_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input dusty_soul_loop.wav --bpm 90 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input dusty_soul_loop.wav --grid 16 --pads 16 --bpm 90 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 90 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input dusty_soul_loop.wav --reimagine --adg --target ableton --bpm 90 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input dusty_soul_loop.wav --stems --reimagine --target mpc --bars 4 --bpm 90 --out chops_**********
```

## **********
_pitched-up chipmunk-soul vocal chops, rearranged_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input otis_vocal.mp3 --bpm 92 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input otis_vocal.mp3 --grid 16 --pads 16 --bpm 92 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 92 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input otis_vocal.mp3 --reimagine --adg --target ableton --bpm 92 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input otis_vocal.mp3 --stems --reimagine --target mpc --bars 4 --bpm 92 --out chops_**********
```

## **********
_tight chopped stabs into a new melody, hard boom-bap_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input jazz_stab.wav --bpm 93 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input jazz_stab.wav --grid 16 --pads 16 --bpm 93 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 93 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input jazz_stab.wav --reimagine --adg --target ableton --bpm 93 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input jazz_stab.wav --stems --reimagine --target mpc --bars 4 --bpm 93 --out chops_**********
```

## **********
_clean grid-quantized soul loops, lightly pitched_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input soul_45.wav --bpm 86 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input soul_45.wav --grid 16 --pads 16 --bpm 86 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 86 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input soul_45.wav --reimagine --adg --target ableton --bpm 86 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input soul_45.wav --stems --reimagine --target mpc --bars 4 --bpm 86 --out chops_**********
```

## **********
_gritty, pitched-down, dusty lo-fi soul_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input kungfu_soul.wav --bpm 88 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input kungfu_soul.wav --grid 16 --pads 16 --bpm 88 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 88 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input kungfu_soul.wav --reimagine --adg --target ableton --bpm 88 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input kungfu_soul.wav --stems --reimagine --target mpc --bars 4 --bpm 88 --out chops_**********
```

## **********
_loose unquantized jazz chops, dusty and varied_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input obscure_jazz.wav --bpm 87 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input obscure_jazz.wav --grid 16 --pads 16 --bpm 87 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 87 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input obscure_jazz.wav --reimagine --adg --target ableton --bpm 87 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input obscure_jazz.wav --stems --reimagine --target mpc --bars 4 --bpm 87 --out chops_**********
```

## **********
_smooth soulful horns/jazz, filtered, layered_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input horn_loop.wav --bpm 91 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input horn_loop.wav --grid 16 --pads 16 --bpm 91 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 91 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input horn_loop.wav --reimagine --adg --target ableton --bpm 91 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input horn_loop.wav --stems --reimagine --target mpc --bars 4 --bpm 91 --out chops_**********
```

## **********
_big triumphant pitched-up soul, energetic_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input triumph_soul.wav --bpm 96 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input triumph_soul.wav --grid 16 --pads 16 --bpm 96 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 96 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input triumph_soul.wav --reimagine --adg --target ableton --bpm 96 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input triumph_soul.wav --stems --reimagine --target mpc --bars 4 --bpm 96 --out chops_**********
```

## **********
_hazy looped/halftime, filtered, psychedelic_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input hazy_psych.wav --bpm 82 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input hazy_psych.wav --grid 16 --pads 16 --bpm 82 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 82 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input hazy_psych.wav --reimagine --adg --target ableton --bpm 82 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input hazy_psych.wav --stems --reimagine --target mpc --bars 4 --bpm 82 --out chops_**********
```

## **********
_lo-fi swung short chops, gritty_

```bash
# 1) signature style, transient chops (no AI)
python scripts/sample_chop.py --producer ********** --input lofi_chop.wav --bpm 89 --out chops_**********
# 2) clean 16-slice grid for tight pads (no AI)
python scripts/sample_chop.py --producer ********** --input lofi_chop.wav --grid 16 --pads 16 --bpm 89 --target both --out chops_**********
# 3) AI: separate the source and chop the melodic stem
python scripts/sample_chop.py --producer ********** --input full_song.mp3 --stems --bpm 89 --out chops_**********
# 4) AI: audio2audio flip of each master + Ableton Drum Rack
python scripts/sample_chop.py --producer ********** --input lofi_chop.wav --reimagine --adg --target ableton --bpm 89 --out chops_**********
# 5) AI: both, MPC export, longer 4-bar loops
python scripts/sample_chop.py --producer ********** --input lofi_chop.wav --stems --reimagine --target mpc --bars 4 --bpm 89 --out chops_**********
```

