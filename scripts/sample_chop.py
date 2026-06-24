#!/usr/bin/env python3
"""
sample_chop.py  -  Chop a sample into something new (Dilla / Kanye style), then
                   export 5 variations ready for MPC One+ and Ableton Push 2.

What it does
------------
Given a WAV/MP3, it detects chop points (transients or a beat grid), then builds
5 rearranged VARIATIONS using classic hip-hop sampling moves:
  dilla      off-grid swing + tiny per-hit pitch drift, quantize "off" (humanised)
  chipmunk   pitched-up soul chop (the Kanye "Otis"/"Through the Wire" move)
  stutter    rapid retrigger/roll on accents
  reverse    reversed-tail swells woven into the loop
  halftime   stretched, spaced-out placement

Per variation you get:
  master.wav            the rendered, rearranged chop loop
  slices/01.wav..NN     the individual chop one-shots ("stems") used, one per pad
  pattern.mid           the sequence that triggers the pads (note 36 = pad 1)
  master_sliced.wav     the master with embedded WAV cue markers (auto-slice)
  manifest.json         bpm, slice map, the step pattern
  mpc/program.xpm       an MPC drum program mapping the slices to pads (best-effort)
  ableton/              slices + pattern.mid + a Drum Rack .adg (with --adg) + how-to

Works standalone (just renders audio). For Ableton/Push: drop slices/ onto a Drum
Rack (Push 2 plays the pads), or import master_sliced.wav and Slice-to-MIDI. For
MPC One+: copy the variation folder to the MPC and load program.xpm, or drag the
slices onto pads.

Optional AI:
  --stems       split the source with audio-separator and chop the MELODIC stem
  --reimagine   AI-flip the master via audio2audio (Stable Audio) for a 6th, hybrid take

Usage
-----
  python sample_chop.py --input soul_loop.wav --bpm 90 --out chops
  python sample_chop.py --input vocal.mp3 --pads 16 --grid 16 --target both --adg --out chops
"""
import argparse
import gzip
import json
import os
import struct
import sys
import wave

import numpy as np


# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Chop points come from librosa onset detection (transient chops) or an even
#     beat grid (--grid N per bar). We cap to --pads slices (MPC/Drum-Rack = 16).
#   - "stems" here = the individual chop one-shots (one per pad), not source stems
#     (use --stems for true source separation of the melodic layer before chopping).
#   - Variations are deterministic per --seed so a run is reproducible.
#   - master_sliced.wav embeds a 'cue ' chunk so MPC/!some! DAWs can auto-find chops.
#   - .xpm (MPC) and .adg (Ableton) are best-effort; the GUARANTEED path is always
#     the numbered slices/ folder (drag onto pads) + pattern.mid.
#   - Targets Python 3.11; deps: numpy, librosa, soundfile, mido (requirements.txt).
# ---------------------------------------------------------------------------

SR = 44100
PAD_BASE_NOTE = 36  # MPC pad 1 / Ableton Drum Rack C1

# Top-10 sample-chopping producers -> a 5-variation style set + global feel params.
# styles draw from move primitives: dilla, chipmunk, stutter, reverse, halftime,
# loop (long minimally-rearranged phrase), gridchop (tight quantized).
# params: swing, density(lower=busier), pitch_bias(semitones), drift(micro pitch),
# dust(0-1 lowpass grit), quantize(snap, no swing).
PRODUCERS = {
    "j_dilla":       {"styles": ["dilla", "dilla", "chipmunk", "reverse", "stutter"],
                      "params": {"swing": 0.16, "density": 0.58, "pitch_bias": 0, "drift": True, "dust": 0.20, "quantize": False}},
    "kanye_west":    {"styles": ["chipmunk", "chipmunk", "stutter", "loop", "dilla"],
                      "params": {"swing": 0.08, "density": 0.55, "pitch_bias": 4, "drift": False, "dust": 0.10, "quantize": False}},
    "dj_premier":    {"styles": ["gridchop", "gridchop", "stutter", "reverse", "gridchop"],
                      "params": {"swing": 0.0, "density": 0.66, "pitch_bias": 0, "drift": False, "dust": 0.25, "quantize": True}},
    "9th_wonder":    {"styles": ["gridchop", "chipmunk", "loop", "gridchop", "stutter"],
                      "params": {"swing": 0.04, "density": 0.55, "pitch_bias": 2, "drift": False, "dust": 0.10, "quantize": True}},
    "rza":           {"styles": ["loop", "dilla", "reverse", "halftime", "stutter"],
                      "params": {"swing": 0.10, "density": 0.60, "pitch_bias": -2, "drift": True, "dust": 0.50, "quantize": False}},
    "madlib":        {"styles": ["dilla", "loop", "reverse", "stutter", "halftime"],
                      "params": {"swing": 0.18, "density": 0.50, "pitch_bias": 0, "drift": True, "dust": 0.45, "quantize": False}},
    "pete_rock":     {"styles": ["loop", "gridchop", "chipmunk", "loop", "stutter"],
                      "params": {"swing": 0.06, "density": 0.60, "pitch_bias": 1, "drift": False, "dust": 0.30, "quantize": False}},
    "just_blaze":    {"styles": ["chipmunk", "chipmunk", "loop", "stutter", "gridchop"],
                      "params": {"swing": 0.05, "density": 0.50, "pitch_bias": 5, "drift": False, "dust": 0.05, "quantize": False}},
    "the_alchemist": {"styles": ["loop", "halftime", "loop", "reverse", "dilla"],
                      "params": {"swing": 0.12, "density": 0.70, "pitch_bias": -1, "drift": True, "dust": 0.55, "quantize": False}},
    "knxwledge":     {"styles": ["dilla", "stutter", "chipmunk", "reverse", "halftime"],
                      "params": {"swing": 0.17, "density": 0.52, "pitch_bias": 1, "drift": True, "dust": 0.50, "quantize": False}},
}


