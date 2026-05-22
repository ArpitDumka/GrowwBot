"""Phase 3.1 — Text cleaning before chunking.

Rules (``docs/architecture.md`` §3.1):

- Collapse multi-space / multi-newline.
- Drop headers/footers repeated on **many** pages (optional corpus-level line set).
- Preserve numeric tokens with units (``0.85%``, ``₹500``, ``3 years``).
- Strip emojis and C0/C1 control characters; keep ``₹``, ``%``, digits, letters.

Also applies edge-case **3.02** (decimal fraction continued on the next line
after ``.``) and a minimal **3.08** line denylist for glossary-style pollution
(see ``docs/edge-cases/phase-3-chunking.md``).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

# --- Edge 3.02: fractional part broken across newline (e.g. "4,433.\n98 Cr") ---
_DECIMAL_NEWLINE_FRAC = re.compile(r"(\.)\s*\n\s*(\d+)")

# --- Strip emoji / pictographs (no extra deps) ---
_EMOJI_AND_PICTO = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "\U000023E9-\U000023FA"  # UI symbols
    "\U0000FE0F"  # VS16
    "\U0000200D"  # ZWJ
    "]+",
    flags=re.UNICODE,
)

# C0/C1 controls except common whitespace (keep TAB/LF/CR for line ops; stripped later)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f\xad]")

# --- Edge 3.08: glossary / "Understand terms" style lines (substring match, casefold) ---
_DEFINITION_LINE_MARKERS: tuple[str, ...] = (
    "understand terms",
    "annualised returns",
    "annualized returns",
    "absolute returns",
    "expense ratio a fee payable",
    "expense ratio is the",
    "what is expense ratio",
    "what is nav",
    "net asset value (nav)",
)


def normalize_boilerplate_line(line: str) -> str:
    """Normalize a single line for cross-page frequency matching."""
    return " ".join(line.split()).strip()


def compute_corpus_boilerplate_lines(
    page_texts: Sequence[str],
    *,
    min_fraction: float = 0.8,
    min_len: int = 12,
    max_len: int = 220,
) -> frozenset[str]:
    """Lines that appear in at least ``min_fraction`` of pages (normalized).

    Used to drop headers/footers **repeated on (nearly) every page** (§3.1).
    """
    texts = list(page_texts)
    n = len(texts)
    if n == 0:
        return frozenset()
    need = max(1, int(n * min_fraction + 0.999999))  # ceil without import
    per_doc_lines: list[set[str]] = []
    for t in texts:
        seen: set[str] = set()
        for raw in t.splitlines():
            key = normalize_boilerplate_line(raw)
            if min_len <= len(key) <= max_len:
                seen.add(key)
        per_doc_lines.append(seen)

    counts: dict[str, int] = {}
    for seen in per_doc_lines:
        for ln in seen:
            counts[ln] = counts.get(ln, 0) + 1

    return frozenset(ln for ln, c in counts.items() if c >= need)


def join_split_numbers(text: str) -> str:
    """Repair decimal fractions broken across a newline (edge case 3.02)."""
    prev = None
    out = text
    while prev != out:
        prev = out
        out = _DECIMAL_NEWLINE_FRAC.sub(r".\2", out)
    return out


def _strip_emoji_and_controls(text: str) -> str:
    out_chars: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == "Cs":  # surrogate — drop
            continue
        if cat in ("Cc", "Cf") and ch not in "\t\n\r":
            continue
        out_chars.append(ch)
    s = "".join(out_chars)
    s = _EMOJI_AND_PICTO.sub("", s)
    s = _CONTROL_CHARS.sub("", s)
    return s


def _drop_definition_marker_lines(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        low = line.casefold()
        if any(m in low for m in _DEFINITION_LINE_MARKERS):
            continue
        kept.append(line)
    return "\n".join(kept)


def _drop_corpus_lines(text: str, corpus_lines: frozenset[str]) -> str:
    if not corpus_lines:
        return text
    out_lines: list[str] = []
    for raw in text.splitlines():
        key = normalize_boilerplate_line(raw)
        if key and key in corpus_lines:
            continue
        out_lines.append(raw)
    return "\n".join(out_lines)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace to a single ASCII space."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(
    text: str,
    *,
    corpus_boilerplate_lines: frozenset[str] | None = None,
    join_split_numeric_tokens: bool = True,
    drop_definition_marker_lines: bool = True,
) -> str:
    """Apply Phase 3.1 cleaning rules and return a single-line-ish string."""
    t = text
    if join_split_numeric_tokens:
        t = join_split_numbers(t)
    if drop_definition_marker_lines:
        t = _drop_definition_marker_lines(t)
    if corpus_boilerplate_lines:
        t = _drop_corpus_lines(t, corpus_boilerplate_lines)
    t = _strip_emoji_and_controls(t)
    return collapse_whitespace(t)
