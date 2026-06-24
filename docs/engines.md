# Generation engines — comparison & when to use which

Co-Produce AI can drive several music models. Pick one through the unified
router (`scripts/generate_engine.py --engine <name>`), the dashboard, or each
engine's own workflow script. All listed here are self-hostable and
commercial-use-friendly except where noted.

## Prompt → beat / instrumental

| Engine | Script | License | Best for | Notes |
| --- | --- | --- | --- | --- |
| `sa3` | sa3_workflow.py | Stability Community (≤$1M) | **your-sound LoRA**, sample packs | recommended default for packs |
| `sao` | generate.py | Stability Community | full fine-tune control | heavier to train |
| `ace-step` | ace_step_workflow.py | Apache-2.0 | **fast** (<2s/A100), also vocals, LoRA | REST server on :8001 |
| `musicgen` | musicgen_workflow.py | commercial-OK | **melody conditioning** (hum→beat) | `facebook/musicgen-melody` |

## Lyrics → full song (with vocals)

| Engine | Script | License | Best for | Notes |
| --- | --- | --- | --- | --- |
| `yue` | yue_workflow.py | Apache-2.0 | **lyrics→5-min song**, strong vocals | ~16–24 GB VRAM, closest to Suno |
| `diffrhythm` | diffrhythm_workflow.py | open | **fast** lyric drafts | diffusion, great for iterating |
| `heartmula` | song_generate.py | Apache-2.0 | full songs | existing path |
| `ace-step` | ace_step_workflow.py | Apache-2.0 | lyrics+tags→song, fast | shared with prompt path |

Commercial cloud models (Suno v5.5, Udio v1.5) are **not self-hostable** — only
callable by API — so they aren't embedded; add them as optional paid backends if
you want top-end drafts.

## Vocals: ACE Studio

`vocal_guide.py` prepares ACE Studio inputs from a beat: a flow/melody MIDI on
the key+BPM grid, syllable-segmented lyrics, and (new) **expression envelopes** —
power (CC11), breathiness (CC74), and pitch inflection (pitchwheel), plus a
`<out>_expression.json` the ACE Bridge can apply per note. ACE Studio also does
voice **cloning** (clone your own voice once, reuse it across tracks) — the vocal
counterpart to the "your own sound" thesis.

## Quick picks

- Sample pack in *your* sound → **sa3**.
- Fast instrumental idea → **ace-step**; around a hum/melody → **musicgen**.
- Your lyrics → finished rap song → **yue** (quality) or **diffrhythm** (speed first, then re-render).
- Vocals over a beat in your voice → **vocal_guide.py** → ACE Studio (clone) → ACE Bridge.

## Unified router

```bash
python scripts/generate_engine.py --list
python scripts/generate_engine.py --engine sa3 --plan prompts/pack_plan.example.json --out generated
python scripts/generate_engine.py --engine musicgen --prompt "boom bap, dusty, 90 bpm" --melody hum.wav --out gen
python scripts/generate_engine.py --engine yue --yue ~/YuE --lyrics verse.txt --genre "hip hop, 90 bpm" --out songs
```

Cloud setup: `cloud/yue_setup.sh`, `cloud/diffrhythm_setup.sh`, `cloud/musicgen_setup.sh`
(and the existing `cloud/ace_step_setup.sh`, `cloud/sa3_setup.sh`, `cloud/heartmula_setup.sh`).

## Readiness check

Before a run, see what's actually installed:

```bash
python scripts/engine_doctor.py            # green/red table per engine
python scripts/engine_doctor.py --json     # machine-readable (dashboard uses this)
```

It only probes imports/paths/REST — no models loaded, no GPU touched. The
dashboard's **🩺 Engine status** tab renders the same check as green/red dots.

### Preflight + auto-install

The YuE / DiffRhythm / MusicGen workflows **self-check before running** and refuse
to start if their deps are missing, printing the exact fix. Add `--install` to
auto-install (pip/git, cross-platform) and continue, or `--skip-check` to bypass:

```bash
python scripts/musicgen_workflow.py --prompt "boom bap, 90 bpm" --install
python scripts/engine_doctor.py --install yue --yue ~/YuE   # install one engine directly
```

Auto-install covers musicgen (pip), yue/diffrhythm/heartmula/sao (git clone + pip).
ace-step is a REST server — start it with `cloud/ace_step_setup.sh` (not auto-started).
