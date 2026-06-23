#!/usr/bin/env python3
"""
ace_step_workflow.py  -  Drive ACE-Step 1.5 (alternative engine to Stable Audio 3).

ACE-Step 1.5 (github.com/ace-step/ACE-Step-1.5) is an MIT-licensed music model
(no revenue cap) that does BOTH instrumental beats and full songs with vocals
(lyrics + tags), plus cover/repaint, runs on low VRAM, and trains a personal
LoRA from a handful of songs. It exposes a REST API; this is a thin HTTP client
to that server, mirroring sa3_workflow.py so you can A/B both engines.

Operator notes (the non-obvious bits):
  - Start the server first: cd ACE-Step-1.5 && uv run acestep-api  (-> http://localhost:8001)
  - Flow is async: /release_task -> task_id, poll /query_result until status==1, download /v1/audio.
  - 'thinking=true' lets the planner LM fill bpm/key + enhance prompts (best quality). batch_size max 8.
  - MIT license = commercial OK with no revenue cap (unlike Stable Audio's $1M cap).

Subcommands: models | generate | song | cover | train
Usage:
    python ace_step_workflow.py models
    python ace_step_workflow.py generate --plan prompts/pack_plan.example.json --out generated_ace
    python ace_step_workflow.py song --prompt "boom bap, dusty, male rap vocals, 90 BPM" --lyrics-file verse.txt --bpm 90 --key "F minor" --duration 180 --out song
    python ace_step_workflow.py cover --src mybeat.wav --prompt "drum and bass, reese bass" --strength 0.5 --out remix
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path


def _headers(args):
    h = {"Content-Type": "application/json"}
    key = args.api_key or os.environ.get("ACESTEP_API_KEY", "")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _submit(args, payload):
    import requests
    r = requests.post(f"{args.host}/release_task", headers=_headers(args), json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["task_id"]


def _wait(args, task_id, poll=3.0, timeout=1800):
    import requests
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.post(f"{args.host}/query_result", headers=_headers(args),
                          json={"task_id_list": [task_id]}, timeout=60)
        r.raise_for_status()
        row = r.json()["data"][0]
        st = row.get("status")
        if st == 1:
            return json.loads(row["result"])
        if st == 2:
            raise RuntimeError(f"task {task_id} failed")
        time.sleep(poll)
    raise TimeoutError(f"task {task_id} timed out")


def _download(args, file_url, dest):
    import requests
    url = file_url if file_url.startswith("http") else f"{args.host}{file_url}"
    r = requests.get(url, headers=_headers(args), timeout=120)
    r.raise_for_status()
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    Path(dest).write_bytes(r.content)


def _gen_one(args, payload, out_dir, stem):
    tid = _submit(args, payload)
    print(f"  submitted {tid} ...")
    ext = payload.get("audio_format") or "wav"
    for i, item in enumerate(_wait(args, tid), 1):
        _download(args, item["file"], Path(out_dir) / f"{stem}_{i:02d}.{ext}")
        print(f"  saved {stem}_{i:02d}.{ext}")


def cmd_models(args):
    import requests
    d = requests.get(f"{args.host}/v1/models", headers=_headers(args), timeout=30).json()["data"]
    print("Default:", d.get("default_model"))
    for m in d.get("models", []):
        print("  -", m["name"], "(default)" if m.get("is_default") else "")


def cmd_generate(args):
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    for cat in plan["categories"]:
        n = int(cat.get("count", 1)); secs = float(cat.get("seconds", 30))
        print(f"[{cat['name']}] {n} x {secs}s")
        made = 0
        while made < n:
            bs = min(8, n - made)
            payload = {"prompt": cat["prompt"], "audio_duration": secs, "thinking": True,
                       "batch_size": bs, "audio_format": args.format}
            if args.model:
                payload["model"] = args.model
            if plan.get("bpm"):
                payload["bpm"] = int(plan["bpm"])
            _gen_one(args, payload, Path(args.out) / cat["name"], f"{cat['name']}_{made+1}")
            made += bs
    print(f"\nDone -> {args.out}/  (run postprocess.py next)")


def cmd_song(args):
    lyrics = Path(args.lyrics_file).read_text(encoding="utf-8") if args.lyrics_file else ""
    payload = {"prompt": args.prompt, "lyrics": lyrics, "thinking": True, "use_format": True,
               "audio_duration": float(args.duration), "audio_format": args.format, "vocal_language": args.lang}
    if args.model:
        payload["model"] = args.model
    if args.bpm:
        payload["bpm"] = int(args.bpm)
    if args.key:
        payload["key_scale"] = args.key
    _gen_one(args, payload, str(Path(args.out).parent or "."), Path(args.out).stem)


def cmd_cover(args):
    payload = {"prompt": args.prompt, "task_type": "cover", "thinking": False,
               "src_audio_path": str(Path(args.src).resolve()),
               "audio_cover_strength": float(args.strength), "audio_format": args.format}
    if args.model:
        payload["model"] = args.model
    _gen_one(args, payload, str(Path(args.out).parent or "."), Path(args.out).stem)


def cmd_train(args):
    print("LoRA training — two ways:")
    print("  1) Easiest: ACE-Step Gradio UI -> 'LoRA Training' tab -> one-click annotate+train (~8 songs, ~1h on 12GB).")
    print("  2) REST: preprocess audio to tensors per docs/en/LoRA_Training_Tutorial.md, then")
    print("     POST {host}/v1/training/start  (or /v1/training/start_lokr for faster LoKr).")
    print("  Your build_captions.py captions feed the annotation step.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("ACESTEP_API", "http://localhost:8001"))
    ap.add_argument("--api-key", default="")
    ap.add_argument("--model", default="", help="DiT model name (blank=server default); see `models`")
    ap.add_argument("--format", default="wav")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models").set_defaults(fn=cmd_models)
    sub.add_parser("train").set_defaults(fn=cmd_train)
    p = sub.add_parser("generate"); p.add_argument("--plan", required=True); p.add_argument("--out", default="generated_ace"); p.set_defaults(fn=cmd_generate)
    p = sub.add_parser("song"); p.add_argument("--prompt", required=True); p.add_argument("--lyrics-file"); p.add_argument("--bpm", type=int); p.add_argument("--key"); p.add_argument("--duration", type=float, default=180); p.add_argument("--lang", default="en"); p.add_argument("--out", default="ace_song.wav"); p.set_defaults(fn=cmd_song)
    p = sub.add_parser("cover"); p.add_argument("--src", required=True); p.add_argument("--prompt", required=True); p.add_argument("--strength", type=float, default=0.5); p.add_argument("--out", default="ace_cover.wav"); p.set_defaults(fn=cmd_cover)
    args = ap.parse_args()
    try:
        args.fn(args)
    except Exception as e:
        sys.exit(f"ACE-Step API error: {e}\nIs the server running?  cd ACE-Step-1.5 && uv run acestep-api")


if __name__ == "__main__":
    main()
