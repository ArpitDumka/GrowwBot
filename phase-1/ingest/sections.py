"""Load ``config/sections.yaml`` (Groww heading synonyms → canonical section ids)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_PATH = CONFIG_DIR / "sections.yaml"

# Keys expected for Phase 2 parser + Phase 3 chunking (architecture §3.2).
REQUIRED_CANONICAL_SECTIONS = frozenset(
    {
        "header",
        "fund_details",
        "exit_load_tax",
        "minimum_investments",
        "holdings",
        "about",
        "fund_managers",
        "lock_in_banner",
    }
)


class SectionsConfigError(ValueError):
    """``sections.yaml`` failed structural validation."""


def load_sections(path: Path | None = None) -> dict[str, Any]:
    """Return the parsed YAML document (top-level keys: ``sections``, comments)."""
    p = path or DEFAULT_PATH
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SectionsConfigError("sections.yaml must be a mapping at the top level")
    sections = raw.get("sections")
    if not isinstance(sections, dict) or not sections:
        raise SectionsConfigError("sections.yaml: missing or empty 'sections' mapping")

    missing = REQUIRED_CANONICAL_SECTIONS - frozenset(sections.keys())
    if missing:
        raise SectionsConfigError(f"sections.yaml: missing canonical keys: {sorted(missing)}")

    for key, spec in sections.items():
        if key in ("header", "lock_in_banner"):
            if not isinstance(spec, dict):
                raise SectionsConfigError(f"sections.{key}: expected a mapping with detect_by/pattern")
            continue
        if not isinstance(spec, list) or not spec:
            raise SectionsConfigError(
                f"sections.{key}: expected a non-empty list of heading synonym strings"
            )
    return raw


def section_synonym_map(doc: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """``canonical_section_id`` → list of Groww heading strings (excludes regex-only rows)."""
    d = doc or load_sections()
    sections = d.get("sections") or {}
    out: dict[str, list[str]] = {}
    for canonical, spec in sections.items():
        if isinstance(spec, list):
            out[canonical] = [str(x) for x in spec]
    return out
