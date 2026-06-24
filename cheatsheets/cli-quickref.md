# CLI quick reference

All scripts are in `scripts/`. Run `python scripts/<name>.py --help` for full flags.

## Prep & analyze
| Script | Does | Key flags |
| --- | --- | --- |
| `organize_soundbank.py` | classify/sort a messy library | `--input --output --move --ai-tags` |
| `mp3_to_wav.py` | batch MP3→WAV | `--input --output --mirror --resume` |
| `remove_vocals.py` | stem separation (BS-RoFormer) | `--input --output --engine --mp3` |
| `deep_listen.py` | analyze tempo/key/events/vibe | `--input --for-captions --no-vibe` |
| `auto_tag.py` | mood/vibe tags | `--stems-dir --engine heuristic\|qwen3-omni\|clap` |
| `genius_lookup.py` | producer/album/year | `--beats --token --resume` |
| `build_captions.py` | fuse analysis+tags+genius → caption | `--beats --reports` |
| `prepare_dataset.py` / `validate_dataset.py` | build/check training set | `--input --output --bpm-min --bpm-max` |
| `playlist_meta.py` | Spotify playlist metadata | `-pl --audio-features --samples -f md\|json\|csv` |
| `genre_playlists.py` | best playlists per genre | `-g <genre>\|all --limit -f md\|json` |
| `playlist_catalog.py` | per-song catalog (metadata + Genius link, no lyrics) | `--json --out --resume` |
| `sample_dna.py` | sample lineage \u2192 original prompts + audio2audio flips | `--catalog --out --flips --flip-input` |

## Generate & transform
| Script | Does | Key flags |
| --- | --- | --- |
| `sa3_workflow.py` | Stable Audio 3 (LoRA) | `prepare\|plan\|flip\|song --model --lora` |
| `ace_step_workflow.py` | ACE-Step 1.5 engine | `generate\|song\|cover\|train --host` |
| `generate.py` | Stable Audio Open inference | `--plan --steps --cfg` |
| `audio2audio.py` | flip a sound | `--input --prompt --strength` |
| `remix.py` | genre transform / mashup | `--input --genre --mode` |
| `beat_builder.py` | beats from your samples | `--style --bpm --bars --count` |
| `song_generate.py` | full songs w/ vocals (HeartMuLa) | `--lyrics-file --tags --duration` |

## Creative Lab
`microvariants.py` · `groove_dna.py` · `flip_lineage.py` · `destroy_heal.py` ·
`ab_models.py` · `call_response.py`* · `ecosystem_pack.py` (plan\|verify) ·
`curation_loop.py` (score\|promote) · `push_generation_server.py`* · `ableton_bridge.py`†
&nbsp;&nbsp;*long-running &nbsp; †needs Ableton + AbletonOSC

## VST / lyrics / finish
`plugin_scan.py` · `vst_instrument.py` · `vst_chain.py` · `vocal_guide.py` ·
`lyric_analyze.py` · `lyric_generate.py` · `lyric_to_beat.py` ·
`postprocess.py` · `build_pack.py` · `provenance.py`

## Dashboard
`python dashboard.py` → every script above as a tab, with live logs, Audition,
Cloud/Deploy, Server/API, and Inspiration tabs.
