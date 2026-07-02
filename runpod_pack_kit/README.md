# RunPod Pack Kit — Demo Sample Packs & One-Command Build

Everything renders in **SA3 song mode at 3:08** for solid quality and sonics. One rented GPU,
one command: train (optional) → generate full songs → carve one-shots → split stems → label by
key/BPM → zip → ship.

## The four packs

| Pack | Vibe | Contents |
|---|---|---|
| **Boom-Bap Dust · Vol. 1** | Dusty vinyl chops, warm upright bass, swung drums. `boom bap · dusty · soulful` | 24 songs + one-shots · WAV + stems · key & BPM labeled |
| **Trap Nights · Vol. 1** | Booming 808s, crisp hats, dark melodies. `trap · 808 heavy · dark` | 20 songs + one-shots · WAV + stems · 130–150 BPM |
| **Drill Sessions** | Sliding 808s, eerie bells, sparse hats. `drill · hypnotic · sub bass` | 18 songs + one-shots · WAV + stems · 140–146 BPM |
| **Lo-Fi After Hours** | Mellow Rhodes, tape saturation, vinyl crackle. `lofi · warm · nostalgic` | 22 songs + one-shots · WAV + stems · 70–85 BPM |

## 1. Train one LoRA per pack (optional)

Training learns from your **caption sidecars**, not a prompt — so each pack's training profile is
the caption vocabulary its dataset split is filtered to (and what you generate with):

| Pack | Training caption profile |
|---|---|
| Boom-Bap Dust | `hip hop, 86–94 BPM, key of {key}, boom bap, dusty vinyl, warm, mellow, laid back, swung drums, gritty, soulful, melodic` |
| Trap Nights | `hip hop, 130–150 BPM, key of {key}, trap, dark, 808 heavy, sub bass, gritty, energetic, hypnotic, melodic` |
| Drill Sessions | `hip hop, 140–146 BPM, key of {key}, drill, dark, hypnotic, sliding 808, sub bass, sparse drums, eerie, distorted` |
| Lo-Fi After Hours | `hip hop, 70–85 BPM, key of {key}, lofi, tape saturated, dusty vinyl, vinyl crackle, warm, nostalgic, mellow, laid back, melodic` |

```bash
cd /workspace/stable-audio-3
bash /workspace/runpod_pack_kit/make_style_datasets.sh   # symlink-splits sa3_beats by caption
bash /workspace/runpod_pack_kit/train_all_4.sh           # 4 sequential runs (r16a16_lr2e4 recipe)
```

Skip training if your existing LoRA covers all four lanes — just point `LORA=` at it.

## 2. Build everything — one line (song mode, 3:08)

```bash
LORA=/workspace/sweeps/run_r16a16_lr2e4/<best>.safetensors \
  bash /workspace/runpod_pack_kit/build_all.sh all
```

Every output is a full **3:08 song** (`SONG_DUR=188`), `STEPS=250`, `CFG=8`. Builds the 4 packs
(songs + onset-sliced one-shots + demucs stems, key & BPM in every filename, zipped per pack) **and**
every Part 4 prompt — starters, 20 arrangements, 100 capability presets, 20 PRO presets. Resumable;
ends with a master zip.

Knobs: `SONG_DUR=188 STEPS=250 CFG=8 STR=0.7 STEMS=1 ONESHOTS=12`. Flips need `IN=/workspace/mybeat.wav`.

> **⚠️ Song mode required.** Generation calls `scripts/sa3_workflow.py song` — not the trainer's
> `--demo_every` auto-demos. Confirm song mode works on the pod before a full run. ~160 full songs
> is heavy GPU time — run `packs` and `part4` separately, or `STEMS=0` for a fast first pass.

## 3. Ship to Windows

```bash
runpodctl send /workspace/coproduce_build/coproduce_all_<date>.zip   # on pod → prints code
runpodctl receive <code>                                             # on Windows (PowerShell)
# or: scp -P <PORT> root@<POD_IP>:/workspace/coproduce_build/coproduce_all_*.zip $env:USERPROFILE\Downloads\
```

## Contents

```
runpod_pack_kit/
├── build_all.sh                 master one-liner (packs | part4 | flips | all) — song mode, 3:08
├── make_style_datasets.sh       caption-filtered symlink splits of sa3_beats
├── train_all_4.sh               the 4 LoRA training runs
└── prompts/
    ├── pack_{boombap,trap,drill,lofi}.txt   84 style prompts (BPM|KEY|prompt)
    ├── part4_starter*.txt        17 palette + 5 verbose starters
    ├── part4_arrangement.txt     20 arrangement songs
    ├── part4_capability.txt      100 capability presets
    ├── part4_pro.txt             20 PRO presets (cfg/steps/seed/negatives)
    └── part4_flips.sh            20 flip commands
```
