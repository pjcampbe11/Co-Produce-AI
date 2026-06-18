#!/usr/bin/env bash
# ============================================================
# RunPod paste-script: bulk vocal removal on a rented GPU.
# 1) Deploy an RTX 4090 pod (PyTorch CUDA 12, 60GB volume at /workspace).
# 2) Open the Web Terminal and paste THIS ENTIRE FILE, press Enter.
# It installs deps, fetches the playlist, removes vocals, packages results.
# ============================================================
set -euo pipefail
cd /workspace

echo "=== [1/5] installing ==="
pip install -q "audio-separator[gpu]" yt-dlp

echo "=== [2/5] writing remove_vocals.py ==="
cat > /workspace/remove_vocals.py <<'PYEOF'
#!/usr/bin/env python3
"""
remove_vocals.py
One job: strip vocals from a large set of MP3/WAV files.

Engines (June 2026):
  roformer (default) - BS-RoFormer via the audio-separator package. Current
                       SOTA (~12.9 dB vocals SDR vs ~9 for htdemucs).
                       pip install "audio-separator[gpu]"   (or [cpu])
  demucs             - htdemucs fallback, also gives you 4-stem separation.
                       pip install demucs

See README_vocal_removal.md for setup and details.

Usage:
    python remove_vocals.py --input songs/ --output instrumentals/
    python remove_vocals.py --input songs/ --output out/ --engine demucs --keep-vocals
"""
import argparse
import shutil
import subprocess
import os
import sys
import tempfile
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aif", ".aiff"}
ROFORMER_MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"


def gpu_status():
    """Return (on_gpu: bool, human_readable: str)."""
    bits = []
    torch_cuda = False
    try:
        import torch
        torch_cuda = torch.cuda.is_available()
        if torch_cuda:
            bits.append(f"torch CUDA: {torch.cuda.get_device_name(0)}")
        else:
            bits.append("torch CUDA: NOT available")
    except Exception as e:
        bits.append(f"torch: {e}")
    ort_cuda = False
    try:
        import onnxruntime as ort
        provs = ort.get_available_providers()
        ort_cuda = "CUDAExecutionProvider" in provs
        bits.append("onnxruntime: " + ("CUDA" if ort_cuda else "CPU-only " + str(provs)))
    except Exception:
        bits.append("onnxruntime: not installed (roformer uses torch)")
    return (torch_cuda or ort_cuda), " | ".join(bits)


def dest_for(f, in_path, out_root, ext, mirror):
    """Return (instrumental_dest, vocals_dest), mirroring subfolders if requested."""
    if mirror and in_path.is_dir():
        rel = f.relative_to(in_path).parent
        d = out_root / rel
    else:
        d = out_root
    return (d / f"{f.stem}_instrumental{ext}", d / f"{f.stem}_vocals{ext}")


def collect(in_path, out_root, ext, overwrite, mirror):
    files = ([in_path] if in_path.is_file()
             else sorted(p for p in in_path.rglob("*") if p.suffix.lower() in AUDIO_EXTS))
    if not files:
        sys.exit("No audio files found.")
    todo = [f for f in files
            if overwrite or not dest_for(f, in_path, out_root, ext, mirror)[0].exists()]
    print(f"{len(files)} file(s) found, {len(todo)} to process.")
    return todo


def run_roformer(args, todo, out_root, ext):
    try:
        from audio_separator.separator import Separator
    except ImportError:
        sys.exit('audio-separator not installed:  pip install "audio-separator[gpu]"')
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        _sep_kw = {"output_dir": tmp, "output_format": ext.lstrip(".").upper()}
        if os.environ.get("AUDIO_SEPARATOR_MODELS"):
            _sep_kw["model_file_dir"] = os.environ["AUDIO_SEPARATOR_MODELS"]
        sep = Separator(**_sep_kw)
        sep.load_model(model_filename=args.model)
        for i, f in enumerate(todo, 1):
            print(f"\n[{i}/{len(todo)}] {f.name}")
            try:
                outputs = sep.separate(str(f))
            except Exception as e:
                print(f"  FAILED: {e}")
                failed.append(str(f))
                continue
            inst_dest, vox_dest = dest_for(f, Path(args.input), out_root, ext, args.mirror)
            inst_dest.parent.mkdir(parents=True, exist_ok=True)
            got = False
            for o in outputs:
                op = Path(tmp) / Path(o).name
                if not op.exists():
                    op = Path(o)
                low = op.name.lower()
                if "instrumental" in low:
                    shutil.move(str(op), str(inst_dest))
                    got = True
                elif "vocal" in low and args.keep_vocals:
                    shutil.move(str(op), str(vox_dest))
            if not got:
                failed.append(str(f))
    return failed


