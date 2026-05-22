"""robots.txt compliance (edge case 2.09)."""

from __future__ import annotations

import logging
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger(__name__)


def fetch_robots_txt(client: httpx.Client, base: str = "https://groww.in") -> RobotFileParser:
    """Fetch and parse ``/robots.txt`` for *base* host."""
    url = f"{base.rstrip('/')}/robots.txt"
    resp = client.get(url, timeout=30.0)
    resp.raise_for_status()
    rp = RobotFileParser()
    rp.set_url(url)
    rp.parse(resp.text.splitlines())
    log.info("Loaded robots.txt from %s (status %s)", url, resp.status_code)
    return rp


def assert_can_fetch(rp: RobotFileParser, user_agent: str, url: str) -> None:
    if not rp.can_fetch(user_agent, url):
        raise RuntimeError(
            f"robots.txt disallows fetch for {user_agent!r} -> {url!r} "
            "(policy: hard fail; edge case 2.09)"
        )
