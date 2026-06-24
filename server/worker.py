"""Worker entrypoint: `python -m server.worker`.

Consumes the queues named in WORKER_QUEUES (comma-sep); defaults to BOTH the
CPU and GPU lanes so a single worker handles everything in dev. In production
run CPU-only workers (WORKER_QUEUES=beat-cpu) and GPU workers on GPU hosts
(WORKER_QUEUES=beat-gpu).
"""
from redis import Redis
from rq import Worker, Queue

from .config import settings
from .db import init_db


def _queue_names() -> list[str]:
    raw = settings.WORKER_QUEUES.strip()
    if raw:
        return [q.strip() for q in raw.split(",") if q.strip()]
    return [settings.CPU_QUEUE, settings.GPU_QUEUE]


def main() -> None:
    init_db()
    conn = Redis.from_url(settings.REDIS_URL)
    queues = [Queue(n, connection=conn) for n in _queue_names()]
    print(f"[worker] listening on: {', '.join(_queue_names())}")
    Worker(queues, connection=conn).work(with_scheduler=True)


if __name__ == "__main__":
    main()
