#!/usr/bin/env python3
"""
dashboard.py  -  Local web dashboard for the whole toolkit (Gradio).

One control panel for every stage: organize -> separate -> analyze -> tag ->
caption -> prepare -> validate -> train -> generate -> post -> pack -> provenance,
plus beat builder, full songs, VST chains, a Creative Lab, an audio auditioner,
a Cloud/Deploy reference, and a Server/API tab that can launch the SaaS API,
worker, tests, and drive the API client. Each tool streams its live log; results
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

# --- (legacy) Python 3.9 gradio_client shim; harmless no-op on 3.11+: bool schema fields
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
    ("\U0001F39A\uFE0F MP3 \u2192 WAV", "mp3_to_wav.py", [
        F("--input", "File/folder of mp3s", "text"),
        F("--output", "Output folder", "text"),
        F("--sample-rate", "Resample Hz (0=keep)", "num", 0),
        F("--bit-depth", "Bit depth", "choice", "16", ["16", "24", "32"]),
        F("--mirror", "Mirror subfolders", "bool", True),
        F("--resume", "Skip existing", "bool", True),
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
        F("--engine", "Engine", "choice", "auto", ["auto", "heuristic", "qwen3-omni", "qwen2-audio", "clap"], info="heuristic = local DSP, no model/GPU"),
        F("--limit", "Limit (0 = all)", "num", 0),
        F("--shuffle", "Random selection order", "bool", True),
        F("--resume", "Resume", "bool", True),
    ]),
    ("Genius metadata", "genius_lookup.py", [
        F("--beats", "Beats folder", "dir"),
        F("--token", "Genius API token (or GENIUS_TOKEN env)", "text"),
        F("--min-score", "Min match score 0-1", "num", 0.5),
        F("--delay", "Seconds between API calls", "num", 0.5),
        F("--limit", "Limit (0 = all)", "num", 0),
        F("--resume", "Resume (skip enriched)", "bool", True),
    ]),
    ("\U0001F3B5 Spotify playlist meta", "playlist_meta.py", [
        F("--playlist", "Playlist URL / URI / id", "text", info="-pl / --playlist"),
        F("--format", "Output format", "choice", "md", ["md", "json", "csv"]),
        F("--sort", "Sort", "choice", "added", ["added", "popularity", "release", "name"]),
        F("--audio-features", "Add BPM/key/energy", "bool", True),
        F("--samples", "Add sample data (Genius)", "bool", False),
        F("--whosampled", "Also WhoSampled (RapidAPI)", "bool", False),
        F("--limit", "Limit (0 = all)", "num", 0),
        F("--out", "Save report to file", "text"),
    ]),
    ("\U0001F3A7 Genre playlists", "genre_playlists.py", [
        F("--genre", "Genre (or 'all')", "choice", "hiphop",
          ["hiphop", "boom_bap", "trap", "drill", "lofi", "rock", "metal", "rockmetal", "dubstep", "dnb", "all"]),
        F("--limit", "Results per platform", "num", 5),
        F("--format", "Format", "choice", "md", ["md", "json"]),
        F("--out", "Save to file", "text"),
    ]),
    ("\U0001F4D1 Song catalog (Genius)", "playlist_catalog.py", [
        F("--json", "playlist_meta JSON", "text", info="playlist_full.json"),
        F("--out", "Catalog folder", "text", "catalog"),
        F("--limit", "Limit (0 = all)", "num", 0),
        F("--resume", "Resume (skip done)", "bool", True),
        F("--index-only", "Only rebuild INDEX.md", "bool", False),
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
    ("\U0001F4DD Lyric analyze", "lyric_analyze.py", [
        F("--input", "Lyrics folder (.txt)", "text", info="F:/RAP_ARCHIVES/lyrics"),
        F("--out", "Output model dir", "text", "lyric_model"),
    ]),
    ("\u270D\uFE0F Lyric generate (Ollama)", "lyric_generate.py", [
        F("--model-dir", "Style model dir", "text", "lyric_model"),
        F("--mode", "Mode", "choice", "verse", ["verse", "hook"]),
        F("--mood", "Mood (blank = your dominant)", "text"),
        F("--theme", "Theme / about", "text"),
        F("--bars", "Bars", "num", 16),
        F("--variations", "Variations", "num", 1),
        F("--model", "Ollama model", "text", "llama3.1:8b"),
        F("--out", "Output folder", "text", "verses"),
    ]),
    ("\U0001F39A\uFE0F Lyric \u2192 beat brief", "lyric_to_beat.py", [
        F("--lyrics", "Lyric .txt file", "text"),
        F("--genre", "Genre", "choice", "auto", ["auto", "hiphop", "trap", "dnb", "dubstep"]),
        F("--out", "Output folder", "text", "beat_brief"),
    ]),
    ("\U0001F3B6 ACE-Step 1.5 (alt engine)", "ace_step_workflow.py", [
        F("", "Subcommand", "positional", "generate", ["models", "generate", "song", "cover", "train"]),
        F("--plan", "Pack plan JSON (generate)", "text"),
        F("--prompt", "Prompt/tags (song/cover)", "text"),
        F("--lyrics-file", "Lyrics .txt (song)", "text"),
        F("--bpm", "BPM (song)", "num", None),
        F("--key", "Key e.g. F minor (song)", "text"),
        F("--duration", "Seconds (song)", "num", 180),
        F("--src", "Source audio (cover)", "text"),
        F("--strength", "Cover strength 0-1", "num", 0.5),
        F("--model", "DiT model (blank=default)", "text"),
        F("--out", "Output", "text", "generated_ace"),
        F("--host", "API host", "text", "http://localhost:8001"),
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
    ("\U0001F3A4 YuE (lyrics\u2192song)", "yue_workflow.py", [
        F("--yue", "YuE repo path", "text", info="~/YuE (see cloud/yue_setup.sh)"),
        F("--lyrics", "Lyrics .txt", "text"),
        F("--genre", "Genre/style tags", "text", info="hip hop, boom bap, male rapper, 90 bpm"),
        F("--segments", "Segments (length)", "num", 2),
        F("--out", "Output", "text", "songs"),
    ]),
    ("\U0001F3A4 DiffRhythm (fast)", "diffrhythm_workflow.py", [
        F("--diffrhythm", "DiffRhythm repo path", "text"),
        F("--lyrics", "Lyrics .lrc/.txt", "text"),
        F("--prompt", "Style prompt", "text"),
        F("--ref-audio", "Ref audio (optional)", "text"),
        F("--out", "Output", "text", "drafts"),
        F("--chunked", "Chunked (low VRAM)", "bool", False),
    ]),
    ("\U0001F3B9 MusicGen (+melody)", "musicgen_workflow.py", [
        F("--prompt", "Prompt", "text"),
        F("--melody", "Melody WAV (optional)", "text"),
        F("--model", "Model", "choice", "facebook/musicgen-medium",
          ["facebook/musicgen-small", "facebook/musicgen-medium", "facebook/musicgen-large", "facebook/musicgen-melody"]),
        F("--duration", "Seconds", "num", 12),
        F("--count", "Clips", "num", 4),
        F("--out", "Output", "text", "musicgen_out"),
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
    # ---- Creative Lab: advanced/experimental generators ----
    ("\U0001F9EC Sample DNA", "sample_dna.py", [
        F("--catalog", "Catalog folder", "text", "catalog"),
        F("--pack-name", "Pack name", "text", "Crate DNA Vol 1"),
        F("--bpm", "BPM", "num", 90),
        F("--key", "Key e.g. F minor", "text"),
        F("--out", "Write pack plan JSON", "text", "prompts/sample_dna.json"),
        F("--report", "Print lineage summary", "bool", True),
        F("--flips", "N flip prompts (0=off)", "num", 0),
        F("--flip-input", "Source WAV to flip (optional)", "text"),
        F("--strength", "Flip strength 0-1", "num", 0.55),
        F("--variations", "Variations per flip", "num", 2),
        F("--out-dir", "Flips output dir", "text", "flips"),
        F("--pretrained", "HF model for flips", "text", "stabilityai/stable-audio-open-1.0"),
    ]),
    ("\U0001F9EA Micro-variants", "microvariants.py", [
        F("--input", "Source wav", "file"),
        F("--prompt", "Prompt", "text"),
        F("--variants", "Variants", "num", 8),
        F("--strength", "Strength (small)", "num", 0.15),
        F("--steps", "Steps", "num", 80),
        F("--out", "Output folder", "text"),
    ]),
    ("\U0001F9EA Groove DNA", "groove_dna.py", [
        F("--input", "Reference groove wav", "file"),
        F("--name", "Groove name", "text"),
        F("--engine", "Beat engine", "choice", "auto", ["auto", "beat_this", "librosa"]),
        F("--out", "Output folder", "text", "grooves"),
    ]),
    ("\U0001F9EA Flip lineage", "flip_lineage.py", [
        F("--input", "Source wav", "file"),
        F("--stage", "Stage prompt", "text", info="one stage; repeat via CLI for a chain"),
        F("--steps", "Steps", "num", 100),
        F("--cfg", "CFG", "num", 7),
        F("--out", "Output folder", "text"),
    ]),
    ("\U0001F9EA Destroy & heal", "destroy_heal.py", [
        F("--input", "Source wav", "file"),
        F("--chain", "Destroy chain JSON", "text"),
        F("--prompt", "Heal prompt", "text"),
        F("--heal-strength", "Heal strength", "num", 0.25),
        F("--steps", "Steps", "num", 100),
        F("--keep-destroyed", "Keep destroyed stage", "bool", False),
        F("--out", "Output folder", "text"),
    ]),
    ("\U0001F9EA A/B two models", "ab_models.py", [
        F("--plan", "Pack plan JSON", "file"),
        F("--model-a-config", "Model A config", "text"),
        F("--model-a-ckpt", "Model A ckpt", "text"),
        F("--model-a-pretrained", "Model A HF id", "text"),
        F("--model-b-config", "Model B config", "text"),
        F("--model-b-ckpt", "Model B ckpt", "text"),
        F("--model-b-pretrained", "Model B HF id", "text"),
        F("--base-seed", "Base seed", "num", 1234),
        F("--steps", "Steps", "num", 100),
        F("--cfg", "CFG", "num", 7),
        F("--out", "Output folder", "text"),
    ]),
    ("\U0001F9EA Call & response (watch)", "call_response.py", [
        F("--watch", "Folder to watch", "dir"),
        F("--respond", "Responder model/config", "text"),
        F("--prompt", "Prompt", "text"),
        F("--strength", "Strength", "num", 0.45),
        F("--variations", "Variations", "num", 2),
        F("--steps", "Steps", "num", 80),
        F("--poll", "Poll seconds", "num", 2.0),
    ]),
    ("\U0001F9EA Ecosystem pack", "ecosystem_pack.py", [
        F("", "Subcommand", "positional", "plan", ["plan", "verify"]),
        F("--base", "(plan) base wav", "text"),
        F("--dir", "(verify) pack folder", "text"),
        F("--key", "Key e.g. F minor", "text"),
        F("--bpm", "BPM", "num", None),
        F("--name", "(plan) name", "text"),
        F("--bpm-tolerance", "(verify) BPM tolerance", "num", 3),
        F("--report-only", "(verify) report only", "bool", False),
        F("--out", "(plan) output", "text"),
    ]),
    ("\U0001F9EA Curation loop", "curation_loop.py", [
        F("", "Subcommand", "positional", "score", ["score", "promote"]),
        F("--candidates", "(score) candidates folder", "text"),
        F("--reference", "(score) reference folder", "text"),
        F("--keep-top", "(score) keep top fraction", "num", 0.1),
        F("--keep-dir", "Keep/promote folder", "text"),
        F("--dataset-dir", "(promote) dataset out", "text"),
        F("--base-prompt", "(promote) base prompt", "text", "hip hop"),
    ]),
    ("\U0001F9EA Push gen server", "push_generation_server.py", [
        F("--presets", "Push presets JSON", "file"),
        F("--out", "Output folder", "text"),
        F("--host", "Host", "text", "127.0.0.1"),
        F("--port", "Port", "num", 11001),
        F("--steps", "Steps", "num", 60),
    ]),
    ("\U0001F9EA Ableton bridge", "ableton_bridge.py", [
        F("--beat", "Beat wav", "file"),
        F("--track", "Track index", "num", 0),
        F("--scene", "Scene index", "num", 0),
        F("--host", "Host", "text", "127.0.0.1"),
        F("--port", "Port", "num", 11000),
        F("--fire", "Fire clip", "bool", False),
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


def run_cmd(cmd, cwd=None, env_extra=None):
    """Stream an arbitrary command (used by the Server / API tab for uvicorn,
    the worker, pytest, docker compose, and the Python API client)."""
    import os as _os
    env = dict(_os.environ)
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items() if v not in (None, "")})
    log = "$ " + " ".join(cmd) + "\n\n"
    yield log
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, cwd=cwd or str(ROOT), env=env)
    except Exception as e:
        yield log + f"\nFAILED TO START: {e}"
        return
    for line in iter(proc.stdout.readline, ""):
        log += line
        yield log[-12000:]
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
  <h1>\U0001F3B9 Co-Produce AI <span class="accent">/ Studio Dashboard</span></h1>
  <p>Train your own hip-hop model and run the full pipeline \u2014 organize \u00B7 separate \u00B7 analyze \u00B7 tag \u00B7 caption \u00B7 prepare \u00B7 train \u00B7 generate \u00B7 process \u00B7 pack. Each tab runs a step and streams its log live.</p>
</div>
"""


