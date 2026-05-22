from mf_index.models import ChunkRecord
from mf_retrieve.boosts import compute_boost
from mf_retrieve.config_loader import RetrievalConfig


def _chunk(**kwargs) -> ChunkRecord:
    base = dict(
        chunk_id="hdfc_midcap#header",
        text="Expense ratio 0.77%",
        source_id="hdfc_midcap",
        url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        section="header",
        scheme="HDFC Mid Cap Fund",
        category="Mid Cap",
        last_updated="2026-05-12",
        fields_detected=[],
        doc_type="facts",
    )
    base.update(kwargs)
    return ChunkRecord(**base)


def test_section_boost_without_field_tag():
    cfg = RetrievalConfig(
        field_boost=0.12,
        section_boost=0.08,
        field_section_map={"expense_ratio": ("header", "fund_details")},
    )
    c = _chunk(section="header")
    assert compute_boost(c, "expense_ratio", cfg) == 0.08


def test_field_and_section_boost_stack():
    cfg = RetrievalConfig(
        field_boost=0.12,
        section_boost=0.08,
        field_section_map={"exit_load": ("exit_load_tax",)},
    )
    c = _chunk(section="exit_load_tax", fields_detected=["exit_load"])
    assert compute_boost(c, "exit_load", cfg) == 0.2
