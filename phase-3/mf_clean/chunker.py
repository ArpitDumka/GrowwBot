"""Section-aware chunking (architecture §3.2), Groww §3.3 prep, §3.4 chunk objects, §3.7 caps."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from mf_clean.chunk_models import Chunk, NormalizedDocument, SectionBlock
from mf_clean.cleaner import clean_text
from mf_clean.field_detector import detect_fields
from mf_clean.groww_clean import strip_groww_ui_noise
from mf_clean.paths import PHASE2_PROCESSED

# --- §3.7 proxies (true tokens need an embedder tokenizer) ---
_MIN_WORDS = 30
_MAX_WORDS = 600
# Keep dedicated chunks for short but high-value sections (problem-statement facts).
_NO_MERGE_SECTIONS = frozenset({"minimum_investments", "lock_in_banner"})


def fetched_to_last_updated(fetched_at: str) -> str:
    """``2026-05-14T20:15:22Z`` → ``2026-05-14`` (edge 3.13)."""
    s = fetched_at.strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s[:10] if s else ""


def _word_count(text: str) -> int:
    return len(text.split())


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " …"


_HOLDINGS_HEADER = re.compile(r"^Holdings\s*\(\d+\)\s*", re.I)
_ASSET_ROW = re.compile(r"(\d+\.\d{2})\s*$")


def reduce_holdings_top10(
    text: str,
    *,
    corpus_boilerplate_lines: frozenset[str] | None = None,
    apply_clean: bool = True,
) -> str:
    """Keep top 10 positions by stated Assets % (edge 3.10).

    Groww often ships holdings as one dense line: ``…Ltd.Equity4.50%Next…``.
    We split on ``%`` and parse a trailing ``X.XX`` weight per segment.
    """
    t = text.strip()
    t = _HOLDINGS_HEADER.sub("", t)
    if "NameSectorInstrumentsAssets" in t:
        t = t.split("NameSectorInstrumentsAssets", 1)[-1].strip()
    parts = [p.strip() for p in t.split("%") if p.strip()]
    rows: list[tuple[str, float]] = []
    for p in parts:
        if p.casefold().startswith("see all"):
            break
        m = _ASSET_ROW.search(p)
        if not m:
            continue
        try:
            pct = float(m.group(1))
        except ValueError:
            continue
        name_body = p[: m.start()].strip()
        if len(name_body) < 3:
            continue
        rows.append((name_body, pct))
    rows.sort(key=lambda x: x[1], reverse=True)
    top = rows[:10]
    if not top:
        return (
            clean_text(text, corpus_boilerplate_lines=corpus_boilerplate_lines)
            if apply_clean
            else text.strip()
        )
    lines = [f"{name} — {pct:.2f}%" for name, pct in top]
    merged = "Top holdings (by weight): " + "; ".join(lines)
    if len(rows) > 10:
        merged += f" (+ {len(rows) - 10} more holdings omitted)"
    if apply_clean:
        return clean_text(merged, corpus_boilerplate_lines=corpus_boilerplate_lines)
    return merged.strip()


def _prepare_section_text(
    block: SectionBlock,
    *,
    corpus_boilerplate_lines: frozenset[str] | None,
    apply_cleaning: bool,
    apply_groww_section_clean: bool,
) -> str:
    raw0 = strip_groww_ui_noise(block.text) if apply_groww_section_clean else block.text
    if block.section == "holdings":
        return reduce_holdings_top10(
            raw0,
            corpus_boilerplate_lines=corpus_boilerplate_lines,
            apply_clean=apply_cleaning,
        )
    raw = raw0
    if not apply_cleaning:
        return raw.strip()
    return clean_text(raw, corpus_boilerplate_lines=corpus_boilerplate_lines)


def _doc_type_for_section(section: str) -> Literal["facts", "performance"]:
    return "performance" if section == "performance" else "facts"


def _merge_tiny_chunks(chunks: list[Chunk]) -> None:
    """Merge ``facts`` chunks under ``_MIN_WORDS`` into the **previous** facts chunk (§3.7)."""
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if (
            c.doc_type == "performance"
            or c.section in _NO_MERGE_SECTIONS
            or _word_count(c.text) >= _MIN_WORDS
        ):
            i += 1
            continue
        prev = i - 1
        if prev < 0:
            i += 1
            continue
        tgt = chunks[prev]
        if tgt.doc_type != "facts":
            i += 1
            continue
        new_t = f"{tgt.text}\n\n[{c.section}]\n{c.text}".strip()
        new_f = sorted(set(tgt.fields_detected) | set(c.fields_detected))
        tgt = tgt.model_copy(update={"text": new_t, "fields_detected": new_f})
        if _word_count(tgt.text) > _MAX_WORDS:
            tgt = tgt.model_copy(update={"text": _truncate_words(tgt.text, _MAX_WORDS)})
        chunks[prev] = tgt
        chunks.pop(i)


def chunk_normalized_document(
    doc: NormalizedDocument,
    *,
    apply_cleaning: bool = True,
    apply_groww_section_clean: bool = True,
    corpus_boilerplate_lines: frozenset[str] | None = None,
) -> list[Chunk]:
    """One chunk per section (§3.2); ``performance`` → ``doc_type=performance``."""
    last_updated = fetched_to_last_updated(doc.fetched_at)
    chunks: list[Chunk] = []

    for block in doc.sections:
        text = _prepare_section_text(
            block,
            corpus_boilerplate_lines=corpus_boilerplate_lines,
            apply_cleaning=apply_cleaning,
            apply_groww_section_clean=apply_groww_section_clean,
        )
        if not text.strip():
            continue
        if _word_count(text) > _MAX_WORDS:
            text = _truncate_words(text, _MAX_WORDS)
        doc_type = _doc_type_for_section(block.section)
        fields = (
            detect_fields(text, section=block.section, category=doc.category)
            if doc_type == "facts"
            else []
        )
        chunks.append(
            Chunk(
                chunk_id=f"{doc.source_id}#{block.section}",
                text=text,
                source_id=doc.source_id,
                url=doc.url,
                section=block.section,
                scheme=doc.scheme,
                category=doc.category,
                publisher="Groww",
                last_updated=last_updated,
                fields_detected=fields,
                doc_type=doc_type,
            )
        )

    _merge_tiny_chunks(chunks)
    return chunks


def load_normalized_document(path: Path) -> NormalizedDocument:
    return NormalizedDocument.model_validate_json(path.read_text(encoding="utf-8"))


def iter_processed_json_paths(processed_dir: Path = PHASE2_PROCESSED) -> list[Path]:
    """All ``*.json`` under processed dir except ingest manifests."""
    if not processed_dir.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(processed_dir.glob("*.json")):
        if p.name.startswith("ingest_manifest"):
            continue
        out.append(p)
    return out


def chunk_corpus(
    processed_dir: Path = PHASE2_PROCESSED,
    *,
    apply_cleaning: bool = True,
    apply_groww_section_clean: bool = True,
    corpus_boilerplate_lines: frozenset[str] | None = None,
) -> list[Chunk]:
    """Chunk every normalized document in ``phase-2/data/processed/``."""
    all_chunks: list[Chunk] = []
    paths = iter_processed_json_paths(processed_dir)
    raw_texts = [p.read_text(encoding="utf-8") for p in paths]
    docs = [NormalizedDocument.model_validate_json(t) for t in raw_texts]
    boiler = corpus_boilerplate_lines
    if boiler is None and len(docs) > 1:
        from mf_clean.cleaner import compute_corpus_boilerplate_lines

        page_texts = ["\n\n".join(f"{b.section}\n{b.text}" for b in d.sections) for d in docs]
        boiler = compute_corpus_boilerplate_lines(page_texts, min_fraction=0.8)

    for doc in docs:
        all_chunks.extend(
            chunk_normalized_document(
                doc,
                apply_cleaning=apply_cleaning,
                apply_groww_section_clean=apply_groww_section_clean,
                corpus_boilerplate_lines=boiler,
            )
        )
    return all_chunks


def chunks_to_jsonl(chunks: Sequence[Chunk]) -> str:
    return "\n".join(c.model_dump_json() for c in chunks)
