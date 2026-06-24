#!/usr/bin/env python3
"""End-to-end Python client for the CoProduce AI SaaS API.

Does the full loop: (optionally) sign up for an API key, submit a job, poll
until it completes, and download the resulting audio.

Examples
--------
  # first run: create an account, then generate a beat and save it
  python beat_client.py --base-url http://localhost:8000 --signup you@example.com \
      --task beat --param style=trap --param bpm=140 --out trap.wav

  # later: reuse your key
  python beat_client.py --key bt_xxx --task beat --param style=boom_bap --out bb.wav

  # a CPU tagging job (prints JSON, no download)
  python beat_client.py --key bt_xxx --task tag --param path=/data/x.wav
"""
import argparse
import sys
import time

import requests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--key", help="API key (bt_...). Omit with --signup to create one.")
    ap.add_argument("--signup", metavar="EMAIL", help="create an account, print + use the new key")
    ap.add_argument("--admin-token", default="", help="X-Admin-Token (if public signup is off)")
    ap.add_argument("--task", default="beat", help="beat | tag | flip | remix | song")
    ap.add_argument("--param", action="append", default=[], metavar="k=v",
                    help="job param (repeatable), e.g. --param style=trap --param bpm=140")
    ap.add_argument("--out", help="download the result wav to this path (if the job makes audio)")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between status polls")
    a = ap.parse_args()
    base = a.base_url.rstrip("/")

    key = a.key
    if a.signup:
        h = {"X-Admin-Token": a.admin_token} if a.admin_token else {}
        r = requests.post(f"{base}/v1/signup", json={"email": a.signup}, headers=h, timeout=30)
        r.raise_for_status()
        d = r.json()
        key = d["api_key"]
        print(f"signed up: {d['email']}  credits={d['credits']}\nAPI KEY (save this): {key}")
    if not key:
        sys.exit("provide --key or --signup EMAIL")

    H = {"authorization": f"Bearer {key}"}

    # parse --param k=v into a dict, coercing ints/floats
    params = {}
    for kv in a.param:
        if "=" not in kv:
            sys.exit(f"bad --param '{kv}', expected k=v")
        k, v = kv.split("=", 1)
        if v.isdigit():
            v = int(v)
        else:
            try:
                v = float(v)
            except ValueError:
                pass
        params[k] = v

    # submit
    r = requests.post(f"{base}/v1/jobs", headers=H,
                      json={"task": a.task, "params": params}, timeout=30)
    if r.status_code == 402:
        sys.exit("out of credits — buy a plan at /pricing")
    r.raise_for_status()
    job = r.json()
    job_id = job["id"]
    print(f"submitted {a.task} job {job_id} (cost {job['cost']} credits)")

    # poll
    while True:
        s = requests.get(f"{base}/v1/jobs/{job_id}", headers=H, timeout=30).json()
        print("status:", s["status"])
        if s["status"] == "completed":
            print("result:", s.get("result"))
            break
        if s["status"] == "failed":
            sys.exit(f"job failed: {s.get('error')}")
        time.sleep(a.interval)

    # download
    if a.out:
        rr = requests.get(f"{base}/v1/jobs/{job_id}/result", headers=H, timeout=120)
        if rr.status_code == 200:
            with open(a.out, "wb") as f:
                f.write(rr.content)
            print(f"wrote {a.out} ({len(rr.content)} bytes)")
        else:
            print(f"no downloadable file (status {rr.status_code})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
