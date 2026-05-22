"""§6.1 [A] metadata pre-filter helpers."""

from __future__ import annotations

from mf_index.models import ChunkRecord


def is_excluded_doc_type(chunk: ChunkRecord, exclude: tuple[str, ...]) -> bool:
    return chunk.doc_type in exclude


def find_section_chunk(
    chunks: list[ChunkRecord],
    source_id: str,
    section: str,
    exclude_doc_types: tuple[str, ...],
) -> ChunkRecord | None:
    target = f"{source_id}#{section}"
    for c in chunks:
        if c.chunk_id == target or (c.source_id == source_id and c.section == section):
            if is_excluded_doc_type(c, exclude_doc_types):
                continue
            return c
    return None


def find_header_chunk(chunks: list[ChunkRecord], source_id: str) -> ChunkRecord | None:
    target = f"{source_id}#header"
    for c in chunks:
        if c.chunk_id == target and c.doc_type == "facts":
            return c
    for c in chunks:
        if c.source_id == source_id and c.section == "header" and c.doc_type == "facts":
            return c
    return None


def filter_scheme_chunks(
    chunks: list[ChunkRecord],
    scheme: str,
    exclude_doc_types: tuple[str, ...],
) -> list[ChunkRecord]:
    return [
        c
        for c in chunks
        if c.scheme == scheme and not is_excluded_doc_type(c, exclude_doc_types)
    ]


def find_field_chunk(
    chunks: list[ChunkRecord],
    source_id: str,
    field_id: str | None,
    preferred_sections: tuple[str, ...],
    exclude_doc_types: tuple[str, ...],
) -> ChunkRecord | None:
    """Fast-path: section chunk that tags ``field_id`` (§6.1 [A]).

    Groww corpus stores Latest NAV / AUM in ``about``; try configured order first,
    then any same-scheme chunk that tags the field (``about`` before ``header``).
    """
    if not field_id or not source_id:
        return None

    def _match(sec: str) -> ChunkRecord | None:
        target = f"{source_id}#{sec}"
        for c in chunks:
            if c.chunk_id == target or (c.source_id == source_id and c.section == sec):
                if is_excluded_doc_type(c, exclude_doc_types):
                    continue
                if field_id in c.fields_detected:
                    return c
        return None

    for sec in preferred_sections:
        hit = _match(sec)
        if hit:
            return hit

    fallback_order = ("about", "fund_details", "header", "exit_load_tax", "fund_managers", "holdings")
    candidates = [
        c
        for c in chunks
        if c.source_id == source_id
        and field_id in c.fields_detected
        and not is_excluded_doc_type(c, exclude_doc_types)
    ]
    if not candidates:
        return None
    by_section = {c.section: c for c in candidates}
    for sec in fallback_order:
        if sec in by_section:
            return by_section[sec]
    return candidates[0]
