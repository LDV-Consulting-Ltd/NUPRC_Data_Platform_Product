"""
Tests: catalog registry returns only canonical tables; duplicate (etl_ vs legacy) suppression.
"""
import pytest

from app.services.catalog_registry import (
    CANONICAL_TABLES,
    get_tables_for_layer,
    DEPRECATED_TABLE_PATTERNS,
    _is_deprecated,
)


def test_bronze_canonical_list():
    """Bronze layer canonical list includes etl_* tables only."""
    assert "etl_oil_production_raw" in CANONICAL_TABLES["bronze"]
    assert "etl_gas_production_raw" in CANONICAL_TABLES["bronze"]
    assert "etl_rig_disposition_raw" in CANONICAL_TABLES["bronze"]
    assert "etl_concessions_raw" in CANONICAL_TABLES["bronze"]
    assert "etl_concessions_sections" in CANONICAL_TABLES["bronze"]
    assert "oil_production_status_raw" not in CANONICAL_TABLES["bronze"]
    assert "oil_production_raw" not in CANONICAL_TABLES["bronze"]


def test_deprecated_patterns_match_legacy():
    """Deprecated patterns match legacy table names."""
    assert _is_deprecated("oil_production_status_raw") is True
    assert _is_deprecated("oil_production_raw") is True
    assert _is_deprecated("gas_production_status_raw") is True
    assert _is_deprecated("rig_disposition_raw") is True
    assert _is_deprecated("concession_situation_raw") is True
    assert _is_deprecated("etl_oil_production_raw") is False


@pytest.fixture
def db_available():
    try:
        from app.core.db import engine
        from sqlalchemy import text
        with engine.connect() as cxn:
            cxn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def test_get_tables_for_layer_returns_only_canonical_names(db_available):
    """With include_deprecated=False, returned physical_name must be in CANONICAL_TABLES for that layer."""
    if not db_available:
        pytest.skip("Database not available")
    from app.core.db import engine
    for layer in ("bronze", "silver", "gold"):
        canonical = set(CANONICAL_TABLES.get(layer, []))
        tables = get_tables_for_layer(engine, layer, include_deprecated=False)
        for t in tables:
            assert t["physical_name"] in canonical, (
                f"layer={layer} should not return non-canonical table {t['physical_name']}"
            )


def test_get_tables_for_layer_bronze_no_legacy_duplicates(db_available):
    """GET /catalog/tables?layer=bronze (include_deprecated=False) must not return legacy 0-row duplicates."""
    if not db_available:
        pytest.skip("Database not available")
    from app.core.db import engine
    tables = get_tables_for_layer(engine, "bronze", include_deprecated=False)
    physical_names = {t["physical_name"] for t in tables}
    # Must not include legacy names that are deprecated (even if they exist in DB with 0 rows)
    legacy = {"oil_production_status_raw", "oil_production_raw", "gas_production_status_raw", "rig_disposition_raw", "concession_situation_raw"}
    for name in legacy:
        assert name not in physical_names, f"Legacy table {name} must not appear when include_deprecated=False"
    # Should only contain canonical bronze tables that exist
    for name in physical_names:
        assert name in CANONICAL_TABLES["bronze"], f"Bronze table list must only contain canonical names, got {name}"
