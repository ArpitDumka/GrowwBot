"""Run evaluation harness over QA set."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from mf_eval.checks import run_all_checks
from mf_eval.loaders import load_qa_set, load_targets, load_tolerances
from mf_eval.models import CaseResult, EvalReport, QaCase
from mf_eval.paths import EVAL_DIR, REPORT_JSON, REPORT_MD
from mf_eval.report import write_report_md
from mf_eval.stub_llm import EvalStubLLM


def _load_banned() -> tuple[str, ...]:
    try:
        from mf_compose.output_guard import load_banned_tokens

        return load_banned_tokens()
    except Exception:
        return (
            "recommend",
            "should you invest",
            "best fund",
            "guaranteed return",
        )


_INDEX_CACHE: dict[tuple[bool, bool], Any] = {}


def _get_index(*, test_embedder: bool, test_reranker: bool):  # noqa: ARG001
    key = (test_embedder, test_reranker)
    if key not in _INDEX_CACHE:
        from mf_retrieve.pipeline import load_index

        _INDEX_CACHE[key] = load_index(test_embedder=test_embedder)
    return _INDEX_CACHE[key]


def _run_pipeline(
    question: str,
    *,
    test_reranker: bool,
    live_groq: bool,
    test_embedder: bool = False,
) -> dict[str, Any]:
    from mf_compose.composer import compose_from_ask
    from mf_compose.pipeline import ensure_paths, load_env
    from mf_retrieve.pipeline import ask

    load_env()
    ensure_paths()
    llm = None if live_groq else EvalStubLLM()
    idx = _get_index(test_embedder=test_embedder, test_reranker=test_reranker)
    ask_result = ask(
        question,
        index=idx,
        test_embedder=test_embedder,
        test_reranker=test_reranker,
    )
    composed = compose_from_ask(ask_result, llm=llm)
    c = composed
    return {
        "outcome": c.outcome.value,
        "answer": c.text,
        "citation_url": c.citation_url,
        "chunk_id": c.chunk_id,
        "trace_id": "",
    }


def _run_api(question: str, base_url: str, timeout: float) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/v1/chat"
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json={"query": question})
        r.raise_for_status()
        data = r.json()
    return {
        "outcome": data.get("outcome", "ERROR"),
        "answer": data.get("answer", ""),
        "citation_url": data.get("citation_url"),
        "chunk_id": data.get("chunk_id"),
        "trace_id": data.get("trace_id", r.headers.get("x-trace-id", "")),
    }


def _compute_metrics(results: list[CaseResult]) -> dict[str, Any]:
    by_type: dict[str, list[CaseResult]] = {}
    for r in results:
        by_type.setdefault(r.case.expected_type, []).append(r)

    factual = by_type.get("factual", [])
    refuse_types = ("advisory", "performance", "pii", "oos_wrong_amc", "oos_non_mf")
    refuse_cases = [r for t in refuse_types for r in by_type.get(t, [])]

    factual_pass = sum(1 for r in factual if r.passed)
    refuse_expected = sum(1 for r in refuse_cases if r.case.expected_outcome == "REFUSED")
    refuse_correct = sum(
        1 for r in refuse_cases if r.case.expected_outcome == "REFUSED" and r.outcome == "REFUSED"
    )
    refused_actual = [r for r in results if r.outcome == "REFUSED"]
    refuse_precision = (
        sum(1 for r in refused_actual if r.case.expected_outcome == "REFUSED") / len(refused_actual)
        if refused_actual
        else 1.0
    )

    latencies = sorted(r.latency_ms for r in results)
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    citation_cases = [r for r in factual if r.case.expected_outcome == "ANSWERED"]
    citation_ok = sum(
        1
        for r in citation_cases
        if any(c.name == "citation_url" and c.passed for c in r.checks)
    )

    return {
        "factual_accuracy": factual_pass / len(factual) if factual else 1.0,
        "citation_correctness": citation_ok / len(citation_cases) if citation_cases else 1.0,
        "refusal_precision": refuse_precision,
        "refusal_recall": refuse_correct / refuse_expected if refuse_expected else 1.0,
        "p95_latency_ms": p95,
        "p95_latency_seconds": p95 / 1000.0,
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
    }


def _targets_met(metrics: dict[str, Any], targets: dict[str, float]) -> bool:
    mapping = {
        "factual_accuracy": "factual_accuracy_min",
        "citation_correctness": "citation_correctness_min",
        "refusal_precision": "refusal_precision_min",
        "refusal_recall": "refusal_recall_min",
        "p95_latency_seconds": "p95_latency_seconds_max",
    }
    for metric, target_key in mapping.items():
        val = metrics.get(metric, 0)
        target = targets.get(target_key)
        if target is None:
            continue
        if target_key.endswith("_max"):
            if val > target:
                return False
        else:
            if val < target:
                return False
    return True


def run_eval(
    *,
    mode: str = "pipeline",
    api_url: str | None = None,
    test_reranker: bool = True,
    live_groq: bool = False,
    ci_mode: bool = False,
    skip_link_check: bool = False,
    limit: int | None = None,
) -> EvalReport:
    cases = load_qa_set()
    if limit:
        cases = cases[:limit]
    tol = load_tolerances()
    if skip_link_check:
        tol = type(tol)(
            fields=tol.fields,
            max_days_since_verified=tol.max_days_since_verified,
            link_timeout=tol.link_timeout,
            link_retries=tol.link_retries,
            link_soft_fail=True,
        )
    targets_cfg = load_targets(ci_mode=ci_mode)
    banned = _load_banned()

    results: list[CaseResult] = []
    for case in cases:
        t0 = time.perf_counter()
        try:
            if mode == "api":
                if not api_url:
                    raise ValueError("api_url required for api mode")
                payload = _run_api(case.question, api_url, timeout=30.0)
            else:
                payload = _run_pipeline(
                    case.question,
                    test_reranker=test_reranker,
                    live_groq=live_groq,
                    test_embedder=False,
                )
        except Exception as e:
            payload = {
                "outcome": "ERROR",
                "answer": str(e),
                "citation_url": None,
                "chunk_id": None,
                "trace_id": "",
            }
        elapsed = int((time.perf_counter() - t0) * 1000)

        checks = run_all_checks(
            case,
            outcome=payload["outcome"],
            answer=payload["answer"],
            citation_url=payload.get("citation_url"),
            chunk_id=payload.get("chunk_id"),
            tol=tol,
            banned=banned,
        )
        results.append(
            CaseResult(
                case=case,
                outcome=payload["outcome"],
                answer=payload["answer"],
                citation_url=payload.get("citation_url"),
                latency_ms=elapsed,
                checks=checks,
                trace_id=payload.get("trace_id", ""),
                chunk_id=payload.get("chunk_id"),
            )
        )

    metrics = _compute_metrics(results)
    met = _targets_met(metrics, targets_cfg.metrics)

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    report = EvalReport(
        mode=mode,
        total=len(results),
        passed=metrics["passed"],
        failed=metrics["failed"],
        skipped_link=sum(
            1 for r in results for c in r.checks if c.name == "link_resolves" and c.skipped
        ),
        results=results,
        metrics=metrics,
        targets_met=met,
    )
    write_report_md(report, REPORT_MD)
    REPORT_JSON.write_text(
        json.dumps(
            {
                "mode": mode,
                "metrics": metrics,
                "targets_met": met,
                "passed": report.passed,
                "failed": report.failed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report
