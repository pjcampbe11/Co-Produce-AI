# Cloud connect cheat-sheet (RunPod)

Quick reference for connecting this machine to RunPod — S3 network volume and
SSH. Filled in with the known IDs/endpoints; **secrets are never stored here**
(keys live in your AWS profile / `~/.ssh`, not in the repo).

Known values:

| Thing            | Value                                   |
| ---------------- | --------------------------------------- |
| Network volume / bucket | `d39orqnjjh`                     |
| Datacenter / region     | `eu-ro-1`                        |
| S3 endpoint             | `https://s3api-eu-ro-1.runpod.io` |
| SSH key (Windows)       | `%USERPROFILE%\.ssh\id_ed25519`  |

---

## 1. S3 network volume (AWS CLI, PowerShell 7)

Credentials come from **RunPod console -> Settings -> S3 API Keys** (separate
from your normal RunPod API key; the secret is shown only once). These are S3
API keys, not your account password.

One-time install (if needed):

```powershell
winget install -e --id Amazon.AWSCLI
```

One-time profile setup (paste your two S3 keys):

```powershell
aws configure set aws_access_key_id "YOUR_S3_ACCESS_KEY_ID" --profile runpod; aws configure set aws_secret_access_key "YOUR_S3_SECRET" --profile runpod; aws configure set region eu-ro-1 --profile runpod
```

List the volume:

```powershell
aws s3 ls --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io s3://d39orqnjjh/
```

Upload a file (RunPod needs the checksum flag):

```powershell
aws s3 cp .\myfile.wav s3://d39orqnjjh/myfile.wav --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io --checksum-algorithm CRC32
```

Upload a whole folder (e.g. push beats once, read from any pod):

```powershell
aws s3 cp "F:\RAP_ARCHIVES\raw_beats" s3://d39orqnjjh/raw_beats/ --recursive --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io --checksum-algorithm CRC32
```

Download from the volume back to local:

```powershell
aws s3 cp s3://d39orqnjjh/raw_beats/ "F:\RAP_ARCHIVES\raw_beats" --recursive --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io
```

Tip: the bucket name is the volume ID and the region must match the volume's
datacenter, or you get signature/endpoint errors.

---

## 2. SSH (PowerShell 7 on Windows)

One-time: generate a key and register it with your account.

```powershell
ssh-keygen -t ed25519 -C "patcampbell82@gmail.com"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

If `ssh-keygen` is missing, run as Admin once:
`Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0`

Then paste the clipboard into **SSH Public Keys** at
<https://www.console.runpod.io/user/settings> (must start with `ssh-ed25519`,
one key per line).

Connect — copy the exact command from the pod's **Connect** tab:

Basic (proxied, no file transfer):

```powershell
ssh <pod-id>@ssh.runpod.io -i $env:USERPROFILE\.ssh\id_ed25519
```

Full SSH over exposed TCP (supports scp/sftp — pick a pod with a public IP):

```powershell
ssh root@<pod-ip> -p <port> -i $env:USERPROFILE\.ssh\id_ed25519
```

Move data over SCP:

```powershell
# push beats up
scp -P <port> -i $env:USERPROFILE\.ssh\id_ed25519 -r "F:\RAP_ARCHIVES\raw_beats" root@<pod-ip>:/workspace/
# pull results back
scp -P <port> -i $env:USERPROFILE\.ssh\id_ed25519 -r root@<pod-ip>:/workspace/out "F:\RAP_ARCHIVES\out"
```

Gotcha: if SSH asks for a **password**, the key isn't registered correctly —
usually the fingerprint (`SHA256:...`) was pasted instead of the real
`ssh-ed25519 AAAA...` key, or the `ssh-ed25519` prefix was dropped. RunPod SSH
never needs a password.

---

## 3. Which transfer method when?

- **S3 volume** — persistent storage shared across pods. Push your dataset
  once; every new pod mounts/reads it. Best for `raw_beats`, models, datasets.
- **SCP (full SSH)** — one-off transfers to/from a specific running pod.
- **runpodctl send/receive** — quick ad-hoc transfer with a code, no key setup.
