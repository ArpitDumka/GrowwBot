"""Per-case eval checks (§9.3)."""

from __future__ import annotations

import re
import time
from datetime import date
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from mf_eval.loaders import parse_verified_date
from mf_eval.models import CaseResult, CheckResult, QaCase

if TYPE_CHECKING:
    from mf_eval.loaders import ToleranceConfig

_BANNED_DEFAULT = (
    "recommend",
    "should you invest",
    "best fund",
    "guaranteed return",
    "you should buy",
    "i suggest",
)
_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)]+)\)")
_NUM_RE = re.compile(
    r"(?:₹|rs\.?)\s*[\d,.]+(?:\s*(?:cr|lakh|lac|crore))?|\d+(?:[.,]\d+)?\s*%",
    re.I,
)
_FOOTER_RE = re.compile(r"Last updated from sources:\s*(\d{4}-\d{2}-\d{2})", re.I)


def _answer_body(text: str) -> str:
    lines = [
        ln for ln in text.splitlines()
        if not ln.strip().startswith("[Source]") and not ln.strip().lower().startswith("source:")
    ]
    lines = [ln for ln in lines if not _FOOTER_RE.match(ln.strip())]
    return "\n".join(lines).strip()


def _sentences(body: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", body.strip())
    return [p for p in parts if p][:10]


def check_outcome(case: QaCase, outcome: str) -> CheckResult:
    if case.expected_type in ("oos_wrong_amc", "oos_non_mf"):
        ok = outcome in ("REFUSED", "NOT_FOUND")
        return CheckResult(
            "outcome",
            ok,
            f"expected REFUSED or NOT_FOUND, got {outcome}",
        )
    ok = outcome == case.expected_outcome
    return CheckResult(
        "outcome",
        ok,
        f"expected {case.expected_outcome}, got {outcome}",
    )


def check_must_contain(case: QaCase, answer: str) -> list[CheckResult]:
    out: list[CheckResult] = []
    lower = answer.lower()
    for token in case.must_contain:
        if case.match_type == "regex":
            ok = bool(re.search(token, answer, re.I))
        else:
            ok = token.lower() in lower
        out.append(CheckResult(f"contains:{token[:24]}", ok, f"missing {token!r}" if not ok else ""))
    return out


def check_must_not_contain(case: QaCase, answer: str) -> list[CheckResult]:
    out: list[CheckResult] = []
    lower = answer.lower()
    for token in case.must_not_contain:
        ok = token.lower() not in lower
        out.append(CheckResult(f"absent:{token[:24]}", ok, f"found forbidden {token!r}" if not ok else ""))
    return out


def check_banned_tokens(
    case: QaCase,
    answer: str,
    banned: tuple[str, ...] = _BANNED_DEFAULT,
) -> CheckResult:
    if case.expected_outcome == "REFUSED":
        return CheckResult("banned_tokens", True, "refusal template may quote denylist phrases", skipped=True)
    lower = answer.lower()
    hit = [t for t in banned if t in lower]
    return CheckResult("banned_tokens", not hit, f"found: {hit}" if hit else "")


def check_sentence_count(case: QaCase, answer: str) -> CheckResult:
    if case.expected_outcome != "ANSWERED":
        return CheckResult("sentence_count", True, "skipped", skipped=True)
    body = _answer_body(answer)
    n = len(_sentences(body))
    ok = n <= case.max_sentences
    return CheckResult("sentence_count", ok, f"{n} sentences (max {case.max_sentences})")


def check_field_expectations(
    case: QaCase, answer: str, tol: ToleranceConfig
) -> list[CheckResult]:
    out: list[CheckResult] = []
    if not case.expected_fields:
        return out
    body = _answer_body(answer)
    for exp in case.expected_fields:
        if exp.pattern:
            ok = bool(re.search(exp.pattern, answer, re.I))
            out.append(CheckResult(f"field:{exp.field}", ok, exp.pattern))
            continue
        if exp.value is not None:
            found: list[float] = []
            for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*%", body):
                try:
                    found.append(float(x.replace(",", "")))
                except ValueError:
                    continue
            tol_val = exp.tolerance
            if tol_val is None and exp.field in tol.fields:
                tol_val = float(tol.fields[exp.field].get("tolerance", 0.01))
            tol_val = tol_val or 0.01
            ok = any(abs(v - exp.value) <= tol_val for v in found)
            out.append(
                CheckResult(
                    f"field:{exp.field}",
                    ok,
                    f"expected ~{exp.value}{exp.unit or ''}, found {found}",
                )
            )
    return out


def check_citation_url(case: QaCase, answer: str, citation_url: str | None) -> CheckResult:
    if case.expected_outcome != "ANSWERED":
        return CheckResult("citation_present", True, "n/a", skipped=True)
    links = _LINK_RE.findall(answer)
    if case.expected_url:
        norm = case.expected_url.rstrip("/").lower()
        ok = any(norm in u.rstrip("/").lower() for _, u in links) or (
            citation_url and norm in citation_url.rstrip("/").lower()
        )
        return CheckResult("citation_url", ok, f"expected {case.expected_url}")
    ok = bool(links) or bool(citation_url)
    return CheckResult("citation_present", ok, "no citation link")


def check_link_resolves(
    case: QaCase,
    answer: str,
    citation_url: str | None,
    tol: ToleranceConfig,
) -> CheckResult:
    if case.expected_outcome != "ANSWERED":
        return CheckResult("link_resolves", True, "n/a", skipped=True)
    url = citation_url
    if not url:
        m = _LINK_RE.search(answer)
        url = m.group(2) if m else None
    if not url or "groww.in" not in url:
        return CheckResult("link_resolves", False, "no url to check")

    last_err = ""
    for attempt in range(tol.link_retries + 1):
        try:
            with httpx.Client(timeout=tol.link_timeout, follow_redirects=True) as client:
                r = client.head(url)
                if r.status_code in (200, 301, 302, 303, 307, 308):
                    return CheckResult("link_resolves", True, f"HTTP {r.status_code}")
                if r.status_code == 405:
                    r = client.get(url)
                    if r.status_code < 400:
                        return CheckResult("link_resolves", True, f"HTTP GET {r.status_code}")
                last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)[:120]
        if attempt < tol.link_retries:
            time.sleep(0.5)

    if tol.link_soft_fail:
        return CheckResult("link_resolves", True, f"skipped soft-fail: {last_err}", skipped=True)
    return CheckResult("link_resolves", False, last_err)


