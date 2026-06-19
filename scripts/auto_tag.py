#!/usr/bin/env python3
"""
auto_tag.py  -  Open-vocabulary vibe/mood tagging from the AUDIO ITSELF.

Instead of scoring against a fixed list (the CLAP path in 07/23), this asks an
audio-language model to LISTEN and describe the track in free-form text, then
distills concise tags. It can analyze the full mix, just the vocal, just the
beat (instrumental), or all of them separately so tags are attributed to source
(e.g. vocal -> "aggressive melodic delivery", beat -> "dark dusty trap").

Engines (auto-detected, best first):
  qwen3-omni   Qwen3-Omni Captioner - most detailed free-form audio captions
  qwen2-audio  Qwen2-Audio-7B-Instruct - lighter audio LLM, prompt-driven
  clap         fallback: zero-shot vs an EXPANDED vocab (still list-based)
    pip install transformers accelerate torchaudio    (qwen)
    pip install laion-clap                              (fallback)

Stem separation (for --source vocals/beat/all) uses audio-separator (BS-RoFormer),
already used by remove_vocals.py.   pip install "audio-separator[gpu]"

Writes <file>.tags.json next to each audio file, in the shape prepare_dataset.py
reads ({"tags": [...]}), plus per-source detail and the raw caption.

Usage:
    python auto_tag.py --input "F:/Sound Bank Organized" --source full --resume
    python auto_tag.py --input songs/ --source all --engine qwen2-audio --resume
    python auto_tag.py --input track.mp3 --source beat        # tag the instrumental only

PAIRED MODE (you already stemmed your songs into parallel folders with matching
filenames - recommended layout):
    F:/STEMS/full/...   F:/STEMS/vocals/...   F:/STEMS/beat/...   (same relative
    path + filename in each). Tags from all available stems of a song are MERGED
    into one set (with per-source attribution) and a copy of that set is written
    next to every stem, so prepare_dataset.py finds it whichever stem you train on.

    python auto_tag.py --full-root F:/STEMS/full --vocals-root F:/STEMS/vocals \
        --beat-root F:/STEMS/beat --resume
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - USE_TF=0 is set at import to keep transformers off a (often broken) TensorFlow.
#   - Engine auto-picks: qwen if transformers present, else CLAP. Qwen wants ~16 GB VRAM.
#   - --limit N counts NEWLY-tagged items (skips already-done), so repeated runs walk the dataset.
#   - Supports parallel-folder OR *_instrumental/_vocals suffix stem layouts.
# ---------------------------------------------------------------------------
import os as _os
_os.environ.setdefault("USE_TF", "0")          # keep transformers off TensorFlow
_os.environ.setdefault("USE_TORCH", "1")
_os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
import argparse
import json
import random
import re
import os
import sys
import tempfile
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".ogg", ".m4a"}
CAPTION_PROMPT = (
    "Listen to this audio and describe it for a music sample library. Cover mood, "
    "energy level, genre/subgenre, era, instrumentation, vocal style if present, and "
    "production texture. Then give a single line of 6-12 concise lowercase tags "
    "separated by commas, prefixed with TAGS:. Be specific and honest to the audio."
)

# expanded fallback vocab (only used by the clap engine)
CLAP_VOCAB = [
    "dark", "bright", "aggressive", "mellow", "melancholic", "uplifting", "eerie",
    "dreamy", "nostalgic", "triumphant", "tense", "playful", "romantic", "gritty",
    "smooth", "epic", "minimal", "lush", "raw", "polished", "soulful", "jazzy",
    "hard hitting", "laid back", "energetic", "hypnotic", "spacey", "warm", "cold",
    "boom bap", "trap", "drill", "lofi", "rnb", "soul", "funk", "rock", "metal",
    "punk", "house", "techno", "dubstep", "drum and bass", "ambient", "orchestral",
    "dusty vinyl", "tape saturated", "distorted", "clean", "reverb drenched", "dry",
    "808 heavy", "sub bass", "reese bass", "wobble bass", "piano led", "guitar driven",
    "synth heavy", "string section", "male vocal", "female vocal", "rap vocal",
    "vocal chops", "instrumental", "1970s", "1990s", "modern",
]


# ---------- stem separation ----------
def separate(path, tmp):
    """Return dict of available sources: full + (vocals, beat) if separator works."""
    sources = {"full": str(path)}
    try:
        from audio_separator.separator import Separator
    except ImportError:
        return sources, "audio-separator not installed - only --source full available"
    _sep_kw = {"output_dir": tmp}
    if os.environ.get("AUDIO_SEPARATOR_MODELS"):
        _sep_kw["model_file_dir"] = os.environ["AUDIO_SEPARATOR_MODELS"]
    sep = Separator(**_sep_kw)
    sep.load_model(model_filename="model_bs_roformer_ep_317_sdr_12.9755.ckpt")
    outs = sep.separate(str(path))
    for o in outs:
        op = Path(tmp) / Path(o).name
        op = op if op.exists() else Path(o)
        low = op.name.lower()
        if "instrumental" in low:
            sources["beat"] = str(op)
        elif "vocal" in low:
            sources["vocals"] = str(op)
    return sources, None


# ---------- engines ----------
_ENGINE = {}

def _load_qwen(model_id):
    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM
    proc = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype="auto",
        device_map="cuda" if torch.cuda.is_available() else "cpu")
    return proc, model

def caption_qwen(audio_path, engine):
    """Free-form caption via a Qwen audio LLM. Returns raw text."""
    import librosa
    model_id = ("Qwen/Qwen3-Omni-30B-A3B-Captioner" if engine == "qwen3-omni"
                else "Qwen/Qwen2-Audio-7B-Instruct")
    if "qwen" not in _ENGINE:
        _ENGINE["qwen"] = _load_qwen(model_id)
    proc, model = _ENGINE["qwen"]
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    conv = [{"role": "user", "content": [
        {"type": "audio", "audio": audio},
        {"type": "text", "text": CAPTION_PROMPT}]}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
    inputs = proc(text=text, audios=[audio], sampling_rate=sr, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    out = model.generate(**inputs, max_new_tokens=256)
    return proc.batch_decode(out, skip_special_tokens=True)[0]

def tags_from_caption(caption):
    m = re.search(r"TAGS:\s*(.+)", caption, re.IGNORECASE | re.DOTALL)
    raw = m.group(1) if m else caption
    tags = [re.sub(r"[^a-z0-9 +&'-]", "", t.strip().lower()) for t in raw.split(",")]
    return [t for t in tags if 2 <= len(t) <= 40][:12]

def caption_clap(audio_path):
    import numpy as np
    if "clap" not in _ENGINE:
        import laion_clap
        m = laion_clap.CLAP_Module(enable_fusion=False)
        m.load_ckpt()
        temb = m.get_text_embedding([f"the sound of {v}" for v in CLAP_VOCAB], use_tensor=False)
        _ENGINE["clap"] = (m, temb / np.linalg.norm(temb, axis=1, keepdims=True))
    m, temb = _ENGINE["clap"]
    a = m.get_audio_embedding_from_filelist([str(audio_path)], use_tensor=False)
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    sims = (a @ temb.T)[0]
    order = np.argsort(-sims)[:10]
    return [CLAP_VOCAB[i] for i in order if sims[i] >= 0.25], "clap zero-shot (list-based fallback)"


def tag_source(audio_path, engine):
    if engine in ("qwen3-omni", "qwen2-audio"):
        cap = caption_qwen(audio_path, engine)
        return tags_from_caption(cap), cap
    tags, note = caption_clap(audio_path)
    return tags, note


def run_suffix(args, engine):
    """One folder of *_vocals / *_instrumental pairs (remove_vocals.py output),
    full songs optionally matched from --full-root by base name."""
    stems = Path(args.stems_dir)
    full_idx = _index_basename(args.full_root) if args.full_root else {}
    songs = {}  # base -> {source: path}
    for f in stems.rglob("*"):
        if f.suffix.lower() not in AUDIO_EXTS:
            continue
        name = f.stem
        if name.endswith(args.beat_suffix):
            base = name[: -len(args.beat_suffix)]
            songs.setdefault(base.lower(), {})["beat"] = f
        elif name.endswith(args.vocal_suffix):
            base = name[: -len(args.vocal_suffix)]
            songs.setdefault(base.lower(), {})["vocals"] = f
    for base, srcs in songs.items():
        if base in full_idx:
            srcs["full"] = full_idx[base]
    # honor --source: 'beat' tags only instrumentals, etc. 'all' keeps everything.
    if args.source != "all":
        for base in list(songs):
            songs[base] = {s: pth for s, pth in songs[base].items() if s == args.source}
            if not songs[base]:
                del songs[base]
    keys = sorted(songs)
    if not keys:
        sys.exit(f"No *_{args.vocal_suffix}/*_{args.beat_suffix} pairs found in {stems}")
    print(f"Songs: {len(keys)} (full songs matched: {sum('full' in songs[k] for k in keys)})")
    _tag_groups([(k, songs[k]) for k in keys], engine, args)


def _index_basename(root):
    out = {}
    for f in Path(root).rglob("*"):
        if f.suffix.lower() in AUDIO_EXTS:
            out[f.stem.lower()] = f
    return out


def _tag_groups(items, engine, args):
    """Shared tagging loop for paired/suffix modes. items: list of (key, {source:path}).
    With --limit N, processes up to N NOT-already-done songs (skips don't count),
    so repeated --limit N --resume runs walk through the dataset in chunks."""
    items = list(items)
    if getattr(args, "shuffle", False):
        random.Random(args.seed if args.seed >= 0 else None).shuffle(items)
    ok = skipped = failed = 0
    for i, (key, present) in enumerate(items, 1):
        anchor = present.get("beat") or present.get("full") or next(iter(present.values()))
        if args.resume and anchor.with_suffix(anchor.suffix + ".tags.json").exists():
            skipped += 1
            continue
        try:
            per_source, merged, captions = {}, [], {}
            for s, path in present.items():
                tags, cap = tag_source(str(path), engine)
                per_source[s] = tags
                captions[s] = cap
                merged += tags
            seen, dedup = set(), []
            for tg in merged:
                if tg and tg not in seen:
                    seen.add(tg); dedup.append(tg)
            blob = json.dumps({"tags": dedup, "by_source": per_source, "engine": engine,
                               "caption": captions, "song": key}, indent=2)
            for path in present.values():
                path.with_suffix(path.suffix + ".tags.json").write_text(blob, encoding="utf-8")
            print(f"[{i}/{len(items)}] {key}: {', '.join(dedup[:8])}")
            ok += 1
            if args.limit and ok >= args.limit:
                print(f"(reached --limit {args.limit} newly-tagged this run)")
                break
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(items)}] FAILED {key}: {e}")
    print(f"\n=== {ok} tagged, {skipped} already-done/skipped, {failed} failed ===")


def _index_root(root):
    """Map relative-path-key -> file, for pairing across stem roots."""
    if not root:
        return {}
    root = Path(root)
    out = {}
    for f in root.rglob("*"):
        if f.suffix.lower() in AUDIO_EXTS:
            out[str(f.relative_to(root)).lower()] = f
    return out


def run_paired(args, engine):
    roots = {"full": args.full_root, "vocals": args.vocals_root, "beat": args.beat_root}
    idx = {k: _index_root(v) for k, v in roots.items()}
    keys = sorted(set().union(*[set(d) for d in idx.values()]))
    if not keys:
        sys.exit("No audio found under the given stem roots.")
    print(f"Paired songs: {len(keys)} "
          f"(full={len(idx['full'])}, vocals={len(idx['vocals'])}, beat={len(idx['beat'])})")

    items = [(k, {s: idx[s][k] for s in ("full", "vocals", "beat") if k in idx[s]}) for k in keys]
    _tag_groups(items, engine, args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Audio file or folder (single-folder mode)")
    ap.add_argument("--full-root", help="Paired mode: folder of full-song stems")
    ap.add_argument("--vocals-root", help="Paired mode: folder of vocal stems")
    ap.add_argument("--beat-root", help="Paired mode: folder of beat/instrumental stems")
    ap.add_argument("--stems-dir", help="Suffix mode: ONE folder of *_vocals/*_instrumental pairs "
                    "(e.g. the output of remove_vocals.py --keep-vocals)")
    ap.add_argument("--beat-suffix", default="_instrumental")
    ap.add_argument("--vocal-suffix", default="_vocals")
    ap.add_argument("--source", choices=["full", "vocals", "beat", "all"], default="full",
                    help="Which audio to analyze. vocals/beat/all need stem separation.")
    ap.add_argument("--engine", choices=["auto", "qwen3-omni", "qwen2-audio", "clap"],
                    default="auto")
    ap.add_argument("--resume", action="store_true", help="Skip files that already have .tags.json (guarantees no beat is tagged twice across runs)")
    ap.add_argument("--limit", type=int, default=0, help="Process up to N not-yet-done items this run")
    ap.add_argument("--shuffle", action="store_true", help="Random selection order, so each --limit batch is a random sample of what's left")
    ap.add_argument("--seed", type=int, default=-1, help="Seed for --shuffle (default: truly random each run)")
    args = ap.parse_args()

    # resolve engine
    engine = args.engine
    if engine == "auto":
        try:
            import transformers  # noqa
            engine = "qwen2-audio"  # safe default; pass --engine qwen3-omni for max detail
        except ImportError:
            engine = "clap"
    print(f"Engine: {engine}   Source: {args.source}")

    if args.stems_dir:
        return run_suffix(args, engine)
    if args.full_root or args.vocals_root or args.beat_root:
        return run_paired(args, engine)

    if not args.input:
        ap.error("Provide --input (single-folder mode) or stem roots (--full-root/--vocals-root/--beat-root).")
    p = Path(args.input)
    files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.suffix.lower() in AUDIO_EXTS)
    if not files:
        sys.exit("No audio found.")
    if args.shuffle:
        random.Random(args.seed if args.seed >= 0 else None).shuffle(files)

    need_stems = args.source in ("vocals", "beat", "all")
    ok = skipped = failed = 0
    for i, f in enumerate(files, 1):
        sidecar = f.with_suffix(f.suffix + ".tags.json")
        if args.resume and sidecar.exists():
            skipped += 1
            continue
        try:
            with tempfile.TemporaryDirectory() as tmp:
                if need_stems:
                    sources, warn = separate(f, tmp)
                    if warn and args.source != "full":
                        print(f"  ({warn})")
                else:
                    sources = {"full": str(f)}
                wanted = (["vocals", "beat"] if args.source == "all"
                          else [args.source]) if need_stems else ["full"]
                per_source, all_tags, caption = {}, [], {}
                for s in wanted:
                    if s not in sources:
                        continue
                    tags, cap = tag_source(sources[s], engine)
                    per_source[s] = tags
                    caption[s] = cap
                    all_tags += [f"{t}" for t in tags]
                # dedupe, preserve order
                seen, merged = set(), []
                for t in all_tags:
                    if t and t not in seen:
                        seen.add(t)
                        merged.append(t)
                sidecar.write_text(json.dumps({
                    "tags": merged, "by_source": per_source,
                    "engine": engine, "caption": caption}, indent=2), encoding="utf-8")
                print(f"[{i}/{len(files)}] {f.name}: {', '.join(merged[:8])}")
                ok += 1
                if args.limit and ok >= args.limit:
                    print(f"(reached --limit {args.limit} newly-tagged this run)")
                    break
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(files)}] FAILED {f.name}: {e}")
    print(f"\n=== {len(files)} files: {ok} tagged, {skipped} skipped, {failed} failed ===")
    if failed and engine != "clap":
        print("If failures are model/VRAM related, try --engine clap (lighter, list-based).")


if __name__ == "__main__":
    main()
