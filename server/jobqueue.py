"""RQ queues (Redis-backed). Two lanes so GPU work only lands on GPU workers."""
from redis import Redis
from rq import Queue

from .config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
cpu_queue = Queue(settings.CPU_QUEUE, connection=redis_conn, default_timeout=settings.JOB_TIMEOUT)
gpu_queue = Queue(settings.GPU_QUEUE, connection=redis_conn, default_timeout=settings.JOB_TIMEOUT)


def queue_for(task: str) -> Queue:
    """Route a task to the GPU lane if it needs a GPU, else the CPU lane."""
    from .tasks import GPU_TASKS
    return gpu_queue if task in GPU_TASKS else cpu_queue
