#!/usr/bin/env python3
"""
engine_doctor.py  -  Check that each generation engine's deps/repo are present.

Prints a green/red readiness table so you know what will actually run before you
kick off a job. Pure-stdlib checks (import probes + path checks + a Redis/REST
ping where relevant) - it does NOT load models or hit GPUs.

Usage:
    python engine_doctor.py                 # human table
    python engine_doctor.py --json          # machine-readable (used by the dashboard)
    python engine_doctor.py --yue ~/YuE --diffrhythm ~/DiffRhythm --ace-host http://localhost:8001
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Pure-stdlib readiness checker - probes imports / repo paths / a REST ping only;
#   - it NEVER imports torch-heavy modules, loads a model, or touches a GPU.
#   - preflight() is the gate each engine workflow calls at startup; install_engine()
#   - does cross-platform (pip/git) auto-fixes. ace-step is a REST server, so it can't
#   - be auto-started - we print the cloud/ace_step_setup.sh instruction instead.
#   - Targets Python 3.11; pure-Python, deps via requirements.txt.
# ---------------------------------------------------------------------------
import argparse
import importlib.util
import json
import os
import sys
import urllib.request


def _have(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _ping(url, timeout=2):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


def check(args):
    torch = _have("torch")
    rows = []

    def row(engine, kind, ready, detail):
        rows.append({"engine": engine, "kind": kind, "ready": ready, "detail": detail})

    # Stable Audio Open / SA3 - need torch + stable_audio_tools (from source)
    sat = _have("stable_audio_tools")
    row("sao", "prompt", torch and sat,
        "ok" if (torch and sat) else f"need {'torch ' if not torch else ''}{'stable-audio-tools' if not sat else ''}".strip())
    sa3 = _have("stable_audio_3")
    row("sa3", "prompt", torch and (sa3 or sat),
        "ok" if (torch and (sa3 or sat)) else "need torch + stable-audio-3 (uv sync --extra lora)")

    # ACE-Step - REST server reachable?
    ace_ok = _ping(args.ace_host.rstrip("/") + "/docs") or _ping(args.ace_host.rstrip("/"))
    row("ace-step", "both", ace_ok, "server up at " + args.ace_host if ace_ok else f"start server (cloud/ace_step_setup.sh); none at {args.ace_host}")

    # MusicGen - audiocraft
    ac = _have("audiocraft")
    row("musicgen", "prompt", torch and ac, "ok" if (torch and ac) else "pip install audiocraft torch torchaudio")

    # YuE - repo checkout + torch
    yue_ok = bool(args.yue) and os.path.exists(os.path.join(os.path.expanduser(args.yue or ""), "inference", "infer.py")) and torch
    row("yue", "lyrics", yue_ok, "ok" if yue_ok else "clone YuE (cloud/yue_setup.sh) and pass --yue <path>")

    # DiffRhythm - repo checkout
    dr = os.path.expanduser(args.diffrhythm or "")
    dr_ok = bool(args.diffrhythm) and any(os.path.exists(os.path.join(dr, *p)) for p in
                                          (("infer", "infer.py"), ("scripts", "infer.py"), ("infer.py",))) and torch
    row("diffrhythm", "lyrics", dr_ok, "ok" if dr_ok else "clone DiffRhythm (cloud/diffrhythm_setup.sh) and pass --diffrhythm <path>")

    # HeartMuLa - heartlib importable or repo path
    hm = _have("heartlib") or (bool(args.heartlib) and os.path.isdir(os.path.expanduser(args.heartlib or "")))
    row("heartmula", "lyrics", torch and hm, "ok" if (torch and hm) else "install heartlib (cloud/heartmula_setup.sh)")

    return {"torch": torch, "engines": rows}


REPOS = {
    "yue": "https://github.com/multimodal-art-projection/YuE.git",
    "diffrhythm": "https://github.com/ASLP-lab/DiffRhythm.git",
    "heartmula": "https://github.com/HeartMuLa/heartlib.git",
    "sat": "https://github.com/Stability-AI/stable-audio-tools.git",
}


def _pip(*pkgs):
    return [sys.executable, "-m", "pip", "install", "-q", *pkgs]


def install_engine(engine, paths=None):
    """Best-effort, cross-platform dependency install for one engine.
    Uses pip / git only (works on Windows + Linux). Returns True if it ran."""
    import subprocess
    paths = paths or {}
    steps = []
    if engine == "musicgen":
        steps = [_pip("audiocraft", "torch", "torchaudio")]
    elif engine in ("sao", "sa3"):
        if not os.path.isdir("stable-audio-tools"):
            steps.append(["git", "clone", REPOS["sat"]])
        steps.append(_pip("-e", "./stable-audio-tools"))
        if engine == "sa3":
            print("[install] sa3 LoRA also needs stable-audio-3 (uv sync --extra lora) - see cloud/sa3_setup.sh", file=sys.stderr)
    elif engine in ("yue", "diffrhythm"):
        default = {"yue": "YuE", "diffrhythm": "DiffRhythm"}[engine]
        path = os.path.expanduser(paths.get(engine) or os.path.join(os.getcwd(), default))
        if not os.path.exists(path):
            steps.append(["git", "clone", REPOS[engine], path])
        steps.append(_pip("-r", os.path.join(path, "requirements.txt")))
    elif engine == "heartmula":
        if not os.path.isdir("heartlib"):
            steps.append(["git", "clone", REPOS["heartmula"]])
        steps.append(_pip("-e", "./heartlib"))
    elif engine == "ace-step":
        print("[install] ace-step runs as a REST server - start it with cloud/ace_step_setup.sh "
              "(can't auto-start a server safely).", file=sys.stderr)
        return False
    else:
        return False
    for cmd in steps:
        print("$ " + " ".join(cmd), file=sys.stderr)
        subprocess.run(cmd)
    return True


def _ns(**paths):
    return argparse.Namespace(
        ace_host=paths.get("ace_host", os.environ.get("ACESTEP_HOST", "http://localhost:8001")),
        yue=paths.get("yue", os.environ.get("YUE_REPO", "")),
        diffrhythm=paths.get("diffrhythm", os.environ.get("DIFFRHYTHM_REPO", "")),
        heartlib=paths.get("heartlib", os.environ.get("HEARTLIB_REPO", "")))


def preflight(engine, install=False, **paths):
    """Used by each workflow at startup. Returns True if the engine is ready;
    if not and install=True, attempts the install and re-checks."""
    res = check(_ns(**paths))
    row = next((r for r in res["engines"] if r["engine"] == engine), None)
    if row and row["ready"]:
        return True
    detail = row["detail"] if row else "unknown engine"
    print(f"[{engine}] NOT READY: {detail}", file=sys.stderr)
    if install:
        print(f"[{engine}] attempting auto-install (pip/git)...", file=sys.stderr)
        install_engine(engine, paths)
        res = check(_ns(**paths))
        row = next((r for r in res["engines"] if r["engine"] == engine), None)
        if row and row["ready"]:
            print(f"[{engine}] ready after install.", file=sys.stderr)
            return True
        print(f"[{engine}] STILL not ready: {row['detail'] if row else '?'}", file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser(description="Readiness check for each generation engine.")
    ap.add_argument("--json", action="store_true", help="machine-readable output (for the dashboard)")
    ap.add_argument("--ace-host", default=os.environ.get("ACESTEP_HOST", "http://localhost:8001"))
    ap.add_argument("--yue", default=os.environ.get("YUE_REPO", ""))
    ap.add_argument("--diffrhythm", default=os.environ.get("DIFFRHYTHM_REPO", ""))
    ap.add_argument("--heartlib", default=os.environ.get("HEARTLIB_REPO", ""))
    ap.add_argument("--install", metavar="ENGINE", help="auto-install one engine's deps (pip/git) then re-check")
    args = ap.parse_args()

    if args.install:
        ok = preflight(args.install, install=True, ace_host=args.ace_host,
                       yue=args.yue, diffrhythm=args.diffrhythm, heartlib=args.heartlib)
        sys.exit(0 if ok else 1)

    res = check(args)
    if args.json:
        print(json.dumps(res, indent=2))
        return
    print(f"torch available: {'yes' if res['torch'] else 'NO (most engines need it)'}\n")
    print(f"{'engine':12} {'kind':7} {'status':7} detail")
    print("-" * 64)
    for r in res["engines"]:
        mark = "READY" if r["ready"] else "MISS"
        print(f"{r['engine']:12} {r['kind']:7} {mark:7} {r['detail']}")
    ready = sum(1 for r in res["engines"] if r["ready"])
    print(f"\n{ready}/{len(res['engines'])} engines ready.")


if __name__ == "__main__":
    main()
