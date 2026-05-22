"""Minimal in-process Prometheus-style metrics for Phase 10 observability."""

from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: Counter[tuple[str, str, str]] = Counter()
        self._guard_violations: Counter[str] = Counter()
        self._llm_unavailable = 0

    def observe_chat(self, payload: dict[str, Any]) -> None:
        outcome = str(payload.get("outcome") or "unknown").lower()
        used_llm = "true" if payload.get("used_llm") else "false"
        source = str((payload.get("log_safe") or {}).get("source") or "unknown")
        violations = payload.get("guard_violations") or []

        with self._lock:
            self._requests[(outcome, used_llm, source)] += 1
            for violation in violations:
                self._guard_violations[str(violation)] += 1
            if outcome == "error" and used_llm == "false":
                self._llm_unavailable += 1

    def render_prometheus(self) -> str:
        lines = [
            "# HELP requests_total Chat requests by outcome, LLM usage, and source.",
            "# TYPE requests_total counter",
        ]
        with self._lock:
            for (outcome, used_llm, source), count in sorted(self._requests.items()):
                lines.append(
                    'requests_total{'
                    f'outcome="{_esc(outcome)}",used_llm="{used_llm}",source="{_esc(source)}"'
                    f"}} {count}"
                )

            lines.extend(
                [
                    "# HELP guard_violation_total Output guard violations by rule.",
                    "# TYPE guard_violation_total counter",
                ]
            )
            for rule, count in sorted(self._guard_violations.items()):
                lines.append(f'guard_violation_total{{rule="{_esc(rule)}"}} {count}')

            lines.extend(
                [
                    "# HELP llm_unavailable_total LLM fallback/error responses.",
                    "# TYPE llm_unavailable_total counter",
                    f"llm_unavailable_total {self._llm_unavailable}",
                ]
            )
        return "\n".join(lines) + "\n"


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')

