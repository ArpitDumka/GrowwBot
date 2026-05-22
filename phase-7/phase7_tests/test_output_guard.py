from mf_compose.output_guard import GuardContext, apply_output_guard, extract_numbers

ALLOWED = frozenset({"https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"})


def test_guard_fixes_missing_citation_and_footer():
    raw = "Exit load is Nil."
    ctx = GuardContext(
        chunk_text="Exit load Nil Stamp duty 0.005%",
        citation_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        last_updated="2026-05-16",
        allowed_urls=ALLOWED,
    )
    out, violations = apply_output_guard(raw, ctx)
    assert "Source: https://groww.in/" in out
    assert "Last updated from sources: 2026-05-16" in out
    assert "missing_citation" in violations


def test_banned_token_replaced():
    raw = "I recommend this fund. [Source](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)"
    ctx = GuardContext(
        chunk_text="text",
        citation_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        last_updated="2026-05-16",
        allowed_urls=ALLOWED,
    )
    out, violations = apply_output_guard(raw, ctx)
    assert "recommend" in violations[0] or "banned" in violations[0]
    assert "can't recommend" in out.lower() or "amfiindia" in out


def test_llm_footer_date_replaced_with_chunk_metadata():
    raw = (
        "Exit load is Nil.\n"
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
        "Last updated from sources: 2026-05-19"
    )
    ctx = GuardContext(
        chunk_text="Exit load Nil",
        citation_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        last_updated="2026-05-21",
        allowed_urls=ALLOWED,
    )
    out, violations = apply_output_guard(raw, ctx)
    assert "Last updated from sources: 2026-05-21" in out
    assert "footer_date_corrected" in violations


def test_bare_rs_not_counted_as_number():
    assert "rs." not in extract_numbers("No charges in Rs.")
    assert extract_numbers("No charges in Rs.") == set()


def test_lock_in_answer_with_rs_phrase_not_not_found():
    raw = (
        "The lock-in period is 3 years. No charges in Rs.\n"
        "[Source](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)\n"
        "Last updated from sources: 2026-05-16"
    )
    ctx = GuardContext(
        chunk_text="3-year lock-in. ELSS funds have a mandatory lock-in.",
        citation_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        last_updated="2026-05-16",
        allowed_urls=ALLOWED,
    )
    out, violations = apply_output_guard(raw, ctx)
    assert not any("invented_numbers" in v for v in violations)
    assert "couldn't find" not in out.lower()


def test_invented_number_triggers_not_found():
    raw = (
        "The expense ratio is 99.99%.\n"
        "[Source](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)\n"
        "Last updated from sources: 2026-05-16"
    )
    ctx = GuardContext(
        chunk_text="Exit load Nil",
        citation_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        last_updated="2026-05-16",
        allowed_urls=ALLOWED,
    )
    out, violations = apply_output_guard(raw, ctx)
    assert "invented_numbers" in violations[0]
    assert "couldn't find" in out.lower()
