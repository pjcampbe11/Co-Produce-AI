# Pipeline cheat sheet (crate → pack)

The standard order. GPU steps run locally or on a pod (see saas-and-cloud.md).

```bash
# 0) (optional) MP3 library -> WAV
python scripts/mp3_to_wav.py --input "F:/in" --output "F:/wav" --mirror --resume

# 1) organize the soundbank
python scripts/organize_soundbank.py --input "F:/SoundBank" --output "F:/Organized" --move --resume

# 2) separate vocals/stems (if working from full songs)
python scripts/remove_vocals.py --input "F:/Organized" --output "F:/stems" --engine roformer

# 3) analyze + 4) tag + 5) enrich + 6) caption  (beats only)
python scripts/deep_listen.py  --input "F:/RAP_ARCHIVES/raw_beats" --for-captions --resume
python scripts/auto_tag.py     --stems-dir "F:/RAP_ARCHIVES/raw_beats" --source beat --engine heuristic --resume
python scripts/genius_lookup.py --beats "F:/RAP_ARCHIVES/raw_beats" --resume
python scripts/build_captions.py --beats "F:/RAP_ARCHIVES/raw_beats"

# 7) build + validate the dataset
python scripts/prepare_dataset.py  --input "F:/RAP_ARCHIVES/raw_beats" --output dataset --name-contains _instrumental
python scripts/validate_dataset.py --dataset dataset

# 8) train (cloud GPU) -> 9) generate -> 10) finish
python scripts/sa3_workflow.py prepare --dataset dataset --data-dir sa3_data
python scripts/sa3_workflow.py plan --model medium-base --lora hiphop_v1.safetensors --plan prompts/pack_plan.example.json --out generated
python scripts/postprocess.py --input generated --output processed --lufs -14
python scripts/build_pack.py  --input processed --pack-name "Dusty Crates Vol 1" --out packs
python scripts/provenance.py  --pack packs/DustyCratesVol1 --dataset dataset --generated generated
```

Tagging is **optional** — `build_captions.py` works from deep_listen + genius alone.
