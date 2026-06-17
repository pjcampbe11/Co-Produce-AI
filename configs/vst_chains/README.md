# Ready-made VST3 chains (built from your installed plugins)

These reference real plugins in `C:\Program Files\Common Files\VST3` and run
through `09_vst_chain.py` (pedalboard hosts them headlessly - no DAW).

| Chain | For | Plugins |
|---|---|---|
| `dusty_boombap.json` | hip-hop character (technique #4/#9) | Saturn 2 -> TR5 TASCAM 388 -> Pro-C 2 -> Pro-Q 3 -> Pro-L 2 |
| `metal_master.json` | rock/metal | Pro-Q 3 -> Trash -> Pro-C 2 -> Pro-L 2 |
| `bassmusic_neuro.json` | dubstep/dnb | Thermal -> Portal -> Pro-Q 3 -> Pro-L 2 |
| `destroy_extreme.json` | 16_destroy_heal.py input | Dirt -> TR5 Tape 80 -> Thermal -> Pro-L 2 |
| `ozone_vocal_suppress.json` | last-resort vocal removal | Ozone 11 Master Rebalance |

## First run - dial each plugin in by ear (one time)

pedalboard loads plugins at their default state. To set them up, open each
plugin's GUI once and the settings are captured for the whole batch:

```bat
:: see a plugin's tweakable parameter names
python scripts\09_vst_chain.py --list-params "C:\Program Files\Common Files\VST3\FabFilter\FabFilter Saturn 2.vst3"

:: open the GUI of chain item 0, dial it, close window -> applied to the batch
python scripts\09_vst_chain.py --input "F:\samples_in" --output "F:\samples_out" --chain configs\vst_chains\dusty_boombap.json --edit 0
```

## Batch process (drives can differ from where the repo lives)

```bat
python scripts\09_vst_chain.py --input "F:\RAP_ARCHIVES\raw_beats" --output "F:\RAP_ARCHIVES\beats_dusty" --chain configs\vst_chains\dusty_boombap.json
```

## Notes
- pedalboard renders offline at the file's sample rate; mono or stereo in = same out.
- VST3 paths use forward slashes in JSON - valid on Windows.
- Vocal removal: prefer `11_remove_vocals.py` (BS-RoFormer). Use
  `ozone_vocal_suppress.json` only if you specifically want the Ozone route;
  open it with `--edit 0` and pull the Vocals slider to minimum.
- Technique #4 (bake your mix into the model): run your TRAINING dataset through
  a character chain BEFORE fine-tuning, so the model learns your sound.
