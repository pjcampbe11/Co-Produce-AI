# RUNBOOK — chained commands (your setup)

Scripts: `C:\Users\12242\Documents\Desktop\samplePack-toolkit\scripts`
Beats (instrumentals, already separated): `F:\RAP_ARCHIVES\raw_beats`
`&&` = PowerShell 7 (stops on first failure). On PS 5.1 use `;`.

## Phase 1 — Caption + prepare + validate (local)
```powershell
cd "C:\Users\12242\Documents\Desktop\samplePack-toolkit\scripts"
python deep_listen.py --input "F:\RAP_ARCHIVES\raw_beats" --out "F:\RAP_ARCHIVES\raw_beats" --for-captions --resume && `
python build_captions.py --beats "F:\RAP_ARCHIVES\raw_beats" && `
python prepare_dataset.py --input "F:\RAP_ARCHIVES\raw_beats" --output "F:\dataset_beats" --name-contains _instrumental && `
python validate_dataset.py --dataset "F:\dataset_beats"
```
Must print "Dataset is ready for training." First deep_listen file is slow (model load) — normal.

## Phase 2 — Train on the pod (SA3 LoRA)
PC:  `.\runpodctl.exe send "F:\dataset_beats"`   (note the code)
Pod:
```bash
runpodctl receive <code>
bash /workspace/toolkit/cloud/sa3_setup.sh
python /workspace/toolkit/scripts/sa3_workflow.py prepare --dataset /workspace/dataset_beats --data-dir /workspace/sa3_beats
cd /workspace/stable-audio-3 && uv run python scripts/train_lora.py --model medium-base \
  --data_dir /workspace/sa3_beats --rank 16 --adapter_type dora-rows --steps 2500 \
  --exclude seconds_total --output_dir /workspace/lora_beats
runpodctl send /workspace/lora_beats/lora_step2500.safetensors   # receive on PC
```
Watch demo audio; stop when it sounds like you but isn't copying tracks.

## Phase 3 — Generate + post-process (local or pod)
Edit prompts\pack_plan.example.json first (your trained vocabulary; 2-3x overgenerate).
```powershell
python sa3_workflow.py plan --model medium-base --lora "F:\lora_step2500.safetensors" --plan "..\prompts\pack_plan.example.json" --out "F:\generated" && `
python postprocess.py --input "F:\generated" --output "F:\processed" --lufs -14
```

## Phase 4 — Human QA (manual)
Listen to all of F:\processed; delete duds/off-grid/wrong-key. 200-sample pack <- 500+ gens.

## Phase 5 — Pack + provenance (local)
```powershell
python build_pack.py --input "F:\processed" --pack-name "Dusty Crates Vol 1" --out "F:\packs" && `
python provenance.py --pack "F:\packs\DustyCratesVol1" --dataset "F:\dataset_beats" --generated "F:\generated" --run-name beats-v1 --statement "All training audio owned/cleared."
```

## Anytime — flip a sound (audio-to-audio)
```powershell
python audio2audio.py --model-config model_config.json --ckpt hiphop_v1.ckpt --input "F:\my_break.wav" `
  --prompt "hip hop, boom bap, 90 BPM, dusty drum break, vinyl" --strength 0.5 --variations 4 --out "F:\flipped" && `
python postprocess.py --input "F:\flipped" --output "F:\flipped_processed" --lufs -14
```

## Or: the dashboard
```powershell
cd "C:\Users\12242\Documents\Desktop\samplePack-toolkit"
python dashboard.py
```
Every step above as buttons + live logs.
