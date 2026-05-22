from mf_api.bootstrap import load_bootstrap


def test_sample_questions_validated():
    boot = load_bootstrap()
    assert len(boot.sample_questions) >= 3
    assert boot.disclaimer.startswith("Facts-only")
    assert boot.welcome_message
    assert boot.input_placeholder


def test_bootstrap_endpoint(api_client):
    r = api_client.get("/api/v1/bootstrap")
    assert r.status_code == 200
    data = r.json()
    assert data["title_suffix"] == "Facts-only"
    assert len(data["sample_questions"]) >= 3
    assert data.get("welcome_message")
    assert data.get("input_placeholder")
    assert data["client_timeout_hint_seconds"] >= 30  # set in config/api.yaml
