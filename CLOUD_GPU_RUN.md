# Bulk vocal removal on a rented RTX 4090 (RunPod)

Your set: ~2,970 mp3s / ~11 GB. A 2060 = multi-day; a 4090 = ~1-2 h of GPU
(~$1-2) + your upload/download time. Everything's resumable.

## 0. The honest bottleneck
Transfer, not compute. 11 GB up + ~15-20 GB back (instrumentals + vocals).
On home upstream that's the slow part. Budget for it; the GPU itself is cheap.

## 1. Spin up the pod
1. Make a RunPod account, add ~$5 credit (runpod.io).
2. Deploy a **GPU Pod** -> pick **RTX 4090** (~$0.34-0.70/hr).
3. Template: **RunPod PyTorch 2.x (CUDA 12.x)**. Container disk 20 GB,
   add a **Volume 60 GB** mounted at `/workspace` (room for in + out).
4. Deploy, then "Connect" -> Web Terminal (or SSH).

## 2. Install on the pod
```bash
cd /workspace
pip install "audio-separator[gpu]"
# grab the script (clone your repo, or just upload remove_vocals.py)
git clone https://github.com/pjcampbe11/musicgen-sampling-toolkit.git toolkit  # private: use a token URL
```

## 3. Get your mp3s onto the pod  (pick ONE)

**A. runpodctl (simplest for big folders)** - install RunPod CLI on your PC:
```powershell
# on YOUR PC (PowerShell)
runpodctl send "F:\RAP_ARCHIVES\mp3"
# it prints a one-time code; on the POD run:
#   runpodctl receive <code>
```

**B. rclone via cloud storage** (resumable, good for flaky connections):
upload `F:\RAP_ARCHIVES\mp3` to Google Drive/Backblaze/S3 with rclone, then on
the pod `rclone copy remote:mp3 /workspace/mp3`.

**C. Skip the upload entirely** - re-fetch on the pod with yt-dlp (gigabit
there). Only if you don't need your exact sorted/curated set:
```bash
pip install yt-dlp
yt-dlp -x --audio-format mp3 --download-archive done.txt \
  -o '%(playlist_index)s - %(title)s.%(ext)s' 'https://www.youtube.com/playlist?list=PLb3DZrKKAtMo'
```

## 4. Run it (GPU auto-used; verify)
```bash
cd /workspace
python toolkit/scripts/remove_vocals.py \
  --input /workspace/mp3 --output /workspace/raw_beats \
  --mp3 --keep-vocals --require-gpu
```
First lines should say `Acceleration: GPU [torch CUDA: NVIDIA GeForce RTX 4090]`
and `2970 file(s) found, ... to process`. ~1-2 h total. Resumable if it drops.

## 5. Pull results back to your PC
```powershell
# on the POD: package, then send
#   cd /workspace && tar czf raw_beats.tgz raw_beats && runpodctl send raw_beats.tgz
# on YOUR PC:
#   runpodctl receive <code>
#   tar xzf raw_beats.tgz   (or 7-Zip on Windows)
```
Or rclone the `raw_beats` folder up to cloud storage and down to `F:\RAP_ARCHIVES\`.

## 6. TERMINATE the pod
Stop AND terminate it in the RunPod console the moment the download's done -
you're billed per second while it exists. Delete the volume too if you don't
need it (volumes bill even when the pod is stopped).

## Cost
GPU ~$1-2 for the run. Volume pennies/hr. Total under ~$5 including slack.
Compare: the 2060 would tie up your machine for days.

## While you're paying for a 4090...
Consider doing the GPU-heavy steps in the same session: auto-tagging
(auto_tag.py --engine qwen3-omni) and even a LoRA train (TRAIN_BEATS.md)
run far faster here too. Batch them before you terminate.
