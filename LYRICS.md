# Lyric model (your voice -> verses/hooks -> beats)

Train on YOUR own lyrics, generate new bars in your style with a LOCAL model,
then turn them into beats. Fully private (Ollama runs on your PC).

Lyrics live in `F:\RAP_ARCHIVES\lyrics` (folder of .txt).

## 1. Profile your style
```
python scripts\lyric_analyze.py --input "F:\RAP_ARCHIVES\lyrics" --out lyric_model
```
Splits into verses/hooks, measures flow density, rhyme rate, vocabulary, themes,
and mood. Writes `lyric_model\style_profile.json` (+ a readable style summary)
and `corpus.jsonl` (your sections, used as few-shot examples).

## 2. One-time Ollama setup
- Install Ollama: https://ollama.com
- Pull a model: `ollama pull llama3.1:8b`  (or qwen2.5:7b / mistral)
- `pip install requests`
(On a 6GB 2060, an 8B model in 4-bit runs but slowly; a 3B like `llama3.2:3b`
is snappier. Bigger/better = run on a cloud GPU pod with Ollama.)

## 3. Generate in your style
```
python scripts\lyric_generate.py --model-dir lyric_model --mode verse --mood dark ^
   --theme "grinding through the cold" --bars 16 --variations 2 --out verses
python scripts\lyric_generate.py --model-dir lyric_model --mode hook --mood triumphant --out hooks
```
Injects your style summary + your real sections as voice anchors; writes .txt files.
NOTE: it's a writing aid in your voice - always edit; small corpora make models
echo your phrasing, so treat output as a draft and keep it yours.

## 4. Turn a lyric into a beat brief + flow MIDI
```
python scripts\lyric_to_beat.py --lyrics verses\verse_dark_01.txt --out beat_brief
```
Infers mood + flow -> suggests genre/BPM/key + a beat prompt, writes a pack_plan,
and prints the exact `sa3_workflow.py song` and `vocal_guide.py` commands so the
lyric seeds your tuned beat model and the ACE Studio vocal flow.

## The full loop
your lyrics -> lyric_analyze -> lyric_generate (your voice) -> lyric_to_beat
-> sa3_workflow/beat_builder (instrumental in your trained sound) + vocal_guide
-> ACE Studio (vocal) -> Ableton (ACE Bridge) -> finished track.
