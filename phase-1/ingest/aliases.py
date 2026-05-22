"""Scheme alias registry (Phase 1.5).

Loads ``config/aliases.yaml`` and exposes a normalize-then-lookup resolver. The
resolver is used by the Phase 5 scheme extractor. It also enforces invariants
required by edge cases 1.04 (no ambiguous aliases), 1.10 (each surface form
maps to exactly one scheme), and 1.08 (Unicode normalization).

Run ``python -m ingest.aliases`` to print a validation summary.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

from config import ALIASES_YAML
from ingest.sources import SourceRegistry, load_sources

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_AMP_RE = re.compile(r"\s*&\s*")


class AliasValidationError(Exception):
    """Raised when ``aliases.yaml`` violates a corpus-level invariant."""


def normalize(text: str) -> str:
    """Aggressive normalization for alias comparison.

    Lowercases, NFKC-normalizes, expands ``&`` -> ``and``, then strips every
    non-alphanumeric character. The result is a comparison key, NOT a
    display string.

    >>> normalize("HDFC Pharma & Healthcare Fund")
    'hdfcpharmaandhealthcarefund'
    >>> normalize("  hdfc  mid-cap  ")
    'hdfcmidcap'
    """
    s = unicodedata.normalize("NFKC", text).casefold()
    s = _AMP_RE.sub(" and ", s)
    return _NON_ALNUM_RE.sub("", s)


@dataclass(frozen=True)
class AliasMatch:
    """Result of a successful alias lookup."""

    canonical: str
    surface_form: str
    legacy: bool


class AliasRegistry:
    """Read-only alias map. Resolves a free-form query token to a scheme."""

    def __init__(
        self,
        aliases: dict[str, list[str]],
        legacy_aliases: dict[str, list[str]],
    ) -> None:
        self._aliases = {k: tuple(v) for k, v in aliases.items()}
        self._legacy_aliases = {k: tuple(v) for k, v in legacy_aliases.items()}

        self._index: dict[str, AliasMatch] = {}
        for canonical, surfaces in self._aliases.items():
            self._index[normalize(canonical)] = AliasMatch(canonical, canonical, False)
            for surface in surfaces:
                self._index[normalize(surface)] = AliasMatch(canonical, surface, False)
        for canonical, surfaces in self._legacy_aliases.items():
            for surface in surfaces:
                key = normalize(surface)
                self._index.setdefault(
                    key, AliasMatch(canonical, surface, True)
                )

    def canonicals(self) -> tuple[str, ...]:
        return tuple(self._aliases.keys())

    def surface_forms(self) -> tuple[str, ...]:
        forms: list[str] = []
        for surfaces in self._aliases.values():
            forms.extend(surfaces)
        return tuple(forms)

    def resolve(self, text: str) -> AliasMatch | None:
        """Exact-normalized lookup; returns ``None`` on miss.

        >>> r = load_aliases(_test=True)  # doctest: +SKIP
        """
        return self._index.get(normalize(text))

    def find_in_query(self, query: str) -> AliasMatch | None:
        """Try to find any alias as a substring of ``query`` (normalized).

        Picks the **longest** matching surface form so that
        ``"hdfc mid cap fund"`` beats ``"hdfc mid cap"``.
        """
        nq = normalize(query)
        best: tuple[int, AliasMatch] | None = None
        for key, match in self._index.items():
            if key and key in nq:
                if best is None or len(key) > best[0]:
                    best = (len(key), match)
        return best[1] if best else None


def _load_raw(path: Path | str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"aliases.yaml not found at {yaml_path}")
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    aliases = data.get("aliases") or {}
    legacy = data.get("legacy_aliases") or {}
    if not isinstance(aliases, dict) or not aliases:
        raise AliasValidationError(
            f"top-level 'aliases:' map missing or empty in {yaml_path}"
        )
    for k, v in aliases.items():
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise AliasValidationError(
                f"aliases.{k!r} must be a list of strings; got {type(v).__name__}"
            )
    for k, v in legacy.items():
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise AliasValidationError(
                f"legacy_aliases.{k!r} must be a list of strings; got {type(v).__name__}"
            )
    return aliases, legacy


def _enforce_invariants(
    aliases: dict[str, list[str]],
    legacy: dict[str, list[str]],
    registry: SourceRegistry,
) -> None:
    canonical_schemes = set(registry.schemes())

    # Each canonical key must be a known scheme.
    unknown_canonicals = set(aliases.keys()) - canonical_schemes
    if unknown_canonicals:
        raise AliasValidationError(
            f"aliases reference unknown schemes (not in sources.yaml): "
            f"{sorted(unknown_canonicals)}"
        )
    unknown_legacy_canonicals = set(legacy.keys()) - canonical_schemes
    if unknown_legacy_canonicals:
        raise AliasValidationError(
            f"legacy_aliases reference unknown schemes: "
            f"{sorted(unknown_legacy_canonicals)}"
        )

    # Every scheme must have at least one alias (Phase 1.6 exit criterion).
    missing = canonical_schemes - set(aliases.keys())
    if missing:
        raise AliasValidationError(
            f"schemes missing from aliases.yaml: {sorted(missing)}"
        )

    # Each alias must be unique across schemes (edge case 1.10).
    all_aliases: list[tuple[str, str]] = []
    for canonical, surfaces in aliases.items():
        for s in surfaces:
            all_aliases.append((normalize(s), canonical))
    for canonical, surfaces in legacy.items():
        for s in surfaces:
            all_aliases.append((normalize(s), canonical))

    by_key: dict[str, list[str]] = {}
    for key, canonical in all_aliases:
        by_key.setdefault(key, []).append(canonical)
    collisions = {
        key: sorted(set(owners))
        for key, owners in by_key.items()
        if len(set(owners)) > 1
    }
    if collisions:
        raise AliasValidationError(
            "alias collisions (same surface form maps to multiple schemes): "
            + "; ".join(f"{k!r}->{v}" for k, v in collisions.items())
        )

    # Forbid empty alias strings.
    empties = [
        (canonical, s)
        for canonical, surfaces in aliases.items()
        for s in surfaces
        if not s.strip()
    ]
    if empties:
        raise AliasValidationError(f"empty alias strings: {empties}")


def load_aliases(
    path: Path | str = ALIASES_YAML,
    registry: SourceRegistry | None = None,
) -> AliasRegistry:
    """Load and fully validate ``aliases.yaml``.

    Args:
        path: YAML path (defaults to ``config/aliases.yaml``).
        registry: source registry; loaded fresh if not provided.
    """
    aliases, legacy = _load_raw(path)
    reg = registry or load_sources()
    _enforce_invariants(aliases, legacy, reg)
    return AliasRegistry(aliases, legacy)


def _format_summary(registry: AliasRegistry) -> str:
    lines = [
        f"aliases.yaml: OK "
        f"({len(registry.canonicals())} schemes, "
        f"{len(registry.surface_forms())} aliases)",
        "",
        f"{'scheme':<35} {'#aliases':>9}",
        f"{'-' * 35} {'-' * 9}",
    ]
    for canonical in registry.canonicals():
        n = sum(1 for _ in registry._aliases[canonical])
        lines.append(f"{canonical:<35} {n:>9}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    try:
        registry = load_aliases()
    except (FileNotFoundError, AliasValidationError) as e:
        print(f"aliases.yaml: FAIL\n{e}", file=sys.stderr)
        return 1
    print(_format_summary(registry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
