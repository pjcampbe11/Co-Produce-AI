# clients/python — API example (signup → submit → download)

A single-file client for the Co-Produce AI SaaS API ([README §35](../../README.md#35-saas)).

```bash
pip install -r requirements.txt

# create an account + generate a beat, save the wav
python beat_client.py --base-url http://localhost:8000 --signup you@example.com \
    --task beat --param style=trap --param bpm=140 --out trap.wav

# reuse your key next time
python beat_client.py --key bt_xxx --task beat --param style=boom_bap --out bb.wav
```

It signs up (or uses `--key`), submits a job, polls to completion, and downloads
the audio. Use `--admin-token` if the server has public signup disabled.
