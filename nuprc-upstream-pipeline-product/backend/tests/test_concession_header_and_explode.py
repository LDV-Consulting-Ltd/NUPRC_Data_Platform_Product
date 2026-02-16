"""
Tests: concession header detection (whitelist + blacklist), explode multi-value rows.
"""
import pytest


def test_header_detection_known_headers_true():
    """Known section headers are detected as headers."""
    from etl.concession import is_header_line

    assert is_header_line("PETROLEUM EXPLORATION LICENCE (PEL)") is True
    assert is_header_line("PETROLEUM PROSPECTING LICENCES (PPLs) WITH SUBSISTING TENURES") is True
    assert is_header_line("PETROLEUM MINING LEASES (PMLs) WITH SUBSISTING TENURES") is True
    assert is_header_line("  PETROLEUM   EXPLORATION   LICENCE   (PEL)  ") is True
    assert is_header_line("PETROLEUM EXPLORATION LICENCE") is True


def test_header_detection_company_line_false():
    """Company/data lines are not detected as headers (blacklist)."""
    from etl.concession import is_header_line

    assert is_header_line("WATLNE SYSTEMS LTD 23.29 (Onshore)") is False
    assert is_header_line("SOME COMPANY LIMITED") is False
    assert is_header_line("NIGERIA PLC") is False
    assert is_header_line("PEL 123") is False
    assert is_header_line("OML 42") is False
    assert is_header_line("Block 10% SQ.KM") is False


def test_explode_row_two_companies_two_rows():
    """A row with two newline-separated companies produces 2 output rows with row_split_count=2."""
    from etl.concession import explode_row

    row = {
        "name_of_company": "Company A\nCompany B",
        "block_excised_from": "Block 1",
        "equity_distribution": "50%",
    }
    multi_cols = ["name_of_company", "block_excised_from", "equity_distribution"]
    out = explode_row(row, multi_cols)
    assert len(out) == 2
    assert out[0]["row_split_count"] == 2
    assert out[1]["row_split_count"] == 2
    assert out[0]["row_split_index"] == 0
    assert out[1]["row_split_index"] == 1
    assert out[0]["name_of_company"] == "Company A"
    assert out[1]["name_of_company"] == "Company B"
    # Single-value columns repeated
    assert out[0]["block_excised_from"] == "Block 1"
    assert out[1]["block_excised_from"] == "Block 1"


def test_explode_row_single_value_unchanged():
    """Row with no newlines returns one row with row_split_count=1."""
    from etl.concession import explode_row

    row = {"name_of_company": "Only One Co", "block": "B1"}
    out = explode_row(row, ["name_of_company", "block"])
    assert len(out) == 1
    assert out[0]["row_split_count"] == 1
    assert out[0]["row_split_index"] == 0
    assert out[0]["name_of_company"] == "Only One Co"


def test_concession_parser_returns_category_full():
    """Concession parser returns rows with concession_category_full (and payload has row_split_*)."""
    from etl.concession import extract_concession_pdf, UNKNOWN_CATEGORY
    import os

    try:
        import pdfplumber
    except ImportError:
        pytest.skip("pdfplumber not installed")
    base = os.path.dirname(os.path.dirname(__file__))
    for candidate in [
        os.path.join(base, "..", "sample data", "NUPRC-Concession-Situation-Final-Merged-@-1st-January-2026.pdf"),
        os.path.join(base, "sample data", "NUPRC-Concession-Situation-Final-Merged-@-1st-January-2026.pdf"),
    ]:
        if os.path.isfile(candidate):
            raw_rows, section_events = extract_concession_pdf(candidate)
            assert isinstance(raw_rows, list)
            assert isinstance(section_events, list)
            for r in raw_rows:
                assert "concession_category_full" in r
                assert "payload" in r
                assert "row_split_index" in r["payload"]
                assert "row_split_count" in r["payload"]
            for s in section_events:
                assert "concession_category" in s
            return
    pytest.skip("No sample concession PDF found in repo")
