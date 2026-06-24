"""Test fixtures: one temp SQLite DB (tables reset per test), fakeredis instead
of real Redis, and a stubbed queue so no worker is needed."""
import os
import tempfile

# Set env BEFORE importing the server package so settings/engine bind to it.
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/t.db"
os.environ["RESULTS_DIR"] = f"{_TMP}/results"
os.environ["ALLOW_SIGNUP"] = "true"
os.environ["ADMIN_TOKEN"] = "secret123"
os.environ["FREE_CREDITS"] = "2"
os.environ["RATE_LIMIT_PER_MIN"] = "1000"
os.environ["SIGNUP_LIMIT_PER_MIN"] = "1000"

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    import server.db as db
    # fresh tables per test for isolation
    SQLModel.metadata.drop_all(db.engine)
    SQLModel.metadata.create_all(db.engine)

    fake = fakeredis.FakeStrictRedis()
    import server.jobqueue as q
    monkeypatch.setattr(q, "redis_conn", fake)
    enq = []
    monkeypatch.setattr(q.cpu_queue, "enqueue", lambda *a, **k: enq.append(("cpu", a)))
    monkeypatch.setattr(q.gpu_queue, "enqueue", lambda *a, **k: enq.append(("gpu", a)))

    import server.ratelimit as rl
    monkeypatch.setattr(rl, "redis_conn", fake)

    import server.app as appmod
    from fastapi.testclient import TestClient
    with TestClient(appmod.app) as c:
        c._enq = enq
        yield c
