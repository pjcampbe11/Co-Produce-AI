#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Co-Produce AI — build EVERYTHING in one shot  (SONG MODE, full-length)
#
# One-liner (from /workspace on the pod, kit unzipped to /workspace/runpod_pack_kit):
#   LORA=/workspace/sweeps/run_r16a16_lr2e4/<best>.safetensors bash /workspace/runpod_pack_kit/build_all.sh all
#
# EVERYTHING renders in SA3 **song mode** at >= 3:08 (188s) for solid quality & sonics.
#
# Modes:
#   packs   → the 4 style packs (full 3:08 songs + carved one-shots + stems, zipped per pack)
#   part4   → every Part 4 prompt set: starter, arrangement, capability(100), PRO(20) — all full songs
#   flips   → the 20 flips (also needs IN=/path/to/beat.wav)
#   all     → packs + part4  (add flips by also setting IN=...)
#
# Env overrides:
#   SONG_DUR=188     length of EVERY render (3:08). Raise for longer.
#   STEPS=250        diffusion steps — higher = more detail/sonics
#   CFG=8            guidance scale (prompt adherence)
#   STR=0.7          LoRA strength
#   STEMS=1          demucs 4-stem split per song (0 to skip — much faster)
#   ONESHOTS=12      one-shots carved per pack
#   RESUME on by default — re-run and it skips anything already rendered.
#
# NOTE: song mode is required (this is not the trainer's --demo_every auto-demos).
#       Verify `sa3_workflow.py song` works on the pod before a full run.
#       ~160 full songs total is heavy GPU time — it's resumable, do it in batches
#       (run `packs` and `part4` separately, or set STEMS=0 for a fast first pass).
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
MODE="${1:-all}"
LORA="${LORA:?Set LORA=/path/to/your .safetensors checkpoint}"
IN="${IN:-}"
SONG_DUR="${SONG_DUR:-188}"     # 3:08 — everything is a full song
STEPS="${STEPS:-250}"
CFG="${CFG:-8}"
STR="${STR:-0.7}"
STEMS="${STEMS:-1}"
ONESHOTS="${ONESHOTS:-12}"
REPO="${REPO:-/workspace/stable-audio-3}"
PY="$REPO/.venv/bin/python"
WF="$REPO/scripts/sa3_workflow.py"
KIT="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-/workspace/coproduce_build}"
NEG="off-key, out of tune, vocals, singing, muddy mix, clipping, harsh noise"
FAILED=0

gen() { # 1:prompt 2:dur 3:lora-strength 4:cfg 5:steps 6:seed 7:negative 8:out
  [ -f "$8" ] && { echo "  ✓ exists, skip: $(basename "$8")"; return 0; }
  mkdir -p "$(dirname "$8")"
  echo "  ► $(basename "$8")  (${2}s, str $3, cfg $4, steps $5, seed $6)"
  WANDB_MODE=disabled "$PY" "$WF" song --model medium-base --lora "$LORA" \
    --lora-strength "$3" --prompt "$1" --duration "$2" \
    --cfg "$4" --steps "$5" --seed "$6" --negative "$7" --out "$8" \
    || { echo "  ✗ FAILED: $8"; FAILED=$((FAILED+1)); }
}

keytag() { local k="$1"; k="${k/ minor/min}"; k="${k/ major/maj}"; k="${k//#/s}"; echo "${k// /}"; }

oneshots() { # 1:pack_dir  — carve one-shots from the pack's songs via onset slicing
  "$PY" - "$1" "$ONESHOTS" <<'PYEOF'
import sys, os, glob
pack, want = sys.argv[1], int(sys.argv[2])
try:
    import librosa, soundfile as sf, numpy as np
except ImportError:
    os.system(f"{sys.executable} -m pip -q install librosa soundfile"); import librosa, soundfile as sf, numpy as np
os.makedirs(f"{pack}/One-Shots", exist_ok=True)
made = 0
for wav in sorted(glob.glob(f"{pack}/Songs/*.wav")):
    if made >= want: break
    y, sr = librosa.load(wav, sr=None, mono=False)
    mono = y.mean(axis=0) if y.ndim > 1 else y
    on = librosa.onset.onset_detect(y=mono, sr=sr, units="samples", backtrack=True)
    for s in on[:3]:
        if made >= want: break
        e = min(s + int(0.6*sr), (y.shape[-1] if y.ndim>1 else len(y)))
        seg = y[..., s:e].copy()
        n = seg.shape[-1]
        if n < int(0.05*sr): continue
        fade = np.linspace(1, 0, min(int(0.02*sr), n))
        seg[..., -len(fade):] *= fade
        made += 1
        base = os.path.basename(wav).replace("_song","").replace(".wav","")
        sf.write(f"{pack}/One-Shots/{base}_oneshot_{made:02d}.wav", seg.T if seg.ndim>1 else seg, sr)
print(f"  one-shots: {made} → {pack}/One-Shots")
PYEOF
}

