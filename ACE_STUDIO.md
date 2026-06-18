# ACE Studio integration (AI vocals over your beats)

ACE Studio is an AI singing/rapping voice synthesizer (Verse25, 140+ voices,
incl. a Rap genre) that turns MIDI + lyrics into vocals. It's GUI/VST-driven
(no CLI/API), and you already have ACE Bridge (VST3/ARA) in Ableton. So the
toolkit can't render ACE vocals headlessly, but it CAN prepare ACE's inputs.

## Where it fits
Three vocal paths now:
- **Instrumental only** - SA3 (`sa3_workflow.py song`). No vocals.
- **Auto full song w/ vocals** - HeartMuLa (`song_generate.py`). One-shot, less control.
- **Controllable studio vocals - ACE Studio (recommended for quality/control)**:
  toolkit makes the beat -> `vocal_guide.py` makes a flow MIDI + lyrics in the
  beat's key/BPM -> ACE sings/raps it -> ACE Bridge layers it over the beat in
  Ableton, tempo-synced.

## Workflow
1. Build/choose a beat; know its BPM + key (Deep Listen writes them, or pass manually).
2. Write lyrics (one line per bar-phrase; `[Verse]`/`[Hook]` headers ignored).
3. Generate the guide:
   ```
   python scripts/vocal_guide.py --beat "F:/.../MyBeat_instrumental.mp3" \
       --lyrics verse.txt --style rap --out guide
   # or explicit: --bpm 90 --key "F minor"
   ```
   Outputs `guide.mid` (flow aligned to the beat's grid/key) + `guide_lyrics.txt`
   (syllable-segmented to map onto notes).
4. In ACE Studio: new track -> import `guide.mid` -> paste the lyrics onto the
   notes -> choose a Rap (or sung) voice -> tweak timing/pitch -> render.
5. In Ableton: ACE Bridge plays the vocal tempo-synced over your beat. Bounce,
   then run the bounce through your VST chain (`vst_chain.py`) if you want.

## Notes
- `--style rap` = monotone/2-note rhythmic scaffold (you'll humanize in ACE).
  `--style sung` = simple stepwise topline in the key's scale as a melody seed.
- ACE also has its own Stem Splitter + Vocal->MIDI; for separation the toolkit's
  `remove_vocals.py` (BS-RoFormer) is comparable. ACE's Vocal->MIDI is unique
  (extract a melody from an existing vocal) - a handy manual step in ACE itself.
- Rights: AI vocals you generate are yours per ACE's license; the lyrics/melody
  you provide should be your own.
