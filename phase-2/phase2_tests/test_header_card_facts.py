from mf_ingest.parser_html import _extract_scheme_card_facts

CARD = """Equity Mid Cap Very High Risk
NAV: 15 May '26
₹218.42
Min. for SIP
₹100
Fund size (AUM)
₹94,744.72 Cr
Expense ratio
0.75%"""

HTML_SNIPPET = '<span>Expense ratio</span><span class="bodyLargeHeavy">0.75%</span>'


def test_extract_expense_ratio_and_nav():
    facts = _extract_scheme_card_facts(CARD)
    assert "0.75%" in facts
    assert "218.42" in facts
    assert "100" in facts


def test_extract_from_html_when_card_sparse():
    facts = _extract_scheme_card_facts("", html=HTML_SNIPPET)
    assert "0.75%" in facts