build_pack() { # 1:prefix 2:folder-name 3:manifest
  local prefix="$1" name="$2" mf="$KIT/prompts/$3" dir="$OUT/packs/$2" i=0
  echo "═══ PACK: $name  (full ${SONG_DUR}s songs) ═══"
  mkdir -p "$dir/Songs"
  while IFS='|' read -r bpm key prompt; do
    case "$bpm" in ''|\#*) continue;; esac
    i=$((i+1))
    # drop the "loop" token so song mode builds a full arrangement in the pack's style
    local sp="${prompt/, loop,/, full track,}"
    gen "$sp" "$SONG_DUR" "$STR" "$CFG" "$STEPS" "$((7000+i))" "$NEG" \
        "$dir/Songs/${prefix}_$(printf %02d "$i")_${bpm}BPM_$(keytag "$key")_song.wav"
  done < "$mf"
  oneshots "$dir"
  if [ "$STEMS" = "1" ]; then
    echo "  stems (demucs)…"
    "$PY" -c "import demucs" 2>/dev/null || "$PY" -m pip -q install demucs
    "$PY" -m demucs -n htdemucs --out "$dir/Stems" "$dir/Songs"/*.wav || echo "  ✗ demucs failed (pack still valid without stems)"
  fi
  ( cd "$OUT/packs" && zip -qr "${name}.zip" "$name" ) && echo "  ✓ $OUT/packs/${name}.zip"
}

part4() {
  echo "═══ PART 4: starters (§9) — full ${SONG_DUR}s songs ═══"
  local i=0
  while read -r prompt; do
    case "$prompt" in ''|\#*) continue;; esac; i=$((i+1))
    local sp="${prompt/, loop,/, full track,}"
    gen "$sp" "$SONG_DUR" "$STR" "$CFG" "$STEPS" "$((100+i))" "$NEG" "$OUT/part4/starter/starter_$(printf %02d $i).wav"
  done < "$KIT/prompts/part4_starter.txt"
  i=0
  while read -r prompt; do
    case "$prompt" in ''|\#*) continue;; esac; i=$((i+1))
    gen "$prompt" "$SONG_DUR" "$STR" "$CFG" "$STEPS" "$((200+i))" "$NEG" "$OUT/part4/starter/verbose_$(printf %02d $i).wav"
  done < "$KIT/prompts/part4_starter_verbose.txt"
  echo "═══ PART 4: arrangement set (§10) — full ${SONG_DUR}s songs ═══"
  sed 's/\r$//' "$KIT/prompts/part4_arrangement.txt" | while IFS='|' read -r name prompt dur str; do
    case "$name" in ''|\#*) continue;; esac
    gen "$prompt" "$SONG_DUR" "${str:-0.6}" "$CFG" "$STEPS" 42 "$NEG" "$OUT/part4/arrangement/${name}.wav"
  done
  echo "═══ PART 4: capability library (§11, 100 presets) — full ${SONG_DUR}s songs ═══"
  sed 's/\r$//' "$KIT/prompts/part4_capability.txt" | while IFS='|' read -r name prompt dur str; do
    case "$name" in ''|\#*) continue;; esac
    local sp="${prompt/, loop,/, full track,}"
    gen "$sp" "$SONG_DUR" "${str:-0.7}" "$CFG" "$STEPS" 42 "$NEG" "$OUT/part4/capability/${name}.wav"
  done
  echo "═══ PART 4: PRO presets (§13) — full ${SONG_DUR}s songs ═══"
  sed 's/\r$//' "$KIT/prompts/part4_pro.txt" | while IFS='|' read -r name prompt dur str cfg steps seed negp; do
    case "$name" in ''|\#*) continue;; esac
    gen "$prompt" "$SONG_DUR" "${str:-0.7}" "${cfg:-$CFG}" "${steps:-$STEPS}" "${seed:-42}" "${negp:-$NEG}" "$OUT/part4/pro/${name}.wav"
  done
}

flips() {
  [ -n "$IN" ] || { echo "flips: set IN=/path/to/beat.wav — skipping"; return; }
  echo "═══ PART 4: 20 flips (§12) on $IN ═══"
  mkdir -p /workspace/flips
  ( cd "$REPO" && LORA="$LORA" IN="$IN" bash "$KIT/prompts/part4_flips.sh" )
}

command -v zip >/dev/null || { apt-get update -qq && apt-get install -y -qq zip; }
mkdir -p "$OUT"
case "$MODE" in
  packs) build_pack BBD "Boom-Bap_Dust_Vol1" pack_boombap.txt
         build_pack TRN "Trap_Nights_Vol1"   pack_trap.txt
         build_pack DRS "Drill_Sessions"     pack_drill.txt
         build_pack LAH "LoFi_After_Hours"   pack_lofi.txt ;;
  part4) part4 ;;
  flips) flips ;;
  all)   build_pack BBD "Boom-Bap_Dust_Vol1" pack_boombap.txt
         build_pack TRN "Trap_Nights_Vol1"   pack_trap.txt
         build_pack DRS "Drill_Sessions"     pack_drill.txt
         build_pack LAH "LoFi_After_Hours"   pack_lofi.txt
         part4; [ -n "$IN" ] && flips ;;
  *) echo "usage: build_all.sh [packs|part4|flips|all]"; exit 1 ;;
esac

echo "─── master zip ───"
( cd "$OUT" && zip -qr "coproduce_all_$(date +%Y%m%d).zip" packs part4 2>/dev/null )
ls -lh "$OUT"/*.zip "$OUT"/packs/*.zip 2>/dev/null
echo
echo "DONE. Failures: $FAILED"
echo "Ship to Windows:  runpodctl send $OUT/coproduce_all_$(date +%Y%m%d).zip"
