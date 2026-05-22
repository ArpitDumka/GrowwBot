from fastapi.testclient import TestClient

from mf_api.app import create_app
from mf_api.rate_limit import RateLimiter


def test_rate_limit_returns_429():
    from mf_compose.groq_client import StubLLMClient

    limiter = RateLimiter(requests_per_minute=2)
    llm = StubLLMClient("Exit load Nil.\nSource: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\nLast updated from sources: 2026-05-16")
    app = create_app(test_reranker=True, llm=llm, rate_limiter=limiter)
    client = TestClient(app)
    payload = {"query": "What is the exit load on HDFC ELSS Tax Saver Fund?"}
    for _ in range(2):
        assert client.post("/api/v1/chat", json=payload).status_code == 200
    r = client.post("/api/v1/chat", json=payload)
    assert r.status_code == 429
    assert "Retry-After" in r.headers
