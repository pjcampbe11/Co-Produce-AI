# Train a beat model on all ~1,500 instrumentals (full-set, recommended)

Assumes: beats tagged (24_auto_tag.py) -> `.tags.json` next to each
`*_instrumental` in `F:\RAP_ARCHIVES\raw_beats`, and F:-drive caching set
(cloud/use_F_drive.ps1). You train on the WHOLE set at once; the dataloader
shuffles and reuses files across epochs automatically - no manual batching.

## 1. Prepare the dataset (beats only, tags merged into prompts)
```powershell
python scripts\01_prepare_dataset.py --input "F:\RAP_ARCHIVES\raw_beats" `
  --output "F:\dataset_beats" --name-contains _instrumental --max-seconds 40
```
- `--name-contains _instrumental` -> ignores the `_vocals` files.
- Long instrumentals are sliced into <=40 s clips (so 1,500 songs become more
  training clips - good). 44.1 kHz stereo WAV + a prompt sidecar per clip.

## 2. Validate before spending GPU time
```powershell
python scripts\02_validate_dataset.py --dataset "F:\dataset_beats"
```
Fix any errors it reports (silence, bad prompts). Note total hours it prints.

## 3. Convert to Stable Audio 3 LoRA format
```powershell
python scripts\22_sa3_workflow.py prepare --dataset "F:\dataset_beats" --data-dir "F:\sa3_beats"
```
Writes audio + `.txt` caption pairs SA3's trainer expects.

## 4. Train the LoRA (16 GB+ GPU; local or a rented pod)
Inside the stable-audio-3 repo (see cloud/sa3_setup.sh):
```bash
uv run python scripts/train_lora.py --model medium-base \
  --data_dir F:/sa3_beats --rank 16 --adapter_type dora-rows \
  --steps 2500 --exclude seconds_total --output_dir F:/lora_beats
```
- **All ~1,500 at once**: every clip goes in `--data_dir`; the trainer samples
  randomly, reshuffling each epoch. You do NOT pick sets of 250.
- **Steps**: ~2000-3000 is a reasonable range for this dataset size. WATCH the
  demo audio the trainer logs - stop when it sounds like your beats but isn't
  copying specific tracks (overfitting).
- VRAM tight? add `--base_precision bf16 --adapter_type lora-xs` (~5.5 GB).
- `--exclude seconds_total` prevents conditioner hijack on a focused set.

## 5. Generate with your model
```powershell
python scripts\22_sa3_workflow.py plan --model medium-base `
  --lora F:\lora_beats\lora_step2500.safetensors `
  --plan prompts\pack_plan.example.json --out F:\generated
```
Then 04_postprocess.py -> human QA -> 05_build_pack.py -> 21_provenance.py.

## 6. Refine (optional)
Curate the best generations (12_curation_loop.py), then CONTINUE training from
this checkpoint with `--lora_checkpoint F:\lora_beats\lora_step2500.safetensors`.

## Cost/time reality
1,500 beats -> a few thousand clips. LoRA at ~2500 steps: ~1-2 h on an RTX 4090
(~$0.34/hr) = a couple dollars. Prep/validate/convert are free and local.
