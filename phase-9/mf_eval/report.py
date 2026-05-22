"""Markdown report writer (§9.3)."""

from __future__ import annotations

from pathlib import Path

from mf_eval.models import EvalReport


def write_report_md(report: EvalReport, path: Path) -> None:
    lines = [
        "# Phase 9 — Eval Report",
        "",
        f"- **Mode:** {report.mode}",
        f"- **Total:** {report.total}",
        f"- **Passed:** {report.passed}",
        f"- **Failed:** {report.failed}",
        f"- **Targets met:** {'yes' if report.targets_met else 'no'}",
        "",
        "## Metrics (§9.2)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    m = report.metrics
    lines.extend(
        [
            f"| Factual accuracy | {m.get('factual_accuracy', 0):.1%} |",
            f"| Citation correctness | {m.get('citation_correctness', 0):.1%} |",
            f"| Refusal precision | {m.get('refusal_precision', 0):.1%} |",
            f"| Refusal recall | {m.get('refusal_recall', 0):.1%} |",
            f"| p95 latency | {m.get('p95_latency_seconds', 0):.2f}s |",
            "",
            "## Per-question results",
            "",
        ]
    )

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"### {status} — `{r.case.id}`")
        lines.append("")
        lines.append(f"- **Q:** {r.case.question}")
        lines.append(f"- **Type:** {r.case.expected_type} | **Outcome:** {r.outcome} (expected {r.case.expected_outcome})")
        lines.append(f"- **Latency:** {r.latency_ms} ms")
        failed = [c for c in r.checks if not c.passed and not c.skipped]
        if failed:
            lines.append("- **Failed checks:**")
            for c in failed:
                lines.append(f"  - `{c.name}`: {c.detail}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
