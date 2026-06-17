# Training: Specs, Costs & Dataset Sizing
*Verified against June 2026 cloud GPU pricing. Prices move - re-check before a run.*

## The mental model (read this first)

Cost is **GPU-hours**, not per-file. The model takes random crops from your
dataset across thousands of training *steps*; every file is seen many times. A
500-file run and a 3,000-file run to the same step count cost almost the same.
So "cost per WAV" isn't really a thing - "cost per training run" is.

"How many at once?" = two different numbers:
- **Dataset size**: ALL your files go in one folder; the dataloader samples them.
- **Batch size**: how many crops the GPU processes per step (typically 4-8),
  limited by VRAM - not something you scale with dataset size.

## Two training paths in the toolkit

### A) Stable Audio 3 LoRA  (recommended - 22_sa3_workflow.py)
A small adapter (~50-200 MB .safetensors) on top of SA3. Cheap, fast, stackable.

| Spec | Value |
|---|---|
| Min VRAM | ~2.5 GB (Small) / ~6.5 GB (Medium); ~5.5 GB Medium with `--base_precision bf16 --adapter_type lora-xs` |
| Recommended GPU | RTX 4090 (24 GB) - huge headroom; A5000/A40 fine |
| Steps | ~1000 default (more for big/varied data) |
| Wall time | ~20-60 min on a 4090 for Medium |
| **Cost per run** | **~$0.50-2** (RTX 4090 ~$0.34/hr; even 3-4 GPU-hrs incl. setup = a couple dollars) |
| Min dataset | 20-50 clips works; hundreds is better |

### B) Stable Audio Open 1.0 full fine-tune  (cloud/runpod_setup.sh)
Updates all model weights. Maximum ownership of the sound; heavier.

| Spec | Value |
|---|---|
| Min VRAM | 24 GB (RTX 4090, batch 2 + grad accumulation) |
| Recommended GPU | A100 40-80 GB or A6000 48 GB (batch 8) |
| Steps | 5k-20k (watch the demo audio; stop when it sounds like YOUR aesthetic) |
| Wall time | a few hours to ~a day |
| **Cost per run** | **~$8-40** (A100 ~$1.39/hr on-demand, ~$0.52-0.67/hr on Vast marketplace) |
| Min dataset | 5-10+ hours of audio recommended |

Current sample rates (June 2026): RTX 4090 ~$0.34/hr, A100 40-80GB ~$1.39/hr
on-demand (~$0.52-0.67 marketplace), H100 ~$1.50-2.89/hr. Billed per second -
terminate the instant it's done.

## What's an "acceptable" dataset? (1k / 2k / 3k?)

Curation beats count. Targets per **style LoRA**:

| Dataset | Verdict |
|---|---|
| < 50 clips | works for a tight one-trick style; risks overfitting |
| 200-800 | the sweet spot for a focused genre/era LoRA - **start here** |
| 1,000-2,000 | great for a broad, versatile model; diminishing returns begin |
| 3,000+ | fine, but ONLY if every file is on-aesthetic and well-labeled; |
|         | 3k messy files train WORSE than 800 curated ones (mushy prompts, |
|         | conflicting styles -> generic output) |

So: **you don't need 3k.** 500-1,500 well-tagged, QA'd, same-genre files is the
target. Use separate LoRAs per genre rather than one giant mixed dataset
(GENRE_EXPANSION.md). Run the AI-tagging + Deep Listen passes first so labels
are accurate - label quality moves output quality more than file count.

## Per-run economics that actually matter

- A full product line = a handful of LoRA runs (one per genre, plus curation
  re-rolls via 12_curation_loop.py). At ~$1-2 each, your whole training spend
  to launch is **under ~$20**, even with experimentation.
- Generation (after training) is pennies per pack, or free on a local 8 GB+ GPU.
- The expensive resource is YOUR time curating and QA-ing - not GPU.

## Step-by-step cost walkthrough (one genre)

1. Organize + tag locally (07, --ai-tags) - free, your PC, hours of compute.
2. Prepare + validate (01, 02) - free, local.
3. Upload dataset to pod - minutes.
4. SA3 LoRA train, ~1000 steps - ~$1-2, ~30-60 min.
5. Generate a test batch, listen - pennies.
6. Curate keepers (12), retrain from them if needed - another ~$1-2.
7. Repeat per genre.

Total to a sellable first model: typically **$5-15** of GPU + your listening time.
