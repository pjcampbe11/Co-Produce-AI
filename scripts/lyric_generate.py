#!/usr/bin/env python3
"""
lyric_generate.py  -  Generate verses/hooks in YOUR style via a LOCAL Ollama model.

Uses the style_profile.json + corpus.jsonl from lyric_analyze.py: it injects your
style summary as the system prompt and a few of YOUR real sections as few-shot
examples, so the local model writes in your voice. Fully local & private (your
lyrics never leave your machine).

Setup (one-time):
    1. Install Ollama: https://ollama.com  (Windows installer)
    2. Pull a model:  ollama pull llama3.1:8b   (or qwen2.5:7b, mistral, etc.)
    pip install requests

Usage:
    python lyric_generate.py --model-dir lyric_model --mode verse --mood dark \
        --theme "grinding through the cold" --bars 16 --variations 2 --out verses
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Local Ollama only (private). Injects your style summary + a few of your REAL sections as voice anchors.
#   - Small corpora make the model echo your phrasing - treat output as a DRAFT in your voice and edit it.
# ---------------------------------------------------------------------------
import argparse
import json
import random
import sys
from pathlib import Path


def load(model_dir):
    p = Path(model_dir)
    profile = json.loads((p / "style_profile.json").read_text(encoding="utf-8"))
    corpus = [json.loads(l) for l in (p / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return profile, corpus


def pick_examples(corpus, mode, k=3):
    pref = [c for c in corpus if c["type"] in (("hook", "chorus") if mode == "hook" else ("verse",))]
    pool = pref or corpus
    random.shuffle(pool)
    return pool[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="lyric_model")
    ap.add_argument("--mode", choices=["verse", "hook"], default="verse")
    ap.add_argument("--mood", default="", help="e.g. dark, triumphant, reflective")
    ap.add_argument("--theme", default="", help="what it's about")
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--variations", type=int, default=1)
    ap.add_argument("--model", default="llama3.1:8b", help="Ollama model name")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--out", default="lyric_out")
    args = ap.parse_args()

    import requests
    profile, corpus = load(args.model_dir)
    examples = pick_examples(corpus, args.mode)
    ex_text = "\n\n".join("\n".join(e["lines"]) for e in examples)

    system = (
        "You are a ghostwriter emulating ONE rapper's personal style. Study the style "
        "profile and the real example sections, then write NEW original bars in that voice. "
        "Match the flow density, rhyme approach, vocabulary, and mood. Do not copy lines from "
        "the examples. Output ONLY the lyrics, no commentary.\n\n"
        f"STYLE PROFILE: {profile['style_summary']}\n"
        f"Target flow: ~{profile['avg_syllables_per_line']} syllables/line. "
        f"Rhyme: {profile['rhyme_style']}.\n\n"
        f"REAL EXAMPLES (this artist's actual writing, for voice only):\n{ex_text}"
    )
    mood = args.mood or (profile["dominant_moods"][0] if profile["dominant_moods"] else "")
    user = (f"Write a {args.bars}-bar {args.mode}" +
            (f" with a {mood} mood" if mood else "") +
            (f", about: {args.theme}" if args.theme else "") +
            f". Use [{'Hook' if args.mode=='hook' else 'Verse'}] as the only header.")

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    for v in range(1, args.variations + 1):
        try:
            r = requests.post(f"{args.host}/api/chat", timeout=180, json={
                "model": args.model, "stream": False,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "options": {"temperature": 0.9, "top_p": 0.95},
            })
            r.raise_for_status()
            text = r.json()["message"]["content"].strip()
        except Exception as e:
            sys.exit(f"Ollama call failed ({e}). Is Ollama running and '{args.model}' pulled? "
                     f"Try: ollama pull {args.model}")
        fn = out / f"{args.mode}_{mood or 'any'}_{v:02d}.txt"
        fn.write_text(text, encoding="utf-8")
        print(f"\n===== {fn.name} =====\n{text}")
    print(f"\nSaved to {out}/  -> feed to vocal_guide.py or lyric_to_beat.py next.")


if __name__ == "__main__":
    main()
