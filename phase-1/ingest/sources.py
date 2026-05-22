"""Source registry loader + validator (Phase 1).

Reads ``config/sources.yaml``, validates per-row with pydantic, and enforces
corpus-level invariants (counts, uniqueness, category coverage). The validated
registry is the **single source of truth** consumed by:

- the Phase 2 fetcher (which URLs to pull),
- the Phase 7 output guard (allow-listed citation URLs — see edge case 1.12),
- the Phase 9 eval harness (coverage check — see edge case 9.13).

Run ``python -m ingest.sources`` to print a validation summary.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from config import SOURCES_YAML
from ingest.url_utils import canonical_url, is_groww_mutual_fund_url

EXPECTED_SOURCE_COUNT = 10
MIN_CATEGORIES = 5
_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class SourceValidationError(Exception):
    """Raised when ``sources.yaml`` violates a corpus-level invariant."""


class Source(BaseModel):
    """Single registry entry. Mirrors the YAML row shape."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=3, max_length=64)
    scheme: str = Field(min_length=3)
    category: str = Field(min_length=2)
    url: str
    publisher: str
    refresh_frequency_days: int = Field(ge=1, le=365)

    @field_validator("id")
    @classmethod
    def _id_is_snake_case(cls, v: str) -> str:
        if not _ID_RE.fullmatch(v):
            raise ValueError(
                f"id {v!r} must match {_ID_RE.pattern} (lowercase snake_case)"
            )
        return v

    @field_validator("publisher")
    @classmethod
    def _publisher_is_groww(cls, v: str) -> str:
        if v != "Groww":
            raise ValueError(
                f"publisher must be 'Groww' (corpus is locked to Groww); got {v!r}"
            )
        return v

    @model_validator(mode="after")
    def _url_is_groww_mf(self) -> "Source":
        if not is_groww_mutual_fund_url(self.url):
            raise ValueError(
                f"url {self.url!r} must be an https://groww.in/mutual-funds/<slug> URL"
            )
        if self.url != canonical_url(self.url):
            raise ValueError(
                f"url {self.url!r} is not in canonical form; "
                f"expected {canonical_url(self.url)!r}"
            )
        return self


class SourceRegistry:
    """Read-only collection of validated ``Source`` rows."""

    def __init__(self, sources: list[Source]) -> None:
        self._sources: tuple[Source, ...] = tuple(sources)
        self._by_id = {s.id: s for s in self._sources}
        self._by_scheme = {s.scheme: s for s in self._sources}

    @property
    def sources(self) -> tuple[Source, ...]:
        return self._sources

    def __iter__(self) -> Iterable[Source]:
        return iter(self._sources)

    def __len__(self) -> int:
        return len(self._sources)

    def by_id(self, source_id: str) -> Source:
        return self._by_id[source_id]

    def by_scheme(self, scheme: str) -> Source:
        return self._by_scheme[scheme]

    def schemes(self) -> tuple[str, ...]:
        return tuple(s.scheme for s in self._sources)

    def urls(self) -> tuple[str, ...]:
        return tuple(s.url for s in self._sources)

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({s.category for s in self._sources}))

    def citation_allowlist(self) -> frozenset[str]:
        """Canonical URLs that the Phase 7 output guard will accept."""
        return frozenset(canonical_url(s.url) for s in self._sources)


def _enforce_invariants(sources: list[Source]) -> None:
    if len(sources) != EXPECTED_SOURCE_COUNT:
        raise SourceValidationError(
            f"expected exactly {EXPECTED_SOURCE_COUNT} sources, found {len(sources)}"
        )

    ids = [s.id for s in sources]
    dup_ids = [k for k, v in Counter(ids).items() if v > 1]
    if dup_ids:
        raise SourceValidationError(f"duplicate ids: {dup_ids}")

    schemes = [s.scheme for s in sources]
    dup_schemes = [k for k, v in Counter(schemes).items() if v > 1]
    if dup_schemes:
        raise SourceValidationError(f"duplicate schemes: {dup_schemes}")

    canonical_urls = [canonical_url(s.url) for s in sources]
    dup_urls = [k for k, v in Counter(canonical_urls).items() if v > 1]
    if dup_urls:
        raise SourceValidationError(f"duplicate URLs (after canonicalization): {dup_urls}")

    categories = {s.category for s in sources}
    if len(categories) < MIN_CATEGORIES:
        raise SourceValidationError(
            f"corpus must span >= {MIN_CATEGORIES} distinct categories, "
            f"found {len(categories)}: {sorted(categories)}"
        )


def load_sources(path: Path | str = SOURCES_YAML) -> SourceRegistry:
    """Load and fully validate ``sources.yaml``.

    Raises:
        FileNotFoundError: if the YAML file is missing.
        SourceValidationError: on any invariant violation.
        pydantic.ValidationError: on per-row schema violation.
    """
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"sources.yaml not found at {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    raw_rows = data.get("sources")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise SourceValidationError(
            f"top-level 'sources:' list missing or empty in {yaml_path}"
        )

    sources: list[Source] = []
    errors: list[str] = []
    for idx, row in enumerate(raw_rows):
        try:
            sources.append(Source(**row))
        except ValidationError as e:
            errors.append(f"row #{idx} ({row.get('id', '?')}): {e}")

    if errors:
        raise SourceValidationError(
            "per-row validation failed:\n  - " + "\n  - ".join(errors)
        )

    _enforce_invariants(sources)
    return SourceRegistry(sources)


def _format_summary(registry: SourceRegistry) -> str:
    lines = [
        f"sources.yaml: OK ({len(registry)} entries, "
        f"{len(registry.categories())} categories)",
        "",
        f"{'id':<22} {'category':<14} {'scheme'}",
        f"{'-' * 22} {'-' * 14} {'-' * 40}",
    ]
    for s in registry:
        lines.append(f"{s.id:<22} {s.category:<14} {s.scheme}")
    lines.append("")
    lines.append("categories: " + ", ".join(registry.categories()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    try:
        registry = load_sources()
    except (FileNotFoundError, SourceValidationError, ValidationError) as e:
        print(f"sources.yaml: FAIL\n{e}", file=sys.stderr)
        return 1
    print(_format_summary(registry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
