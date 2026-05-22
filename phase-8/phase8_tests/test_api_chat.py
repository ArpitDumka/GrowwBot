from mf_api.app import TRACE_HEADER


def test_chat_post_only(api_client):
    r = api_client.post(
        "/api/v1/chat",
        json={"query": "What is the exit load on HDFC ELSS Tax Saver Fund?"},
    )
    assert r.status_code == 200
    assert TRACE_HEADER in r.headers
    body = r.json()
    assert body["outcome"] == "ANSWERED"
    assert "Source: https://groww.in/" in body["answer"]
    assert body["disclaimer"].startswith("Facts-only")
    assert body["trace_id"] == r.headers[TRACE_HEADER]


def test_advisory_refused(api_client):
    r = api_client.post(
        "/api/v1/chat",
        json={"query": "Should I invest in HDFC Mid Cap Fund?"},
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "REFUSED"
    assert r.json()["used_llm"] is False


def test_query_too_short(api_client):
    r = api_client.post("/api/v1/chat", json={"query": ""})
    assert r.status_code == 422


def test_greeting_friendly_reply(api_client):
    r = api_client.post("/api/v1/chat", json={"query": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"] == "ANSWERED"
    assert body["citation_url"] is None  # no citation for chitchat
    assert body["answer"]  # non-empty
    assert "indexed" not in body["answer"].lower()


def test_ok_conversational_not_not_found(api_client):
    r = api_client.post("/api/v1/chat", json={"query": "ok"})
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"] == "ANSWERED"
    assert "scheme pages" not in body["answer"].lower()
    assert "indexed" not in body["answer"].lower()


def test_other_amc_blocked(api_client):
    r = api_client.post(
        "/api/v1/chat",
        json={"query": "Tell me about SBI Small Cap Fund"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"] == "REFUSED"
    assert "10 HDFC schemes" in body["answer"]
    assert body["used_llm"] is False


def test_healthz(api_client):
    assert api_client.get("/healthz").json()["status"] == "ok"


def test_root_returns_backend_info(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "backend"
    assert body["status"] == "running"
    assert "/healthz" in body["endpoints"]["health"]
