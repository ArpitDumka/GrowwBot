"""§3.4 chunk schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mf_clean.chunk_models import Chunk
from mf_clean.chunk_schema import SPEC_34_KEYS, chunk_model_json_schema, chunk_to_spec_dict


def test_chunk_model_json_schema_has_core_properties() -> None:
    schema = chunk_model_json_schema()
    assert schema.get("title") == "Chunk"
    props = schema.get("properties") or {}
    for key in ("chunk_id", "text", "source_id", "url", "section", "fields_detected"):
        assert key in props


def test_chunk_to_spec_dict_matches_architecture_keys() -> None:
    c = Chunk(
        chunk_id="hdfc_midcap#exit_load_tax",
        text="Exit load 1%.",
        source_id="hdfc_midcap",
        url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        section="exit_load_tax",
        scheme="HDFC Mid Cap Fund",
        category="Mid Cap",
        last_updated="2026-05-13",
        fields_detected=["exit_load", "tax"],
        doc_type="facts",
    )
    d = chunk_to_spec_dict(c)
    assert set(d.keys()) == SPEC_34_KEYS
    assert "doc_type" not in d


def test_chunk_id_validation() -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="badid",
            text="x",
            source_id="s",
            url="https://groww.in/x",
            section="header",
            scheme="S",
            category="C",
            last_updated="2026-01-01",
        )


def test_last_updated_must_be_iso_date() -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="a#b",
            text="x",
            source_id="a",
            url="https://groww.in/x",
            section="b",
            scheme="S",
            category="C",
            last_updated="01-01-2026",
        )


def test_url_must_be_http_scheme() -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="a#b",
            text="x",
            source_id="a",
            url="ftp://x",
            section="b",
            scheme="S",
            category="C",
            last_updated="2026-01-01",
        )
