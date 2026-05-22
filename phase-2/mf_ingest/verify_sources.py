"""Phase 1.6 network exit criteria: robots.txt + HTTP 200 for every registry URL."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from mf_ingest.fetcher import RateLimiter, build_client
from mf_ingest.paths import USER_AGENT, ensure_phase1_on_sys_path
from mf_ingest.robots import assert_can_fetch, fetch_robots_txt

if TYPE_CHECKING:
    from collections.abc import Sequence

log = logging.getLogger(__name__)


def _head_or_get(client: httpx.Client, url: str) -> httpx.Response:
    r = client.head(url, follow_redirects=True)
    if r.status_code == 405:
        r = client.get(url, follow_redirects=True)
    return r


def verify_registry_urls(
    *,
    client: httpx.Client | None = None,
    own_client: bool = True,
) -> tuple[bool, list[str]]:
    """Load ``phase-1`` sources; assert robots allows each URL; require HTTP 200.

    Uses at most **one request per second** after ``robots.txt`` (same policy as
    :class:`GrowwFetcher`).

    Returns ``(True, [])`` on success, or ``(False, [error, ...])``.
    """
    ensure_phase1_on_sys_path()
    from ingest.sources import load_sources  # noqa: PLC0415

    errors: list[str] = []
    own = own_client and client is None
    c = client or build_client()
    limiter = RateLimiter()
    try:
        rp = fetch_robots_txt(c)
        sources = load_sources()
        for src in sources:
            try:
                assert_can_fetch(rp, USER_AGENT, src.url)
            except RuntimeError as e:
                errors.append(f"{src.id}: robots.txt — {e}")
                continue

            limiter.acquire()
            try:
                resp = _head_or_get(c, src.url)
            except httpx.HTTPError as e:
                errors.append(f"{src.id}: request failed — {e!r}")
                continue

            if resp.status_code != 200:
                errors.append(f"{src.id}: expected HTTP 200, got {resp.status_code} for {src.url}")
    finally:
        if own:
            c.close()

    return (len(errors) == 0, errors)


def format_verify_report(ok: bool, errors: Sequence[str]) -> str:
    if ok:
        return "verify: all registry URLs allowed by robots.txt and returned HTTP 200."
    lines = ["verify: failed.", *[f"  - {e}" for e in errors]]
    return "\n".join(lines)