def _dust(y, amount):
    """Cheap lowpass + grit (moving average) for that sampled/vinyl feel. 0..1."""
    if amount <= 0:
        return y
    k = max(1, int(2 + amount * 8))
    return np.convolve(y, np.ones(k) / k, mode="same").astype(np.float32)


def load(path, sr=SR):
    import librosa
    y, _ = librosa.load(os.path.expanduser(path.strip().strip('"').strip("'")), sr=sr, mono=True)
    peak = float(np.max(np.abs(y)) or 1.0)
    return (y / peak * 0.97).astype(np.float32)


def find_chops(y, sr, pads, grid):
    import librosa
    if grid > 0:
        # even grid: 'grid' slices per detected bar (fallback: whole-file grid)
        tempo = float(np.atleast_1d(librosa.beat.tempo(y=y, sr=sr))[0]) or 90.0
        bar = int(sr * 4 * 60.0 / tempo)
        n = max(pads, 1)
        step = max(1, (bar if bar < len(y) else len(y)) // grid)
        bounds = list(range(0, len(y), step))[: pads + 1]
    else:
        env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=env, sr=sr, units="samples", backtrack=True)
        onsets = [int(o) for o in onsets]
        if 0 not in onsets:
            onsets = [0] + onsets
        # keep the strongest 'pads' onsets if too many
        if len(onsets) > pads:
            strength = [env[min(len(env) - 1, int(o * len(env) / len(y)))] for o in onsets]
            keep = sorted(sorted(range(len(onsets)), key=lambda i: -strength[i])[:pads])
            onsets = [onsets[i] for i in keep]
        bounds = onsets + [len(y)]
    # build slices
    slices = []
    for i in range(len(bounds) - 1):
        a, b = bounds[i], bounds[i + 1]
        if b - a > int(0.03 * sr):       # ignore <30ms crumbs
            slices.append(y[a:b])
    return slices[:pads] if slices else [y]


def _env(seg, sr):
    # short fade in/out to avoid clicks on rearranged hits
    n = min(len(seg), int(0.004 * sr))
    if n > 1:
        seg = seg.copy()
        seg[:n] *= np.linspace(0, 1, n)
        seg[-n:] *= np.linspace(1, 0, n)
    return seg


def pitch(seg, sr, semi):
    if semi == 0:
        return seg
    import librosa
    return librosa.effects.pitch_shift(seg, sr=sr, n_steps=semi).astype(np.float32)


def stretch(seg, rate):
    if rate == 1.0:
        return seg
    import librosa
    return librosa.effects.time_stretch(seg, rate=rate).astype(np.float32)


