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
    ("\U0001F501 Remix (AI)", "remix.py", [
        F("--input", "Song/beat to remix", "text"),
        F("--genre", "Target genre", "choice", "dnb", ["hiphop", "rockmetal", "dubstep", "dnb"]),
        F("--mode", "Mode", "choice", "full", ["full", "mashup"]),
        F("--current", "(mashup) current genre", "text"),
        F("--strength", "Strength 0-1 (blank=auto)", "num", None),
        F("--variations", "Variations", "num", 3),
        F("--pretrained", "HF model id (or use ckpt below)", "text", "stabilityai/stable-audio-open-1.0"),
        F("--model-config", "model_config.json (your model)", "text"),
        F("--ckpt", "your ckpt (optional)", "text"),
        F("--out", "Output folder", "text"),
    ]),
    ("Scan plugins", "plugin_scan.py", [
        F("--dirs", "Extra folder to scan (optional)", "text"),
    ]),
    ("VST3 instrument (MIDI\u2192audio)", "vst_instrument.py", [
        F("--vst3", "Instrument .vst3 path", "text", info="C:/Program Files/Common Files/VST3/Battery 4.vst3"),
        F("--midi", "Input MIDI file", "text"),
        F("--out", "Output WAV", "text"),
        F("--chain", "Effect chain JSON (optional)", "text"),
        F("--duration", "Seconds (blank = auto)", "num", None),
    ]),
    ("Vocal guide (ACE Studio)", "vocal_guide.py", [
        F("--beat", "Beat audio (reads BPM/key)", "text"),
        F("--bpm", "BPM (blank if --beat given)", "num", None),
        F("--key", "Key e.g. F minor", "text"),
        F("--lyrics", "Lyrics .txt", "text"),
        F("--style", "Style", "choice", "rap", ["rap", "sung"]),
        F("--out", "Output prefix", "text"),
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


THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.orange,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    body_background_fill="#0B162A",
    body_background_fill_dark="#0B162A",
    body_text_color="#EAF0F7",
    body_text_color_subdued="#9FB3C8",
    block_background_fill="#0F2038",
    block_border_color="#1D3357",
    block_border_width="1px",
    block_radius="14px",
    block_label_text_color="#FF8A3D",
    block_title_text_color="#FF8A3D",
    input_background_fill="#13243F",
    input_border_color="#26405F",
    input_border_color_focus="#C83803",
    button_primary_background_fill="#C83803",
    button_primary_background_fill_hover="#E2540F",
    button_primary_text_color="#FFFFFF",
    button_secondary_background_fill="#1D3357",
    button_secondary_text_color="#EAF0F7",
    slider_color="#C83803",
)

CSS = """
.gradio-container {max-width:1280px !important; margin:auto;}
#hdr {background:linear-gradient(120deg,#0B162A 0%,#13294B 100%);
      border:1px solid #1D3357; border-radius:16px; padding:20px 26px; margin-bottom:14px;
      border-left:6px solid #C83803;}
#hdr h1 {margin:0; font-size:26px; font-weight:800; letter-spacing:.3px; color:#FFFFFF;}
#hdr .accent {color:#FF8A3D;}
#hdr p {margin:6px 0 0; color:#9FB3C8; font-size:13px;}
.tabitem {padding-top:8px;}
button.primary, .primary {font-weight:700 !important; letter-spacing:.2px;}
footer {display:none !important;}
.logbox textarea {background:#06101F !important; color:#7CF2B0 !important;
      font-family:'JetBrains Mono',monospace !important; font-size:12.5px !important;
      border-radius:10px !important;}
label span {font-weight:600 !important;}
.tab-nav button {font-weight:600 !important;}
.tab-nav button.selected {color:#FF8A3D !important; border-bottom-color:#C83803 !important;}
"""

HEADER = """
<div id="hdr">
  <h1>\U0001F3B9 Beat Toolkit <span class="accent">/ Studio Dashboard</span></h1>
  <p>Train your own hip-hop model and run the full pipeline \u2014 organize \u00B7 separate \u00B7 analyze \u00B7 tag \u00B7 caption \u00B7 prepare \u00B7 train \u00B7 generate \u00B7 process \u00B7 pack. Each tab runs a step and streams its log live.</p>
</div>
"""


def build_ui():
    with gr.Blocks(title="Beat Toolkit \u2014 Dashboard", theme=THEME, css=CSS) as app:
        gr.HTML(HEADER)
        with gr.Tab("\u2699\uFE0F  Settings"):
            gr.Markdown("### Environment\nPoint the dashboard at your Python and scripts folder.")
            py = gr.Textbox(CONFIG["python"], label="Python executable")
            sd = gr.Textbox(CONFIG["scripts_dir"], label="Scripts folder")
            save = gr.Button("Save settings", variant="primary")
            saved = gr.Markdown()
            def _save(p, s):
                CONFIG["python"], CONFIG["scripts_dir"] = p, s
                return "\u2705 Saved."
            save.click(_save, [py, sd], saved)

        for label, script, fields in TOOLS:
            with gr.Tab(label):
                gr.Markdown(f"#### {label}\n<span style='color:#9FB3C8'>Runs <code>{script}</code>. "
                            "Fill what you need, then Run \u2014 the log streams on the right.</span>")
                with gr.Row():
                    with gr.Column(scale=1):
                        comps = []
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
                        run = gr.Button(f"\u25B6  Run {label}", variant="primary")
                    with gr.Column(scale=1):
                        out = gr.Textbox(label="Live log", lines=24, max_lines=24,
                                         autoscroll=True, elem_classes=["logbox"])
                run.click(lambda *vals, _f=fields, _s=script: (yield from run_tool(_f, _s, *vals)),
                          inputs=comps, outputs=out)


        with gr.Tab("\U0001F50C Plugins"):
            gr.Markdown("#### Plugin browser\nRun **Scan plugins** first, then pick one to copy its path into vst_chain / vst_instrument.")
            import json as _json
            cat_path = ROOT / "plugins_catalog.json"
            def _load_cat():
                if cat_path.exists():
                    try:
                        d = _json.loads(cat_path.read_text(encoding="utf-8"))
                        return gr.Dropdown(choices=[f"{c['name']}  [{c['format']}/{c['kind']}]  ::  {c['path']}" for c in d])
                    except Exception:
                        pass
                return gr.Dropdown(choices=["(no catalog yet - run Scan plugins)"])
            pick = gr.Dropdown(label="Installed plugins", choices=[], interactive=True)
            reload_btn = gr.Button("Load / refresh catalog", variant="primary")
            chosen_path = gr.Textbox(label="Selected plugin path (copy this)")
            reload_btn.click(_load_cat, None, pick)
            pick.change(lambda s: s.split("::")[-1].strip() if s and "::" in s else "", pick, chosen_path)

        with gr.Tab("\U0001F3A7  Audition"):
            gr.Markdown("#### Audition + Remix\nList audio, click a file to play \u2014 then remix it into another genre.")
            folder = gr.Textbox(label="Folder", value=str(ROOT))
            with gr.Row():
                listing = gr.Dropdown(label="Audio files", choices=[], interactive=True, scale=3)
                refresh = gr.Button("List audio", variant="primary", scale=1)
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
            gr.Markdown("---\n##### \U0001F501 Remix the selected file")
            with gr.Row():
                rgenre = gr.Dropdown(["hiphop", "rockmetal", "dubstep", "dnb"], value="dnb", label="Genre")
                rmode = gr.Dropdown(["full", "mashup"], value="full", label="Mode")
                rmodel = gr.Textbox("stabilityai/stable-audio-open-1.0", label="Model (HF id or ckpt path)")
            rout = gr.Textbox(str(ROOT / "remixes"), label="Output folder")
            rbtn = gr.Button("\U0001F501  Remix selected", variant="primary")
            rlog = gr.Textbox(label="Remix log", lines=12, elem_classes=["logbox"])
            def _remix(src, genre, mode, model, outd):
                if not src:
                    yield "Pick a file in the list above first."
                    return
                fields = [
                    {"flag": "--input", "kind": "text"}, {"flag": "--genre", "kind": "text"},
                    {"flag": "--mode", "kind": "text"}, {"flag": "--out", "kind": "text"},
                ]
                vals = [src, genre, mode, outd]
                mid = str(model).strip()
                if mid.lower().endswith(".ckpt"):
                    fields += [{"flag": "--ckpt", "kind": "text"}]; vals += [mid]
                else:
                    fields += [{"flag": "--pretrained", "kind": "text"}]; vals += [mid]
                yield from run_tool(fields, "remix.py", *vals)
            rbtn.click(_remix, [listing, rgenre, rmode, rmodel, rout], rlog)
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
