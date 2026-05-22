"""sections.yaml loader."""

from __future__ import annotations

import pytest

from ingest.sections import (
    REQUIRED_CANONICAL_SECTIONS,
    SectionsConfigError,
    load_sections,
    section_synonym_map,
)


def test_load_sections_roundtrip() -> None:
    doc = load_sections()
    assert "sections" in doc
    assert REQUIRED_CANONICAL_SECTIONS <= frozenset(doc["sections"].keys())


def test_section_synonym_map_non_empty_lists() -> None:
    m = section_synonym_map()
    assert m["fund_details"]
    assert m["exit_load_tax"]


def test_load_sections_rejects_empty(tmp_path) -> None:
    p = tmp_path / "sections.yaml"
    p.write_text("sections: {}\n", encoding="utf-8")
    with pytest.raises(SectionsConfigError, match="empty"):
        load_sections(p)
