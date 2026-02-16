"""
Tests: Excel link extraction (oil/gas/rig), concession PDF download, concession parser category.
"""
import pytest


def test_excel_links_oil():
    """Excel link extraction returns a list (may be empty if page structure changes)."""
    from etl.scrape import get_excel_links_oil
    links, err = get_excel_links_oil()
    assert err is None, f"Scrape failed: {err}"
    assert isinstance(links, list)
    # If page has Excel links, we get non-empty; otherwise empty (no PDFs)
    for L in links:
        assert "url" in L and "filename" in L
        assert L["url"].lower().endswith((".xlsx", ".xls"))


def test_excel_links_gas():
    from etl.scrape import get_excel_links_gas
    links, err = get_excel_links_gas()
    assert err is None
    assert isinstance(links, list)
    for L in links:
        assert L["url"].lower().endswith((".xlsx", ".xls"))


def test_excel_links_rig():
    from etl.scrape import get_excel_links_rig
    links, err = get_excel_links_rig()
    assert err is None
    assert isinstance(links, list)
    for L in links:
        assert L["url"].lower().endswith((".xlsx", ".xls"))


def test_concession_pdf_download():
    """Concession PDF URL is reachable (or skip if network fails)."""
    from etl.acquire import download_concession_pdf
    from etl.sources import CONCESSION_PDF_URL
    path, sha, err = download_concession_pdf(CONCESSION_PDF_URL, "concession")
    if err:
        pytest.skip(f"Concession PDF not reachable: {err}")
    assert path is not None and path.exists()
    assert sha is not None and len(sha) == 64


def test_concession_parser_assigns_category():
    """Concession parser returns rows and sections with concession_category."""
    from etl.concession import extract_concession_pdf
    import os
    try:
        import pdfplumber
    except ImportError:
        pytest.skip("pdfplumber not installed")
    # Sample PDF: repo root is parent of backend
    base = os.path.dirname(os.path.dirname(__file__))  # backend/
    for candidate in [
        os.path.join(base, "..", "sample data", "NUPRC-Concession-Situation-Final-Merged-@-1st-January-2026.pdf"),
        os.path.join(base, "sample data", "NUPRC-Concession-Situation-Final-Merged-@-1st-January-2026.pdf"),
    ]:
        if os.path.isfile(candidate):
            raw_rows, section_events = extract_concession_pdf(candidate)
            assert isinstance(raw_rows, list)
            assert isinstance(section_events, list)
            for r in raw_rows:
                assert "concession_category_full" in r or "concession_category" in r
                assert "payload" in r
            for s in section_events:
                assert "concession_category" in s
            return
    pytest.skip("No sample concession PDF found in repo")
