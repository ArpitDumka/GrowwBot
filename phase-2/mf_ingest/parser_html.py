"""Groww mutual-fund HTML → normalized sections (architecture §2.1–§3.2)."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

import trafilatura
import yaml
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser

from mf_ingest.models import NormalizedDocument, SectionBlock, utc_now_iso
from mf_ingest.paths import MIN_SECTIONS_OK, SECTIONS_YAML

log = logging.getLogger(__name__)

_LOCK_IN_RE = re.compile(
    r"ELSS\s*[•·\-]\s*\d+Y\s*Lock-in",
    re.I,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_section_synonyms(path: Path = SECTIONS_YAML) -> dict[str, list[str]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sections = raw.get("sections") or {}
    out: dict[str, list[str]] = {}
    for canonical, spec in sections.items():
        if isinstance(spec, list):
            out[canonical] = [str(x) for x in spec]
        elif isinstance(spec, dict) and "pattern" in spec:
            out[canonical] = []  # regex-only section
        else:
            out[canonical] = []
    return out


def _build_heading_map(synonyms: dict[str, list[str]]) -> dict[str, str]:
    """Lower-cased heading text → canonical section id."""
    m: dict[str, str] = {}
    for canonical, phrases in synonyms.items():
        if canonical in ("header", "lock_in_banner"):
            continue
        for p in phrases:
            key = p.strip().lower()
            if key in m and m[key] != canonical:
                log.debug(
                    "heading map collision %r -> %s (overridden by %s)",
                    key,
                    m[key],
                    canonical,
                )
            m[key] = canonical
    return m


def _canonical_for_h2_title(title: str, heading_map: dict[str, str]) -> str | None:
    if not title or not title.strip():
        return None
    key = title.strip().lower()
    canonical = heading_map.get(key)
    if canonical:
        return canonical
    for hk, cid in heading_map.items():
        if hk in key or key in hk:
            return cid
    tl = title.lower()
    if "return" in tl or "ranking" in tl or "calculator" in tl:
        return "performance"
    return None


def _merge_h2_buckets(buckets: dict[str, list[str]]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for k, parts in buckets.items():
        merged[k] = "\n\n".join(parts)
    return merged


def _collect_h2_sections_selectolax(html: str, heading_map: dict[str, str]) -> dict[str, str]:
    """Fast path: Lexbor via selectolax (architecture §2.1)."""
    tree = HTMLParser(html)
    buckets: dict[str, list[str]] = {}
    for h2 in tree.css("h2"):
        title = (h2.text(deep=True, strip=True) or "").strip()
        canonical = _canonical_for_h2_title(title, heading_map)
        if not canonical:
            continue
        buf: list[str] = []
        n = h2.next
        while n is not None:
            if n.tag in ("h1", "h2"):
                break
            if n.tag:
                txt = (n.text(deep=True, strip=True) or "").strip()
                if txt:
                    buf.append(txt)
            n = n.next
        body = " ".join(buf).strip()
        if not body:
            continue
        buckets.setdefault(canonical, []).append(f"{title}\n{body}")
    return _merge_h2_buckets(buckets)


def _heading_section_body(
    el,
    *,
    break_tags: frozenset[str] | None = None,
) -> str:
    """Text after a section heading: direct siblings, then parent's following siblings (Groww)."""
    stop = break_tags if break_tags is not None else frozenset({"h1", "h2", "h3"})
    buf: list[str] = []
    for sib in el.find_next_siblings():
        if sib.name in stop:
            break
        t = sib.get_text(" ", strip=True)
        if t:
            buf.append(t)
    text = " ".join(buf).strip()
    if text:
        return text
    par = el.parent
    if par is not None:
        buf2: list[str] = []
        for sib in par.find_next_siblings():
            if sib.name in stop:
                break
            t2 = sib.get_text(" ", strip=True)
            if t2:
                buf2.append(t2)
        return " ".join(buf2).strip()
    return ""


def _collect_structural_sections_bs4(html: str, heading_map: dict[str, str]) -> dict[str, str]:
    """Collect ``h2`` and ``h3`` in **document order** (Groww uses ``h3`` for most body sections)."""
    soup = BeautifulSoup(html, "html.parser")
    buckets: dict[str, list[str]] = {}

    for el in soup.find_all(["h2", "h3"]):
        title = el.get_text(strip=True)
        if not title or title.lower().startswith("understand terms"):
            continue
        canonical = _canonical_for_h2_title(title, heading_map)
        if not canonical:
            continue

        text = _heading_section_body(el)
        if not text:
            continue
        buckets.setdefault(canonical, []).append(f"{title}\n{text}")

    return _merge_h2_buckets(buckets)


def _collect_h2_sections_bs4(html: str, heading_map: dict[str, str]) -> dict[str, str]:
    """Legacy: ``h2``-only pages (fixtures / older markup)."""
    soup = BeautifulSoup(html, "html.parser")
    buckets: dict[str, list[str]] = {}

    for h2 in soup.find_all("h2"):
        title = h2.get_text(strip=True)
        canonical = _canonical_for_h2_title(title, heading_map)
        if not canonical:
            continue

        text = _heading_section_body(h2, break_tags=frozenset({"h1", "h2"}))
        if not text:
            continue
        buckets.setdefault(canonical, []).append(f"{title}\n{text}")

    return _merge_h2_buckets(buckets)


def _collect_h2_sections(html: str, heading_map: dict[str, str]) -> dict[str, str]:
    """Prefer combined ``h2``+``h3`` extraction; fall back to ``h2``-only paths."""
    merged = _collect_structural_sections_bs4(html, heading_map)
    if merged:
        return merged
    tree = HTMLParser(html)
    if tree.css("h2"):
        return _collect_h2_sections_selectolax(html, heading_map)
    if "<h2" in html.lower():
        log.debug("selectolax found no h2 nodes; falling back to BeautifulSoup (h2-only)")
        return _collect_h2_sections_bs4(html, heading_map)
    return {}


