"""RQ queue wiring (Redis-backed)."""
from redis import Redis
from rq import Queue

from .config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
job_queue = Queue(settings.QUEUE_NAME, connection=redis_conn,
                  default_timeout=settings.JOB_TIMEOUT)
