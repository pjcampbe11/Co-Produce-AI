"""End-to-end API tests (fakeredis, stubbed queue)."""


def _signup(client, email="u@example.com", headers=None):
    return client.post("/v1/signup", json={"email": email}, headers=headers or {})


def test_health(client):
    assert client.get("/healthz").json()["ok"] is True


def test_signup_grants_credits_and_key(client):
    r = _signup(client)
    assert r.status_code == 200
    d = r.json()
    assert d["api_key"].startswith("bt_")
    assert d["credits"] == 2


def test_auth_required(client):
    assert client.get("/v1/me").status_code == 401
    assert client.get("/v1/me", headers={"authorization": "Bearer nope"}).status_code == 401


def test_job_meters_credits(client):
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    assert client.get("/v1/me", headers=H).json()["credits"] == 2
    j = client.post("/v1/jobs", headers=H, json={"task": "beat", "params": {"style": "trap"}})
    assert j.status_code == 200 and j.json()["cost"] == 1
    assert client.get("/v1/me", headers=H).json()["credits"] == 1


def test_unknown_task_400(client):
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    assert client.post("/v1/jobs", headers=H, json={"task": "nope"}).status_code == 400


def test_insufficient_credits_402(client):
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    client.post("/v1/jobs", headers=H, json={"task": "beat"})  # 2 -> 1
    client.post("/v1/jobs", headers=H, json={"task": "beat"})  # 1 -> 0
    assert client.post("/v1/jobs", headers=H, json={"task": "beat"}).status_code == 402


def test_gpu_task_routes_to_gpu_lane(client):
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    # give enough credits for the flip (cost 2): top up via a fresh account is simpler
    client.post("/v1/jobs", headers=H, json={"task": "flip", "params": {"path": "x.wav"}})
    lanes = [lane for lane, _ in client._enq]
    assert "gpu" in lanes  # flip -> gpu queue


def test_cpu_task_routes_to_cpu_lane(client):
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    client.post("/v1/jobs", headers=H, json={"task": "beat"})
    assert client._enq[-1][0] == "cpu"


def test_pricing_page(client):
    r = client.get("/pricing")
    assert r.status_code == 200 and "Plans" in r.text


def test_admin_token_signup_when_public_off(client, monkeypatch):
    import server.app as appmod
    monkeypatch.setattr(appmod.settings, "ALLOW_SIGNUP", False)
    assert _signup(client, "a@b.com").status_code == 403
    r = _signup(client, "a@b.com", headers={"X-Admin-Token": "secret123"})
    assert r.status_code == 200


def test_rate_limit_429(client, monkeypatch):
    import server.app as appmod
    monkeypatch.setattr(appmod.settings, "RATE_LIMIT_PER_MIN", 2)
    key = _signup(client).json()["api_key"]
    H = {"authorization": f"Bearer {key}"}
    codes = [client.post("/v1/jobs", headers=H, json={"task": "beat"}).status_code for _ in range(4)]
    assert 429 in codes  # at least one request throttled
