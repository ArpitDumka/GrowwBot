"""HTTP fetcher: robots, rate limit, retries, conditional GET (edge cases 2.01–2.11)."""

from __future__ import annotations

import errno
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from urllib.robotparser import RobotFileParser

from mf_ingest.encoding import decode_html_bytes
from mf_ingest.paths import USER_AGENT
from mf_ingest.robots import assert_can_fetch

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Outcome of a single GET."""

    ok: bool
    status_code: int
    final_url: str
    html: str | None
    raw_bytes: bytes | None
    encoding_used: str | None
    etag: str | None
    last_modified: str | None
    not_modified: bool
    error: str | None
    legally_blocked: bool = False


class RateLimiter:
    """At most one request per ``min_interval`` seconds (architecture: ≤1 req/s)."""

    def __init__(self, min_interval: float = 1.05) -> None:
        self.min_interval = min_interval
        self._last = 0.0

    def acquire(self) -> None:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()


class GrowwFetcher:
    """Polite synchronous fetcher for ``groww.in`` scheme pages."""

    def __init__(
        self,
        *,
        robots: RobotFileParser,
        user_agent: str = USER_AGENT,
        timeout: float = 45.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._robots = robots
        self._ua = user_agent
        self._timeout = timeout
        self._own_client = client is None
        self._client = client or httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Language": "en-IN,en;q=0.9"},
            follow_redirects=True,
            timeout=timeout,
            limits=httpx.Limits(max_connections=5),
        )
        self.rate = RateLimiter()

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> "GrowwFetcher":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request_headers(self, conditional: dict[str, str] | None) -> dict[str, str]:
        h: dict[str, str] = {}
        if conditional:
            h.update(conditional)
        return h

    def fetch(
        self,
        url: str,
        *,
        conditional_headers: dict[str, str] | None = None,
    ) -> FetchResult:
        assert_can_fetch(self._robots, self._ua, url)
        self.rate.acquire()

        last_exc: Exception | None = None
        for attempt in range(5):
            try:
                resp = self._client.get(
                    url,
                    headers=self._request_headers(conditional_headers),
                )
            except httpx.ReadError as e:
                last_exc = e
                log.warning("ReadError on %s attempt %s: %s", url, attempt + 1, e)
                time.sleep((2**attempt) + random.random())
                continue
            except OSError as e:
                if e.errno == errno.ENOSPC:
                    log.error("DISK_FULL while fetching %s", url)
                    raise
                last_exc = e
                time.sleep((2**attempt) + random.random())
                continue

            sc = resp.status_code

            if sc == 451:
                log.error("HTTP 451 legally blocked: %s", url)
                return FetchResult(
                    ok=False,
                    status_code=451,
                    final_url=str(resp.url),
                    html=None,
                    raw_bytes=None,
                    encoding_used=None,
                    etag=resp.headers.get("etag"),
                    last_modified=resp.headers.get("last-modified"),
                    not_modified=False,
                    error="HTTP 451 Unavailable For Legal Reasons",
                    legally_blocked=True,
                )

            if sc == 304:
                return FetchResult(
                    ok=True,
                    status_code=304,
                    final_url=str(resp.url),
                    html=None,
                    raw_bytes=None,
                    encoding_used=None,
                    etag=resp.headers.get("etag"),
                    last_modified=resp.headers.get("last-modified"),
                    not_modified=True,
                    error=None,
                )

            if sc in (429, 503, 504):
                wait = min(16.0, (2**attempt) + random.random())
                log.warning(
                    "HTTP %s on %s — backing off %.1fs (attempt %s/5)",
                    sc,
                    url,
                    wait,
                    attempt + 1,
                )
                time.sleep(wait)
                continue

            if sc >= 400:
                return FetchResult(
                    ok=False,
                    status_code=sc,
                    final_url=str(resp.url),
                    html=None,
                    raw_bytes=None,
                    encoding_used=None,
                    etag=None,
                    last_modified=None,
                    not_modified=False,
                    error=f"HTTP {sc}",
                )

            raw = resp.content
            text, enc = decode_html_bytes(raw)
            return FetchResult(
                ok=True,
                status_code=sc,
                final_url=str(resp.url),
                html=text,
                raw_bytes=raw,
                encoding_used=enc,
                etag=resp.headers.get("etag"),
                last_modified=resp.headers.get("last-modified"),
                not_modified=False,
                error=None,
            )

        return FetchResult(
            ok=False,
            status_code=0,
            final_url=url,
            html=None,
            raw_bytes=None,
            encoding_used=None,
            etag=None,
            last_modified=None,
            not_modified=False,
            error=f"fetch failed after retries: {last_exc!r}",
        )


def build_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=45.0,
    )
