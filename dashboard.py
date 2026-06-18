#!/usr/bin/env python3
"""
dashboard.py  -  Local web dashboard for the whole toolkit (Gradio).

One control panel for every stage: organize -> separate -> analyze -> tag ->
caption -> prepare -> validate -> train -> generate -> post -> pack -> provenance,
plus beat builder, full songs, VST chains, and an audio auditioner. Each tool
gets a form; Run launches the script as a job and streams its live log; results
can be browsed and played back.

Run:
    pip install gradio
    python dashboard.py
Then open the printed URL (default http://127.0.0.1:7860).

GPU jobs (training/generation) run wherever you launch this — local GPU, or run
this dashboard ON a cloud pod to drive its GPU. Long jobs stream logs live.
"""
import subprocess
import sys
from pathlib import Path

import gradio as gr

# --- Fix a known gradio_client bug on Python 3.9: schema fields that are bool
# (e.g. additionalProperties: true) crash get_type with
# "TypeError: argument of type 'bool' is not iterable". Guard both functions. ---
try:
    import gradio_client.utils as _gcu
    _o1 = _gcu._json_schema_to_python_type
    def _safe1(schema, defs=None):
        if isinstance(schema, bool):
            return "Any"
        return _o1(schema, defs)
    _gcu._json_schema_to_python_type = _safe1
    _o2 = _gcu.get_type
    def _safe2(schema):
        if isinstance(schema, bool):
            return "Any"
        return _o2(schema)
    _gcu.get_type = _safe2
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
CONFIG = {"python": sys.executable, "scripts_dir": str(SCRIPTS)}

# ---- field kinds: text, dir, file, num, bool, choice, positional ----
def F(flag, label, kind="text", default=None, choices=None, info=""):
    return {"flag": flag, "label": label, "kind": kind, "default": default,
            "choices": choices, "info": info}

