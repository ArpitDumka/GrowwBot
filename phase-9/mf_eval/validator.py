"""Validate QA set coverage vs sources.yaml (edge 9.13)."""

from __future__ import annotations

from collections import defaultdict

from mf_eval.loaders import load_qa_set, load_source_ids


def validate_coverage(*, min_factual_per_scheme: int = 3, min_advisory_per_scheme: int = 1) -> list[str]:
    errors: list[str] = []
    cases = load_qa_set()
    source_ids = load_source_ids()

    if len(cases) < 90:
        errors.append(f"expected at least 90 cases, got {len(cases)}")

    by_scheme_factual: dict[str, int] = defaultdict(int)
    by_scheme_advisory: dict[str, int] = defaultdict(int)

    type_counts: dict[str, int] = defaultdict(int)
    for c in cases:
        type_counts[c.expected_type] += 1
        sid = next((t.split(":")[1] for t in c.tags if t.startswith("scheme:")), None)
        if not sid:
            continue
        if c.expected_type == "factual":
            by_scheme_factual[sid] += 1
        if c.expected_type == "advisory":
            by_scheme_advisory[sid] += 1

    expected_counts = {
        "factual": 40,
        "advisory": 20,
        "performance": 10,
        "pii": 10,
        "oos_wrong_amc": 5,
        "oos_non_mf": 5,
    }
    for t, n in expected_counts.items():
        if type_counts[t] < n:
            errors.append(f"expected_type {t}: need >={n}, got {type_counts[t]}")

    for sid in source_ids:
        if by_scheme_factual[sid] < min_factual_per_scheme:
            errors.append(f"scheme {sid}: need >={min_factual_per_scheme} factual, got {by_scheme_factual[sid]}")
        if by_scheme_advisory[sid] < min_advisory_per_scheme:
            errors.append(f"scheme {sid}: need >={min_advisory_per_scheme} advisory, got {by_scheme_advisory[sid]}")

    ids = {c.id for c in cases}
    if len(ids) != len(cases):
        errors.append("duplicate case ids in qa_set.yaml")

    return errors