def build_variation(style, slices, sr, bpm, bars, seed, p=None):
    """Return (master_audio, used_slices, pattern) for one style, shaped by the
    producer feel params p (swing/density/pitch_bias/drift/dust/quantize)."""
    p = p or {}
    rng = np.random.default_rng(seed)
    quantize = bool(p.get("quantize", False))
    swing = 0.0 if quantize else float(p.get("swing", 0.14))
    pitch_bias = float(p.get("pitch_bias", 0))
    drift = bool(p.get("drift", style == "dilla"))
    dens = p.get("density")
    step = int(sr * 60.0 / bpm / 4)
    steps = bars * 16
    out = np.zeros(steps * step + 4 * sr, dtype=np.float32)
    used, pattern = {}, []
    n = len(slices)
    base_thresh = {"dilla": 0.62, "chipmunk": 0.55, "stutter": 0.5, "reverse": 0.6,
                   "halftime": 0.78, "loop": 0.82, "gridchop": 0.5}

    for s in range(steps):
        if style == "loop":
            if s % 16 != 0:                 # one long phrase per bar
                continue
            idx = (s // 16) % n
        elif style == "gridchop":
            if s % 2 != 0:                  # tight 8th grid
                continue
            idx = (s // 2) % n
        else:
            thresh = dens if dens is not None else base_thresh.get(style, 0.6)
            if rng.random() > thresh and s % 4 != 0:
                continue
            idx = (s // 2 + int(rng.integers(0, max(1, n)))) % n if style != "halftime" else (s // 4) % n

        seg = slices[idx]
        if style == "loop":                 # stitch up to 3 consecutive slices into a phrase
            seg = np.concatenate([slices[(idx + k) % n] for k in range(min(3, n))])
        if style == "chipmunk":
            seg = pitch(seg, sr, float(rng.choice([3, 4, 5, 7])) + pitch_bias)
        elif style == "dilla" and drift:
            seg = pitch(seg, sr, float(rng.choice([-0.5, 0, 0, 0.5])))
        elif style == "reverse" and rng.random() < 0.5:
            seg = seg[::-1].copy()
        elif style == "halftime":
            seg = stretch(seg, 0.8)
        elif pitch_bias:
            seg = pitch(seg, sr, pitch_bias)
        seg = _env(np.asarray(seg, dtype=np.float32), sr)

        pos = s * step
        if (not quantize) and style in ("dilla", "stutter") and s % 2 == 1:
            pos += int(step * swing)
        if pos + len(seg) <= len(out):
            out[pos:pos + len(seg)] += seg[: len(out) - pos]
            used[idx] = slices[idx]
            pattern.append((s, idx))
        if style == "stutter" and s % 4 == 0:
            short = seg[: step // 4]
            for k in range(1, 4):
                p2 = pos + k * (step // 4)
                if p2 + len(short) <= len(out):
                    out[p2:p2 + len(short)] += short
                    pattern.append((s, idx))

    peak = float(np.max(np.abs(out)) or 1.0)
    out = (out / peak * 0.97).astype(np.float32)
    if p.get("dust"):
        out = _dust(out, float(p["dust"]))
        peak = float(np.max(np.abs(out)) or 1.0)
        out = (out / peak * 0.97).astype(np.float32)
    nz = np.where(np.abs(out) > 1e-4)[0]
    if len(nz):
        out = out[: nz[-1] + int(0.2 * sr)]
    return out, used, pattern


# ---------- exporters ----------
def write_wav(path, y, sr=SR):
    import soundfile as sf
    sf.write(path, y, sr, subtype="PCM_16")


def write_wav_with_cues(path, y, slice_starts, sr=SR):
    """Write a 16-bit WAV with a 'cue ' chunk at each slice start (auto-slice)."""
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()
    # standard fmt + data
    fmt = struct.pack("<HHIIHH", 1, 1, sr, sr * 2, 2, 16)
    cues = b""
    for i, start in enumerate(slice_starts):
        # id, position, 'data', chunkstart, blockstart, sampleoffset
        cues += struct.pack("<I4sIIII", i + 1, b"data", start, 0, 0, start)
    cue_chunk = struct.pack("<I", len(slice_starts)) + cues
    def chunk(cid, data):
        return cid + struct.pack("<I", len(data)) + data + (b"\x00" if len(data) % 2 else b"")
    body = b"WAVE" + chunk(b"fmt ", fmt) + chunk(b"cue ", cue_chunk) + chunk(b"data", pcm)
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(body)) + body)


def write_midi(path, pattern, bpm, sr=SR):
    import mido
    tpb = 480
    mid = mido.MidiFile(ticks_per_beat=tpb)
    tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(int(bpm))))
    evs = []
    for (stp, idx) in pattern:
        t = int(stp * tpb / 4)
        evs.append((t, "on", PAD_BASE_NOTE + idx))
        evs.append((t + tpb // 8, "off", PAD_BASE_NOTE + idx))
    evs.sort()
    last = 0
    for t, kind, note in evs:
        tr.append(mido.Message("note_on" if kind == "on" else "note_off",
                               note=note, velocity=100 if kind == "on" else 0,
                               time=max(0, t - last)))
        last = t
    mid.save(path)


def write_xpm(path, program_name, slice_files):
    """Best-effort MPC drum program (.xpm). The guaranteed path is dragging the
    slices onto pads; this just pre-maps them."""
    insts = []
    for i, fn in enumerate(slice_files):
        insts.append(
            f'    <Instrument number="{i}">\n'
            f'      <Layers><Layer number="1"><SampleName>{os.path.splitext(fn)[0]}</SampleName>'
            f'<SampleFile>{fn}</SampleFile><Volume>1.0</Volume></Layer></Layers>\n'
            f'    </Instrument>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<MPCVObject>\n'
           '  <Version><File_Version>2.1</File_Version><Application>MPC</Application></Version>\n'
           f'  <Program type="Drum">\n    <ProgramName>{program_name}</ProgramName>\n'
           f'    <PadNote>{PAD_BASE_NOTE}</PadNote>\n    <Instruments>\n'
           + "\n".join(insts) + '\n    </Instruments>\n  </Program>\n</MPCVObject>\n')
    open(path, "w", encoding="utf-8").write(xml)


def write_adg(path, rack_name, rel_slice_paths):
    """Best-effort Ableton Drum Rack preset (.adg = gzipped XML). Experimental -
    if your Live version rejects it, drag the slices/ folder onto a Drum Rack."""
    branches = []
    for i, rp in enumerate(rel_slice_paths):
        note = PAD_BASE_NOTE + i
        branches.append(f'''        <DrumBranchPreset Id="{i}">
          <BranchInfo><ReceivingNote Value="{127 - note}"/></BranchInfo>
          <DevicePresets><AbletonDevicePreset><Device><OriginalSimpler>
            <Player><MultiSampleMap><SampleParts><MultiSamplePart Id="0">
              <SampleRef><FileRef><RelativePathType Value="3"/>
                <RelativePath Value="{rp}"/><Path Value="{rp}"/>
                <Type Value="2"/></FileRef></SampleRef>
            </MultiSamplePart></SampleParts></MultiSampleMap></Player>
          </OriginalSimpler></Device></AbletonDevicePreset></DevicePresets>
        </DrumBranchPreset>''')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Ableton MajorVersion="5" MinorVersion="11.0_11300" SchemaChangeCount="3" Creator="Co-Produce AI">\n'
           '  <GroupDevicePreset>\n    <Device><DrumGroupDevice/></Device>\n    <BranchPresets>\n'
           + "\n".join(branches) + '\n    </BranchPresets>\n  </GroupDevicePreset>\n</Ableton>\n')
    with gzip.open(path, "wb") as f:
        f.write(xml.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="Chop a sample into 5 MPC/Ableton-ready variations.")
    ap.add_argument("--input", help="source WAV/MP3 to chop")
    ap.add_argument("--out", default="chops", help="output folder")
    ap.add_argument("--bpm", type=float, default=90, help="target BPM for the rearranged loops")
    ap.add_argument("--bars", type=int, default=2, help="bars per variation loop")
    ap.add_argument("--pads", type=int, default=16, help="max chop slices (MPC/Drum Rack = 16)")
    ap.add_argument("--grid", type=int, default=0, help="even slices per bar (0 = transient chops)")
    ap.add_argument("--styles", default="dilla,chipmunk,stutter,reverse,halftime",
                    help="comma list of the 5 variation styles (ignored if --producer set)")
    ap.add_argument("--producer", choices=list(PRODUCERS),
                    help="chop in a known producer's style (overrides --styles)")
    ap.add_argument("--list-producers", action="store_true", help="list producer styles and exit")
    ap.add_argument("--seed", type=int, default=7, help="reproducible randomness")
    ap.add_argument("--target", choices=["mpc", "ableton", "both"], default="both")
    ap.add_argument("--adg", action="store_true", help="also write an Ableton Drum Rack .adg (experimental)")
    ap.add_argument("--stems", action="store_true", help="AI: split source (audio-separator) and chop the melodic stem")
    ap.add_argument("--reimagine", action="store_true", help="AI: also write an audio2audio flip of each master")
    args = ap.parse_args()

    if args.list_producers:
        print("Producers (--producer):")
        for name, cfg in PRODUCERS.items():
            print(f"  {name:14} {' + '.join(cfg['styles'])}")
        return
    if not args.input:
        ap.error("--input is required (unless --list-producers)")

    params = {}
    if args.producer:
        params = PRODUCERS[args.producer]["params"]
        styles = PRODUCERS[args.producer]["styles"]
        print(f"[producer] {args.producer}: {' + '.join(styles)}")
    else:
        styles = [s.strip() for s in args.styles.split(",") if s.strip()][:5]

    src = args.input
    if args.stems:
        try:
            from audio_separator.separator import Separator
            tmp = os.path.join(args.out, "_stems"); os.makedirs(tmp, exist_ok=True)
            sep = Separator(output_dir=tmp); sep.load_model()
            outs = sep.separate(os.path.expanduser(src))
            mel = next((o for o in outs if "instrumental" in o.lower() or "other" in o.lower()), None)
            if mel:
                src = os.path.join(tmp, os.path.basename(mel))
                print(f"[stems] chopping melodic stem: {src}")
        except Exception as e:
            print(f"[stems] separation unavailable ({e}); chopping the full source", file=sys.stderr)

    y = load(src)
    slices = find_chops(y, SR, args.pads, args.grid)
    print(f"[chop] {len(slices)} slices from {os.path.basename(args.input)}")

    os.makedirs(args.out, exist_ok=True)

    for vi, style in enumerate(styles, 1):
        tag = (args.producer + "_") if args.producer else ""
        vdir = os.path.join(args.out, f"var{vi}_{tag}{style}")
        sdir = os.path.join(vdir, "slices"); os.makedirs(sdir, exist_ok=True)
        master, used, pattern = build_variation(style, slices, SR, args.bpm, args.bars, args.seed + vi, params)
        write_wav(os.path.join(vdir, "master.wav"), master)

        # export the used slices as numbered one-shots (the "stems")
        slice_files, starts, abs_pos = [], [], 0
        # write ALL slices (stable pad map), record starts for cue markers
        master_concat = np.zeros(0, dtype=np.float32)
        for i, seg in enumerate(slices):
            fn = f"{i+1:02d}.wav"
            write_wav(os.path.join(sdir, fn), _env(np.asarray(seg, np.float32), SR))
            slice_files.append(fn)
        # cue-marked master: re-derive slice starts on the master grid
        step = int(SR * 60.0 / args.bpm / 4)
        starts = sorted({int(stp * step) for (stp, _ ) in pattern})[: args.pads]
        write_wav_with_cues(os.path.join(vdir, "master_sliced.wav"), master, starts)
        write_midi(os.path.join(vdir, "pattern.mid"), pattern, args.bpm)

        json.dump({"style": style, "producer": args.producer, "bpm": args.bpm, "bars": args.bars,
                   "slices": slice_files, "pad_base_note": PAD_BASE_NOTE,
                   "pattern": pattern, "source": os.path.basename(args.input)},
                  open(os.path.join(vdir, "manifest.json"), "w"), indent=2)

        if args.target in ("mpc", "both"):
            mdir = os.path.join(vdir, "mpc"); os.makedirs(mdir, exist_ok=True)
            for fn in slice_files:
                import shutil; shutil.copy(os.path.join(sdir, fn), os.path.join(mdir, fn))
            write_xpm(os.path.join(mdir, "program.xpm"), f"CoProduce_{style}", slice_files)
        if args.target in ("ableton", "both"):
            adir = os.path.join(vdir, "ableton"); os.makedirs(adir, exist_ok=True)
            import shutil
            for fn in slice_files:
                shutil.copy(os.path.join(sdir, fn), os.path.join(adir, fn))
            shutil.copy(os.path.join(vdir, "pattern.mid"), os.path.join(adir, "pattern.mid"))
            if args.adg:
                write_adg(os.path.join(adir, "DrumRack.adg"), f"CoProduce_{style}", slice_files)
            open(os.path.join(adir, "HOWTO.txt"), "w").write(
                "Ableton / Push 2:\n"
                "1) Drag this folder's .wav files onto an empty Drum Rack (each lands on a pad).\n"
                "2) Drop pattern.mid into a MIDI clip to play the chop sequence (Push pads light up).\n"
                "   Or: drag master_sliced.wav in and use Slice to MIDI for a fresh Drum Rack.\n")

        if args.reimagine:
            try:
                import subprocess
                a2a = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio2audio.py")
                subprocess.run([sys.executable, a2a, "--input", os.path.join(vdir, "master.wav"),
                                "--prompt", f"hip hop {style} sample flip, dusty, vinyl", "--strength", "0.5",
                                "--variations", "1", "--out", os.path.join(vdir, "reimagined")], check=False)
            except Exception as e:
                print(f"[reimagine] skipped: {e}", file=sys.stderr)
        print(f"[var{vi}] {style}: master + {len(slice_files)} slices + pattern.mid -> {vdir}")

    print(f"\nDone -> {args.out}  ({len(styles)} variations). "
          "MPC: load each var*/mpc/program.xpm (or drag slices to pads). "
          "Ableton/Push: drag var*/ableton/ slices onto a Drum Rack + pattern.mid.")


if __name__ == "__main__":
    main()
