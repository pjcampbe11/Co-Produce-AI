# Genre Expansion: Rock/Metal + Dubstep/DnB

The pipeline is genre-agnostic - what changes per genre is the data, the label
vocabulary, the BPM conventions, and the pattern grammar. This guide covers the
two new lines. Everything in the main README applies; only differences are here.

## Model strategy: one LoRA per genre

Do NOT mix genres into one fine-tune - sounds bleed and prompts get mushy.
With Stable Audio 3 (see `sa3_workflow.py`), train a separate LoRA per line:

| LoRA | Trained on | Typical use |
|---|---|---|
| `hiphop_v1.safetensors` | your hip-hop library | existing line |
| `rockmetal_v1.safetensors` | rock/metal library | riffs, kits, full stems |
| `bassmusic_v1.safetensors` | dubstep/dnb library | breaks, reese/wobble, risers |

LoRAs are stackable at runtime - `metal LoRA 1.0 + bassmusic LoRA 0.4` for
hybrid trap-metal/drumstep flavors is a product nobody else ships (ab_models
also works across LoRAs for "two-producer" packs).

## Library layout + label vocabulary (folder names ARE the prompts)

### Rock / Metal
```
raw_library_rockmetal/
  drums_oneshots/kicks|snares|toms|cymbals/   (china, splash, crash, ride)
  drums_loops/rock|metal|dbeat/
  melodic_loops/riffs/        tags.txt: palm-muted, drop C, high-gain, djent, tremolo picked
  melodic_loops/bass/         tags.txt: distorted bass guitar, driving
  melodic_loops/leads/        tags.txt: solo, harmonized leads
  stems/
```
Vocabulary that matters in prompts/tags: palm-muted chugs, drop tuning (drop C/D),
high-gain, djent, blast beat, double kick, d-beat, breakdown, half-time,
room mics, triggered kick, china accents, tremolo picking, power chords.

### Dubstep / DnB
```
raw_library_bassmusic/
  drums_oneshots/kicks|snares|hats|cymbals/
  drums_loops/dnb_breaks|dubstep_halftime/    tags.txt: chopped amen, two step, rolling
  melodic_loops/bass/                          tags.txt: reese, wobble, neuro growl, sub
  melodic_loops/pads|leads/
  fx/risers|impacts|downlifters/
  stems/
```
Vocabulary: reese bass, wobble, LFO growl, neuro, sub drop, amen break,
two-step, rolling, halftime, 140, 174, riser, impact, drop, foghorn, stab.

## BPM conventions (important - detection defaults assume hip-hop)

| Line | Convention | Prep/post flags |
|---|---|---|
| Hip-hop | 60-180 fold (default) | none |
| Rock/Metal | up to ~220 | `--bpm-min 80 --bpm-max 220` |
| DnB | 170-176 (never folded to 87!) | `--bpm-min 100 --bpm-max 200` |
| Dubstep | written 140, FEELS halftime 70 | `--bpm-min 100 --bpm-max 200`; label 140 |

Use those flags on `prepare_dataset.py` and `postprocess.py` per library.
`ecosystem_pack.py verify` already accepts half/double-time matches.

## Beat builder styles (08) - new grids

`--style rock` (120) straight-8ths backbeat | `--style metal` (160-200) double-kick
16ths under halftime backbeat | `--style dbeat` (180) punk drive |
`--style dubstep` (140) halftime, space for wobble, 808 lane = bass stabs |
`--style dnb` (174) two-step | `--style amen` (172-176) ghost-heavy chopped-break feel.

All support `--rotate` (13 micro-variants) and `--groove` (14). Groove DNA is
genre-portable: extract from a classic rock break or an amen and apply to any kit.
For dnb at 174, 16th steps are ~86 ms - keep one-shots tight (run 04 first).

## Pack plans + presets

- `prompts/pack_plan.rock_metal.json` - kits, china/toms, riff loops in E minor @160
- `prompts/pack_plan.dubstep_dnb.json` - breaks @174, halftime @140, reese/wobble, risers
- Push presets: metalriff, metaldrums, dnbbreak, reese, wobble added to
  `prompts/push_presets.example.json`

Ecosystem locks that sell: DnB packs at exactly 174 + one key family;
metal packs per tuning (a "Drop C" series) - tuning-locked packs are the
metal equivalent of key-locked, and nobody does them.

## Creative techniques, genre-translated

- Destroy-and-heal (16): THE dubstep texture machine - wreck a clean bass with
  the destroy chain, heal at 0.2-0.3 with "neuro growl" prompts.
- Flip lineage (15): amen break -> 4 stages -> your legally-distinct house break.
- Micro-variants (13): metal double-kick at 16ths sounds machine-gun fake with
  one sample - 8 kick variants + --rotate fixes exactly that.
- Call-and-response (19): guitarist records a riff -> model answers with the
  harmonized double or the drum part ("metal, drums loops, 160 BPM..." prompt).
- Vocal removal (11): band demos -> instrumentals for remix/sample clearance work.

## QA ears per genre (what to reject)

Rock/metal: flabby low-mids in chugs, fake-sounding cymbal decay, kick click
that disappears in context, riffs that drift off-grid.
Dubstep/dnb: weak sub weight (check on a sub or spectrum - energy must sit
30-60 Hz), mushy break transients, wobbles whose LFO doesn't lock to tempo,
risers that peak early. Reject rates run higher than hip-hop one-shots - plan
3-4x overgeneration for bass music.
