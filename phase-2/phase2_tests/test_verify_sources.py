"""Registry URL verification (robots + HTTP 200)."""

from __future__ import annotations

import httpx

from mf_ingest.verify_sources import verify_registry_urls


def test_verify_registry_urls_all_ok() -> None:
    robots = "User-agent: *\nDisallow:\n"

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if u.endswith("/robots.txt"):
            return httpx.Response(200, text=robots)
        if "/mutual-funds/" in u:
            return httpx.Response(200, text="<html></html>")
        return httpx.Response(404, text="unexpected url")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, follow_redirects=True)
    ok, errors = verify_registry_urls(client=client, own_client=False)
    assert ok
    assert errors == []


def test_verify_registry_urls_reports_bad_status() -> None:
    robots = "User-agent: *\nDisallow:\n"

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if u.endswith("/robots.txt"):
            return httpx.Response(200, text=robots)
        if "hdfc-mid-cap" in u:
            return httpx.Response(503, text="no")
        if "/mutual-funds/" in u:
            return httpx.Response(200, text="ok")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, follow_redirects=True)
    ok, errors = verify_registry_urls(client=client, own_client=False)
    assert not ok
    assert any("hdfc_midcap" in e and "503" in e for e in errors)
