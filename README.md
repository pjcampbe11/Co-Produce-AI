<h1 align="center">🎛️ Beat Toolkit</h1>
<p align="center"><b>Turn your own sound into your own AI.</b><br>
An end-to-end studio that learns <i>your</i> beats, lyrics, and library — then organizes, analyzes, generates, remixes, and packages hip-hop (and rock/metal, dubstep, DnB) from raw crate to finished, rights-traced product.</p>

<p align="center">
<img src="docs/gifs/hero.gif" alt="Beat Toolkit dashboard demo" width="85%">
<br><sub><i>▶ Demo: the dashboard driving the full pipeline — organize → analyze → train → generate → remix → pack. (record at docs/gifs/hero.gif)</i></sub>
</p>

> **Engine note:** recommended generation engine is **Stable Audio 3** (LoRA fine-tuning), with **Stable Audio Open 1.0** as the full-fine-tune alternative — open-weight Stability AI models (Community License). Full songs with vocals use **HeartMuLa** (Apache-2.0). Lyric writing runs on a **local Ollama** model. Vocal synthesis bridges to **ACE Studio**. Everything model/GPU-heavy defaults to a **cloud GPU pod**.

---

## 📖 Table of Contents

### Getting started

1. [What is Beat Toolkit?](#1-what-is-beat-toolkit)
2. [How it all fits together](#2-how-it-all-fits-together)
3. [Quick start](#3-quick-start)
4. [Install & setup](#4-install--setup)
5. [Cloud GPU pod (default for everything GPU)](#5-cloud-gpu-pod-default-for-everything-gpu)
6. [Legal & licensing](#6-legal--licensing)

### The pipeline

7. [Organize your soundbank](#7-organize-your-soundbank)
8. [Remove vocals (stem separation)](#8-remove-vocals)
9. [Deep Listen — analyze any track](#9-deep-listen)
10. [Auto-tag — open-vocabulary mood/vibe](#10-auto-tag)
11. [Genius metadata enrichment](#11-genius-metadata)
12. [Build captions — fuse it all](#12-build-captions)
13. [Prepare & validate the dataset](#13-prepare--validate)
14. [Train your model (cloud)](#14-train-your-model)
15. [Generate samples & packs](#15-generate)
16. [Audio-to-audio (flip a sound)](#16-audio-to-audio)
17. [Remix — genre transform & mashup](#17-remix)
18. [Beat builder — beats from your samples](#18-beat-builder)
19. [VST3 instruments & effect chains](#19-vst3)
20. [Full songs (2–4 min)](#20-full-songs)
21. [ACE Studio vocals](#21-ace-studio)
22. [Lyric model — write in your voice](#22-lyric-model)
23. [Post-process, package, provenance](#23-finish)
24. [Creative Techniques Lab](#24-creative-techniques)
    - [Taste distillation](#ct-curation)
    - [Micro-variants](#ct-microvariants)
    - [Groove DNA](#ct-groove)
    - [Flip lineage](#ct-lineage)
    - [Destroy-and-heal](#ct-destroyheal)
    - [Two-producer packs](#ct-abmodels)
    - [Push as an instrument](#ct-push)
    - [AI session musician](#ct-callresponse)
    - [Ecosystem packs](#ct-ecosystem)
25. [Genre expansion: rock/metal & dubstep/DnB](#25-genre-expansion)
26. [Dashboard (web UI)](#26-dashboard)

### Reference & appendices

27. [Training specs & costs](#27-specs--costs)
28. [Sourcing lossless audio](#28-lossless)
29. [yt-dlp commands](#29-ytdlp)
30. [Business & learning path](#30-business)
31. [Full script reference](#31-scripts)
32. [Engine choice: Stable Audio 3 vs ACE-Step 1.5](#32-engines)
33. [License & notice](#33-license)

> **How to read this:** every feature section follows the same shape — a plain-English **What it is**, a **Demo** gif, the **Setup & run** steps, and **Optional / good-to-have** extras. Demos live in `docs/gifs/` (placeholders — record them from the dashboard). Anything needing a GPU shows the **cloud pod** path first.

---

<a name="1-what-is-beat-toolkit"></a>
## 1. What is Beat Toolkit?

**What it is.** A complete, self-hosted music-production AI suite built around one idea: *your* catalog is the moat. Instead of a generic model, you fine-tune on your own sounds and lyrics so the output sounds like **you**. It spans the whole journey — cleaning and labeling a messy sample library, analyzing and tagging every file, fine-tuning open audio models, generating one-shots/loops/beats/full songs, remixing across genres, writing lyrics in your voice, rendering through your real VST plugins, and shipping provenance-verified sample packs.

**Who it's for.** Producers and small AI-audio services who want owned, rights-clean, genre-deep output — not the homogenized sound of shared models.

<p align="center"><img src="docs/gifs/overview.gif" width="80%"><br><sub><i>▶ Demo: end-to-end — a folder of beats becoming a trained model and a finished pack.</i></sub></p>

<a name="2-how-it-all-fits-together"></a>
## 2. How it all fits together

```
                YOUR RAW MATERIAL                         YOUR MODELS                    OUTPUT
  ┌───────────────────────────────────┐      ┌──────────────────────────┐    ┌──────────────────────┐
  library ─ organize ─┐                │      │  Stable Audio 3 LoRA     │    │  one-shots / loops   │
  songs ─ remove_vocals ─ raw_beats ─┐ ├─ deep_listen ─ auto_tag ─┐      │    │  beats / full songs  │
  lyrics ────────────────────────────┘ │      genius_lookup ──── build_captions ─ prepare ─ validate ─▶ TRAIN ─▶ generate ─▶ postprocess ─▶ build_pack ─▶ provenance ─▶ .zip
  your lyrics ─ lyric_analyze ─ lyric_generate ─ lyric_to_beat ──┘      │      (cloud pod GPU)        remix / audio2audio / beat_builder
  your VSTs ─ plugin_scan ─ vst_instrument / vst_chain ──────────┘      │      ACE Studio vocals (vocal_guide → ACE Bridge → Ableton)
  └───────────────────────────────────┘      └──────────────────────────┘
```

Each box is a script (and a dashboard tab). You can run the whole chain or any single step — they pass data via sidecar files (`.caption.json`, `.tags.json`, `.genius.json`, `.caption.txt`) so steps compose cleanly.

<a name="3-quick-start"></a>
## 3. Quick start

```powershell
git clone https://github.com/pjcampbe11/Beat-Toolkit.git
cd Beat-Toolkit
pip install -r requirements.txt
python dashboard.py          # web UI for everything, or use the CLIs below
```

Fastest path to a result (no training needed): point `beat_builder.py` at an organized sample folder →
```powershell
python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --bars 4 --count 4 --out beats
```

<a name="4-install--setup"></a>
## 4. Install & setup

**Local (CPU-light steps):** Python 3.10+ recommended (3.9 works with caveats). `pip install -r requirements.txt`. Optional features pull extra packages — each section lists them.

**ffmpeg** is needed for MP3/M4A decoding (yt-dlp, librosa fallback): `winget install ffmpeg`.

**Route big model downloads to another drive** (so caches don't fill C:):
```powershell
# run cloud/use_F_drive.ps1, or set these once (Admin PowerShell):
[Environment]::SetEnvironmentVariable("HF_HOME","F:\ai_cache\huggingface","Machine")
[Environment]::SetEnvironmentVariable("TORCH_HOME","F:\ai_cache\torch","Machine")
[Environment]::SetEnvironmentVariable("PANNS_DATA_DIR","F:\ai_cache\panns_data","Machine")
[Environment]::SetEnvironmentVariable("AUDIO_SEPARATOR_MODELS","F:\ai_cache\audio_separator","Machine")
```
*Optional/good-to-have:* a venv (`python -m venv .venv`); a HuggingFace account (gated models need you to accept terms + `hf auth login`).

<a name="5-cloud-gpu-pod-default-for-everything-gpu"></a>
## 5. Cloud GPU pod (default for everything GPU)

**What it is.** Training and large-model generation run on a **rented GPU pod**, not your local card — it's faster, cheaper than it sounds, and avoids dependency pain. This is the **default** for every GPU step in this README; a local GPU is only a fallback.

<p align="center"><img src="docs/gifs/pod.gif" width="80%"><br><sub><i>▶ Demo: spinning up a pod, uploading data, running a step, pulling results.</i></sub></p>

**Minimums (operator picks anything at or above):**

| Step | Min VRAM | Suggested pod |
|---|---|---|
| SA3 **LoRA** train | 16 GB | RTX 4090 / A5000 (24 GB) |
| SAO **full** fine-tune | 24 GB | A100 40–80 GB / A6000 |
| Generation / remix / vocal removal | 8 GB | RTX 4090 / A5000 |
| Lyric LLM (bigger models) | 12–24 GB | any 24 GB |

CPU cores and RAM are the operator's choice — more cores speed up data prep and audio I/O; 8+ vCPU / 32 GB is comfortable. **You provide the account + payment** (I/the toolkit can't rent it for you).

**Setup (RunPod example):** deploy a **PyTorch 2.x / CUDA 12** template, RTX 4090+ , a **persistent volume mounted at `/workspace`** sized for your data (input + output; e.g. 80 GB). Then:
```bash
bash /workspace/toolkit/cloud/sa3_setup.sh        # Stable Audio 3 + LoRA
# or cloud/runpod_setup.sh for the SAO full-fine-tune path
```
Move data with `runpodctl send`/`receive` (peer-to-peer) or rclone. **Terminate the pod when done** — it bills per second.

*Optional/good-to-have:* size the volume generously (a 2-min, multi-stem render can need 25 GB of scratch); batch several GPU steps (train + tag + generate) in one session before terminating; route HF cache to the persistent volume.

<a name="6-legal--licensing"></a>
## 6. Legal & licensing

Read this before commercializing (not legal advice — consult an IP attorney):

- **Training data:** only train on audio you **own or have explicit ML-training rights to**. Owning a sample pack or a record does *not* grant the right to train a generative model on it and sell the output — that's a separate, unsettled rights question. Safest: your own productions, libraries explicitly cleared for AI/ML, public-domain/CC, or cleared-sample services.
- **Base-model license:** Stable Audio (Community License) is free for commercial use under **US$1M** annual revenue; enterprise license above that. **HeartMuLa is Apache-2.0** (no revenue cap) — the cleaner footing for vocal songs. **ACE Studio** vocals are yours per its license.
- **Provenance is your friend:** `provenance.py` records training sources, run id, generation seeds, and per-file hashes into a certificate — evidence you sourced responsibly. It's evidence, not a license; the underlying rights still have to exist.
- **Lossless ≠ rights:** a WAV from YouTube is as infringing as the MP3. Format is sonic; *acquisition/clearance* is legal.

---

<a name="7-organize-your-soundbank"></a>
## 7. Organize your soundbank

**What it is.** Turns a messy, unsorted sample library into the tagged folder structure the toolkit trains and builds from — auto-classifying kicks/snares/hats/percs/808s, drum loops, melodic loops, vocals, FX, and routing MIDI/REX/presets. Classification uses filename keywords first, then audio analysis (spectral/onset features) as a fallback, with a confidence-scored review CSV.

<p align="center"><img src="docs/gifs/organize.gif" width="80%"><br><sub><i>▶ Demo: a chaotic folder → clean tag-folders + review.csv.</i></sub></p>

**Setup & run** (local; pure DSP, no GPU):
```powershell
python scripts/organize_soundbank.py --input "F:/Sound Bank" --output "F:/Sound Bank Organized" --dry-run
python scripts/organize_soundbank.py --input "F:/Sound Bank" --output "F:/Sound Bank Organized" --resume
```
Files are **copied** (originals safe) unless `--move`. `--dry-run` previews to `review.csv`; low-confidence files land in `_review/` for manual sorting. Folder names become training prompt tags, so name them descriptively; drop a `tags.txt` (comma-separated) in any folder to add era/texture descriptors — **this is where your genre knowledge becomes the moat.**

*Optional/good-to-have:* `--ai-tags` runs local CLAP zero-shot tagging after sorting; `--include-nonaudio` routes MIDI/REX/Kontakt presets; on huge banks use `--resume` and run overnight. Windows long-path fix: enable `LongPathsEnabled` if deep pack folders error.

<a name="8-remove-vocals"></a>
## 8. Remove vocals (stem separation)

**What it is.** Strips vocals from a large batch of MP3/WAV to get clean instrumentals (and optional acapellas), using **BS-RoFormer** (current SOTA, ~12.9 dB vocal SDR) with a Demucs fallback.

<p align="center"><img src="docs/gifs/vocal_removal.gif" width="80%"><br><sub><i>▶ Demo: a folder of songs → *_instrumental files, GPU-accelerated.</i></sub></p>

**Setup & run** (GPU — **cloud pod default**; runs locally on 8 GB+):
```bash
pip install "audio-separator[gpu]"
python scripts/remove_vocals.py --input songs/ --output raw_beats/ --mp3 --keep-vocals --require-gpu
```
`--require-gpu` aborts rather than silently crawling on CPU. `--mirror` preserves subfolder structure (use when input is sorted into albums to avoid same-name collisions). It's resumable — re-run to continue.

*Optional/good-to-have:* `--engine demucs` for 4-stem separation; `--keep-vocals` to save acapellas for your lyric/ACE work; on a pod, write the zip to a roomy disk before `runpodctl send` (a 25 GB output won't fit on a full volume).

<a name="9-deep-listen"></a>
## 9. Deep Listen — analyze any track

**What it is.** Learns everything possible about a file: technical truth (sample rate, LUFS, crest/dynamics, stereo correlation, clipping, band-by-band spectrum, lossy-upsample detection), musical analysis (BPM + tempo stability, key, onset density, structure, energy arc), **sound identification** (every event with timestamps across AudioSet's 527 classes via PANNs), and **mood/genre/instrument/production** (CLAP zero-shot). Outputs `.analysis.json` + readable `.analysis.md`.

<p align="center"><img src="docs/gifs/deep_listen.gif" width="80%"><br><sub><i>▶ Demo: drop a track → full technical + musical + vibe report.</i></sub></p>

**Setup & run** (GPU optional — PANNs/CLAP use it if present):
```bash
pip install panns-inference laion-clap beat-this
python scripts/deep_listen.py --input track.mp3 --out reports/
python scripts/deep_listen.py --input "F:/RAP_ARCHIVES/raw_beats" --out "F:/RAP_ARCHIVES/raw_beats" --for-captions --resume
```
`--for-captions` writes a slim `<file>.caption.json` (only what the caption builder needs). Pointing `--out` at the audio folder puts reports adjacent, so `build_captions.py` finds them with no extra flags.

*Optional/good-to-have:* `--no-events`/`--no-vibe` to skip the model layers for a fast technical-only pass; run it on the pod alongside vocal removal; use it as a pre-purchase QA tool on sample packs (the lossy-upsample flag catches fake "WAVs").

<a name="10-auto-tag"></a>
## 10. Auto-tag — open-vocabulary mood/vibe

**What it is.** Tags the *feel* of a beat in free-form language (not a fixed list) by having an audio-language model **listen** and describe it. Can tag the full mix, just the vocal, just the beat, or all stems separately — using your already-separated stems.

<p align="center"><img src="docs/gifs/auto_tag.gif" width="80%"><br><sub><i>▶ Demo: a beat → "dark, dusty, trap, 808-heavy" written to a sidecar.</i></sub></p>

**Setup & run** (GPU — **cloud pod default**; Qwen wants 16 GB+):
```bash
pip install transformers accelerate
python scripts/auto_tag.py --stems-dir "F:/RAP_ARCHIVES/raw_beats" --source beat --engine qwen3-omni --resume
```
Engines: `qwen3-omni` (most detailed) → `qwen2-audio` (lighter) → `clap` (light fallback). `--source beat` tags only `*_instrumental`. `--limit N --shuffle` processes random batches; repeat runs walk the dataset (with `--resume`).

*Optional/good-to-have:* `--source all` tags vocal+beat+full separately for richer captions; pre-stemmed parallel folders or suffix layouts both supported; start with `--limit 25` to sanity-check tag quality before the full archive.

<a name="11-genius-metadata"></a>
## 11. Genius metadata enrichment

**What it is.** Matches each beat to a Genius song by filename and writes a metadata sidecar — **producer, writers, album, release year, URL** (metadata only; never lyrics). Feeds real production lineage into your captions.

<p align="center"><img src="docs/gifs/genius.gif" width="80%"><br><sub><i>▶ Demo: filenames → producer/era metadata sidecars.</i></sub></p>

**Setup & run** (local; needs a free Genius token):
```powershell
# make a client at https://genius.com/api-clients -> Generate Access Token
$env:GENIUS_TOKEN = "your_client_access_token"
pip install requests
python scripts/genius_lookup.py --beats "F:/RAP_ARCHIVES/raw_beats" --resume
```
Cleans track numbers/`_instrumental`/"(OFFICIAL VIDEO)" noise from filenames, takes the best hit, records a `match_score` + `low_confidence` flag so you can spot-check.

*Optional/good-to-have:* `--limit 25` test first; the token stays in an env var (never hard-coded); low-confidence matches are flagged, not trusted blindly.

<a name="12-build-captions"></a>
## 12. Build captions — fuse it all

**What it is.** Composes ONE canonical training caption per beat in a consistent field order — fusing Deep Listen analysis + your auto-tags + Genius producer/era — so your model learns audio *and* production lineage. Leads with a subgenre only when the analysis is confident, else plain `hip hop`.

<p align="center"><img src="docs/gifs/captions.gif" width="80%"><br><sub><i>▶ Demo: three sidecars → "trap, 808 bass, dark, 140 BPM, key of F minor, prod Speaker Knockerz, 2010s".</i></sub></p>

**Setup & run** (local):
```powershell
python scripts/build_captions.py --beats "F:/RAP_ARCHIVES/raw_beats"
```
Writes `<beat>.caption.txt` next to each file; `prepare_dataset.py` uses it verbatim as the training prompt.

*Optional/good-to-have:* `--genre-threshold` tunes how confident a subgenre must be to lead; `--no-genius` to ignore Genius data; `--dry-run` to preview captions before writing.

<a name="13-prepare--validate"></a>
## 13. Prepare & validate the dataset

**What it is.** Converts your library to 44.1 kHz stereo, slices long files under the model window, auto-detects BPM/key, writes per-file prompt sidecars, then validates the set before you spend a cent on GPU.

<p align="center"><img src="docs/gifs/prepare.gif" width="80%"><br><sub><i>▶ Demo: raw beats → clean dataset/ + "ready for training".</i></sub></p>

**Setup & run** (local):
```powershell
python scripts/prepare_dataset.py --input "F:/RAP_ARCHIVES/raw_beats" --output "F:/dataset_beats" --name-contains _instrumental
python scripts/validate_dataset.py --dataset "F:/dataset_beats"
```
`--name-contains _instrumental` includes only beats (skips `_vocals`). Validation fails loudly on wrong sample rates, silence, empty prompts, or over-length files. Genre BPM ranges: add `--bpm-min/--bpm-max` (DnB 100–200 so 174 isn't folded to 87).

*Optional/good-to-have:* spot-check `dataset/prepare_log.txt` and a few sidecar prompts; fix bad folder tags and re-run; treat clipping warnings seriously.

<a name="14-train-your-model"></a>
## 14. Train your model (cloud)

**What it is.** Fine-tunes an open audio model on *your* dataset so generation sounds like your catalog. Two paths: **SA3 LoRA** (recommended — small adapter, ~$1–2, an hour or two, stackable per-genre) and **SAO full fine-tune** (maximum ownership, ~$8–40). Cloud pod is the default.

<p align="center"><img src="docs/gifs/train.gif" width="80%"><br><sub><i>▶ Demo: dataset → LoRA training on a pod, demo audio improving over steps.</i></sub></p>

**Mental model:** cost is **GPU-hours, not per-file** — the loader samples random crops across thousands of steps. A 500-file and a 3,000-file run cost ~the same. You don't pick "sets at once"; you set batch size + steps. **Sweet-spot dataset: 500–1,500 well-labeled, on-aesthetic files** — curation beats raw count.

**Setup & run — SA3 LoRA (cloud pod, 16 GB+):**
```bash
# on the pod (after cloud/sa3_setup.sh)
python /workspace/toolkit/scripts/sa3_workflow.py prepare --dataset /workspace/dataset_beats --data-dir /workspace/sa3_beats
cd /workspace/stable-audio-3 && uv run python scripts/train_lora.py --model medium-base \
  --data_dir /workspace/sa3_beats --rank 16 --adapter_type dora-rows --steps 2500 --exclude seconds_total --output_dir /workspace/lora_beats
runpodctl send /workspace/lora_beats/lora_step2500.safetensors   # receive on your PC
```
Watch the trainer's demo audio; **stop when it sounds like your aesthetic but not like specific files** (overfitting). ~2000–3000 steps is a good range for this size.

**Alternative engine — ACE-Step 1.5 (MIT, no revenue cap):** a second first-class engine (one model for beats *and* vocal songs, no $1M cap). Full setup, examples, and an A/B comparison are in [§32 Engine choice](#32-engines).

**SAO full fine-tune (24 GB+ pod):** `cloud/runpod_setup.sh` then `train.py` (see flags inline). Use when LoRA stops capturing your sound.

*Optional/good-to-have:* one **LoRA per subgenre** (swap/blend at runtime); `--base_precision bf16 --adapter_type lora-xs` for ~5.5 GB VRAM; resume from a checkpoint to continue-train; keep several checkpoints (last isn't always best).

<a name="15-generate"></a>
## 15. Generate samples & packs

**What it is.** Batch-generates audio from a pack plan (counts, durations, prompts) using your fine-tuned model. Over-generate 2–3× and curate hard.

<p align="center"><img src="docs/gifs/generate.gif" width="80%"><br><sub><i>▶ Demo: a pack plan → folders of kicks/snares/loops.</i></sub></p>

**Setup & run** (GPU — **cloud pod default**; runs locally on 8 GB+):
```bash
# SA3:
python scripts/sa3_workflow.py plan --model medium-base --lora my.safetensors --plan prompts/pack_plan.example.json --out generated
# SAO:
python scripts/generate.py --model-config model_config.json --ckpt hiphop_v1.ckpt --plan prompts/pack_plan.example.json --out generated --steps 100 --cfg 7
```
Edit `prompts/pack_plan.example.json` using the **same tag vocabulary you trained with**. `--cfg` = prompt adherence (6–9); sanity-check anytime with the base model via `--pretrained stabilityai/stable-audio-open-1.0`.

**5 examples:**
```bash
# 1. SA3 + your LoRA from a pack plan -> generated/<category>/
python scripts/sa3_workflow.py plan --model medium-base --lora hiphop_v1.safetensors --plan prompts/pack_plan.example.json --out generated
# 2. SAO full-fine-tune checkpoint
python scripts/generate.py --model-config model_config.json --ckpt hiphop_v1.ckpt --plan prompts/pack_plan.example.json --out generated --steps 100 --cfg 7
# 3. base-model sanity check (no training) to test the pipeline
python scripts/generate.py --pretrained stabilityai/stable-audio-open-1.0 --plan prompts/pack_plan.example.json --out test_gen --steps 80
# 4. tighter prompt adherence (higher cfg) for a precise pack
python scripts/generate.py --model-config model_config.json --ckpt hiphop_v1.ckpt --plan prompts/pack_plan.example.json --out generated --cfg 9
# 5. a genre pack plan (rock/metal or dnb) through the same engine
python scripts/sa3_workflow.py plan --model medium-base --lora metal_v1.safetensors --plan prompts/pack_plan.rock_metal.json --out generated_metal
```

*Optional/good-to-have:* SA3 `fill` (inpaint a region) and `extend` (continue a clip) modes; ecosystem-locked plans (see §24) so a whole pack series shares key/BPM.

<a name="16-audio-to-audio"></a>
## 16. Audio-to-audio (flip a sound)

**What it is.** Feed any WAV and get new sounds *derived* from it, steered by a prompt — the model treats your file as the diffusion seed; `--strength` sets how far it transforms (0.2 re-texture → 0.5 real flip → 0.8 loose inspiration).

<p align="center"><img src="docs/gifs/audio2audio.gif" width="80%"><br><sub><i>▶ Demo: a break → four flipped variations.</i></sub></p>

```bash
python scripts/audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input my_break.wav \
  --prompt "hip hop, boom bap, 90 BPM, dusty drum break, vinyl texture" --strength 0.5 --variations 4 --out flipped/
```
**5 examples:**
```bash
# 1. real flip of a drum break (0.5 = clearly transformed but recognizable)
python scripts/audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input break.wav --prompt "hip hop, boom bap, 90 BPM, dusty drum break" --strength 0.5 --variations 4 --out flipped
# 2. subtle re-texture (0.2) — same groove, new character
python scripts/audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input loop.wav --prompt "warm vinyl, tape saturation" --strength 0.2 --out retex
# 3. loose inspiration (0.8) — mostly the prompt, a hint of the source
python scripts/audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input loop.wav --prompt "dark cinematic strings" --strength 0.8 --out loose
# 4. flip a melodic loop into a new key/vibe
python scripts/audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input keys.wav --prompt "soul keys, key of F minor, dusty" --strength 0.45 --variations 3 --out flipped_keys
# 5. no trained model yet? flip with the base model
python scripts/audio2audio.py --pretrained stabilityai/stable-audio-open-1.0 --input break.wav --prompt "lofi hip hop drums" --strength 0.5 --out flipped
```

*Optional/good-to-have:* only feed audio you have rights to (outputs are derivative); run results through `postprocess.py`.

<a name="17-remix"></a>
## 17. Remix — genre transform & mashup

**What it is.** A pure remixer: re-imagine a finished track as **hip-hop / rock-metal / dubstep / DnB** (`full`), or **fuse** a target genre with the track's current vibe (`mashup`).

<p align="center"><img src="docs/gifs/remix.gif" width="80%"><br><sub><i>▶ Demo: one beat → a DnB remix and a trap-mashup.</i></sub></p>

```bash
python scripts/remix.py --pretrained stabilityai/stable-audio-open-1.0 --input song.wav --genre dnb --mode full --variations 3 --out remixes/
python scripts/remix.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input song.wav --genre rockmetal --mode mashup --current "boom bap hip hop" --out remixes/
```
Strength auto-picks (full 0.6 / mashup 0.4). Quality scales with the model — a per-genre LoRA makes remixes far more convincing than the base model.

**5 examples:**
```bash
# 1. full DnB remix of any track
python scripts/remix.py --pretrained stabilityai/stable-audio-open-1.0 --input song.wav --genre dnb --mode full --variations 3 --out remixes
# 2. full dubstep remix
python scripts/remix.py --pretrained stabilityai/stable-audio-open-1.0 --input song.wav --genre dubstep --mode full --out remixes
# 3. rock/metal MASHUP that keeps the original's hip-hop bones
python scripts/remix.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input song.wav --genre rockmetal --mode mashup --current "boom bap hip hop" --out remixes
# 4. hip-hop mashup of a DnB track
python scripts/remix.py --pretrained stabilityai/stable-audio-open-1.0 --input dnb_track.wav --genre hiphop --mode mashup --current "drum and bass" --out remixes
# 5. subtle remix (override strength) — light genre nudge
python scripts/remix.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input song.wav --genre dnb --mode mashup --strength 0.3 --out remixes
```

*Optional/good-to-have:* also available as a **Remix tab** and a **Remix-the-selected-file** panel inside the dashboard's Audition view.

<a name="18-beat-builder"></a>
## 18. Beat builder — beats from your samples

**What it is.** Sequences kicks/snares/hats/percs/808s from your organized library on style grids (boom_bap, trap, drill, lofi, rock, metal, dbeat, dubstep, dnb, amen) with swing + humanization, layers a melodic loop, and outputs master + stems + `pattern.mid` + a manifest of exactly which samples were used. No GPU needed.

<p align="center"><img src="docs/gifs/beat_builder.gif" width="80%"><br><sub><i>▶ Demo: a sample folder → a finished 4-bar beat + MIDI.</i></sub></p>

```bash
python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --bars 4 --count 8 --melodic "F:/SoundBankAI/melodic_loops" --out beats
```
`--rotate` picks a different sample per hit (pair with micro-variants for human feel); `--groove file.groove.json` applies an extracted groove (see §24).

**5 examples:**
```bash
# 1. classic boom bap, 4 bars, 8 beats to choose from
python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --bars 4 --count 8 --out beats
# 2. trap at 140 with 808s
python scripts/beat_builder.py --library "F:/SoundBankAI" --style trap --bpm 140 --bars 4 --count 6 --out beats_trap
# 3. lofi with a melodic loop layered + a swung groove template
python scripts/beat_builder.py --library "F:/SoundBankAI" --style lofi --bpm 82 --melodic "F:/SoundBankAI/melodic_loops" --groove grooves/dilla_a.groove.json --out beats_lofi
# 4. drill, every hit a different sample (human feel)
python scripts/beat_builder.py --library "F:/SoundBankAI" --style drill --bpm 142 --rotate --out beats_drill
# 5. cross-genre: a metal double-kick pattern from your kit (see §25)
python scripts/beat_builder.py --library "F:/SoundBankAI" --style metal --bpm 170 --bars 4 --count 4 --out beats_metal
```

*Optional/good-to-have:* `pattern.mid` drops onto an Ableton Drum Rack (GM mapping: kick 36, snare 38, hat 42, perc 47, 808 35); match the melodic loop's BPM to the beat so it locks.

<a name="19-vst3"></a>
## 19. VST3 instruments & effect chains

**What it is.** Drive your real plugins headlessly with pedalboard — render MIDI through your **instruments** (Battery, Massive, Kontakt, FM8…) and process audio through your **effects** (Saturn, tape, comps, limiters). A scanner catalogs what's installed; the dashboard's Plugin browser lets you pick by name.

<p align="center"><img src="docs/gifs/vst.gif" width="80%"><br><sub><i>▶ Demo: pattern.mid → Battery render → dusty effect chain → finished loop.</i></sub></p>

```bash
pip install pedalboard
python scripts/plugin_scan.py                                   # build plugins_catalog.json
python scripts/vst_instrument.py --vst3 ".../Battery 4.vst3" --midi beats/.../pattern.mid --chain configs/vst_chains/dusty_boombap.json --out kit.wav
python scripts/vst_chain.py --input processed --output processed_vst --chain configs/vst_chains/dusty_boombap.json
```
Ready-made chains built from common plugins live in `configs/vst_chains/` (dusty boom-bap, metal master, bass-music mangle, destroy chain, Ozone vocal-suppress). Use `--edit N` to dial a plugin's GUI once; settings apply to the whole batch. `--list-params` prints automatable names.

**5 examples:**
```bash
# 1. dusty boom-bap glue on a folder of processed samples (Saturn 2 -> TASCAM tape -> Pro-C -> Pro-L)
python scripts/vst_chain.py --input processed --output processed_dusty --chain configs/vst_chains/dusty_boombap.json
# 2. metal master chain (Pro-Q -> Trash -> Pro-C -> Pro-L)
python scripts/vst_chain.py --input metal_loops --output metal_mastered --chain configs/vst_chains/metal_master.json
# 3. bass-music mangle (Thermal -> Portal -> Pro-Q -> Pro-L)
python scripts/vst_chain.py --input bass_loops --output bass_mangled --chain configs/vst_chains/bassmusic_neuro.json
# 4. render a beat's MIDI through your Battery kit AND glue it in one step
python scripts/vst_instrument.py --vst3 "C:/Program Files/Common Files/VST3/Battery 4.vst3" --midi beats/boom_bap_90bpm_01/pattern.mid --chain configs/vst_chains/dusty_boombap.json --out kit_dusty.wav
# 5. last-resort vocal suppression via Ozone Master Rebalance (open GUI to pull Vocals down)
python scripts/vst_chain.py --input songs --output instrumentals --chain configs/vst_chains/ozone_vocal_suppress.json --edit 0
```

*Optional/good-to-have:* **bake your sound into the model** — run your *training dataset* through a character chain before fine-tuning so the model learns your saturation/tape identity; Kontakt needs an `.nki` loaded; ACE Bridge can't render headless (needs the ACE app).

<a name="20-full-songs"></a>
## 20. Full songs (2–4 min)

**What it is.** Beyond loops — complete tracks. **Instrumental** songs via Stable Audio 3 (up to ~380 s, works with your beat LoRA); **songs with vocals from your lyrics** via HeartMuLa (Apache-2.0, no revenue cap).

<p align="center"><img src="docs/gifs/full_songs.gif" width="80%"><br><sub><i>▶ Demo: a prompt → a 3-minute instrumental; lyrics → a sung/rapped song.</i></sub></p>

```bash
# instrumental (SA3), works with your LoRA:
python scripts/sa3_workflow.py song --model medium --lora my.safetensors --prompt "boom bap instrumental, 90 BPM, F minor, vinyl" --duration 180 --out song.wav
# vocals + lyrics (HeartMuLa):  bash cloud/heartmula_setup.sh
python scripts/song_generate.py --heartlib /workspace/heartlib --ckpt /workspace/heartlib/ckpt --lyrics-file prompts/song_lyrics.example.txt --tags "boom bap,hip hop,male vocals,dusty,90 bpm" --duration 3 --out song.mp3 --lazy-load
```
**5 examples:**
```bash
# 1. 3-min instrumental in your trained sound (SA3 + your beat LoRA)
python scripts/sa3_workflow.py song --model medium --lora hiphop_v1.safetensors --prompt "boom bap instrumental, 90 BPM, F minor, dusty soul, vinyl crackle" --duration 180 --out song_boombap.wav
# 2. short 60s dark trap loopable bed
python scripts/sa3_workflow.py song --model medium --prompt "dark trap instrumental, 140 BPM, eerie keys, heavy 808" --duration 60 --out song_trap.wav
# 3. full song WITH rapped vocals from your lyrics (HeartMuLa)
python scripts/song_generate.py --heartlib /workspace/heartlib --ckpt /workspace/heartlib/ckpt --lyrics-file verse.txt --tags "boom bap,hip hop,male rap vocals,dusty,90 bpm" --duration 3 --out song_vocal.mp3 --lazy-load
# 4. sung hook, female vocal, soulful
python scripts/song_generate.py --heartlib /workspace/heartlib --ckpt /workspace/heartlib/ckpt --lyrics-file hook.txt --tags "soul,rnb,female vocals,smooth,warm" --duration 2 --out hook_sung.mp3 --lazy-load
# 5. the MIT engine instead (ACE-Step) — instrumental or vocal in one model
python scripts/ace_step_workflow.py song --prompt "drum and bass, rolling, male rap vocals, 174 BPM" --lyrics-file verse.txt --bpm 174 --key "G minor" --duration 180 --out song_dnb
```

*Optional/good-to-have:* HeartMuLa wants 16 GB+ (`--lazy-load` on a single GPU) → **cloud pod default**; lyric sections use `[Intro]/[Verse]/[Chorus]/[Bridge]/[Outro]`.

<a name="21-ace-studio"></a>
## 21. ACE Studio vocals

**What it is.** The highest-control vocal path — ACE Studio (you own it + ACE Bridge in Ableton) turns MIDI + lyrics into sung/rapped vocals. The toolkit prepares ACE's inputs: a **flow/melody MIDI aligned to your beat's key + BPM**, plus a syllable-segmented lyric file.

<p align="center"><img src="docs/gifs/ace.gif" width="80%"><br><sub><i>▶ Demo: beat + lyrics → flow MIDI → ACE raps it → ACE Bridge over the beat in Ableton.</i></sub></p>

```bash
python scripts/vocal_guide.py --beat MyBeat_instrumental.mp3 --lyrics verse.txt --style rap --out guide
# then: import guide.mid into ACE, paste guide_lyrics.txt onto the notes, pick a Rap voice, render.
```
`--style rap` = rhythmic monotone scaffold; `--style sung` = stepwise topline in the key's scale.

**5 examples:**
```bash
# 1. rap flow MIDI auto-keyed/timed from a beat (reads BPM/key from its Deep Listen sidecar)
python scripts/vocal_guide.py --beat "F:/RAP_ARCHIVES/raw_beats/MyBeat_instrumental.mp3" --lyrics verse.txt --style rap --out guide
# 2. explicit tempo/key when you have no sidecar
python scripts/vocal_guide.py --bpm 90 --key "F minor" --lyrics verse.txt --style rap --out guide
# 3. a sung topline (stepwise melody in the key's scale) for a hook
python scripts/vocal_guide.py --bpm 88 --key "A minor" --lyrics hook.txt --style sung --out hook_guide
# 4. double-time feel — lay 2 bars of lyric per bar of beat for fast flows
python scripts/vocal_guide.py --bpm 150 --key "C minor" --lyrics verse.txt --style rap --bars-per-line 2 --out guide_fast
# 5. feed a generated verse straight in (lyric model -> ACE)
python scripts/lyric_generate.py --model-dir lyric_model --mode verse --mood dark --out verses && python scripts/vocal_guide.py --bpm 90 --key "F minor" --lyrics verses/verse_dark_01.txt --style rap --out guide
```
Then in ACE Studio: import `guide.mid`, paste `guide_lyrics.txt` onto the notes, pick a Rap/sung voice, render; ACE Bridge plays it over the beat in Ableton.

*Optional/good-to-have:* feed lyrics from the lyric model (§22); ACE's own Vocal→MIDI can extract a melody from an existing vocal (a manual step in ACE).

<a name="22-lyric-model"></a>
## 22. Lyric model — write in your voice

**What it is.** Train on *your years of lyrics*, profile your style (flow density, rhyme rate, vocabulary, themes, mood), then generate new verses/hooks in your voice with a **local Ollama** model — fully private. Then seed a beat from any verse.

<p align="center"><img src="docs/gifs/lyrics.gif" width="80%"><br><sub><i>▶ Demo: your lyrics → style profile → a new verse in your voice → a matching beat brief.</i></sub></p>

```powershell
python scripts/lyric_analyze.py --input "F:/RAP_ARCHIVES/lyrics" --out lyric_model
# one-time: install Ollama (ollama.com), `ollama pull llama3.1:8b`, `pip install requests`
python scripts/lyric_generate.py --model-dir lyric_model --mode verse --mood dark --theme "grinding through the cold" --bars 16 --out verses
python scripts/lyric_to_beat.py --lyrics verses/verse_dark_01.txt --out beat_brief   # -> genre/BPM/key + commands
```
**5 examples:**
```bash
# 1. profile your style first (once)
python scripts/lyric_analyze.py --input "F:/RAP_ARCHIVES/lyrics" --out lyric_model
# 2. a dark 16-bar verse on a theme
python scripts/lyric_generate.py --model-dir lyric_model --mode verse --mood dark --theme "grinding through the cold" --bars 16 --out verses
# 3. a triumphant hook (shorter), two variations to pick from
python scripts/lyric_generate.py --model-dir lyric_model --mode hook --mood triumphant --bars 8 --variations 2 --out hooks
# 4. reflective verse with a snappier/lighter local model (faster on a small GPU)
python scripts/lyric_generate.py --model-dir lyric_model --mode verse --mood reflective --model llama3.2:3b --out verses
# 5. turn a generated verse into a matching beat brief (genre/BPM/key + commands)
python scripts/lyric_to_beat.py --lyrics verses/verse_dark_01.txt --out beat_brief
```

*Optional/good-to-have:* small corpora make models echo your phrasing — treat output as a **draft in your voice** and edit; `llama3.2:3b` is snappier on small GPUs, or run Ollama on a **cloud pod** for higher quality.

<a name="23-finish"></a>
## 23. Post-process, package, provenance

**What it is.** Turns raw generations into release-quality samples (reject duds, trim, anti-click fades, loudness-normalize, re-detect BPM/key, 24-bit), assembles a standard sellable pack (One Shots / Loops / Stems, producer-style names, README + license + zip), and writes a provenance certificate.

<p align="center"><img src="docs/gifs/finish.gif" width="80%"><br><sub><i>▶ Demo: generated/ → polished pack.zip + provenance certificate.</i></sub></p>

```bash
python scripts/postprocess.py --input generated --output processed --lufs -14
# ---- HUMAN QA: listen to everything in processed/, delete the weak ones ----
python scripts/build_pack.py --input processed --pack-name "Dusty Crates Vol 1" --out packs
python scripts/provenance.py --pack packs/DustyCratesVol1 --dataset dataset --generated generated --run-name beats-v1 --statement "All training audio owned/cleared."
```
**Human QA is non-negotiable for a paid product** — a 200-sample pack should come from 500+ generations. The model gets you 80% there; your ears do the rest.

*Optional/good-to-have:* `--license-file` for custom terms; rebuild the zip after adding the provenance cert; publish a public hash-verifier so buyers can confirm origin.

<a name="24-creative-techniques"></a>
## 24. Creative Techniques Lab

**What it is.** Techniques the AI-beat crowd isn't doing — built on the loops *between* the tools. Each one below has a one-line idea and **5 concrete ways to use it** with the toolkit. Most are GPU-backed → **cloud pod default**.

<p align="center"><img src="docs/gifs/creative.gif" width="80%"><br><sub><i>▶ Demo: micro-variants + groove transplant + destroy-and-heal.</i></sub></p>

> In the examples, **`<MODEL>`** = either your trained model (`--model-config model_config.json --ckpt hiphop_v1.ckpt`) or the base (`--pretrained stabilityai/stable-audio-open-1.0`).

<a name="ct-curation"></a>
### Taste distillation — `curation_loop.py`
CLAP-rank generations against a folder of your best sounds, keep the closest, retrain on the keepers. Your ear becomes the training signal.
1. Rank 500 generated kicks against your 30 favorites, keep the top 10%: `python scripts/curation_loop.py score --candidates generated/Kicks --reference my_best_kicks --keep-top 0.1 --keep-dir round2/kicks`
2. Keep an absolute best-50 melodic loops (a value ≥1 = a count, not a fraction): `python scripts/curation_loop.py score --candidates generated/MelodicLoops --reference my_best_loops --keep-top 50 --keep-dir round2/loops`
3. Turn the keepers into the next fine-tune dataset: `python scripts/curation_loop.py promote --keep-dir round2 --dataset-dir dataset_round2 --base-prompt "hip hop, dusty"`
4. Closed loop: retrain your LoRA on `dataset_round2`, regenerate, then `score` the new batch against the same reference — each round converges on your taste.
5. QC gate before shipping: `score` a finished pack's candidates against your whole catalog and only keep rows above a similarity you eyeball in the emitted `curation_scores.csv`.

<a name="ct-microvariants"></a>
### Micro-variants — `microvariants.py`
8 subtle takes of each one-shot via low-strength audio-to-audio; pair with `beat_builder --rotate` so no two hits are identical (like a real drummer).
1. 8 takes of every kick: `python scripts/microvariants.py <MODEL> --input organized/drums_oneshots/kicks --variants 8 --strength 0.15 --prompt "hip hop, kicks, one shot, punchy" --out variants/kicks`
2. Tighter snare variants (lower strength = closer to original): `... --input organized/drums_oneshots/snares --strength 0.12 --prompt "hip hop, snares, one shot, cracking" --out variants/snares`
3. Hat variants for rolling hi-hats: `... --input organized/drums_oneshots/hats --strength 0.18 --variants 6 --out variants/hats`
4. 808 variants: `... --input organized/drums_oneshots/808s --strength 0.15 --prompt "808 bass, one shot, sub" --out variants/808s`
5. Build with them so every hit differs: `python scripts/beat_builder.py --library variants --style boom_bap --rotate --bpm 90 --out beats_human`

<a name="ct-groove"></a>
### Groove DNA — `groove_dna.py`
Extract a break's micro-timing + accents into a template (numbers, not audio — no rights issue); apply to your samples via `beat_builder --groove`. "Quantize to Dilla."
1. Extract a swung break's pocket: `python scripts/groove_dna.py --input classic_break.wav --name dilla_a --out grooves`
2. Extract an amen's feel with the better tracker: `python scripts/groove_dna.py --input amen.wav --name amen_01 --engine beat_this --out grooves`
3. Capture your *own* signature pocket from a beat you made: `python scripts/groove_dna.py --input my_best_beat.wav --name my_pocket --out grooves`
4. Play your kit with that timing: `python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --groove grooves/dilla_a.groove.json --out beats_dilla`
5. Groove + variety together: `python scripts/beat_builder.py --library variants --style boom_bap --groove grooves/my_pocket.groove.json --rotate --out beats`

<a name="ct-lineage"></a>
### Flip lineage — `flip_lineage.py`
Chained audio-to-audio (telephone-game morph); every stage's prompt/strength/seed/hash is logged to `lineage.json`. The evolution itself is content.
1. Soul → dark → eerie on a loop: `python scripts/flip_lineage.py <MODEL> --input soul_loop.wav --out lineages/soul --stage "0.3:hip hop, soul keys, dusty" --stage "0.35:hip hop, dark strings, tape" --stage "0.4:hip hop, eerie synth, lofi"`
2. Morph a drum break across genres: `... --input break.wav --out lineages/break --stage "0.4:boom bap drums" --stage "0.5:drum and bass break" --stage "0.5:halftime dubstep drums"`
3. Gentle structure-preserving chain (low strengths): `... --stage "0.25:..." --stage "0.25:..." --stage "0.25:..."`
4. Wander far (high strengths) for happy accidents: `... --stage "0.6:..." --stage "0.6:..."`
5. Keep the `lineage.json` with the pack as a provenance/story artifact (pairs with `provenance.py`).

<a name="ct-destroyheal"></a>
### Destroy-and-heal — `destroy_heal.py`
Wreck audio through an extreme VST chain, then low-strength a2a heals it back toward musicality — the scars that survive are the texture. THE bass-music machine.
1. Dusty boom-bap heal: `python scripts/destroy_heal.py <MODEL> --input loops --chain configs/vst_chains/destroy_extreme.json --prompt "hip hop, dusty vinyl, warm analog" --heal-strength 0.25 --out healed`
2. Neuro bass texture: `... --prompt "drum and bass, neuro growl bass" --heal-strength 0.3 --out healed_neuro`
3. Vinyl-wrecked melodic loop: `... --input melodic_loops --prompt "lofi, vinyl crackle, warped tape" --out healed_lofi`
4. A/B the wreck vs the heal: add `--keep-destroyed` to save both stages side by side.
5. Dial the scar: `--heal-strength 0.15` keeps it gnarly, `0.4` leans on the model to smooth it.

<a name="ct-abmodels"></a>
### Two-producer packs — `ab_models.py`
Same seeds + same plan through two LoRAs; item N in A/ and B/ is the same idea in two sonic personalities.
1. 70s-soul vs Memphis-90s: `python scripts/ab_models.py --plan prompts/pack_plan.example.json --model-a-config cfgA.json --model-a-ckpt soul70s.ckpt --model-b-config cfgB.json --model-b-ckpt memphis90.ckpt --out ab_packs --base-seed 1234`
2. Your model vs the base (how much your LoRA changed it): `... --model-a-config model_config.json --model-a-ckpt hiphop_v1.ckpt --model-b-pretrained stabilityai/stable-audio-open-1.0`
3. Two subgenre LoRAs (boom-bap vs trap) on one plan to compare flips.
4. Reproducible matched pairs: keep `--base-seed` fixed so A and B share seeds.
5. Ship as paired "interpretations" — a Vol-A / Vol-B release from one creative idea.

<a name="ct-push"></a>
### Push as an instrument — `push_generation_server.py`
An OSC server holds your model in memory; map Push pads/knobs (via Live's free Connection Kit OSC Send) to fire generation jobs — generation becomes performance.
1. Launch with presets: `python scripts/push_generation_server.py <MODEL> --presets prompts/push_presets.example.json --out "C:/Ableton/GenSamples"`
2. Map a Push pad → OSC `/gen/preset 3` then `/gen/fire` so one pad spits a kick.
3. Map a knob → `/gen/strength` to morph between re-texture and full flip live.
4. Set `/gen/source <wav>` then fire to get audio-to-audio variations of a loaded loop.
5. Point `--out` at a folder in Live's browser so fired samples land on Push instantly.

<a name="ct-callresponse"></a>
### AI session musician — `call_response.py`
Watches a folder; every clip you export from Live gets answered with N variations in a response folder. Trade bars with a model trained on your catalog.
1. Trade melodic phrases: `python scripts/call_response.py <MODEL> --watch "C:/Ableton/Call" --respond "C:/Ableton/Response" --prompt "hip hop, soul keys response" --strength 0.45 --variations 2`
2. Drum call/response: `... --prompt "boom bap drum fill, dusty" --strength 0.5`
3. More takes per call: `... --variations 4`
4. Tighter answers that stay close to your phrase: `... --strength 0.35`
5. Wire it to Live: export a clip (right-click → Export Audio) into the `--watch` folder; the answer appears in `--respond` to drop on the next scene.

<a name="ct-ecosystem"></a>
### Ecosystem packs — `ecosystem_pack.py`
Lock a whole pack series to one key + BPM so every volume inter-combines; `verify` quarantines mismatches. Modular packs a loose catalog can't promise.
1. Lock a plan to F minor / 90: `python scripts/ecosystem_pack.py plan --base prompts/pack_plan.example.json --key "F minor" --bpm 90 --name "Crate Ecosystem Vol 2" --out prompts/eco_fmin_90_v2.json`
2. Lock a DnB series at 174: `python scripts/ecosystem_pack.py plan --base prompts/pack_plan.dubstep_dnb.json --key "G minor" --bpm 174 --name "Rollers Vol 1" --out prompts/eco_dnb.json`
3. Verify a finished folder matches the lock: `python scripts/ecosystem_pack.py verify --dir processed --key "F minor" --bpm 90`
4. Dry-run the check first (flag, don't move): `python scripts/ecosystem_pack.py verify --dir processed --key "F minor" --bpm 90 --report-only`
5. Build a multi-volume series: lock Vol 1–4 to the same key/BPM so every melodic loop in Vol 3 plays over every drum loop in Vol 1.

<a name="25-genre-expansion"></a>
## 25. Genre expansion: rock/metal & dubstep/DnB

**What it is.** The same pipeline runs three product lines. What changes per genre: library labels, BPM conventions, and pattern grammars.

<p align="center"><img src="docs/gifs/genres.gif" width="80%"><br><sub><i>▶ Demo: same engine, metal double-kick and a 174 DnB break.</i></sub></p>

- **Beat-builder styles:** `rock` `metal` `dbeat` `dubstep` `dnb` `amen` (plus the hip-hop set).
- **BPM ranges:** pass `--bpm-min/--bpm-max` on prep/post — DnB 100–200 (never fold 174→87), metal up to 220.
- **Pack plans:** `prompts/pack_plan.rock_metal.json`, `prompts/pack_plan.dubstep_dnb.json`.
- **Strategy:** one **LoRA per genre** (don't mix); stack them for hybrids (trap-metal, drumstep). Tuning-locked metal series and exact-174 DnB packs are ecosystem products nobody ships.
- **Library vocab:** label palm-muted chugs/drop-tuning/blast-beats (metal); reese/wobble/neuro/amen/two-step (bass music).

QA ears differ: metal → flabby chugs, fake cymbal decay; bass music → check sub weight (30–60 Hz), LFO-locked wobbles. Plan 3–4× overgeneration for bass music.

**5 examples (one per new style):**
```bash
# 1. rock — straight-8ths backbeat at 120
python scripts/beat_builder.py --library "F:/SoundBankAI" --style rock --bpm 120 --bars 4 --count 6 --out beats_rock
# 2. metal — double-kick under a halftime backbeat at 168
python scripts/beat_builder.py --library "F:/SoundBankAI" --style metal --bpm 168 --bars 4 --count 6 --out beats_metal
# 3. d-beat / punk drive at 180
python scripts/beat_builder.py --library "F:/SoundBankAI" --style dbeat --bpm 180 --bars 4 --count 4 --out beats_dbeat
# 4. dubstep — 140 halftime, 808 lane as bass stabs
python scripts/beat_builder.py --library "F:/SoundBankAI" --style dubstep --bpm 140 --bars 4 --count 6 --out beats_dubstep
# 5. DnB two-step / amen at 174 (prepare data with --bpm-min 100 --bpm-max 200 so 174 isn't folded to 87)
python scripts/beat_builder.py --library "F:/SoundBankAI" --style dnb --bpm 174 --bars 4 --count 6 --out beats_dnb
```
Then build genre packs from the matching plans: `prompts/pack_plan.rock_metal.json` and `prompts/pack_plan.dubstep_dnb.json` (feed them to `sa3_workflow.py plan` / `ace_step_workflow.py generate`).

<a name="26-dashboard"></a>
## 26. Dashboard (web UI)

**What it is.** A local Gradio control panel for the whole suite — a tab per stage grouped into sections (Prep & Analyze · Train & Generate · Beats & Sound · Remix · Lyrics · Finish · Plugins), each with live streaming logs, plus an Audition tab with playback and a remix-the-selected-file panel. Bears-themed (navy/orange).

<p align="center"><img src="docs/gifs/dashboard.gif" width="85%"><br><sub><i>▶ Demo: clicking through sections, running a job, auditioning the result.</i></sub></p>

```powershell
pip install gradio
python dashboard.py     # or run_dashboard.bat
```
GPU steps run wherever you launch it — locally, or **run the dashboard on a cloud pod** and open its forwarded port to drive the rented GPU from the same UI. (Behind a VPN/proxy it auto-falls back to a share link.)

*Optional/good-to-have:* point Settings at your Python/scripts; on a pod, expose port 7860.

---

<a name="27-specs--costs"></a>
## 27. Training specs & costs

Cost is **GPU-hours, not per-file.** Indicative (June 2026 rates; verify current):

| Path | Min VRAM | Suggested | Steps | Cost/run |
|---|---|---|---|---|
| SA3 LoRA | 16 GB | RTX 4090 (~$0.34/hr) | ~1–3k | **~$0.50–2** |
| SAO full | 24 GB | A100 (~$1.39/hr) | 5–20k | **~$8–40** |
| Generation | 8 GB | RTX 4090 / A5000 | — | pennies/pack |

**Dataset sizing:** <50 risks overfit; **500–1,500 curated = sweet spot**; 3k+ only if uniformly on-aesthetic (messy 3k trains *worse* than clean 800). Whole launch to a sellable model is typically **under $20** of GPU. The expensive resource is your curation/QA time, not the GPU.

<a name="28-lossless"></a>
## 28. Sourcing lossless audio

You can't un-compress a lossy file — converting MP3→WAV adds nothing. Get true source from: **ripping your own CDs** (EAC/dBpoweramp), **buying WAV/FLAC** (Bandcamp, Beatport, Qobuz), **recording vinyl**, or **cleared-sample services** (Tracklib, Splice). Streaming "lossless" tiers are fine to *listen* to, not to rip for training. Verify with `deep_listen.py` (`rolloff95_hz` + lossy-upsample flag) or Spek. For a pristine commercial model, a **smaller true-WAV core (300–500) beats 1,500 lossy** — source quality > count, and it's the cleaner legal footing.

<a name="29-ytdlp"></a>
## 29. yt-dlp commands

Reference/listening only (lossy source; rights caveats apply — don't train a sellable model on these):
```powershell
# playlist -> WAV, resumable; --download-archive skips finished
.\yt-dlp.exe --playlist-start 1 -x --audio-format wav --download-archive done.txt -o "%(playlist_index)s - %(title)s.%(ext)s" "PLAYLIST_URL"
```
`-P "F:\Downloads"` to target a drive; `.\yt-dlp.exe -U` to update.

<a name="30-business"></a>
## 30. Business & learning path

**Packaging as a service:** the toolkit is ~80% of a SaaS backend (add a job queue + API + Stripe). Differentiators vs Splice/Waves ILLUGEN/Loudly: hip-hop depth, **private models trained on a customer's own sounds**, **provenance certificates**, and groove-level control.
**Products:** (1) provenance-verified ecosystem pack line; (2) "your sound as a model" private fine-tunes (SA3 LoRA collapses the unit cost); (3) groove-DNA template packs.
**Learning path (O'Reilly):** Géron *Hands-On ML* → *Programming PyTorch* (audio ch.) → Foster *Generative Deep Learning* → HF *Hands-On Generative AI* → *Think DSP*. Free: HF Audio Course, "The Sound of AI." Study repos: stable-audio-tools, stable-audio-3, audiocraft, demucs, pedalboard, librosa, CLAP, AbletonOSC.
*(Not financial/legal advice — verify license thresholds and trademarks before commercializing.)*

<a name="31-scripts"></a>
## 31. Full script reference

| Script | Does |
|---|---|
| `organize_soundbank.py` | classify/sort a messy library into tag folders |
| `remove_vocals.py` | batch vocal removal (BS-RoFormer/Demucs) |
| `deep_listen.py` | full technical/musical/sound-event/vibe analysis |
| `auto_tag.py` | open-vocab mood/vibe tags (audio LLM / CLAP) |
| `genius_lookup.py` | producer/album/year metadata from filenames |
| `build_captions.py` | fuse analysis+tags+genius → canonical caption |
| `prepare_dataset.py` / `validate_dataset.py` | dataset prep + preflight checks |
| `sa3_workflow.py` | SA3 prepare/plan/flip/fill/extend/song (LoRA) |
| `generate.py` | SAO batch generation from a pack plan |
| `audio2audio.py` | flip a sound (a2a) |
| `remix.py` | genre transform / mashup |
| `beat_builder.py` | beats from your samples + MIDI |
| `vst_instrument.py` / `vst_chain.py` | render MIDI through synths / process through effects |
| `plugin_scan.py` | catalog installed VST3/VST2 |
| `vocal_guide.py` | beat-aligned flow MIDI + lyrics for ACE Studio |
| `song_generate.py` | full songs w/ vocals (HeartMuLa) |
| `lyric_analyze.py` / `lyric_generate.py` / `lyric_to_beat.py` | your-voice lyric model + beat bridge |
| `postprocess.py` / `build_pack.py` / `provenance.py` | finish, package, certify |
| `microvariants.py` `groove_dna.py` `flip_lineage.py` `destroy_heal.py` `ab_models.py` `curation_loop.py` `push_generation_server.py` `call_response.py` `ecosystem_pack.py` | Creative Techniques Lab (§24) |
| `sat_common.py` `lyric_common.py` `custom_metadata.py` | shared helpers |

`requirements.txt` lists core + per-feature optional deps. `cloud/` has pod setup scripts; `configs/` has dataset/VST-chain configs; `prompts/` has pack plans + example lyrics.

<a name="32-engines"></a>
## 32. Engine choice: Stable Audio 3 vs ACE-Step 1.5

**What it is.** Two interchangeable, first-class generation engines ship in this toolkit. You can A/B them and pick per project — same dataset, same captions, different sound and licensing.

<p align="center"><img src="docs/gifs/engines.gif" width="80%"><br><sub><i>▶ Demo: the same pack plan generated by SA3 and by ACE-Step, side by side.</i></sub></p>

**At a glance:**

| | Stable Audio 3 (`sa3_workflow.py`) | ACE-Step 1.5 (`ace_step_workflow.py`) |
|---|---|---|
| License | Stability Community (free commercial **< $1M/yr**) | **MIT** — commercial, **no revenue cap** |
| Does | instrumentals, inpaint/extend, LoRA | instrumentals **and full songs with vocals**, cover/repaint, LoRA |
| Min VRAM | ~16 GB (LoRA) | ~6 GB (2B turbo) … 20 GB+ (XL) |
| Runs as | Python repo (uv) | **REST server** you call over HTTP |
| Train | `train_lora.py` (~1k steps) | one-click Gradio LoRA (~8 songs, ~1 h on 12 GB) |
| Best for | tight, owned instrumental sound | commercial work + vocal songs in one model |

**Setup — ACE-Step (cloud pod default; runs locally too):**
```bash
bash cloud/ace_step_setup.sh                 # clone ACE-Step-1.5 + uv sync (models auto-download)
cd ACE-Step-1.5 && ACESTEP_API_HOST=0.0.0.0 uv run acestep-api    # REST API on :8001
# (or `uv run acestep` for the Gradio UI, which has the one-click LoRA-training tab)
```
The toolkit talks to that server over HTTP, so **start it first** — `ace_step_workflow.py` errors with "is the server running?" if it's down.

**Examples & how to use them:**
```bash
# list the DiT models the server has loaded
python scripts/ace_step_workflow.py models

# batch instrumentals from a pack plan (same plan files SA3 uses) -> generated_ace/<category>/
python scripts/ace_step_workflow.py generate --plan prompts/pack_plan.example.json --out generated_ace

# a full SONG with vocals from your lyrics + style tags (this is what SA3 can't do)
python scripts/ace_step_workflow.py song --prompt "boom bap, dusty, male rap vocals, 90 BPM"     --lyrics-file verse.txt --bpm 90 --key "F minor" --duration 180 --out song

# COVER / restyle an existing track (lower strength = subtler)
python scripts/ace_step_workflow.py cover --src mybeat.wav --prompt "drum and bass, reese bass" --strength 0.5 --out remix
```
What the examples do: `generate` reuses your existing `prompts/pack_plan.*.json` files (counts/durations/prompts) and writes WAVs per category; `song` is the headline feature — type tags + paste lyrics (use a `lyric_generate.py` verse) and it sings/raps a full track; `cover` reimagines a finished beat in a new genre (great paired with your `remix` workflow). Add `--model <name>` (see `models`) to pick a specific checkpoint, `--format mp3` to change output.

**When to use which.** Reach for **ACE-Step** when you want vocal songs, a clean MIT license for paid work, or low-VRAM/local generation. Stay on **Stable Audio 3** when you've invested in an SA3 LoRA you like, or want its inpaint/extend editing. Output the same pack plan through both, listen, keep the winner.

**LoRA-train your sound on ACE-Step:** the Gradio "LoRA Training" tab does it one-click (~8 songs, ~1 h on a 12 GB GPU); your `build_captions.py` captions feed the annotation step. CLI/REST training: `ace_step_workflow.py train` prints the steps.

*Optional / good-to-have:* run the ACE-Step server **on a cloud pod** and point `--host http://<pod>:8001`; set `ACESTEP_API_KEY` for a shared server; pick the model tier to your GPU (2B turbo for ≤8 GB, XL for 20 GB+); route HF cache to a persistent drive.

---

<a name="33-license"></a>
## 33. License & notice

Fine-tunes/runs Stability AI models (Stable Audio Open 1.0 / Stable Audio 3) under the **Stability AI Community License** (free commercial use under US$1M annual revenue; enterprise above — https://stability.ai/license). Full songs with vocals use **HeartMuLa** (Apache-2.0). Model weights are **not** included. **Only train on audio you own or that is explicitly cleared for ML training.** See §6.
