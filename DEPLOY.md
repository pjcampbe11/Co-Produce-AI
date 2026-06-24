# Deploy & go-live checklist (Co-Producer AI SaaS)

Operational steps to take the [`server/`](server) stack (README §35) from
`docker compose up` to a real, public, billable service. Code is ready; this is
the ops side.

## 1. Datastores (managed, not in-container)

- **Postgres** instead of SQLite. Set `DATABASE_URL=postgresql://USER:PASS@HOST:5432/DB`.
  Use a managed instance (RDS/Cloud SQL/Neon/Supabase). Enable automated backups +
  point-in-time recovery. SQLModel creates tables on first boot; for real schema
  changes adopt Alembic migrations.
- **Redis** managed (ElastiCache/Upstash/Redis Cloud). Set `REDIS_URL`. It backs
  both the job queue and the rate limiter, so size it for both and enable
  persistence if you care about in-flight jobs surviving a restart.

## 2. Workers & GPUs

- Run **API** and **CPU workers** on a cheap always-on box; run **GPU workers** on
  GPU hosts/pods (§34) pointed at the *same* `REDIS_URL` + results volume/bucket.
- Lane split: CPU box `WORKER_QUEUES=beat-cpu`; GPU box `WORKER_QUEUES=beat-gpu`
  (`docker compose -f docker-compose.yml -f docker-compose.gpu.yml up`).
- Scale per lane: `docker compose up --scale worker=N`. Watch queue depth via
  RQ / `GET /v1/jobs` and add workers when the backlog grows.
- **Results storage:** the local `/data` volume only works if API + workers share
  it. Across hosts, switch result storage to S3/object storage (the RunPod S3
  volume in `cloud/connect.md` works) and serve downloads via presigned URLs.

## 3. TLS & reverse proxy

- Terminate TLS at Caddy / Nginx / a cloud LB in front of the API; never expose
  `:8000` directly. Caddy one-liner: reverse-proxy `api.yourdomain.com` → `api:8000`.
- Forward the real client IP (`X-Forwarded-For`) so the signup rate limiter keys
  on the actual IP, and run uvicorn with `--proxy-headers`.

## 4. Stripe go-live

1. Create real **Products & Prices** in the Stripe dashboard (live mode). Put the
   live price ids in `STRIPE_PRICES` (`{"price_live_xxx":{"plan":"creator","credits":500}}`).
2. Set **live** `STRIPE_SECRET_KEY` (`sk_live_...`).
3. Add a webhook endpoint → `https://api.yourdomain.com/v1/webhooks/stripe`,
   subscribe to `checkout.session.completed`, `invoice.paid`,
   `customer.subscription.deleted`; copy its signing secret to `STRIPE_WEBHOOK_SECRET`.
4. Point `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` at your real pages.
5. Test the full loop with a real card in live mode, then refund yourself.

## 5. Security & accounts

- **Turn off open signup:** `ALLOW_SIGNUP=false`. Set a strong `ADMIN_TOKEN` and
  mint accounts via `X-Admin-Token`, or wire your own auth/onboarding in front.
- Keep all secrets in your platform's secret manager, never in git. The
  `.gitignore` already excludes `server/.env`.
- Tune `RATE_LIMIT_PER_MIN` / `SIGNUP_LIMIT_PER_MIN` for your plans.
- Restrict CORS / add an API gateway if browsers call the API directly.

## 6. Observability

- Ship API + worker logs to your platform (uvicorn logs to stdout already).
- Add uptime checks on `GET /healthz`.
- Alert on queue depth, worker failures, and Stripe webhook 4xx/5xx.

## 7. Pre-launch checklist

- [ ] `DATABASE_URL` → Postgres with backups
- [ ] `REDIS_URL` → managed Redis
- [ ] GPU workers running on the `beat-gpu` lane
- [ ] Results in shared/object storage (not a single-host volume)
- [ ] TLS in front; `--proxy-headers`; real client IP forwarded
- [ ] Stripe **live** keys, prices, webhook + signing secret
- [ ] `ALLOW_SIGNUP=false` + `ADMIN_TOKEN` (or real auth)
- [ ] Secrets in a secret manager, not `.env` in the repo
- [ ] `cd server && pytest` green in CI on the release commit
- [ ] Uptime + log + alerting wired
