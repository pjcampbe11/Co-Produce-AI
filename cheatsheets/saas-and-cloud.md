# SaaS + cloud cheat sheet

## Run the service (server/)
```bash
cp server/.env.example server/.env            # add Stripe keys + price map
docker compose up --build                     # api :8000, worker, redis
docker compose up --scale worker=3            # more CPU throughput
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build   # + GPU worker
cd server && pytest                           # 11 tests, no infra needed
```

## API (Bearer bt_… key)
```bash
curl -s -X POST localhost:8000/v1/signup -H 'content-type: application/json' -d '{"email":"you@x.com"}'
curl -s -X POST localhost:8000/v1/jobs   -H "authorization: Bearer $KEY" -H 'content-type: application/json' -d '{"task":"beat","params":{"style":"trap","bpm":140}}'
curl -s localhost:8000/v1/jobs/<id>        -H "authorization: Bearer $KEY"
curl -s localhost:8000/v1/jobs/<id>/result -H "authorization: Bearer $KEY" -o out.wav
```
Tasks/costs: beat 1 · tag 1 · flip 2 · remix 3 · song 5. Lanes: beat/tag→`beat-cpu`, flip/remix/song→`beat-gpu`.

## Pod (RunPod)
```bash
# one-shot setup on a fresh pod
curl -fsSL https://raw.githubusercontent.com/pjcampbe11/Co-Produce-AI/main/cloud/pod_bootstrap.sh | bash
# connect (Connect tab -> SSH over exposed TCP)
ssh root@<POD_IP> -p <PORT> -i $env:USERPROFILE\.ssh\id_ed25519
# move files
scp -P <PORT> -i <KEY> -r "F:\RAP_ARCHIVES\raw_beats" root@<POD_IP>:/workspace/
```

## S3 network volume (upload once, mount anywhere)
```powershell
aws s3 cp "F:\RAP_ARCHIVES\raw_beats" s3://d39orqnjjh/raw_beats/ --recursive `
  --profile runpod --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io --checksum-algorithm CRC32
```
Full details in `cloud/connect.md`, `DEPLOY.md`, and README §33–§35.
