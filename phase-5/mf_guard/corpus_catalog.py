"""List the 10-scheme corpus and answer all-funds field snapshots from chunks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from mf_guard.config_loader import load_field_synonyms
from mf_guard.paths import REPO_ROOT
from mf_guard.phase1_bridge import load_source_registry
from mf_guard.scheme_field import extract_field, find_schemes_in_query, load_alias_registry

_CHUNKS = REPO_ROOT / "phase-3" / "data" / "chunks.jsonl"

_SCHEME_FROM_ASSISTANT = re.compile(
    r"I have factual data for (.+?) from its Groww",
    re.I,
)
_EXPENSE_RE = re.compile(r"Expense ratio \(Direct\):\s*([\d.]+%)", re.I)
_NAV_RE = re.compile(r"Latest NAV is\s*₹?([\d,.]+)", re.I)
_MIN_SIP_RE = re.compile(r"Minimum SIP investment is\s*₹?([\d,.]+)", re.I)

_LIST_PATTERNS = (
    re.compile(r"\b(?:list|name|show|tell)\b.*\b(?:those|the|all|10|ten)\b", re.I),
    re.compile(r"\b(?:which|what)\b.*\b(?:10|ten)\b.*\bfunds?\b", re.I),
    re.compile(r"\bwhat funds?\b.*\b(?:cover|have|know|support)\b", re.I),
    re.compile(r"\b(?:those|the)\s+10\b", re.I),
    re.compile(r"\ball\s+(?:funds|schemes)\s+you\s+cover\b", re.I),
)
_ALL_FUNDS_FIELD = re.compile(
    r"\b(?:all|every|each)\s+(?:funds?|schemes?)\b",
    re.I,
)


@dataclass(frozen=True)
class CatalogReply:
    text: str
    suggested_replies: tuple[str, ...] = ()


def corpus_scheme_names() -> tuple[str, ...]:
    reg = load_source_registry()
    return tuple(s.scheme for s in reg.sources)


def is_list_corpus_query(query: str) -> bool:
    q = query.strip()
    if not q or len(q) > 120:
        return False
    if any(p.search(q) for p in _LIST_PATTERNS):
        return True
    ql = q.casefold()
    return ql in {
        "list funds",
        "list all funds",
        "which funds",
        "which 10 funds",
        "what are the 10 funds",
        "what funds do you cover",
    }


def is_all_funds_field_query(query: str) -> bool:
    q = query.strip()
    if not _ALL_FUNDS_FIELD.search(q):
        return False
    field_id, perf, _unsupported = extract_field(q)
    return field_id is not None and not perf


def scheme_from_prior_turn(
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
) -> str | None:
    if prior_assistant_answer:
        m = _SCHEME_FROM_ASSISTANT.search(prior_assistant_answer)
        if m:
            return m.group(1).strip()
    combined = f"{prior_user_query or ''} {prior_assistant_answer or ''}"
    registry = load_alias_registry()
    matches = find_schemes_in_query(combined, registry)
    if len(matches) == 1:
        return matches[0].canonical
    if prior_user_query:
        user_matches = find_schemes_in_query(prior_user_query, registry)
        if len(user_matches) == 1:
            return user_matches[0].canonical
    return None


def is_field_only_follow_up(query: str) -> bool:
    """Field asked without naming a scheme (e.g. 'expense ratio' after a scheme turn)."""
    q = query.strip()
    if not q or len(q) > 80:
        return False
    if "hdfc" in q.casefold():
        return False
    field_id, perf, unsupported = extract_field(q)
    if unsupported or perf or not field_id:
        return False
    registry = load_alias_registry()
    return len(find_schemes_in_query(q, registry)) == 0


def build_field_question(
    query: str,
    scheme: str,
    field_id: str,
) -> str:
    field_syns, _, _ = load_field_synonyms()
    label = (field_syns.get(field_id) or [field_id.replace("_", " ")])[0]
    return f"What is the {label} of {scheme}?"


def try_build_field_question(
    query: str,
    *,
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
) -> str | None:
    if not is_field_only_follow_up(query):
        return None
    scheme = scheme_from_prior_turn(prior_user_query, prior_assistant_answer)
    if not scheme:
        return None
    field_id, _, _ = extract_field(query)
    if not field_id:
        return None
    return build_field_question(query, scheme, field_id)


@lru_cache(maxsize=1)
def _header_chunks_by_scheme() -> dict[str, tuple[str, str]]:
    """scheme name -> (chunk_text, last_updated)."""
    out: dict[str, tuple[str, str]] = {}
    if not _CHUNKS.is_file():
        return out
    with _CHUNKS.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if not str(row.get("chunk_id", "")).endswith("#header"):
                continue
            scheme = row.get("scheme")
            if scheme:
                out[str(scheme)] = (str(row.get("text", "")), str(row.get("last_updated", "")))
    return out


def _extract_field_value(text: str, field_id: str) -> str | None:
    if field_id == "expense_ratio":
        m = _EXPENSE_RE.search(text)
        return m.group(1) if m else None
    if field_id == "nav":
        m = _NAV_RE.search(text)
        return f"₹{m.group(1)}" if m else None
    if field_id == "min_sip":
        m = _MIN_SIP_RE.search(text)
        return f"₹{m.group(1)}" if m else None
    return None


def try_corpus_catalog_reply(
    query: str,
    *,
    prior_user_query: str | None = None,
    prior_assistant_answer: str | None = None,
) -> CatalogReply | None:
    q = query.strip()

    if is_list_corpus_query(q) or (
        prior_assistant_answer
        and "10 I cover" in prior_assistant_answer
        and re.search(r"\b(?:list|those|the)\s+(?:10|ten|funds?)\b", q, re.I)
    ):
        names = corpus_scheme_names()
        lines = "\n".join(f"{i}. {name}" for i, name in enumerate(names, 1))
        return CatalogReply(
            "I cover these 10 HDFC mutual funds on Groww:\n"
            f"{lines}\n\n"
            "Ask a specific fact about any one — for example: "
            "\"What is the expense ratio of HDFC Liquid Fund?\" or "
            "\"What is the minimum SIP for HDFC ELSS Tax Saver Fund?\"",
            suggested_replies=(
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "Expense ratio for all funds",
            ),
        )

    if is_all_funds_field_query(q):
        field_id, _, _ = extract_field(q)
        if not field_id:
            return None
        field_syns, _, _ = load_field_synonyms()
        label = (field_syns.get(field_id) or [field_id])[0].title()
        headers = _header_chunks_by_scheme()
        rows: list[str] = []
        last_dates: list[str] = []
        for name in corpus_scheme_names():
            text, updated = headers.get(name, ("", ""))
            val = _extract_field_value(text, field_id) if text else None
            if val:
                rows.append(f"• {name}: {val}")
                if updated:
                    last_dates.append(updated)
        if not rows:
            return None
        footer_date = max(last_dates) if last_dates else ""
        body = f"{label} (Direct plan) for all 10 HDFC schemes I cover:\n" + "\n".join(rows)
        if footer_date:
            body += f"\n\nLast updated from sources: {footer_date}"
        body += (
            "\n\nSource: Groww scheme pages (one page per fund). "
            "For exit load, lock-in, or benchmark, ask about a specific fund."
        )
        return CatalogReply(
            body,
            suggested_replies=("What is the exit load on HDFC ELSS Tax Saver Fund?",),
        )

    built = try_build_field_question(
        q,
        prior_user_query=prior_user_query,
        prior_assistant_answer=prior_assistant_answer,
    )
    if built:
        return None  # caller should run normal RAG with built query

    return None
