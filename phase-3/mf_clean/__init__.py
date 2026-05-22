"""Phase 3 — cleaning (§3.1) + Groww strip (§3.3) + chunking (§3.2) + schema (§3.4)."""

from mf_clean.chunk_models import Chunk, NormalizedDocument, SectionBlock
from mf_clean.chunk_schema import (
    SPEC_34_KEYS,
    chunk_model_json_schema,
    chunk_to_spec_dict,
    dumps_chunk_spec_json,
)
from mf_clean.chunker import (
    chunk_corpus,
    chunk_normalized_document,
    chunks_to_jsonl,
    fetched_to_last_updated,
    iter_processed_json_paths,
    load_normalized_document,
    reduce_holdings_top10,
)
from mf_clean.cleaner import (
    clean_text,
    collapse_whitespace,
    compute_corpus_boilerplate_lines,
    join_split_numbers,
    normalize_boilerplate_line,
)
from mf_clean.corpus_stats import (
    CorpusSizeReport,
    assert_chunk_count_in_bounds,
    expected_chunk_bounds,
    summarize_chunk_corpus,
)
from mf_clean.field_detector import (
    CANONICAL_FIELD_IDS,
    detect_fields,
    list_canonical_field_ids,
    validate_fields_detected,
)
from mf_clean.groww_clean import strip_groww_ui_noise

__all__ = [
    "CANONICAL_FIELD_IDS",
    "SPEC_34_KEYS",
    "Chunk",
    "CorpusSizeReport",
    "NormalizedDocument",
    "SectionBlock",
    "chunk_corpus",
    "chunk_model_json_schema",
    "chunk_normalized_document",
    "chunk_to_spec_dict",
    "chunks_to_jsonl",
    "clean_text",
    "collapse_whitespace",
    "assert_chunk_count_in_bounds",
    "compute_corpus_boilerplate_lines",
    "detect_fields",
    "expected_chunk_bounds",
    "dumps_chunk_spec_json",
    "fetched_to_last_updated",
    "iter_processed_json_paths",
    "join_split_numbers",
    "list_canonical_field_ids",
    "load_normalized_document",
    "normalize_boilerplate_line",
    "reduce_holdings_top10",
    "strip_groww_ui_noise",
    "summarize_chunk_corpus",
    "validate_fields_detected",
]
