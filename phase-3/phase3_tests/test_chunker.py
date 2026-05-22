"""Phase 3.2 chunker tests."""

from __future__ import annotations

from mf_clean.chunk_models import NormalizedDocument, SectionBlock
from mf_clean.chunker import (
    chunk_normalized_document,
    reduce_holdings_top10,
)


def _doc(**kwargs) -> NormalizedDocument:
    base = dict(
        source_id="test_src",
        url="https://groww.in/mutual-funds/x",
        fetched_at="2026-05-14T12:00:00Z",
        content_hash="0" * 64,
        scheme="Test Scheme",
        category="Mid Cap",
        publisher="Groww",
    )
    base.update(kwargs)
    return NormalizedDocument.model_validate(base)


def test_performance_section_gets_doc_type_performance() -> None:
    doc = _doc(
        sections=[
            SectionBlock(section="header", text="NAV ₹10 Very High Risk benchmark NIFTY"),
            SectionBlock(section="performance", text="3Y returns +20% category rank 1"),
        ],
    )
    chunks = chunk_normalized_document(doc, apply_cleaning=False)
    perf = next(c for c in chunks if c.section == "performance")
    assert perf.doc_type == "performance"
    assert perf.fields_detected == []


def test_holdings_top10_sorts_by_weight() -> None:
    raw = (
        "Holdings (3)\nNameSectorInstrumentsAssets"
        "SmallCoEquity1.00%"
        "BigCoEquity5.50%"
        "MidCoEquity3.25%"
        "See All"
    )
    out = reduce_holdings_top10(raw, apply_clean=False)
    assert "5.50" in out
    assert out.index("5.50") < out.index("3.25") < out.index("1.00")


def test_chunk_ids_and_schema() -> None:
    filler = " ".join(f"clause{n} applies to redemptions and holding periods." for n in range(12))
    exit_body = (
        "Exit load 1%. Stamp duty 0.005%. Tax if redeemed within one year. "
        "Long statutory text so this section stays its own chunk under the §3.7 word proxy. "
        + filler
    )
    doc = _doc(
        sections=[
            SectionBlock(section="header", text="HDFC X Direct Growth NAV ₹1 expense ratio 0.5%"),
            SectionBlock(section="exit_load_tax", text=exit_body),
        ],
    )
    chunks = chunk_normalized_document(doc)
    ids = {c.chunk_id for c in chunks}
    assert "test_src#header" in ids
    assert "test_src#exit_load_tax" in ids
    h = next(c for c in chunks if c.section == "header")
    assert h.last_updated == "2026-05-14"
    assert h.publisher == "Groww"
    x = next(c for c in chunks if c.section == "exit_load_tax")
    assert "exit_load" in x.fields_detected


def test_lock_in_banner_kept_as_own_chunk() -> None:
    """ELSS lock-in must stay retrievable (problem statement §2)."""
    doc = _doc(
        sections=[
            SectionBlock(
                section="header",
                text=" ".join(f"w{i}" for i in range(40)),
            ),
            SectionBlock(section="lock_in_banner", text="ELSS • 3Y Lock-in"),
        ],
        category="ELSS",
    )
    chunks = chunk_normalized_document(doc, apply_cleaning=False)
    lock = next(c for c in chunks if c.section == "lock_in_banner")
    assert "3Y" in lock.text
    header = next(c for c in chunks if c.section == "header")
    assert "lock_in_banner" not in header.text
