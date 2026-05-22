from mf_index.models import ChunkRecord
from mf_retrieve.config_loader import RetrievalConfig
from mf_retrieve.scoring import combine_final_scores


def _chunk(section: str, fields: list[str]) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=f"hdfc_elss#{section}",
        text="x",
        source_id="hdfc_elss",
        url="https://groww.in/x",
        section=section,
        scheme="HDFC ELSS Tax Saver Fund",
        category="ELSS",
        last_updated="2026-05-16",
        fields_detected=fields,
    )


def test_exit_load_prefers_exit_load_tax_over_about():
    cfg = RetrievalConfig(
        field_section_map={"exit_load": ("exit_load_tax", "header")},
        section_mismatch_penalty=0.25,
        primary_section_bonus=0.15,
    )
    about = _chunk("about", ["tax"])
    exit_sec = _chunk("exit_load_tax", ["exit_load", "tax"])
    rows = [
        (about, 0.98, 0.0, 0.9),
        (exit_sec, 0.74, 0.2, 0.85),
    ]
    ranked = combine_final_scores(rows, "exit_load", cfg)
    assert ranked[0][0].section == "exit_load_tax"
