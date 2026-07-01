<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <img alt="Co-Produce AI" src="assets/logo-dark.svg" width="360">
  </picture>
</p>
<p align="center"><b>Turn your beats, lyrics, and samples into a co-producer that sounds like you.</b><br>
An end-to-end studio that learns <i>your</i> beats, lyrics, and library — then organizes, analyzes, generates, remixes, and packages hip-hop, rock/metal, dubstep, and DnB from raw crate to finished, rights-traced product.</p>
<p align="center"><a href="https://github.com/pjcampbe11/Co-Produce-AI/actions/workflows/ci.yml"><img src="https://github.com/pjcampbe11/Co-Produce-AI/actions/workflows/ci.yml/badge.svg" alt="CI"></a></p>

**▶ Demo — organize → tag → train → generate, end to end**
```console
$ python scripts/organize_soundbank.py --input "F:/Sound Bank" --output "F:/Organized" --resume
Found 14990 audio files.  kicks 1038 · snares 1780 · melodic_loops 4173 ...
$ python scripts/sa3_workflow.py plan --model medium-base --lora hiphop_v1.safetensors --plan prompts/pack_plan.example.json --out generated
[Kicks] 30/30  [Snares] 30/30  [MelodicLoops] 25/25 ...  done -> generated/
$ python scripts/build_pack.py --input processed --pack-name "Dusty Crates Vol 1" --out packs
Pack built: packs/DustyCratesVol1  (212 samples)   Zip: packs/DustyCratesVol1.zip
```

> **Engine note:** recommended generation engine is **Stable Audio 3** (LoRA fine-tuning), with **Stable Audio Open 1.0** as the full-fine-tune alternative — open-weight Stability AI models (Community License). Full songs with vocals use **HeartMuLa** (Apache-2.0). Lyric writing runs on a **local Ollama** model. Vocal synthesis bridges to **ACE Studio**. Everything model/GPU-heavy defaults to a **cloud GPU pod**.

---

## 📖 Table of Contents

### Getting started

