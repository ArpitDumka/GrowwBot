"""URL canonicalization helpers.

Phase 1 owner; used by ``ingest.sources`` (dedup check, edge case 2.14) and
later by the Phase 2 fetcher (redirect handling, edge case 1.01).

Canonical form rules:
- lowercase scheme and host
- strip default ports (``:80`` for http, ``:443`` for https)
- collapse repeated slashes in path
- strip a single trailing slash from path (unless path is just ``/``)
- drop URL fragment (``#...``)
- preserve query string verbatim (order-sensitive for Groww)
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": "80", "https": "443"}
_MULTI_SLASH_RE = re.compile(r"/{2,}")


def canonical_url(url: str) -> str:
    """Return a canonical form of ``url``.

    >>> canonical_url("HTTPS://Groww.IN/mutual-funds/hdfc-mid-cap-fund-direct-growth/")
    'https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth'
    >>> canonical_url("https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth#exit-load")
    'https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth'
    """
    parts = urlsplit(url.strip())

    scheme = parts.scheme.lower()
    host = parts.hostname.lower() if parts.hostname else ""

    port = parts.port
    if port is not None and str(port) != _DEFAULT_PORTS.get(scheme, ""):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = _MULTI_SLASH_RE.sub("/", parts.path or "/")
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    return urlunsplit((scheme, netloc, path, parts.query, ""))


def is_groww_mutual_fund_url(url: str) -> bool:
    """True iff ``url`` is on the Groww mutual-funds path."""
    parts = urlsplit(url)
    return (
        parts.scheme == "https"
        and (parts.hostname or "").lower() == "groww.in"
        and (parts.path or "").startswith("/mutual-funds/")
        and len((parts.path or "").removeprefix("/mutual-funds/")) > 0
    )
