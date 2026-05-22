"""Tests for ``ingest.aliases`` — covers edge cases 1.04, 1.08, 1.10, 1.11."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from config import ALIASES_YAML
from ingest.aliases import (
    AliasRegistry,
    AliasValidationError,
    load_aliases,
    normalize,
)
from ingest.sources import SourceRegistry


# ---------------------------------------------------------------------------
# Normalization (edge case 1.08)
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_casefolds(self) -> None:
        assert normalize("HDFC Mid Cap") == normalize("hdfc mid cap")

    def test_strips_punctuation_and_spaces(self) -> None:
        assert normalize("hdfc  mid-cap") == "hdfcmidcap"

    def test_expands_ampersand_to_and(self) -> None:
        assert normalize("Pharma & Healthcare") == normalize("Pharma and Healthcare")

    def test_drops_smart_quotes_and_accents(self) -> None:
        assert normalize("HDFC \u2018Mid\u2019 Cap") == normalize("HDFC Mid Cap")

    def test_is_idempotent(self) -> None:
        assert normalize(normalize("HDFC Mid Cap")) == normalize("HDFC Mid Cap")


# ---------------------------------------------------------------------------
# Phase 1.6 exit criteria: every scheme has at least one alias
# ---------------------------------------------------------------------------


class TestPhase1ExitCriteria:
    def test_every_scheme_has_aliases(
        self, source_registry: SourceRegistry, alias_registry: AliasRegistry
    ) -> None:
        for scheme in source_registry.schemes():
            assert scheme in alias_registry.canonicals(), (
                f"scheme {scheme!r} has no entry in aliases.yaml"
            )

    def test_no_unknown_schemes_in_aliases(
        self, source_registry: SourceRegistry, alias_registry: AliasRegistry
    ) -> None:
        known = set(source_registry.schemes())
        for canonical in alias_registry.canonicals():
            assert canonical in known, (
                f"aliases.yaml references unknown scheme: {canonical!r}"
            )


# ---------------------------------------------------------------------------
# Resolution behavior
# ---------------------------------------------------------------------------


class TestResolution:
    @pytest.mark.parametrize(
        "query, expected_canonical",
        [
            ("HDFC Mid Cap Fund", "HDFC Mid Cap Fund"),
            ("hdfc midcap", "HDFC Mid Cap Fund"),
            ("hdfc mid-cap", "HDFC Mid Cap Fund"),
            ("HDFC ELSS", "HDFC ELSS Tax Saver Fund"),
            ("hdfc tax saver", "HDFC ELSS Tax Saver Fund"),
            ("hdfc pharma & healthcare", "HDFC Pharma & Healthcare Fund"),
            ("hdfc pharma and healthcare", "HDFC Pharma & Healthcare Fund"),
            ("hdfc silver fof", "HDFC Silver ETF FoF"),
            ("hdfc liquid", "HDFC Liquid Fund"),
            ("hdfc defense", "HDFC Defence Fund"),
        ],
    )
    def test_resolve_exact(
        self, alias_registry: AliasRegistry, query: str, expected_canonical: str
    ) -> None:
        match = alias_registry.resolve(query)
        assert match is not None, f"failed to resolve {query!r}"
        assert match.canonical == expected_canonical

    def test_resolve_unknown_returns_none(self, alias_registry: AliasRegistry) -> None:
        assert alias_registry.resolve("Parag Parikh Flexi Cap") is None

    def test_find_in_query_picks_longest_match(
        self, alias_registry: AliasRegistry
    ) -> None:
        """``"hdfc mid cap fund"`` must win over ``"hdfc mid cap"``."""
        match = alias_registry.find_in_query(
            "what is the expense ratio of hdfc mid cap fund?"
        )
        assert match is not None
        assert match.canonical == "HDFC Mid Cap Fund"

    def test_find_in_query_ignores_unrelated(
        self, alias_registry: AliasRegistry
    ) -> None:
        assert alias_registry.find_in_query("the weather is nice today") is None


# ---------------------------------------------------------------------------
# Edge case 1.11 — legacy aliases
# ---------------------------------------------------------------------------


class TestLegacyAliases:
    def test_hdfc_equity_resolves_to_flexicap_with_legacy_flag(
        self, alias_registry: AliasRegistry
    ) -> None:
        match = alias_registry.resolve("HDFC Equity Fund")
        assert match is not None
        assert match.canonical == "HDFC Flexi Cap Fund"
        assert match.legacy is True

    def test_modern_aliases_are_not_marked_legacy(
        self, alias_registry: AliasRegistry
    ) -> None:
        match = alias_registry.resolve("hdfc flexicap")
        assert match is not None
        assert match.legacy is False


# ---------------------------------------------------------------------------
# Edge case 1.10 — alias collision invariant (validated via temp YAML)
# ---------------------------------------------------------------------------


def _write_aliases(tmp_path: Path, aliases: dict, legacy: dict | None = None) -> Path:
    p = tmp_path / "aliases.yaml"
    body: dict = {"aliases": aliases}
    if legacy is not None:
        body["legacy_aliases"] = legacy
    p.write_text(yaml.safe_dump(body), encoding="utf-8")
    return p


class TestAliasInvariants:
    def test_rejects_collision_across_schemes(
        self, tmp_path: Path, source_registry: SourceRegistry
    ) -> None:
        # Loader requires every scheme in sources.yaml to appear in aliases.yaml.
        # Start from the real file, then force two schemes to share one surface form.
        with ALIASES_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        aliases: dict[str, list[str]] = {
            k: list(v) for k, v in (data.get("aliases") or {}).items()
        }
        scheme_a, scheme_b = source_registry.schemes()[:2]
        collision = "zzz_forced_collision_alias"
        aliases[scheme_a] = aliases.get(scheme_a, []) + [collision]
        aliases[scheme_b] = aliases.get(scheme_b, []) + [collision]
        path = _write_aliases(tmp_path, aliases=aliases, legacy=data.get("legacy_aliases"))
        with pytest.raises(AliasValidationError, match="collision"):
            load_aliases(path, registry=source_registry)

    def test_rejects_unknown_scheme(
        self, tmp_path: Path, source_registry: SourceRegistry
    ) -> None:
        path = _write_aliases(
            tmp_path,
            aliases={"HDFC NonExistent Fund": ["x"]},
        )
        with pytest.raises(AliasValidationError, match="unknown schemes"):
            load_aliases(path, registry=source_registry)

    def test_rejects_missing_scheme(
        self, tmp_path: Path, source_registry: SourceRegistry
    ) -> None:
        scheme_a = source_registry.schemes()[0]
        path = _write_aliases(tmp_path, aliases={scheme_a: ["x"]})
        with pytest.raises(AliasValidationError, match="missing"):
            load_aliases(path, registry=source_registry)

    def test_rejects_empty_aliases_block(
        self, tmp_path: Path, source_registry: SourceRegistry
    ) -> None:
        p = tmp_path / "aliases.yaml"
        p.write_text(yaml.safe_dump({"aliases": {}}), encoding="utf-8")
        with pytest.raises(AliasValidationError, match="empty"):
            load_aliases(p, registry=source_registry)

    def test_rejects_non_string_alias(
        self, tmp_path: Path, source_registry: SourceRegistry
    ) -> None:
        path = _write_aliases(
            tmp_path,
            aliases={source_registry.schemes()[0]: ["ok", 42]},
        )
        with pytest.raises(AliasValidationError, match="list of strings"):
            load_aliases(path, registry=source_registry)
