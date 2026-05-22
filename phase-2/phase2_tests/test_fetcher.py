"""Fetcher tests with ``httpx.MockTransport`` (no network)."""

from __future__ import annotations

import httpx
from urllib.robotparser import RobotFileParser

from mf_ingest.fetcher import GrowwFetcher


def _robots_allow_all() -> RobotFileParser:
    rp = RobotFileParser()
    rp.set_url("https://groww.in/robots.txt")
    rp.parse(["User-agent: *", "Allow: /"])
    return rp


def test_groww_fetcher_200_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><title>T</title><body><h1>Hi</h1></body></html>",
            headers={"etag": '"abc"'},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, follow_redirects=True)
    try:
        with GrowwFetcher(robots=_robots_allow_all(), client=client) as gf:
            r = gf.fetch("https://groww.in/mutual-funds/test-fund")
            assert r.ok
            assert r.html is not None
            assert "Hi" in r.html
            assert r.etag == '"abc"'
    finally:
        client.close()
