#!/usr/bin/env python3
"""
validate_dataset.py
Pre-flight checks before paying for GPU time. Verifies every WAV in the prepared
dataset is readable, 44.1 kHz stereo, non-clipping, within duration bounds, and
has a JSON sidecar with a non-empty prompt. Prints a summary report.

Usage:
    python validate_dataset.py --dataset dataset
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Pre-flight BEFORE paying for GPU: fails on wrong SR, silence, empty prompts, over-window length.
#   - 47 s is the Stable Audio Open window; treat clipping warnings (peak>=0.999) seriously.
# ---------------------------------------------------------------------------
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf

TARGET_SR = 44100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--min-seconds", type=float, default=0.05)
    ap.add_argument("--max-seconds", type=float, default=47.0)
    ap.add_argument("--quick", action="store_true", help="header-only (skip full audio read / clip+silence check) - fast")
    ap.add_argument("--prune", action="store_true", help="DELETE silent / too-short clips (and their .json) instead of erroring")
    args = ap.parse_args()

    root = Path(args.dataset)
    wavs = sorted(root.rglob("*.wav"))
    if not wavs:
        sys.exit("No WAVs found.")
    print(f"Validating {len(wavs)} WAVs in {root} ..."          + ("  (--quick: header-only)" if args.quick else "  (reading audio; ~minutes for thousands of files)"), flush=True)

    errors, warnings, pruned = [], [], []
    kinds, durations = Counter(), []
    with_bpm = with_key = 0
    def _drop(w, why):
        pruned.append(f"{w.name}: {why}")
        try:
            w.unlink(missing_ok=True); w.with_suffix(".json").unlink(missing_ok=True)
        except Exception:
            pass

    try:
        from tqdm import tqdm as _tqdm
        _it = _tqdm(wavs, unit="file")
    except Exception:
        _it = wavs
    for wav in _it:
        try:
            info = sf.info(str(wav))
        except Exception as e:
            errors.append(f"{wav}: unreadable ({e})")
            continue
        if info.samplerate != TARGET_SR:
            errors.append(f"{wav}: sample rate {info.samplerate}, expected {TARGET_SR}")
        if info.channels != 2:
            errors.append(f"{wav}: {info.channels} channels, expected 2")
        dur = info.frames / info.samplerate
        durations.append(dur)
        if dur < args.min_seconds:
            (_drop(wav, f"too short {dur:.2f}s") if args.prune else errors.append(f"{wav}: too short ({dur:.2f}s)"))
            if args.prune:
                continue
        if dur > args.max_seconds:
            errors.append(f"{wav}: too long ({dur:.2f}s) - exceeds model window")

        if not args.quick:
            y, _ = sf.read(str(wav))
            peak = float(np.abs(y).max()) if y.size else 0.0
            if peak >= 0.999:
                warnings.append(f"{wav}: possible clipping (peak {peak:.3f})")
            if peak < 1e-4:
                if args.prune:
                    _drop(wav, "silent"); continue
                errors.append(f"{wav}: silent")

        sidecar = wav.with_suffix(".json")
        if not sidecar.exists():
            errors.append(f"{wav}: missing JSON sidecar")
            continue
        try:
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{sidecar}: invalid JSON ({e})")
            continue
        if not meta.get("prompt", "").strip():
            errors.append(f"{sidecar}: empty prompt")
        kinds[meta.get("kind", "unknown")] += 1
        with_bpm += 1 if meta.get("bpm") else 0
        with_key += 1 if meta.get("key") else 0

    total_h = sum(durations) / 3600
    print(f"\n=== Dataset report: {root} ===")
    print(f"Files: {len(wavs)}   Total audio: {total_h:.2f} h")
    print(f"Kinds: {dict(kinds)}")
    print(f"With BPM: {with_bpm}   With key: {with_key}")
    if durations:
        print(f"Duration: min {min(durations):.2f}s / median {sorted(durations)[len(durations)//2]:.2f}s / max {max(durations):.2f}s")
    print(f"\nWarnings: {len(warnings)}")
    for w in warnings[:20]:
        print("  " + w)
    if pruned:
        print(f"\nPruned (deleted): {len(pruned)}")
        for x in pruned[:20]:
            print("  " + x)
    print(f"\nErrors: {len(errors)}")
    for e in errors[:50]:
        print("  " + e)
    if errors:
        sys.exit("\nFIX ERRORS BEFORE TRAINING.")
    print("\nDataset is ready for training.")


if __name__ == "__main__":
    main()