TOOLS = [
    ("Organize soundbank", "organize_soundbank.py", [
        F("--input", "Input folder (messy library)", "dir", info="e.g. F:\\Sound Bank"),
        F("--output", "Output folder", "dir", info="e.g. F:\\Sound Bank Organized"),
        F("--dry-run", "Dry run (classify only, move nothing)", "bool", True),
        F("--move", "Move instead of copy", "bool", False),
        F("--resume", "Resume (skip existing)", "bool", True),
        F("--ai-tags", "Run CLAP zero-shot tagging after", "bool", False),
        F("--min-confidence", "Min confidence", "num", 0.5),
    ]),
    ("Remove vocals", "remove_vocals.py", [
        F("--input", "Input file/folder", "dir"),
        F("--output", "Output folder", "dir"),
        F("--engine", "Engine", "choice", "roformer", ["roformer", "demucs"]),
        F("--mp3", "Output MP3", "bool", True),
        F("--keep-vocals", "Also keep vocal stems", "bool", False),
        F("--require-gpu", "Require GPU (abort on CPU)", "bool", True),
        F("--mirror", "Mirror subfolder structure", "bool", False),
    ]),
    ("Deep listen (analyze)", "deep_listen.py", [
        F("--input", "Input file/folder", "dir"),
        F("--out", "Reports out folder", "dir"),
        F("--for-captions", "Slim output for captions", "bool", True),
        F("--no-events", "Skip PANNs sound events", "bool", False),
        F("--no-vibe", "Skip CLAP mood/genre", "bool", False),
        F("--resume", "Resume", "bool", True),
    ]),
    ("Auto-tag (open vocab)", "auto_tag.py", [
        F("--stems-dir", "Stems folder (*_instrumental)", "dir"),
        F("--full-root", "Full-songs folder (optional)", "dir"),
        F("--source", "Source", "choice", "beat", ["full", "vocals", "beat", "all"]),
        F("--engine", "Engine", "choice", "auto", ["auto", "qwen3-omni", "qwen2-audio", "clap"]),
        F("--limit", "Limit (0 = all)", "num", 0),
        F("--shuffle", "Random selection order", "bool", True),
        F("--resume", "Resume", "bool", True),
    ]),
    ("Build captions", "build_captions.py", [
        F("--beats", "Beats folder", "dir"),
        F("--reports", "Reports folder (optional)", "dir"),
        F("--genre-threshold", "Subgenre confidence threshold", "num", 0.35),
        F("--dry-run", "Dry run", "bool", True),
        F("--resume", "Resume", "bool", False),
    ]),
    ("Prepare dataset", "prepare_dataset.py", [
        F("--input", "Input (beats/library)", "dir"),
        F("--output", "Dataset output", "dir"),
        F("--name-contains", "Only files containing", "text", "_instrumental"),
        F("--max-seconds", "Max clip seconds", "num", 40),
        F("--bpm-min", "BPM fold min", "num", 60),
        F("--bpm-max", "BPM fold max", "num", 180),
    ]),
    ("Validate dataset", "validate_dataset.py", [
        F("--dataset", "Dataset folder", "dir"),
    ]),
    ("SA3 workflow", "sa3_workflow.py", [
        F("", "Subcommand", "positional", "song", choices=["prepare", "plan", "flip", "fill", "extend", "song"]),
        F("--model", "Model", "choice", "medium", ["small-music", "medium", "medium-base"]),
        F("--lora", "LoRA .safetensors (optional)", "file"),
        F("--prompt", "Prompt", "text"),
        F("--plan", "Pack plan JSON (for 'plan')", "file"),
        F("--input", "Input wav (flip/fill/extend)", "file"),
        F("--duration", "Duration sec (song/flip)", "num", 180),
        F("--dataset", "Dataset dir (for 'prepare')", "dir"),
        F("--data-dir", "SA3 data out (for 'prepare')", "dir"),
        F("--out", "Output", "text"),
    ]),
    ("Generate (SAO)", "generate.py", [
        F("--model-config", "model_config.json", "file"),
        F("--ckpt", "Unwrapped ckpt", "file"),
        F("--pretrained", "Or HF model id", "text"),
        F("--plan", "Pack plan JSON", "file"),
        F("--out", "Output folder", "dir"),
        F("--steps", "Steps", "num", 100),
        F("--cfg", "CFG scale", "num", 7),
    ]),
    ("Audio-to-audio (flip)", "audio2audio.py", [
        F("--model-config", "model_config.json", "file"),
        F("--ckpt", "ckpt", "file"),
        F("--pretrained", "Or HF id", "text"),
        F("--input", "Source wav", "file"),
        F("--prompt", "Prompt", "text"),
        F("--strength", "Strength 0-1", "num", 0.5),
        F("--variations", "Variations", "num", 4),
        F("--out", "Output folder", "dir"),
    ]),
    ("Post-process", "postprocess.py", [
        F("--input", "Generated folder", "dir"),
        F("--output", "Processed folder", "dir"),
        F("--lufs", "Target LUFS (loops)", "num", -14),
        F("--bpm-min", "BPM min", "num", 60),
        F("--bpm-max", "BPM max", "num", 180),
    ]),
    ("Beat builder", "beat_builder.py", [
        F("--library", "Organized library", "dir"),
        F("--style", "Style", "choice", "boom_bap",
          ["boom_bap", "trap", "drill", "lofi", "rock", "metal", "dbeat", "dubstep", "dnb", "amen"]),
        F("--bpm", "BPM", "num", 92),
        F("--bars", "Bars", "num", 4),
        F("--count", "How many beats", "num", 8),
        F("--rotate", "Rotate samples per hit", "bool", False),
        F("--groove", "Groove template JSON", "file"),
        F("--melodic", "Melodic loops folder", "dir"),
        F("--out", "Output", "dir"),
    ]),
    ("VST3 chain", "vst_chain.py", [
        F("--input", "Input folder", "dir"),
        F("--output", "Output folder", "dir"),
        F("--chain", "Chain JSON", "file"),
    ]),
    ("Build pack", "build_pack.py", [
        F("--input", "Processed folder", "dir"),
        F("--pack-name", "Pack name", "text"),
        F("--out", "Packs out folder", "dir", "packs"),
    ]),
    ("Provenance", "provenance.py", [
        F("--pack", "Built pack folder", "dir"),
        F("--dataset", "Dataset dir", "dir"),
        F("--generated", "Generated dir", "dir"),
        F("--run-name", "Training run name", "text"),
        F("--statement", "Rights statement", "text"),
    ]),
    ("Full song (HeartMuLa)", "song_generate.py", [
        F("--heartlib", "heartlib repo path", "dir"),
        F("--ckpt", "ckpt dir", "dir"),
        F("--lyrics-file", "Lyrics .txt", "file"),
        F("--tags", "Style tags (comma,no,spaces)", "text"),
        F("--duration", "Minutes", "num", 3),
        F("--out", "Output", "text"),
        F("--lazy-load", "Lazy load (low VRAM)", "bool", True),
    ]),
]


