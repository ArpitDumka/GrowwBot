from mf_eval.runner import run_eval


def test_eval_smoke_three_cases():
    report = run_eval(ci_mode=True, skip_link_check=True, test_reranker=True, limit=3)
    assert report.total == 3
    assert "factual_accuracy" in report.metrics