def check_staleness(case: QaCase, tol: ToleranceConfig) -> CheckResult:
    vd = parse_verified_date(case.last_verified)
    if not vd:
        return CheckResult("staleness", True, "no last_verified", skipped=True)
    age = (date.today() - vd).days
    ok = age <= tol.max_days_since_verified
    return CheckResult("staleness", ok, f"verified {age} days ago")


def check_pii_leak(case: QaCase, answer: str) -> CheckResult:
    if case.expected_type != "pii":
        return CheckResult("pii_leak", True, "n/a", skipped=True)
    pan = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", answer)
    return CheckResult("pii_leak", not pan, "PAN echoed in answer" if pan else "")


def check_chunk_id(case: QaCase, chunk_id: str | None) -> CheckResult:
    if not case.expected_chunk_id:
        return CheckResult("chunk_id", True, "n/a", skipped=True)
    ok = chunk_id == case.expected_chunk_id
    return CheckResult("chunk_id", ok, f"expected {case.expected_chunk_id}, got {chunk_id}")


def run_all_checks(
    case: QaCase,
    *,
    outcome: str,
    answer: str,
    citation_url: str | None,
    chunk_id: str | None,
    tol: ToleranceConfig,
    banned: tuple[str, ...],
) -> list[CheckResult]:
    checks: list[CheckResult] = [
        check_outcome(case, outcome),
        check_staleness(case, tol),
        check_pii_leak(case, answer),
        check_chunk_id(case, chunk_id),
        *check_must_contain(case, answer),
        *check_must_not_contain(case, answer),
        *check_field_expectations(case, answer, tol),
        check_banned_tokens(case, answer, banned),
        check_sentence_count(case, answer),
        check_citation_url(case, answer, citation_url),
        check_link_resolves(case, answer, citation_url, tol),
    ]
    core = [
        c
        for c in checks
        if c.name == "outcome"
        or (
            not c.skipped
            and c.name.startswith(("contains", "field", "citation", "banned", "sentence", "absent"))
            and c.name != "citation_present"
        )
    ]
    if case.expected_type == "factual" and case.expected_outcome == "ANSWERED":
        core = [c for c in core if c.name in ("outcome",) or c.name.startswith("field:")]
        core.append(next((c for c in checks if c.name == "citation_url"), CheckResult("citation_url", True)))
    overall_ok = all(c.passed for c in core)
    checks.append(CheckResult("overall", overall_ok, ""))
    return checks
