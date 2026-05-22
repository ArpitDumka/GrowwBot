"""Tests for ``ingest.sources`` — Phase 1 exit criteria + edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ingest.sources import (
    EXPECTED_SOURCE_COUNT,
    MIN_CATEGORIES,
    Source,
    SourceRegistry,
    SourceValidationError,
    load_sources,
)
from ingest.url_utils import canonical_url


# ---------------------------------------------------------------------------
# Phase 1.6 — exit criteria
# ---------------------------------------------------------------------------


class TestPhase1ExitCriteria:
    def test_exactly_ten_sources(self, source_registry: SourceRegistry) -> None:
        """Phase 1.6: corpus is closed at 10 entries."""
        assert len(source_registry) == EXPECTED_SOURCE_COUNT == 10

    def test_at_least_five_categories(self, source_registry: SourceRegistry) -> None:
        """Phase 1.2: 5 SEBI categories must be represented."""
        assert len(source_registry.categories()) >= MIN_CATEGORIES

    def test_all_publishers_are_groww(self, source_registry: SourceRegistry) -> None:
        for s in source_registry:
            assert s.publisher == "Groww"

    def test_all_urls_are_groww_mutual_fund(self, source_registry: SourceRegistry) -> None:
        for s in source_registry:
            assert s.url.startswith("https://groww.in/mutual-funds/")

    def test_ids_are_unique(self, source_registry: SourceRegistry) -> None:
        ids = [s.id for s in source_registry]
        assert len(ids) == len(set(ids))

    def test_schemes_are_unique(self, source_registry: SourceRegistry) -> None:
        schemes = [s.scheme for s in source_registry]
        assert len(schemes) == len(set(schemes))

    def test_urls_are_unique_after_canonicalization(
        self, source_registry: SourceRegistry
    ) -> None:
        """Edge case 2.14: dedup after normalization."""
        urls = [canonical_url(s.url) for s in source_registry]
        assert len(urls) == len(set(urls))


# ---------------------------------------------------------------------------
# Edge case 1.12 — citation allow-list is derived from sources.yaml
# ---------------------------------------------------------------------------


class TestCitationAllowlist:
    def test_allowlist_has_same_size_as_registry(
        self, source_registry: SourceRegistry
    ) -> None:
        assert len(source_registry.citation_allowlist()) == len(source_registry)

    def test_allowlist_contains_every_source_url(
        self, source_registry: SourceRegistry
    ) -> None:
        allow = source_registry.citation_allowlist()
        for s in source_registry:
            assert canonical_url(s.url) in allow


# ---------------------------------------------------------------------------
# Per-row pydantic validators
# ---------------------------------------------------------------------------


VALID_ROW = {
    "id": "hdfc_midcap",
    "scheme": "HDFC Mid Cap Fund",
    "category": "Mid Cap",
    "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "publisher": "Groww",
    "refresh_frequency_days": 7,
}


class TestSourceModel:
    def test_happy_path(self) -> None:
        assert Source(**VALID_ROW).id == "hdfc_midcap"

    def test_rejects_non_snake_case_id(self) -> None:
        bad = dict(VALID_ROW, id="HDFC-Midcap")
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_non_groww_publisher(self) -> None:
        bad = dict(VALID_ROW, publisher="AMFI")
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_non_groww_url(self) -> None:
        bad = dict(VALID_ROW, url="https://www.hdfcfund.com/factsheet.pdf")
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_non_https_url(self) -> None:
        bad = dict(VALID_ROW, url="http://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth")
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_non_canonical_url(self) -> None:
        bad = dict(VALID_ROW, url=VALID_ROW["url"] + "/")
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_zero_refresh_frequency(self) -> None:
        bad = dict(VALID_ROW, refresh_frequency_days=0)
        with pytest.raises(Exception):
            Source(**bad)

    def test_rejects_extra_fields(self) -> None:
        bad = dict(VALID_ROW, trust_tier=2)
        with pytest.raises(Exception):
            Source(**bad)


# ---------------------------------------------------------------------------
# Registry-level invariants (simulated via temp YAML files)
# ---------------------------------------------------------------------------


def _write_yaml(tmp_path: Path, sources: list[dict]) -> Path:
    p = tmp_path / "sources.yaml"
    p.write_text(yaml.safe_dump({"sources": sources}), encoding="utf-8")
    return p


def _row(**overrides) -> dict:
    return {**VALID_ROW, **overrides}


class TestRegistryInvariants:
    def test_rejects_when_count_below_ten(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, [_row()])
        with pytest.raises(SourceValidationError, match="exactly 10"):
            load_sources(path)

    def test_rejects_duplicate_ids(self, tmp_path: Path) -> None:
        # id must be >= 3 chars (pydantic); same id on every row triggers registry invariant.
        rows = [
            _row(
                id="dup_scheme",
                scheme=f"Scheme {i}",
                url=f"https://groww.in/mutual-funds/slug-dup-{i}",
            )
            for i in range(10)
        ]
        path = _write_yaml(tmp_path, rows)
        with pytest.raises(SourceValidationError, match="duplicate ids"):
            load_sources(path)

    def test_rejects_duplicate_urls(self, tmp_path: Path) -> None:
        rows = [
            _row(
                id=f"id_{i}",
                scheme=f"Scheme {i}",
                url="https://groww.in/mutual-funds/same-slug",
            )
            for i in range(10)
        ]
        path = _write_yaml(tmp_path, rows)
        with pytest.raises(SourceValidationError, match="duplicate URLs"):
            load_sources(path)

    def test_rejects_too_few_categories(self, tmp_path: Path) -> None:
        rows = [
            _row(
                id=f"id_{i}",
                scheme=f"Scheme {i}",
                category="Mid Cap",
                url=f"https://groww.in/mutual-funds/slug-{i}",
            )
            for i in range(10)
        ]
        path = _write_yaml(tmp_path, rows)
        with pytest.raises(SourceValidationError, match="distinct categories"):
            load_sources(path)

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_sources(tmp_path / "does_not_exist.yaml")


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


class TestRegistryLookups:
    def test_by_id_finds_known(self, source_registry: SourceRegistry) -> None:
        assert source_registry.by_id("hdfc_elss").category == "ELSS"

    def test_by_scheme_finds_known(self, source_registry: SourceRegistry) -> None:
        assert source_registry.by_scheme("HDFC Defence Fund").id == "hdfc_defence"

    def test_by_id_raises_on_unknown(self, source_registry: SourceRegistry) -> None:
        with pytest.raises(KeyError):
            source_registry.by_id("does_not_exist")
