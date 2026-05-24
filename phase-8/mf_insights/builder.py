"""Parse phase-3 chunks into dashboard insights JSON."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from mf_insights.paths import (
    CATEGORY_DEFINITIONS,
    CHUNKS_JSONL,
    DASHBOARD_SOURCE_IDS,
    INSIGHTS_JSON,
    PORTFOLIO_WEIGHTS_YAML,
    SHORT_IDS,
    SHORT_NAMES,
    SOURCES_YAML,
)

DISCLAIMER = (
    "Facts-only dashboard. No investment advice, recommendations, or predictions. "
    "Scheme metrics are parsed from the Groww corpus refreshed by the daily pipeline. "
    "Portfolio weights are illustrative; chart series derived from corpus NAV and historic returns."
)

_EXPENSE_RE = re.compile(r"Expense ratio \(Direct\):\s*([\d.]+)%", re.I)
_NAV_RE = re.compile(r"Latest NAV is\s*₹([\d,.]+)", re.I)
_AUM_RE = re.compile(r"Fund size \(AUM\):\s*₹([\d,.]+)\s*Cr", re.I)
_RISK_RE = re.compile(r"is rated ([A-Za-z ]+?) risk", re.I)
_BENCHMARK_RE = re.compile(r"Fund benchmark (.+?)(?:\s+Scheme Information|$)", re.I)
_MANAGER_RE = re.compile(
    r"investors on \d{1,2} \w+ \d{4}\.\s*([A-Za-z .]+?) is the Current Fund Manager",
    re.I,
)
_OBJECTIVE_RE = re.compile(r"Investment Objective (.+?)(?:\s+Fund benchmark|$)", re.I)
_EXIT_LOAD_RE = re.compile(r"Exit load(?: of|:)?\s*([^.\n]+?)(?:\.| Stamp|$)", re.I)
_LOCK_IN_RE = re.compile(r"(\d+)\s*years?\s*\(statutory\)|lock[- ]?in.*?(\d+)\s*years?", re.I)
_HOLDING_SECTOR_RE = re.compile(r"Equity\s*—\s*([\d.]+)%", re.I)
_RETURN_RE = {
    "1Y": re.compile(r"1 year[^+]*?([+-]?\s*[\d.]+)\s*%", re.I),
    "3Y": re.compile(r"3 years[^+]*?([+-]?\s*[\d.]+)\s*%", re.I),
    "5Y": re.compile(r"5 years[^+]*?([+-]?\s*[\d.]+)\s*%", re.I),
}


def _parse_num(raw: str) -> float:
    cleaned = raw.replace(",", "").replace(" ", "").replace("+", "").strip().rstrip(".")
    return float(cleaned)


def _load_sources() -> list[dict[str, Any]]:
    data = yaml.safe_load(SOURCES_YAML.read_text(encoding="utf-8"))
    return list(data.get("sources") or [])


def _load_chunks(chunks_path: Path | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    """source_id -> section -> chunk row."""
    path = chunks_path or CHUNKS_JSONL
    by_source: dict[str, dict[str, dict[str, Any]]] = {}
    if not path.is_file():
        return by_source
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            sid = str(row.get("source_id", ""))
            section = str(row.get("section", ""))
            by_source.setdefault(sid, {})[section] = row
    return by_source


def _text(chunks: dict[str, dict[str, Any]], section: str) -> str:
    row = chunks.get(section)
    return str(row.get("text", "")) if row else ""


def _parse_returns(*texts: str) -> dict[str, float]:
    out: dict[str, float] = {}
    combined = " ".join(texts)
    for key, pattern in _RETURN_RE.items():
        match = pattern.search(combined)
        if match:
            out[key] = round(_parse_num(match.group(1)), 2)
    return out


def _parse_sectors(holdings_text: str, *, category: str, source_id: str) -> dict[str, float]:
    if source_id == "hdfc_gold_fof":
        return {"Gold": 98.0, "Cash": 2.0}
    if source_id == "hdfc_silver_fof":
        return {"Silver": 97.0, "Cash": 3.0}

    totals: dict[str, float] = {}
    for segment in holdings_text.split(";"):
        match = _HOLDING_SECTOR_RE.search(segment)
        if not match:
            continue
        pct = float(match.group(1))
        prefix = segment[: match.start()].strip()
        if not prefix:
            continue
        sector = prefix.rsplit(" ", 1)[-1].strip()
        if sector.lower() in {"equity", "assets", "instruments"}:
            continue
        totals[sector] = totals.get(sector, 0.0) + pct

    if not totals and category == "Commodities":
        return {"Commodities": 100.0}
    if not totals:
        return {"Diversified": 100.0}

    total = sum(totals.values())
    if total <= 0:
        return totals
    return {k: round(v / total * 100, 1) for k, v in totals.items()}


def _parse_fund(source: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    source_id = str(source["id"])
    if source_id not in DASHBOARD_SOURCE_IDS:
        return None

    header = _text(chunks, "header")
    about = _text(chunks, "about")
    performance = _text(chunks, "performance")
    exit_load = _text(chunks, "exit_load_tax")
    holdings = _text(chunks, "holdings")
    lock_banner = _text(chunks, "lock_in_banner")

    if not header:
        return None

    nav_match = _NAV_RE.search(header) or _NAV_RE.search(about)
    expense_match = _EXPENSE_RE.search(header)
    aum_match = _AUM_RE.search(header)
    risk_match = _RISK_RE.search(about) or _RISK_RE.search(header)
    benchmark_match = _BENCHMARK_RE.search(about)
    manager_match = _MANAGER_RE.search(about)
    objective_match = _OBJECTIVE_RE.search(about)
    exit_match = _EXIT_LOAD_RE.search(exit_load) or _EXIT_LOAD_RE.search(about)

    lock_in: str | None = None
    if source.get("category") == "ELSS":
        lock_in = "3 years (statutory)"
    elif lock_banner:
        lock_match = _LOCK_IN_RE.search(lock_banner)
        if lock_match:
            lock_in = f"{lock_match.group(1) or lock_match.group(2)} years (statutory)"

    category = str(source.get("category", ""))
    last_updated = str(chunks.get("header", {}).get("last_updated", ""))

    returns = _parse_returns(header, performance)
    sectors = _parse_sectors(holdings, category=category, source_id=source_id)

    return {
        "id": SHORT_IDS.get(source_id, source_id),
        "sourceId": source_id,
        "name": str(source.get("scheme", "")),
        "shortName": SHORT_NAMES.get(source_id, str(source.get("scheme", ""))[:12]),
        "nav": round(_parse_num(nav_match.group(1)), 2) if nav_match else 0.0,
        "expenseRatio": round(float(expense_match.group(1)), 2) if expense_match else 0.0,
        "aumCr": round(_parse_num(aum_match.group(1)), 2) if aum_match else 0.0,
        "risk": risk_match.group(1).strip() if risk_match else "—",
        "category": category,
        "benchmark": benchmark_match.group(1).strip() if benchmark_match else "—",
        "manager": manager_match.group(1).strip() if manager_match else "—",
        "lockIn": lock_in,
        "exitLoad": exit_match.group(1).strip() if exit_match else "—",
        "objective": objective_match.group(1).strip() if objective_match else "—",
        "categoryDefinition": CATEGORY_DEFINITIONS.get(category, f"{category} mutual fund category."),
        "sectors": sectors,
        "returns": returns,
        "url": str(source.get("url", "")),
        "lastUpdated": last_updated,
    }


def _load_portfolio_weights() -> list[dict[str, Any]]:
    if not PORTFOLIO_WEIGHTS_YAML.is_file():
        return []
    data = yaml.safe_load(PORTFOLIO_WEIGHTS_YAML.read_text(encoding="utf-8")) or {}
    weights = data.get("weights") or {}
    asset_class = {
        "hdfc_gold_fof": "Gold",
        "hdfc_silver_fof": "Silver",
    }
    holdings: list[dict[str, Any]] = []
    for source_id, weight in weights.items():
        sid = str(source_id)
        holdings.append(
            {
                "fundId": SHORT_IDS.get(sid, sid),
                "sourceId": sid,
                "weightPct": float(weight),
                "assetClass": asset_class.get(sid, "Equity"),
            }
        )
    return holdings


def _market_facts(funds: list[dict[str, Any]]) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    if not funds:
        return facts

    latest = max((f.get("lastUpdated") or "" for f in funds), default="")
    facts.append(
        {
            "id": "corpus-sync",
            "time": f"{latest} · corpus refresh",
            "tag": "Sync",
            "title": "Dashboard metrics updated from Groww corpus",
            "body": "NAV, expense ratio, AUM, returns, and sector weights reflect the latest automated corpus refresh.",
        }
    )

    sorted_returns = sorted(
        [f for f in funds if f.get("returns", {}).get("1Y") is not None],
        key=lambda f: f["returns"]["1Y"],
        reverse=True,
    )
    if sorted_returns:
        top = sorted_returns[0]
        facts.append(
            {
                "id": "return-leader",
                "time": f"{latest} · historical",
                "tag": "Returns",
                "title": f"{top['shortName']} recorded highest 1Y return in indexed set",
                "body": f"Historic 1Y return: {top['returns']['1Y']}%. Past performance is not indicative of future results.",
            }
        )

    gold = next((f for f in funds if f["id"] == "gold"), None)
    if gold:
        facts.append(
            {
                "id": "gold-nav",
                "time": f"{gold.get('lastUpdated', latest)} · NAV",
                "tag": "Gold",
                "title": "HDFC Gold ETF FoF NAV updated",
                "body": f"Latest NAV: ₹{gold['nav']:.2f}. Gold FoF tracks domestic gold prices.",
            }
        )

    commodity = [f for f in funds if f["id"] in {"gold", "silver"}]
    if commodity:
        facts.append(
            {
                "id": "commodity",
                "time": f"{latest} · allocation",
                "tag": "Commodity",
                "title": "Commodity FoF schemes in indexed portfolio",
                "body": "Gold and silver FoF weights are illustrative; metal prices affect underlying ETF NAVs.",
            }
        )

    facts.append(
        {
            "id": "disclaimer",
            "time": f"{latest} · info",
            "tag": "Notice",
            "title": "Informational updates only",
            "body": "These items describe published facts and corpus metadata. They are not trading signals.",
        }
    )
    return facts


def build_insights_payload(*, chunks_path: Path | None = None) -> dict[str, Any]:
    chunk_index = _load_chunks(chunks_path)
    funds: list[dict[str, Any]] = []
    for source in _load_sources():
        sid = str(source["id"])
        fund = _parse_fund(source, chunk_index.get(sid, {}))
        if fund:
            funds.append(fund)

    funds.sort(key=lambda f: f["name"])
    last_updated = max((f.get("lastUpdated") or "" for f in funds), default="")

    return {
        "generatedAt": datetime.now(tz=UTC).isoformat(),
        "lastUpdated": last_updated,
        "disclaimer": DISCLAIMER,
        "funds": funds,
        "portfolioHoldings": _load_portfolio_weights(),
        "marketFacts": _market_facts(funds),
    }


def write_insights(path: Path = INSIGHTS_JSON, *, chunks_path: Path | None = None) -> dict[str, Any]:
    payload = build_insights_payload(chunks_path=chunks_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
