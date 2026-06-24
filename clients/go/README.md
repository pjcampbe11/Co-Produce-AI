# clients/go — typed Go client for the CoProduce AI serverless endpoint

Submits a job to your RunPod Serverless endpoint (see
[README §33](../../README.md#33-serverless)), polls until it's done, and decodes
the returned `wav_b64` straight to a `.wav` file.

## Setup

```powershell
cd clients/go
go mod tidy            # pulls github.com/runpod/go-sdk, writes go.sum
```

## Credentials (set once per shell)

```powershell
$env:RUNPOD_API_KEY="your_runpod_api_key"   # console -> Settings -> API Keys
$env:ENDPOINT_ID="your_endpoint_id"         # console -> Serverless -> your endpoint
```

- **RUNPOD_API_KEY** — RunPod console → **Settings → API Keys → + Create**. Pick
  read/write. Account-wide; shown once, so copy it.
- **ENDPOINT_ID** — RunPod console → **Serverless** → click your endpoint. The id
  is on the page and in its URL: `https://api.runpod.ai/v2/<ENDPOINT_ID>/run`.
  You only have one after you deploy an endpoint (README §33, steps 1–4).

## Run

```powershell
go run . -task beat -style trap -bpm 140 -out trap.wav
go run . -task flip -path in.wav -prompt "dusty soul chop" -out flip.wav
go run . -task tag  -path in.wav            # prints tags JSON, no audio
```

Flags: `-task beat|tag|flip`, `-style`, `-bpm`, `-prompt`, `-path`, `-out`,
`-interval` (poll seconds). Build a standalone exe with `go build -o beatcli.exe .`.
