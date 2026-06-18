# Hip-Hop Sample Pack Toolkit

End-to-end pipeline: your WAV library → fine-tuned audio model → finished, sellable sample packs (one-shots, drum loops/breaks, melodic loops, stems).

> **Engine note:** despite the repo name, this toolkit's recommended generation engine is **Stable Audio 3** (LoRA fine-tuning) with **Stable Audio Open 1.0** as the full-fine-tune alternative — NOT Meta's MusicGen. Both are open-weight Stability AI models under the Stability AI Community License. The scripts are model-agnostic for everything except the generation/training steps, which target Stable Audio.

**Architecture:** fine-tune [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) (stereo, 44.1 kHz, up to ~47 s per generation) using Stability's [stable-audio-tools](https://github.com/Stability-AI/stable-audio-tools). Dataset prep, post-processing, and pack assembly run on any machine; training runs on a rented cloud GPU; generation runs on any ~8 GB+ NVIDIA GPU or cloud.

**Why this model:** open weights, designed for exactly this use case (samples and sound design, not full songs), officially supports fine-tuning on custom data, and the Stability Community License permits commercial use free of charge while your annual revenue is under $1M (above that you need an [enterprise license](https://stability.ai/license)).

## Full songs (2-4 min)

Beyond samples/loops, the toolkit can make complete 2-4 minute tracks - see **FULL_SONGS.md**: instrumental songs via Stable Audio 3 (`sa3_workflow.py song`, works with your beat LoRA), or full songs **with vocals from your lyrics** via HeartMuLa (`song_generate.py`, Apache-2.0, no revenue cap).

## Dashboard (web UI)

Prefer clicking to typing? `dashboard.py` is a local Gradio app with a tab for every pipeline stage (organize, vocal removal, deep listen, auto-tag, captions, prepare, validate, SA3 train/generate, beat builder, VST chains, pack builder, provenance, full songs) plus a live log stream and an audio auditioner. Run `run_dashboard.bat` (or `pip install gradio && python dashboard.py`) and open the printed URL. GPU steps run wherever you launch it — your local GPU, or run the dashboard on a cloud pod to drive its GPU.

## SOTA status (audited June 2026)

| Stage | Current best | In toolkit |
|---|---|---|
| Generation | **Stable Audio 3** (2026-05-20): open weights, licensed training data, LoRA fine-tune on a 16 GB GPU, inpainting + continuation, up to 380 s | `sa3_workflow.py` + `cloud/sa3_setup.sh` - **recommended path for new builds** |
| Deep fine-tune | Stable Audio Open 1.0 + stable-audio-tools (full-weight training) | Steps 1-9 below - still valid when you want maximum model ownership |
| Vocal removal | BS/Mel-RoFormer (~12.9 dB vocals SDR vs ~9 htdemucs) | `remove_vocals.py --engine roformer` (default; demucs fallback) |
| Beat tracking | beat_this (CPJKU) | `groove_dna.py --engine beat_this` (librosa fallback) |
| Audio-text embedding | LAION-CLAP (still standard for curation) | `curation_loop.py` |
| VST hosting | pedalboard (still unchallenged) | `vst_chain.py` |

**Which generation path?** Start with SA3 LoRA: hours and ~$5-15 of GPU instead of a $20-60 full fine-tune, stackable per-style adapters (one LoRA per subgenre - swap or even blend at runtime), and inpainting/extension unlock "fix bars 2-3" and "stretch this 4-bar loop to 8". Move to (or add) the SAO full fine-tune when LoRA stops capturing your sound. Both bases are Stability Community License (commercial OK under $1M revenue). SA3 quickstart:

```bash
bash cloud/sa3_setup.sh                    # on any 16-24GB GPU box
python scripts/sa3_workflow.py prepare --dataset dataset --data-dir sa3_data
# train LoRA (~1000 steps), then:
python scripts/sa3_workflow.py plan --model medium-base --lora my.safetensors \
    --plan prompts/pack_plan.example.json --out generated
python scripts/sa3_workflow.py fill --input beat.wav --start 4 --end 8 \
    --prompt "punchy kick drum fill" --out filled.wav   # inpainting!
```

```
Pipeline:
  raw_library/ ──prepare──▶ dataset/ ──validate──▶ [cloud GPU: train] ──▶ checkpoint
  checkpoint ──generate──▶ generated/ ──postprocess──▶ processed/ ──human QA──▶ build_pack ──▶ PackName.zip
```

---

## Step 0 — Legal ground rules (read first, this is a commercial service)

1. **Training data:** only train on audio you own or have explicit license to use for ML training. Owning a sample pack does NOT automatically grant training rights — check each pack's license for AI/ML clauses. Your own productions are safest.
2. **Model license:** Stability AI Community License — free commercial use under $1M annual revenue; register for enterprise above that. Keep a copy of the license with your records.
3. **Output license:** you decide the terms for your customers. `build_pack.py` writes a standard royalty-free license; edit it or pass `--license-file`.
4. Keep a manifest of every training source file (the prep script logs `source` in each sidecar) — provenance documentation protects you later.

## Step 1 — Organize your library

On your machine, arrange WAVs into tag folders. **Folder names become training prompt tags**, so name them descriptively:

```
raw_library/
  drums_oneshots/kicks/        drums_oneshots/snares/      drums_oneshots/hats/
  drums_loops/boom_bap/        drums_loops/trap/
  melodic_loops/soul_keys/     melodic_loops/dark_strings/
  stems/
```

Optionally add a `tags.txt` in any folder — one comma-separated line of extra descriptors applied to all files inside, e.g. `dusty, vinyl crackle, swung, 1990s boom bap`. The richer and more accurate the tags, the better your prompt control later. **This is where your hip-hop knowledge is the moat — label subgenre, era, texture, and groove character precisely.**

Data targets: 5–10+ hours total is a solid fine-tune. Hundreds of one-shots per drum type, and as many loops as you can clear.

## Step 2 — Prepare the dataset

```bash
pip install -r requirements.txt
python scripts/prepare_dataset.py --input raw_library --output dataset --max-seconds 40
```

Converts everything to 44.1 kHz stereo PCM-16, slices long files under the model's 47 s window, auto-detects BPM and key on loops, and writes a JSON sidecar per file containing the training prompt (folder tags + analysis + tags.txt). Review `dataset/prepare_log.txt` and spot-check sidecar prompts — fix bad folder names/tags and re-run if needed.

## Step 3 — Validate before paying for GPU time

```bash
python scripts/validate_dataset.py --dataset dataset
```

Fails loudly on wrong sample rates, silence, missing/empty prompts, or files exceeding the model window. Fix all errors; treat warnings (clipping) seriously.

## Step 4 — Cloud GPU setup

Rent one of: **A100 80GB** (fastest), **A6000 48GB** (best value), or **RTX 4090 24GB** (works with smaller batch + gradient accumulation). RunPod, Lambda, and Vast.ai all work. Choose a PyTorch 2.x + CUDA 12 template, with a persistent volume mounted at `/workspace`.

```bash
# upload from your machine
scp -r dataset/ root@<pod-ip>:/workspace/dataset/
scp -r hiphop-samplepack-toolkit/ root@<pod-ip>:/workspace/toolkit/

# on the pod
bash /workspace/toolkit/cloud/runpod_setup.sh
```

The script installs stable-audio-tools, logs into Hugging Face (accept the model license on the [model page](https://huggingface.co/stabilityai/stable-audio-open-1.0) first), and downloads `model.ckpt` + `model_config.json`.

## Step 5 — Train

```bash
cd /workspace/stable-audio-tools
wandb login   # recommended: free account for live loss curves + audio demos

python train.py \
  --dataset_config /workspace/toolkit/configs/dataset_config.json \
  --model_config /workspace/base_model/model_config.json \
  --pretrained_ckpt_path /workspace/base_model/model.ckpt \
  --name hiphop-finetune \
  --save_dir /workspace/checkpoints \
  --checkpoint_every 1000 \
  --batch_size 8 \
  --accum_batches 2 \
  --num_gpus 1 \
  --precision 16-mixed \
  --seed 42
```

Notes:
- Flag style differs between stable-audio-tools versions (`--dataset_config` vs `--dataset-config`). Run `python train.py --help` and match it.
- VRAM: batch_size 8 fits an A100/A6000; on a 4090 use `--batch_size 2 --accum_batches 8`.
- **How long:** there is no fixed number — monitor the demo audio that the trainer logs every few hundred steps. For a 5–10 h dataset, useful results typically appear within 5k–20k steps (several hours to ~a day on an A100). Overtraining = outputs that near-copy training data; stop when demos sound like *your aesthetic* but not like *specific files*.
- Checkpoints land in `/workspace/checkpoints/<name>/`. Keep several; the last isn't always the best.

When done, unwrap the training checkpoint into an inference checkpoint and download both files:

```bash
python unwrap_model.py \
  --model_config /workspace/base_model/model_config.json \
  --ckpt_path /workspace/checkpoints/hiphop-finetune/<run>/checkpoints/<step>.ckpt \
  --name hiphop_v1
scp root@<pod-ip>:/workspace/stable-audio-tools/hiphop_v1.ckpt .
scp root@<pod-ip>:/workspace/base_model/model_config.json .
```

## Step 6 — Generate

Edit `prompts/pack_plan.example.json` (counts, durations, prompts — **use the same tag vocabulary you trained with**; that's what the model learned). Generate ~2-3x more than the pack needs so you can curate hard:

```bash
python scripts/generate.py \
  --model-config model_config.json --ckpt hiphop_v1.ckpt \
  --plan prompts/pack_plan.example.json --out generated --steps 100 --cfg 7
```

Runs on the pod or any local NVIDIA GPU with ~8 GB VRAM. `--cfg 7` = prompt adherence (try 6–9); `--steps 100` = quality/speed trade-off. Sanity-check the pipeline anytime with the base model: `--pretrained stabilityai/stable-audio-open-1.0`.

## Step 7 — Post-process

```bash
python scripts/postprocess.py --input generated --output processed --lufs -14
```

Auto-rejects duds, trims silence, adds anti-click fades, peak-normalizes one-shots to -0.3 dBFS, loudness-normalizes loops to -14 LUFS, re-detects BPM/key, exports 24-bit WAV.

## Step 8 — Human QA (non-negotiable for a paid product)

Listen to every file in `processed/`. Delete anything with artifacts, weak hits, off-grid loops, or mislabeled keys (auto-detection is good, not perfect — verify keys on melodic content by ear or in your DAW). A 200-sample pack should come from 500+ generations.

## Step 9 — Build the pack

```bash
python scripts/build_pack.py --input processed --pack-name "Dusty Crates Vol 1" --out packs
```

Produces a standard pack structure (One Shots / Loops / Stems), producer-style names with key & BPM (`DustyCratesVol1_MelodicLoop_05_Fmin_90BPM.wav`), README, LICENSE, and a zip ready to sell.

## Step 6b — Audio-to-audio: flip an existing sound

Feed any WAV to the fine-tuned model and get new sounds *derived* from it, steered by a prompt — the model treats your file as the starting point of the diffusion and `--strength` sets how far it transforms (0.2 = re-texture, 0.5 = a real flip, 0.8 = loose inspiration):

```bash
python scripts/audio2audio.py \
  --model-config model_config.json --ckpt hiphop_v1.ckpt \
  --input my_break.wav \
  --prompt "hip hop, drums loops, boom bap, 90 BPM, dusty drum break, vinyl texture" \
  --strength 0.5 --variations 4 --out flipped/
```

Generate several variations per source and curate. Note: outputs are derivative of the input — only feed it audio you have rights to, same as training data. Run results through `postprocess.py` like any other generation.

---

## Iterating toward "real hip-hop"

The model's authenticity comes from your data and labels, not the architecture. Iteration loop: generate → note what's generically wrong (stiff swing, plastic snares, clean-not-dusty) → add/relabel training data targeting exactly that → fine-tune further from your last checkpoint (`--ckpt_path` resumes a wrapped training checkpoint). Consider separate fine-tunes per product line (a drums-only model and a melodic model) once the single-model version works — specialization measurably improves one-shot quality.

## Utilities: your library, your beats, your VSTs, Ableton

**`organize_soundbank.py` — fix a messy soundbank.** Auto-classifies every file (filename keywords first, audio analysis fallback: spectral/onset features for kick vs hat vs snare, percussive-ratio for drum vs melodic loops) and restructures it into the tag-folder layout the toolkit trains and builds from. Writes `review.csv` with per-file confidence; low-confidence files land in `_review/` for manual sorting. `--dry-run` previews; files are copied (originals untouched) unless `--move`.

```bash
python scripts/organize_soundbank.py --input messy_bank --output organized --dry-run
python scripts/organize_soundbank.py --input messy_bank --output organized
```

After organizing, add `tags.txt` descriptors and the same folder feeds `prepare_dataset.py` for training.

**`beat_builder.py` — beats from YOUR sounds.** Sequences kicks/snares/hats/percs/808s drawn from your organized library on style pattern grids (boom_bap, trap, drill, lofi) with swing and velocity humanization. Each beat outputs master + per-instrument stems + `pattern.mid` + `manifest.json` (exactly which of your samples were used). `--melodic` layers in loops (e.g. from your fine-tuned model, Step 6).

```bash
python scripts/beat_builder.py --library organized --style boom_bap --bpm 92 --bars 4 --count 8 --out beats
```

**`vst_chain.py` — run audio through your real VST3s, no DAW.** Uses [pedalboard](https://github.com/spotify/pedalboard) to host your VST3 plugins headlessly and batch-process any folder (generated samples, built beats) through a chain defined in JSON (`configs/vst_chain.example.json`). `--list-params` prints a plugin's parameter names; `--edit N` opens the plugin's own GUI to dial settings by ear, then applies them to the whole batch.

```bash
pip install pedalboard
python scripts/vst_chain.py --input processed --output processed_vst --chain configs/vst_chain.example.json
```

**`ableton_bridge.py` — automation into Live + Push.** With [AbletonOSC](https://github.com/ideoforms/AbletonOSC) installed as a control surface, this pushes a built beat into a running Live set: sets tempo, creates the MIDI clip with all notes, optionally fires it. Put the manifest's samples in a Drum Rack (kick=C1, snare=D1, hats=F#1, perc=B1, 808=B0) with your VST chain on the track — the pattern now plays through your plugins, and Push edits it natively.

```bash
pip install python-osc mido
python scripts/ableton_bridge.py --beat beats/boom_bap_92bpm_01 --track 0 --scene 0 --fire
```

Full automation loop: `07` organize → `03/06` generate with the fine-tuned model → `08` build beats from your sounds → `09` character-process through your VST3s → `10` land in Ableton/Push → `04`/`05` package what's pack-worthy.

**`remove_vocals.py` — batch vocal removal.** One job: strip vocals from a large set of MP3/WAVs (Demucs). See `README_vocal_removal.md`.

## Genre expansion: Rock/Metal + Dubstep/DnB

The same pipeline now runs three product lines - see **GENRE_EXPANSION.md** for the full guide: per-genre library layouts and label vocabulary, BPM conventions (`--bpm-min/--bpm-max` on 01/04 - DnB at 174 must not fold to 87), six new beat-builder styles (`rock`, `metal`, `dbeat`, `dubstep`, `dnb`, `amen`), genre pack plans (`prompts/pack_plan.rock_metal.json`, `prompts/pack_plan.dubstep_dnb.json`), and the one-LoRA-per-genre training strategy (stackable for hybrid genres).

## Creative Techniques Lab (scripts 12-21)

Techniques the AI beat community isn't doing - all built on the loops between the toolkit's pieces. Scripts marked (GPU) need stable-audio-tools + your checkpoint; the rest run anywhere.

**12 - Taste distillation** (`curation_loop.py`). CLAP-embeds your generations and ranks them by similarity to a folder of your best sounds; keepers get staged (with prompt sidecars) as the next fine-tune round's dataset. Your ear becomes training signal. `pip install laion-clap`. `score` then `promote`, then fine-tune from your last checkpoint.

**2 - Timbre-level humanization** (`microvariants.py` (GPU) + `08 --rotate`). Generate 8 micro-variants of each one-shot at strength 0.15, then `--rotate` makes every hit in a beat a different take. No two hits the same - like a drummer.

**3 - Groove DNA transplants** (`groove_dna.py` + `08 --groove`). Extract the micro-timing + accent fingerprint of any reference break into a 16-step template (numbers, not audio - no rights issues), then play YOUR samples with that exact pocket. Build a groove preset library from the breaks that raised you.

**4 - Bake your mix into the model** (workflow). Before training, run the prepared dataset through your signature chain: `vst_chain.py --input dataset --output dataset_charactered --chain your_chain.json` (copy the .json sidecars over). The model then *generates* sounds wearing your saturation/tape/glue.

**5 - Flip lineages** (`flip_lineage.py` (GPU)). Telephone-game morphing: chained audio-to-audio with a prompt schedule, every stage saved + `lineage.json` (prompts, strengths, seeds, hashes). The evolution is content.

**6 - Destruction-and-heal** (`destroy_heal.py` (GPU)). Wreck audio through an extreme chain (`configs/vst_chain.destroy.example.json`), then low-strength a2a pulls it back toward musicality. The model as restoration glue; surviving scars are the texture.

**7 - Two-producer packs** (`ab_models.py` (GPU)). Same plan, same seeds, two checkpoints (e.g. 70s-soul model vs Memphis-90s model). Item N in A/ and B/ is the same musical idea in two sonic personalities.

**8 - Push as a generation instrument** (`push_generation_server.py` (GPU)). OSC server holding your model in memory: map Push pads/knobs (Live's free Connection Kit OSC Send device) to preset select, strength, and fire. Generated WAVs land in a folder Live's browser watches. `pip install python-osc`.

Ready-made chains built from your installed plugins (Saturn 2, TR5 tape, Thermal, Trash, Dirt...) live in `configs/vst_chains/` - see its README. 

**9 - AI session musician** (`call_response.py` (GPU)). Watches a folder; every clip you export from Live gets answered with N variations in a response folder. Trade bars with a model trained on your own catalog.

**10 - Ecosystem packs** (`ecosystem_pack.py`). `plan` locks every prompt in a pack plan to one key + BPM; `verify` checks post-processed output sidecars against the lock and quarantines mismatches. Pack series where everything combines with everything.

**11 - Provenance as product** (`provenance.py`). Aggregates training sources, run id, generation seeds, and per-file SHA-256 into `PROVENANCE.json` + a human-readable certificate inside the pack. "Rights-cleared, provenance-verified AI" - checkable, not claimed.

Extra installs by technique: `laion-clap` (12), `pedalboard` (4, 6), `python-osc` (8), `mido` (08 MIDI). 

## Deep Listen - `deep_listen.py`

Learn everything possible about any WAV/MP3: technical truth (sample rate, encoding, LUFS, crest/dynamics, stereo correlation, clipping, DC offset, band-by-band spectrum, lossy-upsample detection), musical analysis (BPM + tempo stability via beat_this/librosa, key + confidence, onset density, structure boundaries, energy arc), **sound identification** - every detectable event with timestamps across AudioSet's 527 classes via PANNs (`pip install panns-inference`), and **mood/feeling** - CLAP zero-shot scoring against mood/genre/instrument/production vocabularies (`pip install laion-clap`). Each layer degrades gracefully if its model isn't installed; reports state what ran. Outputs per-file `.analysis.json` + `.analysis.md`.

```bash
python scripts/deep_listen.py --input track.mp3 --out reports/
python scripts/deep_listen.py --input "F:/Sound Bank