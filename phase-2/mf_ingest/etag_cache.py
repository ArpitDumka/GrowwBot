"""Persisted ETag / Last-Modified cache (edge case 2.10)."""

from __future__ import annotations

import json
from pathlib import Path

from mf_ingest.paths import ETAG_CACHE_PATH


class EtagCache:
    """JSON file keyed by canonical URL."""

    def __init__(self, path: Path = ETAG_CACHE_PATH) -> None:
        self.path = path
        self._data: dict[str, dict[str, str | None]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, url: str) -> dict[str, str | None] | None:
        return self._data.get(url)

    def update(
        self,
        url: str,
        *,
        etag: str | None,
        last_modified: str | None,
    ) -> None:
        self._data[url] = {"etag": etag, "last_modified": last_modified}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data, indent=2, sort_keys=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.path)
