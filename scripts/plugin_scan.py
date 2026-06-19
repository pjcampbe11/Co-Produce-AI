#!/usr/bin/env python3
"""
plugin_scan.py  -  Find VST3 / VST2 plugins on this Windows machine.

Scans the standard plugin folders, builds a catalog (name, path, format, a
best-guess instrument-vs-effect tag from the name), and writes
plugins_catalog.json next to the toolkit. The dashboard reads that catalog to
populate plugin dropdowns for vst_chain / vst_instrument so you don't paste paths.

Usage:
    python plugin_scan.py                      # scan default Windows locations
    python plugin_scan.py --dirs "D:/My VSTs"  # add extra folders
"""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Scans the standard Windows VST3/VST2 folders (+ --dirs). .vst3 bundles are recorded but NOT descended into.
#   - instrument-vs-effect is a guess from the name; writes plugins_catalog.json for the dashboard browser.
# ---------------------------------------------------------------------------
import argparse
import json
import os
from pathlib import Path

DEFAULT_DIRS = [
    r"C:\Program Files\Common Files\VST3",
    r"C:\Program Files\Common Files\VST2",
    r"C:\Program Files\VSTPlugins",
    r"C:\Program Files\Steinberg\VstPlugins",
    r"C:\Program Files\Common Files\Steinberg\VST3",
    r"C:\Program Files (x86)\VSTPlugins",
    r"C:\Program Files (x86)\Steinberg\VstPlugins",
]
INSTRUMENT_HINTS = ("kontakt", "battery", "massive", "fm8", "reaktor", "serum",
                    "sylenth", "omnisphere", "nexus", "synth", "piano", "keys",
                    "bass station", "operator", "sampler", "drum", "kit", "vital",
                    "spire", "diva", "phaseplant", "arcade", "playbox", "ace")


def classify(name):
    n = name.lower()
    return "instrument" if any(h in n for h in INSTRUMENT_HINTS) else "effect"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=[], help="Extra folders to scan")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "plugins_catalog.json"))
    args = ap.parse_args()

    seen, catalog = set(), []
    def add(path: Path):
        key = path.name.lower()
        if key in seen:
            return
        seen.add(key)
        fmt = {".vst3": "VST3", ".dll": "VST2", ".vst": "VST"}.get(path.suffix.lower(), "?")
        catalog.append({"name": path.stem, "path": str(path), "format": fmt,
                        "kind": classify(path.stem)})
    for d in DEFAULT_DIRS + args.dirs:
        base = Path(d)
        if not base.is_dir():
            continue
        for root, dnames, fnames in os.walk(base, onerror=lambda e: None):
            rp = Path(root)
            # .vst3 bundles are folders: record them and DON'T descend (avoids
            # crashing on the dll/resources inside, and matches Windows behavior)
            for dn in list(dnames):
                if dn.lower().endswith(".vst3"):
                    add(rp / dn)
                    dnames.remove(dn)
            for fn in fnames:
                low = fn.lower()
                if low.endswith((".vst3", ".dll", ".vst")):
                    add(rp / fn)
    catalog.sort(key=lambda c: c["name"].lower())
    Path(args.out).write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    inst = sum(1 for c in catalog if c["kind"] == "instrument")
    print(f"Found {len(catalog)} plugins ({inst} likely instruments, {len(catalog)-inst} effects).")
    print(f"Catalog: {args.out}")
    for c in catalog[:15]:
        print(f"  [{c['format']}/{c['kind']:10}] {c['name']}")
    if len(catalog) > 15:
        print(f"  ... and {len(catalog)-15} more")


if __name__ == "__main__":
    main()
