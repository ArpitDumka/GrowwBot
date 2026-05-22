"""HTML parser → normalized document."""

from __future__ import annotations

import pytest

from mf_ingest.parser_html import StructuralBreakError, parse_groww_html

FIXTURE_HTML = """
<html><head><title>HDFC Mid Cap Fund Direct Growth - Groww</title></head>
<body>
<h1>HDFC Mid Cap Fund Direct Growth</h1>
<p>Equity Mid Cap Very High Risk</p>
<h2>Exit load, stamp duty and tax</h2>
<div><p>Exit load of 1% if redeemed within 1 year.</p>
<p>Stamp duty on investment: 0.005%</p></div>
<h2>Fund benchmark</h2>
<p>NIFTY Midcap 150 TRI</p>
<h2>Minimum investments</h2>
<p>Min. for SIP ₹100</p>
</body></html>
"""


def test_parse_groww_extracts_sections() -> None:
    raw = FIXTURE_HTML.encode("utf-8")
    doc = parse_groww_html(
        html=FIXTURE_HTML,
        raw_bytes=raw,
        source_id="hdfc_midcap",
        url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        scheme="HDFC Mid Cap Fund",
        category="Mid Cap",
    )
    assert doc.source_id == "hdfc_midcap"
    assert doc.publisher == "Groww"
    names = {s.section for s in doc.sections}
    assert "header" in names
    assert "exit_load_tax" in names
    assert "fund_details" in names
    assert "minimum_investments" in names


def test_parse_raises_structural_break_on_empty() -> None:
    raw = b"<html><body></body></html>"
    with pytest.raises(StructuralBreakError):
        parse_groww_html(
            html=raw.decode(),
            raw_bytes=raw,
            source_id="x",
            url="https://groww.in/mutual-funds/x",
            scheme="X",
            category="Mid Cap",
        )
