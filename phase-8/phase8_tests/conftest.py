import pytest
from fastapi.testclient import TestClient
from mf_compose.groq_client import StubLLMClient

from mf_api.app import create_app


@pytest.fixture
def api_client():
    llm = StubLLMClient(
        "Exit load is Nil.\n"
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
        "Last updated from sources: 2026-05-16"
    )
    app = create_app(test_reranker=True, llm=llm)
    with TestClient(app) as client:
        yield client