def run_demucs(args, todo, out_root, ext):
    if shutil.which("demucs") is None:
        sys.exit("Demucs not found:  pip install demucs")
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(todo, 1):
            print(f"\n[{i}/{len(todo)}] {f.name}")
            cmd = ["demucs", "--two-stems", "vocals", "-n", args.model
                   if args.model != ROFORMER_MODEL else "htdemucs",
                   "-o", tmp, "-j", str(args.jobs)]
            if ext == ".mp3":
                cmd += ["--mp3", "--mp3-bitrate", "320"]
            cmd.append(str(f))
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                failed.append(str(f))
                continue
            model_name = args.model if args.model != ROFORMER_MODEL else "htdemucs"
            stem_dir = Path(tmp) / model_name / f.stem
            no_vox = stem_dir / f"no_vocals{ext}"
            vox = stem_dir / f"vocals{ext}"
            inst_dest, vox_dest = dest_for(f, Path(args.input), out_root, ext, args.mirror)
            inst_dest.parent.mkdir(parents=True, exist_ok=True)
            if no_vox.exists():
                shutil.move(str(no_vox), str(inst_dest))
            else:
                failed.append(str(f))
                continue
            if args.keep_vocals and vox.exists():
                shutil.move(str(vox), str(vox_dest))
            shutil.rmtree(stem_dir, ignore_errors=True)
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="File or folder (recursive)")
    ap.add_argument("--output", required=True)
    ap.add_argument("--engine", choices=["roformer", "demucs"], default="roformer")
    ap.add_argument("--model", default=ROFORMER_MODEL,
                    help=f"roformer: separator model filename (default {ROFORMER_MODEL}); "
                         "demucs: htdemucs | htdemucs_ft")
    ap.add_argument("--keep-vocals", action="store_true")
    ap.add_argument("--mp3", action="store_true", help="Output MP3 320k instead of WAV")
    ap.add_argument("--jobs", type=int, default=1, help="demucs CPU parallel jobs")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--require-gpu", action="store_true",
                    help="Abort instead of running on CPU (avoids accidental multi-day CPU runs)")
    ap.add_argument("--mirror", action="store_true",
                    help="Recreate input subfolder structure in output (prevents same-named "
                         "files in different folders from colliding; recommended for sorted libraries)")
    args = ap.parse_args()

    in_path, out_root = Path(args.input), Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    ext = ".mp3" if args.mp3 else ".wav"
    on_gpu, status = gpu_status()
    print(f"Acceleration: {'GPU' if on_gpu else 'CPU (SLOW)'}  [{status}]")
    if args.require_gpu and not on_gpu:
        sys.exit("No GPU detected and --require-gpu set. Install GPU build:\n"
                 "  pip install \"audio-separator[gpu]\"\n"
                 "  (and a CUDA-enabled torch: pytorch.org/get-started)")
    todo = collect(in_path, out_root, ext, args.overwrite, args.mirror)
    if not todo:
        return
    failed = (run_roformer if args.engine == "roformer" else run_demucs)(args, todo, out_root, ext)
    print(f"\nDone. Instrumentals in {out_root}/")
    if failed:
        print(f"FAILED ({len(failed)}):")
        for f in failed:
            print("  " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
PYEOF

echo "=== [3/5] fetching playlist -> /workspace/mp3 (resumable) ==="
echo "    (skip this block and upload your own mp3s if you prefer your sorted set)"
mkdir -p /workspace/mp3 && cd /workspace/mp3
yt-dlp -x --audio-format mp3 --download-archive done.txt \
  -o '%(playlist_index)s - %(title)s.%(ext)s' \
  'https://www.youtube.com/playlist?list=PLb3DZrKKAtMo'
cd /workspace

echo "=== [4/5] removing vocals (GPU) -> /workspace/raw_beats ==="
python /workspace/remove_vocals.py \
  --input /workspace/mp3 --output /workspace/raw_beats \
  --mp3 --keep-vocals --require-gpu

echo "=== [5/5] packaging results ==="
cd /workspace && tar czf raw_beats.tgz raw_beats
echo ""
echo "DONE. Pull results to your PC:"
echo "   on the pod:   runpodctl send /workspace/raw_beats.tgz"
echo "   on your PC:   runpodctl receive <code-it-prints>"
echo "Then TERMINATE the pod in the RunPod console (billed per second)."
