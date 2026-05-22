"""§7.3 — deterministic post-LLM output guard."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from mf_compose.paths import BANNED_TOKENS_YAML

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# Plain "Source: <url>" (and tolerant variants) — also accepted from LLM output.
_PLAIN_SOURCE_RE = re.compile(r"(?im)^\s*source\s*[:\-]\s*(https?://\S+)\s*$")
_FOOTER_RE = re.compile(r"Last updated from sources:\s*(\d{4}-\d{2}-\d{2})", re.I)
_NUMBER_RE = re.compile(
    r"(?:₹|rs\.?)\s*[\d,.]+(?:\s*(?:cr|lakh|lac|crore))?|\d+(?:[.,]\d+)?\s*%",
    re.I,
)
_PREFIX_RE = re.compile(
    r"^(?:sure[,!]?|here'?s your answer:?|of course[,!]?|certainly[,!]?)\s+",
    re.I,
)
_ABBREV = {"mr", "mrs", "ms", "dr", "inc", "ltd", "rs", "no"}


@dataclass
class GuardContext:
    chunk_text: str
    citation_url: str
    last_updated: str
    allowed_urls: frozenset[str]


@lru_cache(maxsize=1)
def load_banned_tokens(path: Path = BANNED_TOKENS_YAML) -> tuple[str, ...]:
    if not path.is_file():
        return ("recommend", "should you invest", "best fund", "guaranteed return")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("tokens") or []
    return tuple(str(t).lower() for t in items if isinstance(t, str))


def extract_numbers(text: str) -> set[str]:
    """Numeric tokens used for hallucination checks (must contain a digit)."""
    out: set[str] = set()
    for m in _NUMBER_RE.finditer(text):
        token = m.group(0).lower().replace(" ", "")
        if re.search(r"\d", token):
            out.add(token)
    return out


def split_sentences(body: str) -> list[str]:
    body = body.strip()
    if not body:
        return []
    parts = re.split(r"(?<=[.!?])\s+", body)
    out: list[str] = []
    buf: list[str] = []
    for part in parts:
        buf.append(part)
        joined = " ".join(buf)
        words = joined.rstrip().split()
        tail = words[-1].rstrip(".!?").lower() if words else ""
        if tail in _ABBREV:
            continue
        out.append(joined.strip())
        buf = []
    if buf:
        out.append(" ".join(buf).strip())
    return [s for s in out if s][:3]


def _normalize(text: str) -> str:
    text = text.strip()
    prev = None
    while text != prev:
        prev = text
        text = _PREFIX_RE.sub("", text).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


def _format_answer(body_text: str, url: str, label: str, last_updated: str) -> str:
    """Canonical answer footer: visible URL after "Source:".

    Format:
        <body>
        Source: <url>
        Last updated from sources: <YYYY-MM-DD>

    The frontend renders bare URLs as clickable links (parseAnswer.ts).
    """
    _ = label  # backward-compat; label no longer surfaced
    sentences = split_sentences(body_text)
    body = " ".join(sentences[:3])
    return f"{body}\nSource: {url}\nLast updated from sources: {last_updated}".strip()


_BANNED_OTHER_AMC_RE = re.compile(
    r"(?i)\b(?:sbi|icici|axis|nippon|kotak|aditya\s*birla|uti|tata|ppfas|parag\s*parikh|"
    r"motilal|mirae|dsp|franklin|invesco|edelweiss|quant\s+mutual|bandhan|baroda|"
    r"canara|sundaram|jm\s+financial|navi)\b"
)


def apply_smalltalk_guard(raw: str) -> tuple[str, list[str]]:
    """Lightweight guard for LLM smalltalk replies.

    Strips URLs, blocks banned tokens (advice phrasings), blocks other-AMC mentions,
    caps to 2 sentences. Returns ('', [violations]) if the reply cannot be salvaged.
    """
    violations: list[str] = []
    text = _normalize(raw)

    text = _LINK_RE.sub(lambda m: m.group(1) or "", text)
    text = re.sub(r"https?://\S+", "", text).strip()

    lower = text.lower()
    for token in load_banned_tokens():
        if token in lower:
            violations.append(f"banned_token:{token}")
            return "", violations

    if _BANNED_OTHER_AMC_RE.search(text):
        violations.append("other_amc_mentioned")
        return "", violations

    sentences = split_sentences(text)
    cleaned = " ".join(sentences[:2]).strip()
    if not cleaned:
        violations.append("empty_after_clean")
        return "", violations
    return cleaned, violations


def apply_output_guard(raw: str, ctx: GuardContext) -> tuple[str, list[str]]:
    violations: list[str] = []
    text = _normalize(raw)
    lower = text.lower()

    for token in load_banned_tokens():
        if token in lower:
            violations.append(f"banned_token:{token}")
            from mf_guard import templates as t5  # noqa: PLC0415

            return t5.ADVISORY, violations

    answer_nums = extract_numbers(text)
    ctx_nums = extract_numbers(ctx.chunk_text)
    invented = {n for n in answer_nums if n not in ctx_nums}
    if invented:
        violations.append(f"invented_numbers:{sorted(invented)}")
        from mf_retrieve.templates import not_found_message

        return not_found_message(ctx.citation_url), violations

    # Find a citation in EITHER format: `[label](url)` or `Source: <url>`
    md_links = list(_LINK_RE.finditer(text))
    plain_sources = list(_PLAIN_SOURCE_RE.finditer(text))

    if not md_links and not plain_sources:
        violations.extend(["missing_citation", "missing_footer"])
        body = text.split("Last updated")[0].strip()
        return _format_answer(body, ctx.citation_url, "Source", ctx.last_updated), violations

    if md_links and plain_sources:
        violations.append("extra_citations")

    if md_links:
        if len(md_links) > 1:
            violations.append("extra_citations")
        first = md_links[0]
        body = text[: first.start()].strip()
        url = first.group(2).strip()
        if url not in ctx.allowed_urls:
            violations.append("url_not_allowlisted")
            url = ctx.citation_url
        tail = text[first.end() :]
    else:
        first = plain_sources[0]
        body = text[: first.start()].strip()
        url = first.group(1).strip()
        if url not in ctx.allowed_urls:
            violations.append("url_not_allowlisted")
            url = ctx.citation_url
        tail = text[first.end() :]

    footer_match = _FOOTER_RE.search(tail)
    if not footer_match:
        violations.append("missing_footer")
    elif footer_match.group(1) != ctx.last_updated:
        violations.append("footer_date_corrected")

    # Always stamp the corpus date from chunk metadata (never trust the LLM footer).
    return _format_answer(body, url, "Source", ctx.last_updated), violations