1. [What is Co-Produce AI?](#1-what-is-co-produce-ai)
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
33. [Serverless API (RunPod) — host the toolkit as an endpoint](#33-serverless)
34. [Pod workflow — SSH, SCP & cloning the repo to a pod](#34-pod-workflow)
35. [SaaS server — job queue, REST API & Stripe billing](#35-saas)
36. [Requirements & dependencies (with venv setup)](#36-requirements)
37. [Spotify playlist metadata extractor](#37-playlist-meta)
38. [Hip-hop beats inspired by (playlist)](#38-inspired)
39. [Cheat sheets & genre playlist finder](#39-cheatsheets)
40. [Engines & unified generation router](#40-engines-router)
41. [Sample chopper (MPC One+ / Ableton Push)](#41-sample-chop)
42. [License & notice](#42-license)

> **How to read this:** every feature section follows the same shape — a plain-English **What it is**, a **Demo** gif, the **Setup & run** steps, and **Optional / good-to-have** extras. Demos live in `docs/gifs/` (placeholders — record them from the dashboard). Anything needing a GPU shows the **cloud pod** path first.

---

<a name="1-what-is-co-produce-ai"></a>
## 1. What is Co-Produce AI?

**What it is.** A complete, self-hosted music-production AI suite built around one idea: *your* catalog is the moat. Instead of a generic model, you fine-tune on your own sounds and lyrics so the output sounds like **you**. It spans the whole journey — cleaning and labeling a messy sample library, analyzing and tagging every file, fine-tuning open audio models, generating one-shots/loops/beats/full songs, remixing across genres, writing lyrics in your voice, rendering through your real VST plugins, and shipping provenance-verified sample packs.

**Who it's for.** Producers and small AI-audio services who want owned, rights-clean, genre-deep output — not the homogenized sound of shared models.

**▶ Demo — a folder of beats becomes a trained model and a finished pack**
```console
$ python scripts/prepare_dataset.py --input raw_beats --output dataset --name-contains _instrumental
Done. 1500 source files processed.  Log: dataset/prepare_log.txt
$ python scripts/validate_dataset.py --dataset dataset
Files: 3120   Total audio: 9.7 h   Dataset is ready for training.
$ # ... train on a pod ... then:
$ python scripts/build_pack.py --input processed --pack-name "Vol 1" --out packs
Pack built: packs/Vol1  (200 samples)
```

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
git clone https://github.com/pjcampbe11/Co-Produce-AI.git
cd Co-Produce-AI
pip install -r requirements.txt
python dashboard.py          # web UI for everything, or use the CLIs below
```

Fastest path to a result (no training needed): point `beat_builder.py` at an organized sample folder →
```powershell
python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --bars 4 --count 4 --out beats
```

<a name="4-install--setup"></a>
## 4. Install & setup

**Local (CPU-light steps):** **Python 3.11 required** — 3.9 is no longer supported (`thinc`/`spaCy` and parts of the audio stack dropped it). **Make a virtual environment first** so the toolkit's packages stay isolated from system Python:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Optional features pull extra packages — each section lists them, and §42 breaks down every line of `requirements.txt` (what it is and which feature needs it).

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

**▶ Demo — spin up a pod, run a step, pull results**
```console
# on the pod (RTX 4090, /workspace volume):
$ bash /workspace/toolkit/cloud/sa3_setup.sh
Ready. Train a LoRA with:  uv run python scripts/train_lora.py --model medium-base ...
$ runpodctl send /workspace/lora_beats/lora_step2500.safetensors
Code is: 8338-galileo-...   # receive on your PC with: runpodctl receive <code>
```

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

**▶ Demo — a chaotic folder → clean tag-folders + review.csv**
```console
$ python scripts/organize_soundbank.py --input "F:/Sound Bank" --output "F:/Organized" --dry-run
Classifying: 100%|██████████████████| 14990/14990 [04:12<00:00, 59it/s]
=== DRY RUN - nothing moved ===
  drums_oneshots/kicks            1038
  drums_oneshots/snares           1780
  drums_loops                     2604
  melodic_loops                   4173
  _review                          312
Full report: F:/Organized/review.csv
```

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

**▶ Demo — a folder of songs → *_instrumental files (GPU)**
```console
$ python scripts/remove_vocals.py --input mp3 --output raw_beats --mp3 --keep-vocals --require-gpu --mirror
Acceleration: GPU  [torch CUDA: NVIDIA GeForce RTX 4090 | onnxruntime: CUDA]
2982 file(s) found, 2982 to process.
[1/2982] Kendrick Lamar - Backseat Freestyle.mp3   (15.2s)
[2/2982] ...
=== 2982 instrumentals written to raw_beats/ ===
```

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

**▶ Demo — drop a track → full technical + musical + vibe report**
```console
$ python scripts/deep_listen.py --input track.mp3 --out reports/
track.mp3: 92.0 BPM; key F minor (conf 0.71); -9.8 LUFS; feels dark, nostalgic;
           reads as boom bap hip hop; contains kick drum, hi-hat, piano, vinyl crackle
Wrote reports/track.analysis.json + reports/track.analysis.md
```

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

**▶ Demo — a beat → free-form mood/vibe tags written to a sidecar**
```console
$ python scripts/auto_tag.py --stems-dir raw_beats --source beat --engine qwen3-omni --limit 3
Engine: qwen3-omni   Source: beat
[1/3] 002 - Baby Keem: dark, dusty, trap, 808 bass, aggressive, vinyl texture
[2/3] 003 - Young Dolph: soulful, mellow, boom bap, warm keys
=== 3 tagged, 0 skipped, 0 failed ===
```

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

**▶ Demo — filenames → producer/era metadata sidecars**
```console
$ python scripts/genius_lookup.py --beats raw_beats --limit 3
[1/3] Young Dolph - Money Callin  ->  Young Dolph - Money Callin
[2/3] Lil Wayne - Swag Surf  ->  Lil Wayne - Swag Surf  (LOW CONF)
=== 2 matched, 0 no-match, 0 skipped, 1 flagged low-confidence ===
```

**Setup & run** (local; needs a free Genius token). Get the token:

1. Go to <https://genius.com/api-clients> and log in (any Genius/Google account).
2. Click **New API Client**. Enter any **App Name** and **App Website URL** (e.g. `https://coproduceai.com`) → **Save**.
3. On the client page, click **Generate Access Token** and copy the **Client Access Token**.

Then set it and run (key stays in your shell, never in the repo):

```powershell
$env:GENIUS_TOKEN = "paste_client_access_token"
pip install requests
python scripts/genius_lookup.py --beats "F:/RAP_ARCHIVES/raw_beats" --resume
```
macOS/Linux: `export GENIUS_TOKEN=...`. Persist on Windows with `setx GENIUS_TOKEN "..."` (new terminal). Full per-service steps: [`cheatsheets/api-keys.md`](cheatsheets/api-keys.md).
Cleans track numbers/`_instrumental`/"(OFFICIAL VIDEO)" noise from filenames, takes the best hit, records a `match_score` + `low_confidence` flag so you can spot-check.

*Optional/good-to-have:* `--limit 25` test first; the token stays in an env var (never hard-coded); low-confidence matches are flagged, not trusted blindly.

<a name="12-build-captions"></a>
## 12. Build captions — fuse it all

**What it is.** Composes ONE canonical training caption per beat in a consistent field order — fusing Deep Listen analysis + your auto-tags + Genius producer/era — so your model learns audio *and* production lineage. Leads with a subgenre only when the analysis is confident, else plain `hip hop`.

**▶ Demo — three sidecars → one canonical training caption**
```console
$ python scripts/build_captions.py --beats raw_beats
002 - Baby Keem_instrumental.mp3: trap, hi-hat, 808 bass, dark, modern polished
   production, 140 BPM, key of F minor, loop, prod Speaker Knockerz, 2010s
=== 1500 captions written, 0 skipped, 12 had no report ===
```

**Setup & run** (local):
```powershell
python scripts/build_captions.py --beats "F:/RAP_ARCHIVES/raw_beats"
```
Writes `<beat>.caption.txt` next to each file; `prepare_dataset.py` uses it verbatim as the training prompt.

*Optional/good-to-have:* `--genre-threshold` tunes how confident a subgenre must be to lead; `--no-genius` to ignore Genius data; `--dry-run` to preview captions before writing.

<a name="13-prepare--validate"></a>
## 13. Prepare & validate the dataset

**What it is.** Converts your library to 44.1 kHz stereo, slices long files under the model window, auto-detects BPM/key, writes per-file prompt sidecars, then validates the set before you spend a cent on GPU.

**▶ Demo — raw beats → clean dataset/ + 'ready for training'**
```console
$ python scripts/prepare_dataset.py --input raw_beats --output dataset --name-contains _instrumental
Preparing: 100%|██████████| 1500/1500   Done. 1500 source files processed.
$ python scripts/validate_dataset.py --dataset dataset
Files: 3120   Total audio: 9.7 h   Kinds: {'loop': 3120}
Errors: 0   ===  Dataset is ready for training. ===
```

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

**▶ Demo — dataset → LoRA, demo audio improving over steps (on a pod)**
```console
$ uv run python scripts/train_lora.py --model medium-base --data_dir sa3_beats --rank 16 --steps 2500 --save_dir lora_beats
step  500/2500 | loss 0.182 | demo audio -> lora_beats/demos/step500.wav
step 1500/2500 | loss 0.121 | demo audio -> lora_beats/demos/step1500.wav
step 2500/2500 | loss 0.098 | saved lora_beats/lora_step2500.safetensors
```

**Mental model:** cost is **GPU-hours, not per-file** — the loader samples random crops across thousands of steps. A 500-file and a 3,000-file run cost ~the same. You don't pick "sets at once"; you set batch size + steps. **Sweet-spot dataset: 500–1,500 well-labeled, on-aesthetic files** — curation beats raw count.

**Setup & run — SA3 LoRA (cloud pod, 16 GB+):**
```bash
# on the pod (after cloud/sa3_setup.sh)
python /workspace/toolkit/scripts/sa3_workflow.py prepare --dataset /workspace/dataset_beats --data-dir /workspace/sa3_beats
cd /workspace/stable-audio-3 && uv run python scripts/train_lora.py --model medium-base \
  --data_dir /workspace/sa3_beats --rank 16 --adapter_type dora-rows --steps 2500 --exclude seconds_total --save_dir /workspace/lora_beats
runpodctl send /workspace/lora_beats/lora_step2500.safetensors   # receive on your PC
```
Watch the trainer's demo audio; **stop when it sounds like your aesthetic but not like specific files** (overfitting). ~2000–3000 steps is a good range for this size.

**Alternative engine — ACE-Step 1.5 (MIT, no revenue cap):** a second first-class engine (one model for beats *and* vocal songs, no $1M cap). Full setup, examples, and an A/B comparison are in [§32 Engine choice](#32-engines).

**SAO full fine-tune (24 GB+ pod):** `cloud/runpod_setup.sh` then `train.py` (see flags inline). Use when LoRA stops capturing your sound.

*Optional/good-to-have:* one **LoRA per subgenre** (swap/blend at runtime); `--base_precision bf16 --adapter_type lora-xs` for ~5.5 GB VRAM; resume from a checkpoint to continue-train; keep several checkpoints (last isn't always best).

<a name="15-generate"></a>
## 15. Generate samples & packs

**What it is.** Batch-generates audio from a pack plan (counts, durations, prompts) using your fine-tuned model. Over-generate 2–3× and curate hard.

**▶ Demo — a pack plan → folders of kicks/snares/loops**
```console
$ python scripts/sa3_workflow.py plan --model medium-base --lora hiphop_v1.safetensors --plan prompts/pack_plan.example.json --out generated
[Kicks] 1/30 ... 30/30        [Snares] 1/30 ... 30/30
[Hats] 25/25  [DrumLoops] 25/25  [MelodicLoops] 25/25  [Stems] 10/10
Done -> generated/   (run postprocess.py next)
```

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

**▶ Demo — a break → four flipped variations**
```console
$ python scripts/audio2audio.py --ckpt hiphop_v1.ckpt --input break.wav \
    --prompt "boom bap, 90 BPM, dusty drum break" --strength 0.5 --variations 4 --out flipped
1/4 -> break_var01_s0.50_seed1837.wav
2/4 -> break_var02_s0.50_seed40912.wav
3/4 -> ...   Done. Variations in flipped/
```

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

**▶ Demo — one beat → a DnB remix and a trap mashup**
```console
$ python scripts/remix.py --pretrained stabilityai/stable-audio-open-1.0 --input song.wav --genre dnb --mode full --variations 3 --out remixes
Remix [full] -> dnb (strength 0.6)
  1/3 -> song_dnb_full_v01_seed771.wav
  2/3 -> song_dnb_full_v02_seed22310.wav
Done -> remixes/  (run postprocess.py on keepers)
```

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

**▶ Demo — a sample folder → a finished beat + MIDI**
```console
$ python scripts/beat_builder.py --library "F:/SoundBankAI" --style boom_bap --bpm 90 --bars 4 --count 1 --melodic "F:/SoundBankAI/melodic_loops" --out beats
Built beats/boom_bap_90bpm_01
  master.wav (11.7s), stem_kick/snare/hat/perc/melodic.wav, pattern.mid, manifest.json
  kick -> Kick (Cole).wav  snare -> Tappy Rim.wav  melodic -> OS_VC_90_..._Cm.wav
```

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

**▶ Demo — pattern.mid → Battery render → dusty effect chain**
```console
$ python scripts/vst_instrument.py --vst3 ".../Battery 4.vst3" --midi beats/.../pattern.mid \
    --chain configs/vst_chains/dusty_boombap.json --out kit_dusty.wav
Rendering 46 MIDI events -> 11.7s @ 44100 Hz
Applying 5-stage effect chain from configs/vst_chains/dusty_boombap.json
Wrote kit_dusty.wav
```

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

**▶ Demo — a prompt → a 3-min instrumental; lyrics → a sung/rapped song**
```console
$ python scripts/sa3_workflow.py song --model medium --lora hiphop_v1.safetensors \
    --prompt "boom bap instrumental, 90 BPM, F minor, vinyl" --duration 180 --out song.wav
Song (180s) -> song.wav
$ python scripts/song_generate.py --heartlib ./heartlib --ckpt ./heartlib/ckpt \
    --lyrics-file verse.txt --tags "boom bap,male rap vocals,dusty,90 bpm" --duration 3 --out song.mp3
Song -> song.mp3
```

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

**▶ Demo — beat + lyrics → flow MIDI for ACE Studio**
```console
$ python scripts/vocal_guide.py --beat MyBeat_instrumental.mp3 --lyrics verse.txt --style rap --out guide
Wrote guide.mid  (90 BPM, key F minor, style rap)
Wrote guide_lyrics.txt  (16 lines)
In ACE Studio: import guide.mid -> paste lyrics -> pick a Rap voice -> render.
```

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

**▶ Demo — your lyrics → style profile → a new verse in your voice**
```console
$ python scripts/lyric_analyze.py --input "F:/RAP_ARCHIVES/lyrics" --out lyric_model
STYLE SUMMARY: dense flow (~12.4 syl/line), heavy end-rhyme (0.58); dark, reflective ...
$ python scripts/lyric_generate.py --model-dir lyric_model --mode verse --mood dark --bars 16 --out verses
===== verse_dark_01.txt =====
[Verse]
Cold mornings, empty pockets, chasing shadows down the road ...
```

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

**▶ Demo — generated/ → polished pack.zip + provenance certificate**
```console
$ python scripts/postprocess.py --input generated --output processed --lufs -14
Done. Kept 487, auto-rejected 13. Output: processed/
$ python scripts/build_pack.py --input processed --pack-name "Dusty Crates Vol 1" --out packs
Pack built: packs/DustyCratesVol1  (200 samples)   Zip: packs/DustyCratesVol1.zip
$ python scripts/provenance.py --pack packs/DustyCratesVol1 --dataset dataset --run-name beats-v1
Wrote PROVENANCE.json and PROVENANCE_CERTIFICATE.txt
```

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

**▶ Demo — micro-variants + groove transplant + destroy-and-heal**
```console
$ python scripts/microvariants.py --ckpt hiphop_v1.ckpt --input organized/drums_oneshots/kicks --variants 8 --strength 0.15 --prompt "kicks, one shot" --out variants/kicks
Kick (Cole).wav: 8 variants -> variants/kicks/Kick (Cole)/
$ python scripts/groove_dna.py --input classic_break.wav --name dilla_a --out grooves
Groove DNA -> grooves/dilla_a.groove.json  (source 89.1 BPM, 23 onsets)
$ python scripts/destroy_heal.py --ckpt hiphop_v1.ckpt --input loops --chain configs/vst_chains/destroy_extreme.json --prompt "dusty vinyl" --heal-strength 0.25 --out healed
healed: loop1.wav (seed 4471)
```

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
Extract a break's micro-timing + accents into a template (numbers, not audio — no rights issue); apply to your samples via `beat_builder --groove`. "Quantize to **********."
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

> **Run-time notes for these tools.** Most Creative-Lab scripts (and dashboard tabs) are **one-and-done** — they run, write output, and exit. Three behave differently: `push_generation_server.py` (a generation **server**) and `call_response.py` (a folder **watcher**) are **long-running** — they stay up and keep streaming logs until you stop them (Ctrl-C on the CLI, or stop the job in the dashboard), so don't wait for an "exit code" line. And `ableton_bridge.py` needs **Ableton Live already open** with its OSC / Remote-Script listener active on the configured host/port (default `127.0.0.1:11000`); with Live closed it can't connect.

<a name="25-genre-expansion"></a>
## 25. Genre expansion: rock/metal & dubstep/DnB

**What it is.** The same pipeline runs three product lines. What changes per genre: library labels, BPM conventions, and pattern grammars.

**▶ Demo — same engine, metal double-kick and a 174 DnB break**
```console
$ python scripts/beat_builder.py --library "F:/SoundBankAI" --style metal --bpm 168 --count 1 --out beats_metal
Built beats_metal/metal_168bpm_01   (46 MIDI notes — dense double-kick)
$ python scripts/beat_builder.py --library "F:/SoundBankAI" --style dnb --bpm 174 --count 1 --out beats_dnb
Built beats_dnb/dnb_174bpm_01   (two-step break)
```

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

**What it is.** A local Gradio control panel for the whole suite — a tab per stage grouped into sections (Prep & Analyze · Train & Generate · Beats & Sound · Remix · Lyrics · Finish · Plugins), each with live streaming logs, plus an Audition tab with playback and a remix-the-selected-file panel, a **🧪 Creative Lab** tab (micro-variants, groove DNA, flip lineage, destroy & heal, A/B models, call & response, ecosystem packs, curation loop, Push server, Ableton bridge), a **Cloud / Deploy** reference tab, and a **🛰️ Server / API** tab that launches the SaaS API/worker, runs the test suite, and drives the API client (signup→submit→download). Every runnable script in `scripts/` is reachable from the UI. Bears-themed (navy/orange).

Prep & Analyze covers the full tagging/caption pipeline including **Genius metadata** (`genius_lookup.py`) and the auto-tagger's new **`heuristic`** engine (local DSP — no model, GPU, or network), alongside `qwen3-omni`/`qwen2-audio`/`clap`. The **Cloud / Deploy** tab has copy-paste commands for the one-shot pod bootstrap, SCP, the S3 volume, and the serverless endpoint + Go client (mirrors §33–§34).

**▶ Demo — clicking through sections, running a job, auditioning the result**
```console
$ python dashboard.py
Running on local URL:  http://127.0.0.1:7860
# Tabs: ⚙️ Settings · 📥 Prep & Analyze · 🧠 Train & Generate · 🥁 Beats & Sound
#       · 🧪 Creative Lab · 🔁 Remix · ✍️ Lyrics · 📦 Finish · 🔌 Plugins
#       · ☁️ Cloud/Deploy · 🛰️ Server/API · 🎧 Audition
# Each tool form streams its live log on the right; Audition plays + remixes results.
```

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

**Format conversion (`mp3_to_wav.py`).** Batch-decode MP3 (and m4a/ogg/opus/flac/aac) to WAV for DAW/toolkit compatibility — recursive, `--mirror` to keep folders, `--resume`, ffmpeg-backed with a librosa fallback. It's a lossy→PCM decode, so it does **not** recover quality the MP3 discarded (see the caveat above).

**\u25B6 Demo \u2014 batch MP3 \u2192 24-bit WAV**
```console
$ python scripts/mp3_to_wav.py --input "F:/RAP_ARCHIVES/mp3" --output "F:/RAP_ARCHIVES/wav" --bit-depth 24 --mirror --resume
[1/2982] 002 - Baby Keem - Baby Keem.mp3 -> 002 - Baby Keem - Baby Keem.wav
[2/2982] ...
=== 2982 converted, 0 skipped, 0 failed -> F:/RAP_ARCHIVES/wav/ ===
```

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

**Packaging as a service:** the SaaS backend now ships — an authenticated REST API, a Redis/RQ **job queue** with CPU/GPU worker lanes, credit **metering**, **Stripe** billing, a pricing page, rate limiting, and a tested, CI-gated, Docker-compose deployment (see §35 and [`server/`](server); go-live steps in [`DEPLOY.md`](DEPLOY.md)). What's left to launch is operational, not code: managed Postgres + Redis, TLS, your own auth/onboarding, and live Stripe products. Differentiators vs Splice / Waves / Loudly: hip-hop depth, **private models trained on a customer's own sounds**, **provenance certificates**, and groove-level control.
**Products:** (1) provenance-verified ecosystem pack line; (2) "your sound as a model" private fine-tunes (SA3 LoRA collapses the unit cost); (3) groove-DNA template packs.
**Learning path (O'Reilly):** Géron *Hands-On ML* → *Programming PyTorch* (audio ch.) → Foster *Generative Deep Learning* → HF *Hands-On Generative AI* → *Think DSP*. Free: HF Audio Course, "The Sound of AI." Study repos: stable-audio-tools, stable-audio-3, audiocraft, demucs, pedalboard, librosa, CLAP, AbletonOSC.
*(Not financial/legal advice — verify license thresholds and trademarks before commercializing.)*

<a name="31-scripts"></a>
## 31. Full script reference

| Script | Does |
|---|---|
| `organize_soundbank.py` | classify/sort a messy library into tag folders |
| `mp3_to_wav.py` | batch MP3/M4A → WAV converter |
| `remove_vocals.py` | batch vocal removal (BS-RoFormer/Demucs) |
| `deep_listen.py` | full technical/musical/sound-event/vibe analysis |
| `auto_tag.py` | open-vocab mood/vibe tags (audio LLM / CLAP) |
| `genius_lookup.py` | producer/album/year metadata from filenames |
| `build_captions.py` | fuse analysis+tags+genius → canonical caption |
| `prepare_dataset.py` / `validate_dataset.py` | dataset prep + preflight checks |
| `sa3_workflow.py` | SA3 prepare/plan/flip/fill/extend/song (LoRA) |
| `generate.py` | SAO batch generation from a pack plan |
| `ace_step_workflow.py` | ACE-Step 1.5 engine (REST): generate/song/cover/train |
| `audio2audio.py` | flip a sound (a2a) |
| `remix.py` | genre transform / mashup |
| `beat_builder.py` | beats from your samples + MIDI |
| `sample_chop.py` | chop a sample → 5 MPC/Push variations (10 producer styles) |
| `vst_instrument.py` / `vst_chain.py` | render MIDI through synths / process through effects |
| `plugin_scan.py` | catalog installed VST3/VST2 |
| `vocal_guide.py` | beat-aligned flow MIDI + lyrics + expression for ACE Studio |
| `ableton_bridge.py` | fire clips / control Ableton Live via OSC (AbletonOSC) |
| `song_generate.py` | full songs w/ vocals (HeartMuLa) |
| `lyric_analyze.py` / `lyric_generate.py` / `lyric_to_beat.py` | your-voice lyric model + beat bridge |
| `postprocess.py` / `build_pack.py` / `provenance.py` | finish, package, certify |
| `playlist_meta.py` `genre_playlists.py` `playlist_catalog.py` `sample_dna.py` | Spotify playlist metadata, per-genre playlist finder, song catalog (Genius links, no lyrics), sample-lineage→prompts (§37–§39) |
| `microvariants.py` `groove_dna.py` `flip_lineage.py` `destroy_heal.py` `ab_models.py` `curation_loop.py` `push_generation_server.py` `call_response.py` `ecosystem_pack.py` | Creative Techniques Lab (§24) |
| `sat_common.py` `lyric_common.py` `custom_metadata.py` | shared helpers |

`requirements.txt` lists core + per-feature optional deps. `cloud/` has pod setup scripts; `configs/` has dataset/VST-chain configs; `prompts/` has pack plans + example lyrics.

- **Engines/router:** `generate_engine.py` (unified `--engine`), `yue_workflow.py`, `diffrhythm_workflow.py`, `musicgen_workflow.py`, `ace_step_workflow.py`, and `engine_doctor.py` (readiness/auto-install) — see §40 and `docs/engines.md`.

<a name="32-engines"></a>
## 32. Engine choice: Stable Audio 3 vs ACE-Step 1.5

**What it is.** Two interchangeable, first-class generation engines ship in this toolkit. You can A/B them and pick per project — same dataset, same captions, different sound and licensing.

**▶ Demo — the same pack plan through SA3 and through ACE-Step**
```console
$ python scripts/sa3_workflow.py plan --model medium-base --lora hiphop_v1.safetensors --plan prompts/pack_plan.example.json --out gen_sa3
[Kicks] 30/30 ... done -> gen_sa3/
$ python scripts/ace_step_workflow.py generate --plan prompts/pack_plan.example.json --out gen_ace
[Kicks] 30 x 1.5s   submitted ... saved Kicks_1_01.wav ...   Done -> gen_ace/
```

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

<a name="33-serverless"></a>
## 33. Serverless API (RunPod) — host the toolkit as an endpoint

**What it is.** Everything above runs a script on a pod you rent by the hour. A
**Serverless endpoint** instead wraps one toolkit job (generate a beat, tag a
file, flip a sample) behind an HTTPS URL that **auto-scales to zero** — you pay
only for the seconds a request actually runs, with no idle GPU bill. This is how
you'd turn Co-Produce AI into a service (a website "generate" button, a Discord
bot, a batch tagger) instead of a thing you SSH into.

Use it when you want on-demand, pay-per-request inference. Keep using a normal
**pod** (§5) for training, dataset prep, and interactive/dashboard work — those
are long-running and stateful, the opposite of serverless.

**▶ Demo —**

```console
$ # 1) local test of the handler before you ever build an image
$ python serverless/handler.py --test_input '{"input":{"task":"beat","style":"boom_bap","bpm":90}}'
--- Starting Serverless Worker |  Version 1.7.0 ---
INFO   | Using test_input provided via command line
INFO   | local_test | beat_builder: style=boom_bap bpm=90 bars=8
INFO   | job results: {"wav_b64":"UklGR&...","seconds":17.0,"style":"boom_bap"}
INFO   | Local testing complete, exiting.

$ # 2) call the deployed endpoint (async): submit -> poll -> get the wav
$ curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
    -d '{"input":{"task":"beat","style":"trap","bpm":140}}' \
    https://api.runpod.ai/v2/$ENDPOINT_ID/run
{"id":"b1f2-e3","status":"IN_QUEUE"}
$ curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
    https://api.runpod.ai/v2/$ENDPOINT_ID/status/b1f2-e3
{"status":"COMPLETED","output":{"wav_b64":"UklGR&...","seconds":15.2,"style":"trap"}}
```

### How Serverless works (30-second version)

A request hits your **endpoint** -> if no **worker** is warm, one cold-starts
(container boot + model load into VRAM) -> the worker runs your **handler
function** on the JSON `input` -> the result is stored (`/run`, async) or
returned inline (`/runsync`, blocks until done) -> idle workers shut down after
a grace period. Cold starts are the main latency cost; you cut them with
**FlashBoot**, **model caching**, or keeping **active workers ≥ 1**.

### Setup & run

The development loop is: **write a handler -> test locally -> package as a Docker
image -> push to a registry -> create the endpoint -> send requests.**

**1. Write a handler.** A handler takes a job and returns JSON-serializable
output. Drop this at `serverless/handler.py` — it routes one `task` field to the
toolkit scripts you already have:

```python
# serverless/handler.py  -  wraps Co-Produce AI scripts as a RunPod handler
import base64, subprocess, tempfile, os, runpod

def _wav_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def handler(event):
    """event['input'] = {"task": "beat"|"tag"|"flip", ...task-specific args}"""
    inp = event.get("input", {}) or {}
    task = inp.get("task", "beat")
    out = tempfile.mkdtemp()

    if task == "beat":                         # beats from your own samples
        wav = os.path.join(out, "beat.wav")
        subprocess.run(["python", "scripts/beat_builder.py",
                        "--style", inp.get("style", "boom_bap"),
                        "--bpm", str(inp.get("bpm", 90)),
                        "--out", wav], check=True)
        return {"wav_b64": _wav_b64(wav), "style": inp.get("style", "boom_bap")}

    if task == "tag":                          # heuristic tagger (no model dl)
        import sys; sys.path.insert(0, "scripts")
        import auto_tag
        tags, cap = auto_tag.caption_heuristic(inp["path"])
        return {"tags": tags, "caption": cap}

    if task == "flip":                         # audio-to-audio derive
        wav = os.path.join(out, "flip.wav")
        subprocess.run(["python", "scripts/audio2audio.py",
                        "--input", inp["path"], "--prompt", inp.get("prompt", ""),
                        "--strength", str(inp.get("strength", 0.6)),
                        "--out", wav], check=True)
        return {"wav_b64": _wav_b64(wav)}

    return {"error": f"unknown task '{task}'"}

runpod.serverless.start({"handler": handler})  # required entrypoint
```

Test it locally first (no Docker, no cloud) — the SDK gives every handler a
`--test_input` CLI:

```powershell
pip install runpod
python serverless/handler.py --test_input '{\"input\":{\"task\":\"beat\",\"style\":\"boom_bap\",\"bpm\":90}}'
```

**2. Package it as a Docker image.** Serverless runs your code as a container, so
you need a `Dockerfile` (GPU base if the task needs CUDA — generation/flip do,
heuristic tagging does not):

```dockerfile
# serverless/Dockerfile
FROM runpod/base:0.6.2-cuda12.1.0
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt runpod
COPY scripts/ scripts/
COPY serverless/handler.py .
CMD ["python", "-u", "handler.py"]
```

**3. Build & push to a registry** (Docker Hub here; must be a linux/amd64 image):

```powershell
docker build --platform linux/amd64 -t YOUR_DOCKERHUB_USER/co-produce-ai-sls:latest -f serverless/Dockerfile .
docker push YOUR_DOCKERHUB_USER/co-produce-ai-sls:latest
```

*No Docker locally?* Skip steps 2–3 and use RunPod's **GitHub integration** —
point an endpoint at this repo and RunPod builds the image for you on each push.

**4. Create the endpoint.** In the RunPod console -> **Serverless** -> **New
Endpoint**: set the container image (or GitHub repo), pick a GPU tier, and set
scaling — **Max workers** (burst ceiling), **Active workers** (kept warm; 0 =
cheapest, ≥1 = no cold start), **Idle timeout**, and enable **FlashBoot** to
shrink cold starts. Attach your **network volume** (`d39orqnjjh`, §32-ish — see
`cloud/connect.md`) if the handler needs your dataset or model weights.

**5. Send requests.** Each endpoint exposes standard operations under
`https://api.runpod.ai/v2/<ENDPOINT_ID>/` with your `RUNPOD_API_KEY` as a bearer
token:

| Op | Use |
| --- | --- |
| `POST /run` | submit async job -> returns a job `id` (poll `/status/<id>`) |
| `POST /runsync` | submit and block until the result returns (good for short jobs) |
| `GET /status/<id>` | check `IN_QUEUE` / `RUNNING` / `COMPLETED` + output |
| `GET /health` | worker counts and queue depth |

```powershell
$H = @{ Authorization = "Bearer $env:RUNPOD_API_KEY"; "Content-Type" = "application/json" }
$body = '{"input":{"task":"beat","style":"drill","bpm":142}}'
Invoke-RestMethod -Method Post -Headers $H -Body $body `
  -Uri "https://api.runpod.ai/v2/$env:ENDPOINT_ID/runsync"
```

### Five things you can serve this way

1. **Beat-on-demand** — `{"task":"beat","style":"trap","bpm":140}` returns a WAV; wire it to a website "Generate" button.
2. **Hosted tagger** — `{"task":"tag","path":"s3://d39orqnjjh/raw_beats/x.wav"}` runs the heuristic engine; CPU worker, scales to zero, near-free.
3. **Sample flip API** — `{"task":"flip","prompt":"dusty soul chop","strength":0.6}` for an audio-to-audio microservice.
4. **Batch pack job** — submit many `/run` calls; RunPod queues and fans them across workers up to **Max workers**.
5. **Discord/Telegram bot backend** — bot posts the user's prompt to `/runsync`, gets the WAV, uploads it back to chat.

### Call it from Go (typed client)

The repo ships a typed Go client at [`clients/go/`](clients/go) that submits a
job, polls to completion, and decodes the returned `wav_b64` to a `.wav`:

```powershell
cd clients/go
go mod tidy
$env:RUNPOD_API_KEY="your_runpod_api_key"; $env:ENDPOINT_ID="your_endpoint_id"
go run . -task beat -style trap -bpm 140 -out trap.wav
```

```console
$ go run . -task beat -style trap -bpm 140 -out trap.wav
submitted job b1f2-e3-u1 (status IN_QUEUE)
status: IN_PROGRESS
status: IN_PROGRESS
status: COMPLETED
wrote trap.wav (5294412 bytes)
```

Get the two values: **RUNPOD_API_KEY** from the console -> Settings -> API Keys
(account-wide, shown once); **ENDPOINT_ID** from the console -> Serverless ->
your endpoint (also the `<ENDPOINT_ID>` in `api.runpod.ai/v2/<ENDPOINT_ID>/run`).
Uses the official `github.com/runpod/go-sdk`; `Run` returns `{Id,Status}` and
`Status` returns `{Status,Output,Error,...}`. See `clients/go/README.md`.

*Optional / good-to-have:* keep **Active workers = 0** for hobby use (pay only
per request) and bump it to 1 only when latency matters; cache big model weights
on the **network volume** so cold starts skip the download; use **load-balancing
endpoints** (instead of queue-based) if you later want a streaming/real-time
FastAPI server; SSH into a running worker to debug, and watch **logs** in the
console while you iterate. Queue-based endpoints + this handler pattern are the
right default for batch beat/pack generation.

---

<a name="34-pod-workflow"></a>
## 34. Pod workflow — SSH, SCP & cloning the repo to a pod

**What it is.** A **pod** (§5) is a full GPU box you SSH into and run the toolkit
on directly — the right place for training, dataset prep, and heavy tagging. This
section covers getting *in* (SSH), getting *code in* (clone this repo), and
getting *files in and out* (SCP + the S3 network volume). Quick-reference values
and copy-paste commands also live in [`cloud/connect.md`](cloud/connect.md).

> Two transfer paths, different jobs: **SCP** is point-to-point to one running
> pod (fast for a few files); the **S3 network volume** is persistent storage you
> upload once and mount on *any* pod (best for your dataset/models). See §33 and
> `cloud/connect.md` for the S3 side.

**▶ Demo — end-to-end: connect, clone, push beats, run, pull results**

```console
$ # connect (copy the exact command from the pod's Connect tab -> "SSH over exposed TCP")
$ ssh root@213.173.108.12 -p 17445 -i $env:USERPROFILE\.ssh\id_ed25519
root@gpu-pod:/workspace#

root@gpu-pod:/workspace# git clone https://github.com/pjcampbe11/Co-Produce-AI.git
Cloning into 'Co-Produce-AI'... done.
root@gpu-pod:/workspace# pip install -q -r Co-Produce-AI/requirements.txt

$ # (new local terminal) push beats up to the pod's /workspace
$ scp -P 17445 -i $env:USERPROFILE\.ssh\id_ed25519 -r "F:\RAP_ARCHIVES\raw_beats" root@213.173.108.12:/workspace/
Death Wish_instrumental.mp3              100%  6MB   5.9MB/s   00:01
...

root@gpu-pod:/workspace# cd Co-Produce-AI/scripts && python auto_tag.py --stems-dir /workspace/raw_beats --source beat --engine qwen3-omni --resume

$ # pull the tagged sidecars back down
$ scp -P 17445 -i $env:USERPROFILE\.ssh\id_ed25519 -r root@213.173.108.12:/workspace/raw_beats "F:\RAP_ARCHIVES\raw_beats_tagged"
```

### Prerequisites

You need an **SSH key** registered with RunPod and a pod that supports a
**public IP** (so SCP/SFTP work). Generate and register the key once:

```powershell
ssh-keygen -t ed25519 -C "patcampbell82@gmail.com"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard   # paste into console -> Settings -> SSH Public Keys
```

Official templates (Runpod PyTorch, Stable Diffusion) already run an SSH daemon.
On a **custom template**, expose TCP port 22 and start the daemon — replace
`sleep infinity` in your start command with:

```bash
bash -c 'apt update; DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y; \
  mkdir -p ~/.ssh; cd ~/.ssh; chmod 700 ~/.ssh; \
  echo "$PUBLIC_KEY" >> authorized_keys; chmod 700 authorized_keys; \
  service ssh start; sleep infinity'
```

### 1. Connect (SSH)

Open the pod's **Connect** tab in the console and copy the **SSH over exposed
TCP** command (this is the one that supports SCP). Its shape:

```powershell
ssh root@<POD_IP> -p <SSH_PORT> -i $env:USERPROFILE\.ssh\id_ed25519
```

`root` = pod user, `<POD_IP>` = public IP, `<SSH_PORT>` = the mapped external
port (not 22). If it **asks for a password**, the key isn't registered right —
you pasted the `SHA256:` fingerprint instead of the `ssh-ed25519 AAAA...` key,
dropped the `ssh-ed25519` prefix, or pointed `-i` at the wrong file. RunPod SSH
never needs a password.

### 2. Clone this repo onto the pod

The pod has its own disk, so pull the toolkit directly on it:

```bash
cd /workspace
git clone https://github.com/pjcampbe11/Co-Produce-AI.git
pip install -r Co-Produce-AI/requirements.txt
```

Because the repo is **private**, the clone will prompt for a GitHub username +
**personal access token** (as the password). To avoid typing it interactively,
prefix the token in the URL for that one command (then clear your shell history):

```bash
git clone https://USERNAME:YOUR_PAT@github.com/pjcampbe11/Co-Produce-AI.git
```

Clone onto the **network volume** (mounted at `/workspace` when you attach it to
the pod) so the code + any models persist across pods and survive a pod restart.

### One-shot bootstrap (clone + install + ready)

Skip the manual clone/install: paste this on a fresh pod to pull the repo onto
the network volume and install everything in one go ([`cloud/pod_bootstrap.sh`](cloud/pod_bootstrap.sh)):

```bash
curl -fsSL https://raw.githubusercontent.com/pjcampbe11/Co-Produce-AI/main/cloud/pod_bootstrap.sh | bash
```

Private repo (prompts otherwise) — pass a token, which the script clears from the
environment after cloning:

```bash
GH_TOKEN=YOUR_PAT bash -c 'curl -fsSL https://raw.githubusercontent.com/pjcampbe11/Co-Produce-AI/main/cloud/pod_bootstrap.sh | bash'
```

It clones to `/workspace/Co-Produce-AI` (falls back to `$HOME` if no volume),
installs `requirements.txt`, routes HF/torch caches to the volume so future pods
skip re-downloads, and prints the exact tag/enrich/caption commands to run next.
Re-running it just pulls latest and reinstalls (idempotent).

### 3. Copy files TO the pod (SCP)

Run these in a **local** terminal (not the SSH session), using the same IP/port/key:

```powershell
# a single file
scp -P <SSH_PORT> -i $env:USERPROFILE\.ssh\id_ed25519 myfile.wav root@<POD_IP>:/workspace/

# an entire folder (e.g. your beats)
scp -P <SSH_PORT> -i $env:USERPROFILE\.ssh\id_ed25519 -r "F:\RAP_ARCHIVES\raw_beats" root@<POD_IP>:/workspace/
```

### 4. Copy files FROM the pod (SCP)

```powershell
# a single file
scp -P <SSH_PORT> -i $env:USERPROFILE\.ssh\id_ed25519 root@<POD_IP>:/workspace/out/beat.wav .

# an entire results folder
scp -P <SSH_PORT> -i $env:USERPROFILE\.ssh\id_ed25519 -r root@<POD_IP>:/workspace/Co-Produce-AI/out "F:\RAP_ARCHIVES\out"
```

### 5. Or use the S3 network volume (no pod needed to stage data)

Upload your dataset to the volume **once** from your PC, then any pod that mounts
it reads from `/workspace` — no re-SCP per pod. Full commands in
[`cloud/connect.md`](cloud/connect.md); the short version:

```powershell
aws s3 cp "F:\RAP_ARCHIVES\raw_beats" s3://d39orqnjjh/raw_beats/ --recursive `
  --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io --checksum-algorithm CRC32
```

### Five things you'll do this way

1. **Clone + run** — SSH in, `git clone`, `pip install -r requirements.txt`, run any script in `scripts/`.
2. **Stage a dataset** — `scp -r "F:\RAP_ARCHIVES\raw_beats"` up, or push it to the S3 volume once and mount it.
3. **Tag on GPU** — `auto_tag.py --engine qwen3-omni` on the pod (the heavy engine that won't fit your local 6 GB card).
4. **Pull results back** — `scp -r root@<ip>:/workspace/.../out` down to `F:` when a job finishes.
5. **Persist across pods** — clone + cache models onto the network volume so a fresh pod is ready in seconds.

*Optional / good-to-have:* add an `~/.ssh/config` entry (`Host rp` with
`HostName`, `Port`, `User root`, `IdentityFile`) so you can just `ssh rp` and
`scp ... rp:/workspace/`; use `rsync -avP -e "ssh -p <PORT> -i <KEY>"` instead of
SCP for resumable, delta transfers of big folders; and remember **only the
network volume persists** — files written to a pod's local disk vanish when the
pod is terminated.

---

<a name="35-saas"></a>
## 35. SaaS server — job queue, REST API & Stripe billing

**What it is.** The pieces that turn Co-Produce AI from scripts into a **product**:
an authenticated **REST API**, a Redis-backed **job queue** with scalable
workers, per-job credit **metering**, and **Stripe** subscription billing. Lives
in [`server/`](server); one `docker compose up` runs the whole stack.

```
client ──HTTPS──> FastAPI (api) ──enqueue──> Redis ──> Worker(s) ──> scripts/*
                    │  API keys · credit metering          beat/tag/flip/remix/song
                    └── Stripe checkout + webhooks → grants monthly credits
   SQLModel DB: users · api keys · jobs · credit ledger   results on a shared volume
```

**▶ Demo — spin it up, sign up, run a paid job, download the result**

```console
$ cp server/.env.example server/.env      # add Stripe keys + price map
$ docker compose up --build               # api :8000, worker, redis
api-1     | Uvicorn running on http://0.0.0.0:8000
worker-1  | *** Listening on beat-jobs...

$ curl -s -X POST localhost:8000/v1/signup -H 'content-type: application/json' \
    -d '{"email":"you@example.com"}'
{"user_id":"a1b2","api_key":"bt_9f...","credits":10,"note":"store this key now..."}

$ KEY=bt_9f...
$ curl -s -X POST localhost:8000/v1/jobs -H "authorization: Bearer $KEY" \
    -H 'content-type: application/json' -d '{"task":"beat","params":{"style":"trap","bpm":140}}'
{"id":"3c4d","status":"queued","cost":1}
$ curl -s localhost:8000/v1/jobs/3c4d -H "authorization: Bearer $KEY"
{"id":"3c4d","task":"beat","status":"completed","cost":1,"result":{...}}
$ curl -s localhost:8000/v1/jobs/3c4d/result -H "authorization: Bearer $KEY" -o trap.wav
```

### What's in the box

The API (`server/app.py`) exposes signup + API-key auth (`Authorization: Bearer
bt_…`), job submit/list/get, a binary result download, account/usage, a Stripe
checkout endpoint, and a Stripe webhook. Jobs are enqueued to **Redis/RQ**
(`server/queue.py`) and run by one or more **workers** (`server/worker.py` →
`server/tasks.py`), which invoke the same `scripts/` you run by hand. State
(users, API keys, jobs, a credit ledger) is persisted with **SQLModel** —
SQLite by default, point `DATABASE_URL` at Postgres for production.

### Credits & metering

Every task has a credit cost; submitting **reserves** credits up front and the
worker **refunds** them if the job fails. Costs (edit `TASK_COSTS` in
`server/tasks.py`):

| task | credits | runs |
| --- | --- | --- |
| `beat` | 1 | `beat_builder.py` |
| `tag` | 1 | `auto_tag.py` (heuristic engine) |
| `flip` | 2 | `audio2audio.py` |
| `remix` | 3 | `remix.py` |
| `song` | 5 | (wire to `song_generate.py`) |

### Stripe billing

1. Create your products/prices in Stripe, then map each price id to a plan +
   monthly credit grant in the `STRIPE_PRICES` env (JSON).
2. Set `STRIPE_SECRET_KEY`; expose `POST /v1/webhooks/stripe` and put its signing
   secret in `STRIPE_WEBHOOK_SECRET`. Locally: `stripe listen --forward-to localhost:8000/v1/webhooks/stripe`.
3. `POST /v1/billing/checkout {price_id}` returns a Checkout URL.
   `checkout.session.completed` / `invoice.paid` grant credits;
   `customer.subscription.deleted` downgrades to free.

### Five ways to ship it

1. **Public API product** — sell metered access; users hit `/v1/jobs` with their key.
2. **Web app backend** — your site's "Generate" button calls the API and polls for the wav.
3. **Discord/Telegram bot** — bot forwards prompts to `/v1/jobs`, posts the result.
4. **Internal batch farm** — `docker compose up --scale worker=8` to fan out a pack run.
5. **Tiered plans** — free/creator/pro via Stripe prices → different monthly credit grants.

### GPU vs CPU workers

Jobs route to two lanes: CPU tasks (`beat`, `tag`) → `beat-cpu`, GPU tasks
(`flip`, `remix`, `song`) → `beat-gpu`. A worker consumes whatever `WORKER_QUEUES`
lists (blank = both, the dev default). For production, run CPU workers on a cheap
box and GPU workers on GPU hosts/pods (§34) against the same Redis + results
volume. The included GPU override wires a dedicated NVIDIA worker:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Locking down signup

`/v1/signup` is open by default for self-hosting. Before exposing publicly, set
`ALLOW_SIGNUP=false` and (optionally) an `ADMIN_TOKEN` — then accounts can only be
minted by sending `X-Admin-Token: <token>`. Verified: signup returns **403**
without the token and **200** with it.

### Pricing page & client

A ready static **pricing page** is served at **`/pricing`** (Bears-themed, calls
`/v1/billing/checkout` for the plan you pick). A copy-paste **Python client** at
[`clients/python/`](clients/python) does the whole loop:

```bash
python clients/python/beat_client.py --base-url http://localhost:8000     --signup you@example.com --task beat --param style=trap --param bpm=140 --out trap.wav
```

**Rate limiting & tests.** The API rate-limits per key on job submit (`RATE_LIMIT_PER_MIN`) and per IP on signup (`SIGNUP_LIMIT_PER_MIN`) via Redis, returning **429** over the limit. A pytest suite (`server/tests/`, **11 tests**, fakeredis + stubbed queue — no infra needed) covers signup/lockdown, auth, credit metering, CPU/GPU routing, the pricing page, and rate limiting: `cd server && pytest`.

*Optional / good-to-have:* put the API behind a reverse proxy with TLS, move
`DATABASE_URL` to Postgres, and scale workers per lane independently. Full details
+ curl tour in [`server/README.md`](server/README.md); the production go-live checklist (Postgres, TLS, Stripe live keys, object storage, signup lockdown) is in [`DEPLOY.md`](DEPLOY.md). CI runs the test suite on every push.

---

<a name="36-requirements"></a>
## 36. Requirements & dependencies (with venv setup)

**What it is.** A plain-English map of `requirements.txt` — what every package is
for and which feature needs it — plus the one habit that keeps it all tidy: a
**virtual environment**.

### Make a venv first

A venv keeps Co-Produce AI's (many) packages from colliding with other Python on
your machine. Do this once, in the repo folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

You'll see `(.venv)` in your prompt when it's active. Re-activate it each new
terminal. To leave: `deactivate`. (`.venv/` is git-ignored.)

### Core — always installed

| Package | What it's for |
| --- | --- |
| `numpy` | array/DSP math used everywhere |
| `librosa` | audio loading, tempo/key detection, spectral features |
| `soundfile` | read/write WAV/FLAC |
| `pyloudnorm` | LUFS loudness normalization (deep_listen, postprocess) |
| `tqdm` | progress bars |
| `requests` | HTTP — Genius API, ACE-Step REST, Ollama, the API client |
| `mido` | MIDI export (beat builder, vocal guide, Ableton bridge) |
| `gradio` | the local dashboard UI (bundles `gradio_client`) |

### Models & audio processing — per feature

| Package | Feature / scripts |
| --- | --- |
| `torch`, `torchaudio` | model runtime + audio tensors (generate, flip, remix, SA3/SAO) — match your CUDA build at pytorch.org |
| `einops` | tensor reshaping inside the audio models |
| `pedalboard` | headless VST3 hosting (vst_chain, vst_instrument, destroy_heal) |
| `python-osc` | OSC to Ableton Live / Push (ableton_bridge, push_generation_server) |
| `audio-separator[gpu]` | BS-RoFormer vocal/stem separation (remove_vocals); use `[cpu]` if no GPU |
| `demucs` | fallback 4-stem separator |
| `onnxruntime` | optional GPU/CPU capability check for the roformer path |
| `transformers`, `accelerate` | Qwen2-Audio / Qwen3-Omni captioners (auto_tag `--engine qwen*`) |
| `laion-clap` | zero-shot audio↔text tagging (auto_tag `--engine clap`, curation, vibe) |
| `panns-inference` | AudioSet sound-event tagging (deep_listen) |
| `beat-this` | SOTA beat tracking (groove_dna, deep_listen) |
| `wandb`, `huggingface_hub` | training monitoring + model download/auth (cloud GPU) |

### SaaS server — optional (`server/`)

`fastapi`, `uvicorn[standard]`, `sqlmodel`, `pydantic` (API), `redis` + `rq` (job
queue + rate limiter), `stripe` (billing), `python-multipart` (forms), and
`pytest` + `fakeredis` + `httpx` (tests). These also live in
`server/requirements.txt` — the Docker image installs only those. `runpod` powers
the optional `serverless/handler.py`.

### Not on PyPI — install from source

A few engines aren't pip-installable and are set up on the GPU box (commands are
in `requirements.txt`'s footer and the linked sections): **stable-audio-tools**
(SAO fine-tune), **stable-audio-3** (LoRA path, §32), **heartlib** (full songs,
§20), **Ollama** (lyric model, §22), and **AbletonOSC** (in Live, §19). The Go API
client (`clients/go`) needs the Go toolchain, not pip.

*Optional / good-to-have:* you rarely need *everything* — install Core, then add
the block for whatever you're doing (e.g. just `audio-separator` for batch vocal
removal). On a fresh GPU pod, `cloud/pod_bootstrap.sh` installs it all for you.

---

<a name="37-playlist-meta"></a>
## 37. Spotify playlist metadata extractor

**What it is.** `playlist_meta.py` pulls **all available metadata** from a public
Spotify playlist — track titles, artists, album, release date, duration,
popularity, ISRC, explicit flag, and **when each track was added** — plus
optional **audio features** (BPM, key, energy, danceability) and **sample data**.
Point it at a playlist with `-pl` / `--playlist` and choose `md` / `json` / `csv`
output. Reports default to **newest-added first**.

> **Sample source, honestly.** WhoSampled has no free public API (academic/paid
> only, and Spotify acquired it in Nov 2025). So `--samples` uses the **Genius
> `song_relationships`** API — the legitimate "samples / interpolations /
> sampled-in" data — reusing your `GENIUS_TOKEN`. `--whosampled` is an optional
> best-effort path through a RapidAPI provider (needs `RAPIDAPI_KEY`).

**▶ Demo —**

```console
$ python scripts/playlist_meta.py -pl https://open.spotify.com/playlist/7MNBsBwgsqAsRZkdNE4E5Y --audio-features
[playlist_meta] 'Hip-Hop Beats' - 84 tracks
# Hip-Hop Beats
- Owner: you   - Followers: 312   - Tracks: 84
| # | Added | Title | Artists | Album | Release | Len | Pop | BPM | Key |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-20 | ... | ... | ... | 2025-11-03 | 173s | 64 | 142 | F#m |
```

### Setup & run

Create a Spotify app to get the two keys (free, no user login — public reads use
the **Client Credentials** flow). Step by step:

1. Go to <https://developer.spotify.com/dashboard> and log in with any Spotify account.
2. Click **Create app**.
3. Fill in: **App name** and **App description** (anything, e.g. "Co-Produce AI"); for **Redirect URI** enter `http://127.0.0.1:8888/callback` (required even though Client Credentials never uses it).
4. Under **Which API/SDKs are you planning to use?** tick **Web API**.
5. Accept the terms and click **Save**.
6. Open the app → **Settings**. Copy the **Client ID**, then click **View client secret** and copy that too.

Then set the two env vars and run (the keys stay in your shell, never in the repo):

```powershell
$env:SPOTIFY_CLIENT_ID="paste_client_id"; $env:SPOTIFY_CLIENT_SECRET="paste_client_secret"
python scripts/playlist_meta.py -pl <url> --audio-features --format md --out playlist.md
```

macOS/Linux: `export SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=...`. To persist
on Windows, use `setx SPOTIFY_CLIENT_ID "..."` (new terminal required).

**One-time browser login.** As of 2025–2026, Spotify requires a **user token** to
read any playlist's tracks (app-only Client Credentials returns
`401 "Valid user authentication required"`). So:

- In your app's **Settings → Redirect URIs**, add exactly `http://127.0.0.1:8888/callback` and Save (this is required by the OAuth flow).
- Run once with `--login`; a browser opens, you approve, and a refresh token is cached (`~/.coproduce_ai_spotify.json`). Future runs reuse it automatically.

```powershell
python scripts/playlist_meta.py -pl <url> --login        # first time only
python scripts/playlist_meta.py -pl <url> -f md -o playlist.md   # subsequent runs
```

Full per-service key steps are in [`cheatsheets/api-keys.md`](cheatsheets/api-keys.md).

> **Spotify API caveats (2024–2026 changes).** `--audio-features` (BPM/key/energy)
> was **deprecated for apps created after 2024-11-27** — on a new app it returns
> 403, so the tool now warns and continues without those columns. And Client
> Credentials can't read Spotify-owned **editorial/algorithmic** playlists — use
> your own (or any regular public) playlist; the tool prints a clear message if a
> playlist isn't accessible.

Build a per-song **reference catalog** (metadata + Genius links, no lyrics) from
a JSON export with [`scripts/playlist_catalog.py`](scripts/playlist_catalog.py):
`python scripts/playlist_catalog.py --json playlist_full.json --out catalog --resume`
→ writes one file per song + `catalog/INDEX.md`. It does **not** store lyrics
(copyrighted; the Genius API doesn't serve them) — train lyric models on your own
words (§22).

Five ways to use it:

1. **Newest-added report** (default): `-pl <url>` → markdown, newest first.
2. **Spreadsheet**: `-pl <url> -f csv -o playlist.csv`.
3. **Vibe match**: `--audio-features` → BPM/key/energy to find beats that fit.
4. **Sample lineage**: `--samples` (needs `GENIUS_TOKEN`) → what each track samples/interpolates.
5. **Full dump**: `--format json --audio-features --samples --out playlist.json` for downstream tooling.

*Optional / good-to-have:* `--sort popularity|release|name`, `--limit N`, and
`--whosampled` (RapidAPI). Reachable in the dashboard under **Prep & Analyze →
Spotify playlist meta**. Only metadata is fetched — no audio is downloaded.

---

<a name="38-inspired"></a>
## 38. Hip-hop beats inspired by (playlist)

 **[▶ open on Spotify](https://open.spotify.com/playlist/7MNBsBwgsqAsRZkdNE4E5Y)**.

---

<a name="39-cheatsheets"></a>
## 39. Cheat sheets & genre playlist finder

**What it is.** One-page quick references in [`cheatsheets/`](cheatsheets), plus a
tool that finds the **best reference playlists per genre** across Spotify,
YouTube, and SoundCloud.

The cheat sheets ([`cheatsheets/README.md`](cheatsheets/README.md)):

- [`cli-quickref.md`](cheatsheets/cli-quickref.md) — every script + its key flags
- [`pipeline.md`](cheatsheets/pipeline.md) — the crate-to-pack flow, copy-paste
- [`saas-and-cloud.md`](cheatsheets/saas-and-cloud.md) — API/queue/Stripe + pods/SCP/S3
- [`best-songs-by-genre.md`](cheatsheets/best-songs-by-genre.md) — the playlist finder below

### Song catalog & Sample DNA

`playlist_catalog.py` turns a `playlist_meta.py` JSON export into a per-song
**reference catalog** ([`catalog/`](catalog)) — producer, writers, featured,
label, year, ISRC, Spotify + **Genius links**, and full **sample/interpolation
lineage** — all from the Genius API. It stores **no lyrics** (copyrighted; the API
doesn't serve them — read them via the Genius link).

`sample_dna.py` then distills that lineage — which source artists/eras the catalog
flips — into **original** pack-plan prompts you can generate from. It copies
nothing; it uses the factual sampling tradition to craft fresh prompts like
"dusty 70s soul chop, warm Rhodes, vinyl crackle, boom-bap drums":

```powershell
python scripts/playlist_catalog.py --json playlist_full.json --out catalog --resume
python scripts/sample_dna.py --catalog catalog --pack-name "Crate DNA Vol 1" --bpm 90 --key "F minor" --out prompts/sample_dna.json
python scripts/sa3_workflow.py plan --plan prompts/sample_dna.json --out generated
```

That's the legal, creative core of Co-Produce AI: learn the *tradition* from real
credits, then make something new in it — never reproduce the source works.

`sample_dna.py` can also seed **audio-to-audio flips** in the detected era's
texture — give it `--flips N` to write era-textured flip prompts, and add
`--flip-input <your_chop.wav>` to render them through `audio2audio.py`:

```powershell
python scripts/sample_dna.py --catalog catalog --flips 8 --bpm 90 --key "F minor" --flip-input mychop.wav --out-dir flips
```

Each flip is an original chop (e.g. "dusty 70s soul chop, chopped and re-looped, 90 BPM") derived from *your* source sound — not the sampled records.

### Genre playlist finder

`genre_playlists.py` returns top playlists for a genre from **Spotify** (live Web
API), **YouTube** (Data API if `YOUTUBE_API_KEY` is set, else a playlist-search
link), **Apple Music** (catalog search if `APPLE_MUSIC_TOKEN` is set, else a
search link), and **SoundCloud** (genre charts + sets-search links, since its API
is closed). It degrades gracefully — with no keys you still get working YouTube/
Apple Music/SoundCloud links; add Spotify keys for live, ranked results.

**▶ Demo —**

```console
$ python scripts/genre_playlists.py -g dnb
## dnb
**Spotify**
- [Drum & Bass Fix](https://open.spotify.com/playlist/...) — Spotify (120 tracks)
**YouTube**
- [Liquid DnB Mix 2026](https://www.youtube.com/playlist?list=...) — channel
**Apple Music**
- [Search Apple Music](https://music.apple.com/us/search?term=drum%20and%20bass%20playlist)
**SoundCloud**
- [Genre charts](https://soundcloud.com/charts/top?genre=drumbass&country=US)
- [Playlist (sets) search](https://soundcloud.com/search/sets?q=drum%20and%20bass)
```

```powershell
$env:SPOTIFY_CLIENT_ID="xxx"; $env:SPOTIFY_CLIENT_SECRET="yyy"   # optional: $env:YOUTUBE_API_KEY="zzz"
python scripts/genre_playlists.py -g all --limit 8 --format md --out playlists.md
```

Keys are all optional (no keys = working YouTube/Apple Music/SoundCloud links).
For **Spotify**, follow the 6-step app setup in §37. For **YouTube** (live, ranked
playlists instead of a search link):

1. Go to <https://console.cloud.google.com> and create or select a project.
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
3. **APIs & Services → Credentials → Create credentials → API key** → copy it.
4. `$env:YOUTUBE_API_KEY="paste_key"` (macOS/Linux: `export`; persist: `setx`).

**Apple Music** needs a paid-Apple-Developer MusicKit JWT (`APPLE_MUSIC_TOKEN`);
without it you get a search link. All key steps: [`cheatsheets/api-keys.md`](cheatsheets/api-keys.md).

Genres: `hiphop`, `boom_bap`, `trap`, `drill`, `lofi`, `rock`, `metal`,
`rockmetal`, `dubstep`, `dnb`, or `all`. Reachable in the dashboard under
**Prep & Analyze → Genre playlists**. Feed the Spotify hits into `playlist_meta.py`
(§37) to pull full metadata.

*Optional / good-to-have:* for **reference listening only** — don't train a
sellable model on copyrighted tracks (see §6). `--format json` for tooling.

---

<a name="40-engines-router"></a>
## 40. Engines & unified generation router

**What it is.** Co-Produce AI drives several music models; pick one through a
single router instead of remembering which script is which. Full comparison +
"when to use which" in [`docs/engines.md`](docs/engines.md).

**Prompt → beat:** `sa3` (your-sound LoRA), `sao` (full fine-tune), `ace-step`
(fast), `musicgen` (**melody conditioning** — hum→beat). **Lyrics → full song:**
`yue` (lyrics→5-min song, closest to Suno), `diffrhythm` (fast drafts),
`heartmula`, `ace-step`. All self-hostable and commercial-friendly.

**▶ Demo —**

```console
$ python scripts/generate_engine.py --list
  sa3         [prompt] Stable Audio 3 LoRA (your-sound)
  ace-step    [prompt] ACE-Step 1.5 (fast, REST; also does vocals)
  musicgen    [prompt] MusicGen (+ melody conditioning)
  yue         [lyrics] YuE - lyrics to full song
  diffrhythm  [lyrics] DiffRhythm - fast lyrics to song
  ...
```

```powershell
# pick an engine; flags pass through to that engine's workflow
python scripts/generate_engine.py --engine sa3 --plan prompts/pack_plan.example.json --out generated
python scripts/generate_engine.py --engine musicgen --prompt "boom bap, dusty, 90 bpm" --melody hum.wav --out gen
python scripts/generate_engine.py --engine yue --yue ~/YuE --lyrics verse.txt --genre "hip hop, 90 bpm" --out songs
```

New adapters: [`yue_workflow.py`](scripts/yue_workflow.py),
[`diffrhythm_workflow.py`](scripts/diffrhythm_workflow.py),
[`musicgen_workflow.py`](scripts/musicgen_workflow.py) — cloud setup in
`cloud/yue_setup.sh`, `cloud/diffrhythm_setup.sh`, `cloud/musicgen_setup.sh`.

**ACE Studio vocals.** `vocal_guide.py` now also exports **expression envelopes** —
power (CC11), breathiness (CC74), and pitch inflection — as MIDI CC lanes plus a
`<out>_expression.json` the ACE Bridge applies per note, so AI vocals sit far more
naturally. Clone your own voice in ACE Studio once and reuse it across tracks.

Check readiness anytime with `python scripts/engine_doctor.py` (green/red per
engine; no models loaded) — the dashboard's **🩺 Engine status** tab shows the
same. The YuE/DiffRhythm/MusicGen workflows also **preflight automatically** and
refuse to start if deps are missing; add `--install` to auto-fix (pip/git) or
`--skip-check` to bypass. 

*Optional / good-to-have:* `yue` wants a 16–24 GB GPU; use `diffrhythm` for fast
drafts then re-render the keeper in `yue`. `musicgen-melody` is the only engine
that conditions on a hummed/played melody. All engines are reachable in the
dashboard under **Train & Generate**.

---

<a name="41-sample-chop"></a>
## 41. Sample chopper (MPC One+ / Ableton Push)

**What it is.** `sample_chop.py` takes a sample and rebuilds it into **5 new
variations** the way classic producers do — chopping, rearranging, repitching,
reversing, stuttering. Each variation exports a **master loop**, the individual
**chop one-shots** (stems, one per pad), a **MIDI pattern**, a cue-marked master
for auto-slicing, and ready folders for **MPC One+** and **Ableton Push 2**.

It works **standalone** (just renders audio), and the chops drop straight onto
hardware pads. With `--producer` it chops in a known producer's signature style.

**▶ Demo —**

```console
$ python scripts/sample_chop.py --input soul_loop.wav --producer ********** --bpm 90 --out chops
[producer] **********: dilla + dilla + chipmunk + reverse + stutter
[chop] 14 slices from soul_loop.wav
[var1] dilla: master + 14 slices + pattern.mid -> chops/var1_**********_dilla
... 5 variations, each with mpc/ + ableton/ folders
```

### Producer styles (`--producer`)

Ten sample-chopping greats, each mapped to a 5-variation style set + feel
(swing, density, pitch bias, dust, quantize): `**********` (micro-chop, off-quantize
swing), `**********` (chipmunk soul), `**********` (tight chopped stabs),
`**********` (clean grid soul), `**********` (gritty pitched-down), `**********` (loose,
dusty), `**********` (smooth soul/jazz), `**********` (big pitched-up soul),
`**********` (hazy loops/halftime), `**********` (lo-fi swung). List them:
`python scripts/sample_chop.py --list-producers`. **Five worked examples per producer** (with and without the AI flags) are in [`cheatsheets/sample-chop-examples.md`](cheatsheets/sample-chop-examples.md).

### Get it onto your gear

Every variation has a `slices/` folder (numbered one-shots) — the **guaranteed**
path on any device. **MPC One+:** copy the variation folder over and load
`mpc/program.xpm`, or drag the slices onto pads. **Ableton / Push 2:** drag the
`ableton/` WAVs onto a Drum Rack (Push plays the pads) and drop `pattern.mid`
into a clip; or import `master_sliced.wav` and use Slice-to-MIDI. `pattern.mid`
maps pad 1 → note 36.

Five quick examples (no AI — pure DSP, fast, offline):

```powershell
python scripts/sample_chop.py --producer **********    --input dusty_soul_loop.wav --bpm 90 --out chops
python scripts/sample_chop.py --producer **********  --input otis_vocal.mp3 --bpm 92 --target both --out chops
python scripts/sample_chop.py --producer **********  --input jazz_stab.wav --grid 16 --pads 16 --bpm 93 --out chops
python scripts/sample_chop.py --producer **********  --input soul_45.wav --bpm 86 --out chops
python scripts/sample_chop.py --producer **********      --input obscure_jazz.wav --bars 4 --bpm 87 --out chops
```

Five with the AI flags (`--stems` = separate + chop the melodic layer, `--reimagine` = audio2audio flip):

```powershell
python scripts/sample_chop.py --producer **********           --input full_song.mp3 --stems --bpm 88 --out chops
python scripts/sample_chop.py --producer ********** --input hazy_psych.wav --reimagine --adg --target ableton --bpm 82 --out chops
python scripts/sample_chop.py --producer **********     --input horn_loop.wav --stems --reimagine --target mpc --bpm 91 --out chops
python scripts/sample_chop.py --producer **********    --input triumph_soul.wav --reimagine --bars 4 --bpm 96 --out chops
python scripts/sample_chop.py --producer **********     --input lofi_chop.wav --stems --bpm 89 --out chops
```

Full set — five per producer, with and without AI — in [`cheatsheets/sample-chop-examples.md`](cheatsheets/sample-chop-examples.md).

*Optional / good-to-have:* `--stems` separates the source (audio-separator) and
chops the melodic layer; `--reimagine` adds an audio2audio AI flip of each master;
`--adg` writes an Ableton Drum Rack preset (experimental — the slice folder always
works). Only use sources you have the rights to chop (see §6).

---

<a name="42-license"></a>
## 42. License & notice

Fine-tunes/runs Stability AI models (Stable Audio Open 1.0 / Stable Audio 3) under the **Stability AI Community License** (free commercial use under US$1M annual revenue; enterprise above — https://stability.ai/license). Full songs with vocals use **HeartMuLa** (Apache-2.0). Model weights are **not** included. **Only train on audio you own or that is explicitly cleared for ML training.** See §6.
