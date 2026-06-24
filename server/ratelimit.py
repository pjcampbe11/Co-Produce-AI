"""Tiny Redis-backed fixed-window rate limiter.

Keyed by an identity string (API key id or client IP). Uses INCR + EXPIRE on a
per-minute bucket — atomic enough for API throttling and shares the Redis we
already run for the queue. Fails open if Redis is unreachable (don't take the
API down because the limiter blinked).
"""
import time

from fastapi import HTTPException

from .config import settings
from .jobqueue import redis_conn


def check(identity: str, limit: int) -> None:
    """Raise HTTP 429 if `identity` exceeded `limit` requests this minute."""
    if limit <= 0:
        return
    window = int(time.time() // 60)
    bucket = f"rl:{identity}:{window}"
    try:
        n = redis_conn.incr(bucket)
        if n == 1:
            redis_conn.expire(bucket, 70)
    except Exception:
        return  # fail open
    if n > limit:
        raise HTTPException(429, "rate limit exceeded; slow down or upgrade your plan")
