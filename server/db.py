"""Database models and session helpers (SQLModel; SQLite by default, set
DATABASE_URL to a Postgres URL for production)."""
import datetime as dt
import uuid
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine, Session

from .config import settings

engine = create_engine(settings.DATABASE_URL, echo=False,
                       connect_args={"check_same_thread": False}
                       if settings.DATABASE_URL.startswith("sqlite") else {})


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class User(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    email: str = Field(index=True, unique=True)
    plan: str = "free"
    credits: int = 0
    stripe_customer_id: Optional[str] = Field(default=None, index=True)
    created_at: dt.datetime = Field(default_factory=_now)


class ApiKey(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(index=True)
    prefix: str = Field(index=True)        # first 8 chars, shown in UI
    key_hash: str = Field(index=True)      # sha256 of the full key
    created_at: dt.datetime = Field(default_factory=_now)
    last_used: Optional[dt.datetime] = None


class Job(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(index=True)
    task: str
    params_json: str = "{}"
    status: str = Field(default="queued", index=True)  # queued|running|completed|failed
    cost: int = 0
    result_json: Optional[str] = None
    result_path: Optional[str] = None      # path to a produced file (e.g. wav)
    error: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=_now)
    updated_at: dt.datetime = Field(default_factory=_now)


class CreditLedger(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(index=True)
    delta: int = 0                         # +grant / -spend / +refund
    reason: str = ""
    created_at: dt.datetime = Field(default_factory=_now)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
