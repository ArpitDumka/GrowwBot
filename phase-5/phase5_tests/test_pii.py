from mf_guard.models import Intent, Outcome
from mf_guard.pipeline import process_query
from mf_guard.pii import detect_pii, scrub_for_log


def test_pan_obfuscated_spaces():
    r = detect_pii("My PAN is A B C D E 1 2 3 4 F")
    assert r.detected
    assert "pan" in r.types


def test_pan_dots():
    r = detect_pii("ABCDE.1234.F")
    assert r.detected


def test_aadhaar_spaced():
    r = detect_pii("id 1234 5678 9012 please")
    assert r.detected


def test_pii_precedence_over_advisory():
    r = process_query("My PAN is ABCDE1234F, should I invest in HDFC ELSS?")
    assert r.outcome == Outcome.REFUSE
    assert r.intent == Intent.PII


def test_scrub_for_log_no_pan():
    s = scrub_for_log("contact ABCDE1234F today")
    assert "ABCDE1234F" not in s
    assert "[REDACTED_PAN]" in s


def test_refusal_never_contains_query():
    q = "ABCDE1234F"
    r = process_query(f"My PAN is {q}")
    assert q not in (r.message or "")
