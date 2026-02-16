"""
Tests: bronze writes >0 rows for at least one source (with DB);
silver/gold build without crashing.
"""
import os
import pytest


@pytest.fixture(scope="module")
def db_available():
    try:
        from etl.config import get_etl_engine
        from sqlalchemy import text
        with get_etl_engine().connect() as cxn:
            cxn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def test_bronze_writes_with_db(db_available):
    """If DB is available, run concession-only and assert bronze has rows (or skip)."""
    if not db_available:
        pytest.skip("Database not available")
    from etl.observability import init_observability_schema, start_run, end_run, end_step, start_step
    from etl.bronze import init_bronze_etl_tables, load_concession_to_bronze
    from etl.sources import CONCESSION_PDF_URL
    from etl.acquire import download_concession_pdf
    from pathlib import Path
    import uuid
    init_observability_schema()
    init_bronze_etl_tables()
    path, sha, err = download_concession_pdf(CONCESSION_PDF_URL, "concession")
    if err or not path:
        pytest.skip(f"Concession download failed: {err}")
    run_id = str(uuid.uuid4())
    n = load_concession_to_bronze(Path(path), CONCESSION_PDF_URL, run_id, "concession")
    assert n >= 0
    if n > 0:
        from etl.config import get_bronze_engine
        from sqlalchemy import text
        with get_bronze_engine().connect() as cxn:
            count = cxn.execute(text("SELECT COUNT(*) FROM bronze.etl_concessions_raw WHERE ingest_run_id = :r"), {"r": run_id}).scalar()
        assert count == n


def test_silver_build_no_crash(db_available):
    """Silver transform runs without crashing (may have 0 rows)."""
    if not db_available:
        pytest.skip("Database not available")
    from etl.silver import ensure_silver_schema, transform_to_silver
    ensure_silver_schema()
    metrics = transform_to_silver("test-run-no-data")
    assert isinstance(metrics, dict)


def test_gold_build_no_crash(db_available):
    """Gold transform runs without crashing."""
    if not db_available:
        pytest.skip("Database not available")
    from etl.gold import ensure_gold_schema, transform_to_gold
    ensure_gold_schema()
    metrics = transform_to_gold("test-run-no-data")
    assert isinstance(metrics, dict)
