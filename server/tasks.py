"""The worker side: run a queued Job by invoking the toolkit, then persist the
result. Enqueued by the API as server.tasks.run_job(job_id)."""
import base64
import json
import os
import subprocess
import sys
import tempfile

from .config import settings
from .db import Job, get_session, _now

# Credit cost per task (also used by the API to meter/charge).
TASK_COSTS = {
    "beat": 1,
    "tag": 1,
    "flip": 2,
    "remix": 3,
    "song": 5,
}


def _script(name: str) -> str:
    return os.path.join(settings.SCRIPTS_DIR, name)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=settings.REPO_ROOT)


def _execute(task: str, params: dict, out_dir: str) -> dict:
    """Dispatch one task to the toolkit. Returns a result dict; if it produced
    audio, includes 'result_path'."""
    if task == "beat":
        wav = os.path.join(out_dir, "beat.wav")
        _run([settings.PYTHON_BIN, _script("beat_builder.py"),
              "--style", str(params.get("style", "boom_bap")),
              "--bpm", str(params.get("bpm", 90)),
              "--out", wav])
        return {"result_path": wav, "style": params.get("style", "boom_bap")}

    if task == "flip":
        wav = os.path.join(out_dir, "flip.wav")
        _run([settings.PYTHON_BIN, _script("audio2audio.py"),
              "--input", params["path"], "--prompt", params.get("prompt", ""),
              "--strength", str(params.get("strength", 0.6)), "--out", wav])
        return {"result_path": wav}

    if task == "remix":
        _run([settings.PYTHON_BIN, _script("remix.py"),
              "--input", params["path"], "--genre", params.get("genre", "dnb"),
              "--mode", params.get("mode", "full"), "--out", out_dir])
        return {"result_dir": out_dir}

    if task == "tag":
        sys.path.insert(0, settings.SCRIPTS_DIR)
        import auto_tag
        tags, cap = auto_tag.caption_heuristic(params["path"])
        return {"tags": tags, "caption": cap}

    raise ValueError(f"unknown task '{task}'")


def run_job(job_id: str) -> None:
    """RQ entrypoint. Loads the job, runs it, writes status + result back."""
    with get_session() as s:
        job = s.get(Job, job_id)
        if not job:
            return
        job.status = "running"
        job.updated_at = _now()
        s.add(job); s.commit()
        params = json.loads(job.params_json or "{}")
        task = job.task

    out_dir = os.path.join(settings.RESULTS_DIR, job_id)
    os.makedirs(out_dir, exist_ok=True)
    try:
        result = _execute(task, params, out_dir)
        result_path = result.get("result_path")
        with get_session() as s:
            job = s.get(Job, job_id)
            job.status = "completed"
            job.result_json = json.dumps(result)
            job.result_path = result_path
            job.updated_at = _now()
            s.add(job); s.commit()
    except Exception as e:  # noqa: BLE001 - record any failure + refund credits
        with get_session() as s:
            from .db import User, CreditLedger
            job = s.get(Job, job_id)
            job.status = "failed"
            job.error = f"{type(e).__name__}: {e}"
            job.updated_at = _now()
            s.add(job)
            user = s.get(User, job.user_id)  # refund the reserved credits
            if user and job.cost:
                user.credits += job.cost
                s.add(user)
                s.add(CreditLedger(user_id=user.id, delta=job.cost,
                                   reason=f"refund failed job {job_id}"))
            s.commit()