def _scheme_card_text_after_h1(soup: BeautifulSoup) -> str:
    """Text between ``h1`` and first ``h2`` (Groww scheme facts card)."""
    h1 = soup.find("h1")
    if not h1:
        return ""
    parts: list[str] = []
    for sib in h1.find_next_siblings():
        if sib.name == "h2":
            break
        parts.append(sib.get_text("\n", strip=True))
    return "\n".join(p for p in parts if p).strip()


def _text_after_h1(soup: BeautifulSoup) -> str:
    return _scheme_card_text_after_h1(soup).replace("\n", " ")


def _extract_scheme_card_facts(card_text: str, *, html: str = "") -> str:
    """Structured facts from the Groww header card (NAV, expense ratio, min SIP)."""
    lines: list[str] = []
    sources = (card_text, html)
    for src in sources:
        if not src:
            continue
        if not any("Expense ratio" in ln for ln in lines):
            m = re.search(r"Expense\s+ratio.{0,240}?([\d.,]+\s*%)", src, re.I | re.DOTALL)
            if m:
                lines.append(f"Expense ratio (Direct): {m.group(1).strip()}")
        if not any("Latest NAV" in ln for ln in lines):
            m = re.search(
                r"NAV[:\s]*(\d{1,2}\s+\w+[\s']*\d{2,4})?.{0,80}?(?:₹|Rs\.?)\s*([\d,.]+)",
                src,
                re.I | re.DOTALL,
            )
            if m:
                date = (m.group(1) or "").strip()
                val = m.group(2).strip()
                if date:
                    lines.append(f"Latest NAV as of {date} is ₹{val}.")
                else:
                    lines.append(f"Latest NAV is ₹{val}.")
        if not any("Minimum SIP" in ln for ln in lines):
            m = re.search(
                r"Min\.?\s*for\s*SIP.{0,120}?(?:₹|Rs\.?)\s*([\d,.]+)",
                src,
                re.I | re.DOTALL,
            )
            if m:
                lines.append(f"Minimum SIP investment is ₹{m.group(1).strip()}.")
        if not any("Fund size" in ln for ln in lines):
            m = re.search(
                r"Fund\s+size\s*\(AUM\).{0,120}?(?:₹|Rs\.?)\s*([\d,.]+\s*(?:Cr|Lakh|Lac)?)",
                src,
                re.I | re.DOTALL,
            )
            if m:
                lines.append(f"Fund size (AUM): ₹{m.group(1).strip()}.")
    return "\n".join(lines)


def parse_groww_html(
    *,
    html: str,
    raw_bytes: bytes,
    source_id: str,
    url: str,
    scheme: str,
    category: str,
    sections_yaml: Path = SECTIONS_YAML,
) -> NormalizedDocument:
    """Parse HTML into ``NormalizedDocument`` (sections list)."""
    synonyms = load_section_synonyms(sections_yaml)
    heading_map = _build_heading_map(synonyms)

    soup = BeautifulSoup(html, "html.parser")
    header_parts: list[str] = []
    t = soup.find("title")
    if t and t.string:
        header_parts.append(t.string.strip())
    h1 = soup.find("h1")
    if h1:
        header_parts.append(h1.get_text(" ", strip=True))
    card_text = _scheme_card_text_after_h1(soup)
    card_facts = _extract_scheme_card_facts(card_text, html=html)
    if card_facts:
        header_parts.append(card_facts)
    elif card_text:
        header_parts.append(card_text.replace("\n", " "))
    traf = trafilatura.extract(html, include_tables=True, include_comments=False)
    if traf and len(traf) > 200:
        header_parts.append(traf[:4000])

    header_text = "\n".join(p for p in header_parts if p).strip()

    h2_blocks = _collect_h2_sections(html, heading_map)

    lock_text = ""
    m = _LOCK_IN_RE.search(html)
    if m:
        lock_text = m.group(0).strip()

    out_sections: list[SectionBlock] = []
    if header_text:
        out_sections.append(SectionBlock(section="header", text=header_text[:12000]))
    if lock_text:
        out_sections.append(
            SectionBlock(
                section="lock_in_banner",
                text=f"{lock_text}. ELSS investments are subject to a statutory 3-year lock-in.",
            )
        )

    order = (
        "fund_details",
        "exit_load_tax",
        "minimum_investments",
        "holdings",
        "about",
        "fund_managers",
        "performance",
    )
    for key in order:
        if key in h2_blocks and h2_blocks[key].strip():
            out_sections.append(SectionBlock(section=key, text=h2_blocks[key][:20000]))

    for k, v in h2_blocks.items():
        if k in order:
            continue
        if v.strip():
            out_sections.append(SectionBlock(section=k, text=v[:20000]))

    if len(out_sections) < MIN_SECTIONS_OK:
        raise StructuralBreakError(
            f"only {len(out_sections)} section(s) extracted (minimum {MIN_SECTIONS_OK}); "
            "possible Groww layout change (edge case 2.05)"
        )

    return NormalizedDocument(
        source_id=source_id,
        url=url,
        fetched_at=utc_now_iso(),
        content_hash=_sha256_bytes(raw_bytes),
        scheme=scheme,
        category=category,
        publisher="Groww",
        sections=out_sections,
    )


class StructuralBreakError(RuntimeError):
    """Raised when the page shape no longer matches heuristics (edge case 2.05)."""


def section_count(doc: NormalizedDocument) -> int:
    return len(doc.sections)