def run_tool(spec_fields, script, *values):
    args = []
    for field, val in zip(spec_fields, values):
        kind = field["kind"]
        if kind == "bool":
            if val:
                args.append(field["flag"])
        elif kind == "positional":
            if val not in (None, ""):
                args.append(str(val))
        else:
            if val not in (None, "", []):
                args += [field["flag"], str(val)]
    cmd = [CONFIG["python"], str(Path(CONFIG["scripts_dir"]) / script)] + args
    log = "$ " + " ".join(cmd) + "\n\n"
    yield log
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, cwd=str(ROOT))
    except Exception as e:
        yield log + f"\nFAILED TO START: {e}"
        return
    for line in iter(proc.stdout.readline, ""):
        log += line
        yield log[-12000:]  # keep last ~12k chars visible
    proc.wait()
    yield log[-12000:] + f"\n\n=== exit code {proc.returncode} ==="


def build_ui():
    with gr.Blocks(title="Hip-Hop Beat Toolkit") as app:
        gr.Markdown("# 🎛️ Hip-Hop Beat Toolkit — Dashboard\nDrive the full pipeline. "
                    "Each tab runs a step and streams its log. GPU steps run wherever this app runs.")
        with gr.Tab("⚙️ Settings"):
            py = gr.Textbox(CONFIG["python"], label="Python executable")
            sd = gr.Textbox(CONFIG["scripts_dir"], label="Scripts folder")
            save = gr.Button("Save settings")
            saved = gr.Markdown()
            def _save(p, s):
                CONFIG["python"], CONFIG["scripts_dir"] = p, s
                return "Saved."
            save.click(_save, [py, sd], saved)

        for label, script, fields in TOOLS:
            with gr.Tab(label):
                comps = []
                with gr.Row():
                    with gr.Column():
                        for f in fields:
                            k = f["kind"]
                            if k == "bool":
                                comps.append(gr.Checkbox(value=bool(f["default"]), label=f["label"]))
                            elif k in ("choice", "positional") and f["choices"]:
                                comps.append(gr.Dropdown(choices=f["choices"], value=f["default"],
                                                         label=f["label"], allow_custom_value=(k == "positional")))
                            elif k == "num":
                                comps.append(gr.Number(value=f["default"], label=f["label"]))
                            else:
                                comps.append(gr.Textbox(value=f["default"] or "", label=f["label"], info=f["info"]))
                        run = gr.Button(f"Run {label}", variant="primary")
                    with gr.Column():
                        out = gr.Textbox(label="Live log", lines=22, max_lines=22, autoscroll=True)
                run.click(lambda *vals, _f=fields, _s=script: (yield from run_tool(_f, _s, *vals)),
                          inputs=comps, outputs=out)

        with gr.Tab("🎧 Audition"):
            gr.Markdown("Pick a folder, list audio, then click a file to play it.")
            folder = gr.Textbox(label="Folder", value=str(ROOT))
            listing = gr.Dropdown(label="Audio files", choices=[], interactive=True)
            refresh = gr.Button("List audio in folder")
            player = gr.Audio(label="Preview")
            def _list(folder_path):
                base = Path(folder_path)
                if not base.is_dir():
                    return gr.Dropdown(choices=[])
                files = [str(x) for x in sorted(base.rglob("*"))
                         if x.suffix.lower() in (".wav", ".mp3", ".flac", ".aif", ".aiff", ".ogg", ".m4a")]
                return gr.Dropdown(choices=files[:2000])
            refresh.click(_list, folder, listing)
            listing.change(lambda f: f, listing, player)
    return app


if __name__ == "__main__":
    ui = build_ui().queue(default_concurrency_limit=4)
    # A VPN/proxy (e.g. AirVPN) can make gradio's localhost check fail. Try a
    # normal local launch first; if that errors, fall back to a share link.
    try:
        ui.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
    except Exception as e:
        print(f"Local launch failed ({e}); retrying with a public share link...")
        ui.launch(share=True, inbrowser=True)
