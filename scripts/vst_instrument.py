#!/usr/bin/env python3
"""
vst_instrument.py  -  Render MIDI through an instrument VST3, headless.

Companion to vst_chain.py (which processes audio through EFFECT plugins). This
loads an INSTRUMENT plugin (synth/sampler) and renders a MIDI file to audio -
no DAW. Turn beat_builder.py's pattern.mid or vocal_guide.py's flow MIDI into
real audio using your own plugins (Battery 4, Massive, FM8, Kontakt, etc.),
then character-process the result with vst_chain.py.

    pip install pedalboard mido soundfile

Discover a plugin's parameters / dial a sound by ear:
    python vst_instrument.py --list-params "C:/Program Files/Common Files/VST3/Massive X.vst3"
    python vst_instrument.py --vst3 "C:/.../Massive X.vst3" --midi bass.mid --edit --out bass.wav

Render:
    python vst_instrument.py --vst3 "C:/Program Files/Common Files/VST3/Battery 4.vst3" \
        --midi beats/boom_bap_92bpm_01/pattern.mid --out kit.wav
    # then optionally: vst_chain.py --input kit_folder --output out --chain configs/vst_chains/dusty_boombap.json

Notes:
- Pick a preset/kit inside the plugin via --edit (opens its GUI; close to bake in).
- Some instruments need a preset loaded to make sound (e.g. Kontakt needs an .nki).
- Multi-timbral kits (Battery) map MIDI notes to pads; pattern.mid uses GM drum
  notes (kick 36, snare 38, hat 42...) - line your kit up to those or remap.
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Renders MIDI through an INSTRUMENT plugin headless via pedalboard (MIDI msgs carry absolute seconds).
#   - Plugins load at DEFAULT state - use --edit to pick a preset/kit, or it may be silent (Kontakt needs an .nki).
#   - --chain runs an effect chain on the rendered audio in the same pass.
# ---------------------------------------------------------------------------
import argparse
import sys
from pathlib import Path


def midi_to_messages(midi_path):
    """Flatten a MIDI file into mido messages with ABSOLUTE time in seconds."""
    import mido
    mid = mido.MidiFile(str(midi_path))
    tempo = 500000  # default 120 BPM
    abs_t = 0.0
    out = []
    for msg in mido.merge_tracks(mid.tracks):
        abs_t += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
        if msg.type == "set_tempo":
            tempo = msg.tempo
        elif msg.type in ("note_on", "note_off"):
            out.append(msg.copy(time=abs_t))
    end = (out[-1].time + 2.0) if out else 2.0
    return out, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vst3", help="Instrument plugin .vst3 path")
    ap.add_argument("--midi", help="Input MIDI file")
    ap.add_argument("--out", help="Output WAV")
    ap.add_argument("--duration", type=float, help="Seconds (default: MIDI length + 2s tail)")
    ap.add_argument("--sample-rate", type=int, default=44100)
    ap.add_argument("--preset", help="Plugin preset file (.vstpreset) to load")
    ap.add_argument("--params", help='JSON of {param_name: value} to set')
    ap.add_argument("--edit", action="store_true", help="Open the plugin GUI to pick a sound, then render")
    ap.add_argument("--chain", help="Optional effect-chain JSON (same format as vst_chain configs) "
                    "to run on the rendered audio in the same step")
    ap.add_argument("--list-params", metavar="VST3", help="Print a plugin's parameter names and exit")
    args = ap.parse_args()

    from pedalboard import load_plugin

    if args.list_params:
        p = load_plugin(args.list_params)
        print(f"Parameters for {args.list_params}:")
        for name, val in p.parameters.items():
            print(f"  {name:40s} = {val}")
        return

    if not (args.vst3 and args.midi and args.out):
        ap.error("--vst3, --midi and --out are required (or use --list-params).")

    import soundfile as sf

    inst = load_plugin(args.vst3)
    if args.preset:
        inst.load_preset(args.preset)
    if args.params:
        import json
        for k, v in json.loads(args.params).items():
            setattr(inst, k, v)
    if args.edit:
        print("Opening plugin editor - pick your sound/preset, then close the window...")
        inst.show_editor()

    messages, end = midi_to_messages(args.midi)
    duration = args.duration or end
    if not messages:
        sys.exit("No note events found in the MIDI file.")
    print(f"Rendering {len(messages)} MIDI events -> {duration:.1f}s @ {args.sample_rate} Hz")
    audio = inst(messages, duration=duration, sample_rate=args.sample_rate)  # (channels, samples)
    if args.chain:
        import json
        import pedalboard
        from pedalboard import Pedalboard, load_plugin
        cfg = json.loads(Path(args.chain).read_text(encoding="utf-8"))
        fx = []
        for item in cfg.get("chain", []):
            if "vst3" in item:
                fp = load_plugin(item["vst3"])
                if item.get("preset"):
                    fp.load_preset(item["preset"])
                for k, v in item.get("params", {}).items():
                    setattr(fp, k, v)
                fx.append(fp)
            elif "builtin" in item:
                fx.append(getattr(pedalboard, item["builtin"])(**item.get("params", {})))
        if fx:
            print(f"Applying {len(fx)}-stage effect chain from {args.chain}")
            audio = Pedalboard(fx)(audio, args.sample_rate)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.out, audio.T, args.sample_rate, subtype="PCM_24")
    print(f"Wrote {args.out}")
    print("Tip: character-process it with vst_chain.py, or slice/post with postprocess.py")


if __name__ == "__main__":
    main()