def build_ui():
    with gr.Blocks(title="Co-Produce AI \u2014 Dashboard", theme=THEME, css=CSS) as app:
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

        def render_tool(label, script, fields):
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

        # group tools into sections (by script name); leftovers -> "More"
        SECTIONS = [
            ("\U0001F4E5 Prep & Analyze", ["organize_soundbank.py", "mp3_to_wav.py", "remove_vocals.py", "deep_listen.py",
                                           "auto_tag.py", "genius_lookup.py", "playlist_meta.py", "genre_playlists.py", "playlist_catalog.py", "build_captions.py",
                                           "prepare_dataset.py", "validate_dataset.py"]),
            ("\U0001F9E0 Train & Generate", ["sa3_workflow.py", "ace_step_workflow.py", "generate.py", "audio2audio.py",
                                             "yue_workflow.py", "diffrhythm_workflow.py", "musicgen_workflow.py", "song_generate.py"]),
            ("\U0001F941 Beats & Sound", ["beat_builder.py", "vst_instrument.py", "vst_chain.py"]),
            ("\U0001F9EA Creative Lab", ["sample_dna.py", "microvariants.py", "groove_dna.py", "flip_lineage.py", "destroy_heal.py",
                                           "ab_models.py", "call_response.py", "ecosystem_pack.py", "curation_loop.py",
                                           "push_generation_server.py", "ableton_bridge.py"]),
            ("\U0001F501 Remix", ["remix.py"]),
            ("\u270D\uFE0F Lyrics", ["lyric_analyze.py", "lyric_generate.py", "lyric_to_beat.py", "vocal_guide.py"]),
            ("\U0001F4E6 Finish", ["postprocess.py", "build_pack.py", "provenance.py"]),
            ("\U0001F50C Plugins", ["plugin_scan.py"]),
        ]
        by_script = {s: (l, s, f) for (l, s, f) in TOOLS}
        placed = set()
        for sec_label, scripts in SECTIONS:
            with gr.Tab(sec_label):
                with gr.Tabs():
                    for sc in scripts:
                        if sc in by_script:
                            l, s, f = by_script[sc]
                            placed.add(sc)
                            with gr.Tab(l):
                                render_tool(l, s, f)
        leftover = [t for t in TOOLS if t[1] not in placed]
        if leftover:
            with gr.Tab("\u2795 More"):
                with gr.Tabs():
                    for l, s, f in leftover:
                        with gr.Tab(l):
                            render_tool(l, s, f)


        with gr.Tab("\U0001F50C Plugin browser"):
            gr.Markdown("#### Plugin browser\nRun **Plugins → Scan plugins** first, then pick one to copy its path into vst_chain / vst_instrument.")
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

        with gr.Tab("\u2601\uFE0F  Cloud / Deploy"):
            gr.Markdown(
                "#### Cloud / Deploy\n"
                "Reference for running on RunPod and serving the toolkit. Full guides: "
                "README \u00A733 (Serverless) and \u00A734 (Pod workflow); quick values in `cloud/connect.md`.\n\n"
                "**One-shot pod setup** (paste in the pod's SSH session):\n"
                "```bash\n"
                "curl -fsSL https://raw.githubusercontent.com/pjcampbe11/Co-Produce-AI/main/cloud/pod_bootstrap.sh | bash\n"
                "# private repo: GH_TOKEN=YOUR_PAT bash -c 'curl -fsSL .../pod_bootstrap.sh | bash'\n"
                "```\n\n"
                "**SCP files to/from a pod** (local terminal):\n"
                "```powershell\n"
                "scp -P <PORT> -i $env:USERPROFILE\\.ssh\\id_ed25519 -r \"F:\\RAP_ARCHIVES\\raw_beats\" root@<POD_IP>:/workspace/\n"
                "scp -P <PORT> -i $env:USERPROFILE\\.ssh\\id_ed25519 -r root@<POD_IP>:/workspace/out \"F:\\out\"\n"
                "```\n\n"
                "**S3 network volume** (upload once, mount on any pod):\n"
                "```powershell\n"
                "aws s3 cp \"F:\\RAP_ARCHIVES\\raw_beats\" s3://d39orqnjjh/raw_beats/ --recursive --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io --checksum-algorithm CRC32\n"
                "```\n\n"
                "**Serverless endpoint** \u2014 wrap a toolkit task behind an autoscaling HTTPS URL "
                "(`serverless/handler.py` + `serverless/Dockerfile`). Call it from Go with `clients/go` "
                "(`go run . -task beat -style trap -bpm 140 -out trap.wav`). Set `RUNPOD_API_KEY` "
                "(console \u2192 Settings \u2192 API Keys) and `ENDPOINT_ID` (console \u2192 Serverless \u2192 your endpoint).\n\n"
                "**SaaS server** \u2014 turn the toolkit into a product: authenticated REST API + Redis job queue + Stripe billing in `server/` (`docker compose up --build`). See README \u00A735.\n\n"
                "_GPU tip: run **this dashboard** on a pod to drive its GPU from the same UI; expose port 7860._"
            )

        with gr.Tab("\U0001FA7A  Engine status"):
            gr.Markdown("#### Engine readiness\nChecks each generation engine's deps/repo "
                        "(no models loaded). Green = ready to run, red = needs setup. "
                        "Pass repo paths via env (YUE_REPO, DIFFRHYTHM_REPO) or the scripts.")
            est_btn = gr.Button("\U0001F501  Check engines", variant="primary")
            est_html = gr.HTML()
            def _engine_status():
                import subprocess as _sp, json as _json
                try:
                    out = _sp.run([CONFIG["python"], str(SCRIPTS / "engine_doctor.py"), "--json"],
                                  capture_output=True, text=True, cwd=str(ROOT), timeout=30)
                    data = _json.loads(out.stdout)
                except Exception as e:
                    return f"<p style='color:#E24B4A'>doctor failed: {e}</p>"
                rows = ""
                for r in data.get("engines", []):
                    color = "#22C55E" if r["ready"] else "#E24B4A"
                    dot = "\u25CF"
                    rows += (f"<tr><td style='padding:6px 10px;color:{color};font-size:16px'>{dot}</td>"
                             f"<td style='padding:6px 10px;font-weight:600'>{r['engine']}</td>"
                             f"<td style='padding:6px 10px;color:#9FB3C8'>{r['kind']}</td>"
                             f"<td style='padding:6px 10px;color:#9FB3C8'>{r['detail']}</td></tr>")
                torch = "yes" if data.get("torch") else "<span style='color:#E24B4A'>NO</span>"
                return (f"<p style='color:#9FB3C8'>torch available: {torch}</p>"
                        f"<table style='border-collapse:collapse;width:100%'>"
                        f"<tr style='color:#FF8A3D'><th></th><th style='text-align:left;padding:6px 10px'>engine</th>"
                        f"<th style='text-align:left;padding:6px 10px'>kind</th>"
                        f"<th style='text-align:left;padding:6px 10px'>status</th></tr>{rows}</table>")
            est_btn.click(_engine_status, None, est_html)

        with gr.Tab("\U0001F3B6  Inspiration"):
            gr.Markdown("#### Hip-hop beats inspired by\nThe reference playlist this "
                        "toolkit is tuned against. Use **Prep & Analyze \u2192 Spotify playlist "
                        "meta** to pull its full metadata + samples.")
            gr.HTML('<iframe data-testid="embed-iframe" style="border-radius:12px" '
                    'src="https://open.spotify.com/embed/playlist/7MNBsBwgsqAsRZkdNE4E5Y?utm_source=generator" '
                    'width="100%" height="420" frameBorder="0" '
                    'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
                    'loading="lazy"></iframe>')
            gr.Markdown("<span style='color:#9FB3C8'>Tip: the embed mirrors the playlist's own "
                        "order \u2014 sort the playlist by *Date added* in Spotify to play "
                        "newest-first. The metadata report defaults to newest-added first.</span>")

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
        with gr.Tab("\U0001F6F0\uFE0F  Server / API"):
            gr.Markdown(
                "#### SaaS server & API\n"
                "Launch and exercise the [`server/`](server) stack (REST API + job queue + "
                "Stripe). The API/worker need **Redis** running (`docker compose up redis`, or "
                "full stack `docker compose up --build`). Buttons stream live logs; long-running "
                "ones (API, worker) keep running until you stop the job.")
            py = CONFIG["python"]
            with gr.Tabs():
                with gr.Tab("Run / manage"):
                    with gr.Row():
                        api_port = gr.Number(value=8000, label="API port", scale=1)
                        with gr.Column(scale=3):
                            b_redis = gr.Button("\U0001F7E2  Start Redis (docker)", variant="primary")
                            b_api = gr.Button("\u25B6  Start API (uvicorn)", variant="primary")
                            b_worker = gr.Button("\u25B6  Start worker (both lanes)", variant="primary")
                            b_tests = gr.Button("\u25B6  Run server tests (pytest)")
                            b_compose = gr.Button("\u25B6  docker compose up --build (full stack)")
                            b_pricing = gr.Button("\U0001F310  Print pricing URL")
                    srv_log = gr.Textbox(label="Server log", lines=20, max_lines=20,
                                         autoscroll=True, elem_classes=["logbox"])
                    def _start_redis():
                        # Prefer Docker; fall back to a native redis-server if Docker
                        # isn't available but redis-server is on PATH.
                        import shutil
                        if shutil.which("docker"):
                            yield from run_cmd(["docker", "compose", "up", "-d", "redis"])
                            return
                        if shutil.which("redis-server"):
                            yield ("Docker not found - starting native redis-server "
                                   "(leave this job running).\n\n")
                            yield from run_cmd(["redis-server", "--port", "6379"])
                            return
                        yield ("Neither Docker nor redis-server found.\n"
                               "Install Docker Desktop, or a native Redis:\n"
                               "  Windows: use Docker, WSL, or Memurai (memurai.com)\n"
                               "  macOS:   brew install redis && redis-server\n"
                               "  Linux:   sudo apt-get install -y redis-server\n")
                    b_redis.click(_start_redis, None, srv_log)
                    b_api.click(lambda port: (yield from run_cmd(
                        [py, "-m", "uvicorn", "server.app:app", "--host", "127.0.0.1",
                         "--port", str(int(port or 8000))])), api_port, srv_log)
                    b_worker.click(lambda: (yield from run_cmd([py, "-m", "server.worker"])),
                                   None, srv_log)
                    b_tests.click(lambda: (yield from run_cmd([py, "-m", "pytest", "-q"],
                                  cwd=str(ROOT / "server"))), None, srv_log)
                    b_compose.click(lambda: (yield from run_cmd(["docker", "compose", "up", "--build"])),
                                    None, srv_log)
                    b_pricing.click(lambda port: f"Pricing page: http://127.0.0.1:{int(port or 8000)}/pricing",
                                    api_port, srv_log)

                with gr.Tab("API client (signup \u2192 submit \u2192 download)"):
                    gr.Markdown("Drives `clients/python/beat_client.py` against a running API.")
                    with gr.Row():
                        base = gr.Textbox("http://127.0.0.1:8000", label="Base URL")
                        akey = gr.Textbox("", label="API key (bt_...) - or use Signup email")
                        signup = gr.Textbox("", label="Signup email (mints a key)")
                    with gr.Row():
                        ctask = gr.Dropdown(["beat", "tag", "flip", "remix", "song"], value="beat", label="Task")
                        cparams = gr.Textbox("style=trap, bpm=140", label="Params (k=v, comma-sep)")
                        cout = gr.Textbox("out.wav", label="Save audio to")
                    admin = gr.Textbox("", label="Admin token (if signup is locked)")
                    cbtn = gr.Button("\u25B6  Run API job", variant="primary")
                    clog = gr.Textbox(label="Client log", lines=16, elem_classes=["logbox"])
                    def _client(base_url, key, email, task, params, out, admin_tok):
                        cmd = [py, str(ROOT / "clients" / "python" / "beat_client.py"),
                               "--base-url", base_url, "--task", task]
                        if key.strip():
                            cmd += ["--key", key.strip()]
                        elif email.strip():
                            cmd += ["--signup", email.strip()]
                        else:
                            yield "Provide an API key or a signup email."; return
                        if admin_tok.strip():
                            cmd += ["--admin-token", admin_tok.strip()]
                        for kv in [x.strip() for x in params.split(",") if x.strip()]:
                            cmd += ["--param", kv.replace(" ", "")]
                        if out.strip():
                            cmd += ["--out", out.strip()]
                        yield from run_cmd(cmd)
                    cbtn.click(_client, [base, akey, signup, ctask, cparams, cout, admin],
                               clog)

    return app


if __name__ == "__main__":
    ui = build_ui().queue(default_concurrency_limit=4)
    try:
        ui.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
    except Exception as e:
        print(f"Local launch failed ({e}); retrying with a public share link...")
        ui.launch(share=True, inbrowser=True)
