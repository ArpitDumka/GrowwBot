"""Simple in-memory rate limiter (edge 10.05 — 30 req/min)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, *, requests_per_minute: int) -> None:
        self._window = 60.0
        self._limit = max(1, requests_per_minute)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self._window:
                q.popleft()
            if len(q) >= self._limit:
                retry = max(1, int(self._window - (now - q[0])) + 1)
                return False, retry
            q.append(now)
            return True, 0
