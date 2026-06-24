"""Beat Toolkit SaaS API (FastAPI).

Endpoints:
  POST /v1/signup                 -> create account + first API key (dev/self-host)
  POST /v1/keys                   -> mint an additional API key
  GET  /v1/me                     -> account, plan, credit balance
  POST /v1/jobs                   -> submit a job (meters credits), returns job
  GET  /v1/jobs                   -> list your jobs
  GET  /v1/jobs/{id}              -> job status + result
  GET  /v1/jobs/{id}/result       -> download the produced audio (if any)
  POST /v1/billing/checkout       -> Stripe Checkout URL for a subscription
  POST /v1/webhooks/stripe        -> Stripe webhook (grants credits)
  GET  /healthz
"""
import json
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import select

from .auth import current_user, generate_key
from .billing import create_checkout, handle_webhook
from .config import settings
from .db import ApiKey, Job, User, CreditLedger, get_session, init_db, _now
from .queue import job_queue
from .tasks import TASK_COSTS

app = FastAPI(title="Beat Toolkit API", version="1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


# ---------- accounts & keys ----------
class SignupIn(BaseModel):
    email: str


@app.post("/v1/signup")
def signup(body: SignupIn) -> dict:
    if not settings.ALLOW_SIGNUP:
        raise HTTPException(403, "signup disabled")
    with get_session() as s:
        if s.exec(select(User).where(User.email == body.email)).first():
            raise HTTPException(409, "email already registered")
        user = User(email=body.email, credits=settings.FREE_CREDITS)
        s.add(user)
        s.add(CreditLedger(user_id=user.id, delta=settings.FREE_CREDITS, reason="signup"))
        raw, prefix, kh = generate_key()
        s.add(ApiKey(user_id=user.id, prefix=prefix, key_hash=kh))
        s.commit()
        return {"user_id": user.id, "email": user.email,
                "credits": user.credits, "api_key": raw,
                "note": "store this key now; it will not be shown again"}


@app.post("/v1/keys")
def mint_key(user: User = Depends(current_user)) -> dict:
    raw, prefix, kh = generate_key()
    with get_session() as s:
        s.add(ApiKey(user_id=user.id, prefix=prefix, key_hash=kh))
        s.commit()
    return {"api_key": raw, "prefix": prefix}


@app.get("/v1/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"user_id": user.id, "email": user.email,
            "plan": user.plan, "credits": user.credits}


# ---------- jobs ----------
class JobIn(BaseModel):
    task: str
    params: dict = {}


def _job_dict(j: Job) -> dict:
    return {"id": j.id, "task": j.task, "status": j.status, "cost": j.cost,
            "result": json.loads(j.result_json) if j.result_json else None,
            "error": j.error, "created_at": j.created_at.isoformat()}


@app.post("/v1/jobs")
def submit_job(body: JobIn, user: User = Depends(current_user)) -> dict:
    if body.task not in TASK_COSTS:
        raise HTTPException(400, f"unknown task; valid: {sorted(TASK_COSTS)}")
    cost = TASK_COSTS[body.task]
    with get_session() as s:
        u = s.get(User, user.id)
        if u.credits < cost:
            raise HTTPException(402, f"insufficient credits: need {cost}, have {u.credits}")
        u.credits -= cost  # reserve up front; refunded by worker on failure
        s.add(u)
        s.add(CreditLedger(user_id=u.id, delta=-cost, reason=f"job {body.task}"))
        job = Job(user_id=u.id, task=body.task,
                  params_json=json.dumps(body.params), cost=cost, status="queued")
        s.add(job); s.commit()
        job_id = job.id
    job_queue.enqueue("server.tasks.run_job", job_id)
    return {"id": job_id, "status": "queued", "cost": cost}


@app.get("/v1/jobs")
def list_jobs(user: User = Depends(current_user)) -> dict:
    with get_session() as s:
        rows = s.exec(select(Job).where(Job.user_id == user.id)
                      .order_by(Job.created_at.desc())).all()
        return {"jobs": [_job_dict(j) for j in rows]}


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str, user: User = Depends(current_user)) -> dict:
    with get_session() as s:
        j = s.get(Job, job_id)
        if not j or j.user_id != user.id:
            raise HTTPException(404, "job not found")
        return _job_dict(j)


@app.get("/v1/jobs/{job_id}/result")
def get_result(job_id: str, user: User = Depends(current_user)):
    with get_session() as s:
        j = s.get(Job, job_id)
        if not j or j.user_id != user.id:
            raise HTTPException(404, "job not found")
        if j.status != "completed":
            raise HTTPException(409, f"job not complete (status {j.status})")
        if not j.result_path or not os.path.exists(j.result_path):
            raise HTTPException(404, "no downloadable file for this job")
        return FileResponse(j.result_path, media_type="audio/wav",
                            filename=os.path.basename(j.result_path))


# ---------- billing ----------
class CheckoutIn(BaseModel):
    price_id: str


@app.post("/v1/billing/checkout")
def checkout(body: CheckoutIn, user: User = Depends(current_user)) -> dict:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "billing not configured")
    return {"url": create_checkout(user, body.price_id)}


@app.post("/v1/webhooks/stripe")
async def stripe_webhook(request: Request) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        return handle_webhook(payload, sig)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"webhook error: {e}")
