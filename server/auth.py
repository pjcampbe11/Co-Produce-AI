"""API-key auth: generate, hash, and verify keys. Keys are shown to the user
once at creation; only their sha256 hash is stored."""
import hashlib
import secrets

from fastapi import Depends, Header, HTTPException
from sqlmodel import select

from .db import ApiKey, User, get_session


def generate_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, key_hash). full_key is shown to the user once."""
    raw = "bt_" + secrets.token_urlsafe(32)
    return raw, raw[:8], hashlib.sha256(raw.encode()).hexdigest()


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def current_user(authorization: str = Header(default="")) -> User:
    """FastAPI dependency. Expects 'Authorization: Bearer bt_xxx'."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer API key")
    raw = authorization.split(" ", 1)[1].strip()
    kh = hash_key(raw)
    with get_session() as s:
        ak = s.exec(select(ApiKey).where(ApiKey.key_hash == kh)).first()
        if not ak:
            raise HTTPException(401, "invalid API key")
        user = s.get(User, ak.user_id)
        if not user:
            raise HTTPException(401, "user not found")
        return user
