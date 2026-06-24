# server/ — CoProduce AI SaaS backend

Turns the toolkit into a multi-tenant service: an authenticated REST API, a
Redis-backed **job queue** with scalable workers, credit **metering**, and
**Stripe** subscription billing. Full guide: [README §35](../README.md#35-saas).

## Architecture

```
client ──HTTPS──> FastAPI (api)  ──enqueue──> Redis ──> Worker(s) ──> scripts/*
                     │  credits/metering            run beat/tag/flip/remix/song
                     └── Stripe (checkout + webhooks) grants credits
   SQLModel DB (users, api keys, jobs, credit ledger)   results on a shared volume
```

## Run locally

```bash
cp server/.env.example server/.env     # fill in Stripe keys + price map
docker compose up --build              # api :8000, worker (both lanes), redis
docker compose up --scale worker=3     # more throughput

# dedicated GPU worker for flip/remix/song (needs NVIDIA Container Toolkit):
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

**Queues / GPU:** CPU tasks (`beat`,`tag`) use `beat-cpu`; GPU tasks
(`flip`,`remix`,`song`) use `beat-gpu`. A worker consumes `WORKER_QUEUES`
(blank = both). Run CPU workers cheap and GPU workers on GPU hosts.

**Signup lockdown:** set `ALLOW_SIGNUP=false` in production; mint accounts with
`X-Admin-Token: $ADMIN_TOKEN`. A static **pricing page** is at `/pricing`, and a
ready **Python client** lives in `../clients/python/`.

## Quick API tour

```bash
# 1) create an account (returns your API key once)
curl -s -X POST localhost:8000/v1/signup -H 'content-type: application/json' \
  -d '{"email":"you@example.com"}'
# -> {"user_id":"...","api_key":"bt_xxx","credits":10}

KEY=bt_xxx
# 2) submit a job (meters credits)
curl -s -X POST localhost:8000/v1/jobs -H "authorization: Bearer $KEY" \
  -H 'content-type: application/json' -d '{"task":"beat","params":{"style":"trap","bpm":140}}'
# 3) poll + download the wav
curl -s localhost:8000/v1/jobs/<id> -H "authorization: Bearer $KEY"
curl -s localhost:8000/v1/jobs/<id>/result -H "authorization: Bearer $KEY" -o out.wav
# 4) buy a subscription (returns a Stripe Checkout URL)
curl -s -X POST localhost:8000/v1/billing/checkout -H "authorization: Bearer $KEY" \
  -H 'content-type: application/json' -d '{"price_id":"price_creator_monthly"}'
```

## Stripe

1. Create products/prices in the Stripe dashboard; put their ids in
   `STRIPE_PRICES` (price → plan + monthly credits).
2. Set `STRIPE_SECRET_KEY`. For webhooks, add an endpoint to
   `POST /v1/webhooks/stripe` and put its signing secret in
   `STRIPE_WEBHOOK_SECRET`. Locally: `stripe listen --forward-to localhost:8000/v1/webhooks/stripe`.
3. `checkout.session.completed` / `invoice.paid` grant credits;
   `customer.subscription.deleted` downgrades to free.

## Task costs (credits)

| task | cost | runs |
| --- | --- | --- |
| beat | 1 | `beat_builder.py` |
| tag  | 1 | `auto_tag.py` (heuristic) |
| flip | 2 | `audio2audio.py` |
| remix| 3 | `remix.py` |
| song | 5 | (wire to `song_generate.py`) |

Edit `TASK_COSTS` in `server/tasks.py`. GPU tasks (flip/remix/song) need a
GPU-enabled worker — see the commented `deploy:` block in `docker-compose.yml`.

## Rate limiting

Per-API-key on job submit (`RATE_LIMIT_PER_MIN`, default 60) and per-IP on signup
(`SIGNUP_LIMIT_PER_MIN`, default 5), via a Redis fixed-window limiter that fails
open if Redis blinks. Over the limit returns **429**. Set either to `0` to disable.

## Tests

```bash
pip install -r server/requirements.txt   # includes pytest + fakeredis
cd server && pytest                       # 11 tests, no Redis/Stripe needed
```

Covers signup + admin-token lockdown, auth, credit metering (402), CPU/GPU queue
routing, the pricing page, and rate-limit 429 — all with fakeredis and a stubbed
queue, so it runs anywhere.
