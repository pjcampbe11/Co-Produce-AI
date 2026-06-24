"""Worker process entrypoint: `python -m server.worker` (or `rq worker`).

Pulls jobs off the queue and runs server.tasks.run_job. Run as many replicas as
you have GPU/CPU capacity for.
"""
from redis import Redis
from rq import Worker, Queue

from .config import settings
from .db import init_db


def main() -> None:
    init_db()
    conn = Redis.from_url(settings.REDIS_URL)
    worker = Worker([Queue(settings.QUEUE_NAME, connection=conn)], connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
