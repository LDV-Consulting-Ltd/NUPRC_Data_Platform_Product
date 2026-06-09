"""Read-only adapter for catalog registry and data_catalog tables."""
from typing import Any, Optional


def _warning(msg: str, warnings: list[str]) -> None:
    if msg not in warnings:
        warnings.append(msg)


def get_canonical_tables() -> tuple[dict[str, list[str]], list[str]]:
    warnings: list[str] = []
    try:
        from app.services.catalog_registry import CANONICAL_TABLES
        return dict(CANONICAL_TABLES), warnings
    except Exception as exc:
        _warning(f"CANONICAL_TABLES unavailable: {exc}", warnings)
        return {}, warnings


def get_table_display() -> tuple[dict[str, dict[str, str]], list[str]]:
    warnings: list[str] = []
    try:
        from app.services.catalog_registry import TABLE_DISPLAY
        return dict(TABLE_DISPLAY), warnings
    except Exception as exc:
        _warning(f"TABLE_DISPLAY unavailable: {exc}", warnings)
        return {}, warnings


def get_gold_tables() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
        engine = get_engine_for_layer("gold")
        tables = get_tables_for_layer(engine, "gold", include_deprecated=False)
        return tables, warnings
    except Exception as exc:
        _warning(f"Gold catalog tables unavailable: {exc}", warnings)
        return [], warnings


def get_layer_tables(layer: str) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
        engine = get_engine_for_layer(layer)
        tables = get_tables_for_layer(engine, layer, include_deprecated=False)
        return tables, warnings
    except Exception as exc:
        _warning(f"{layer} catalog tables unavailable: {exc}", warnings)
        return [], warnings


def test_database_connectivity() -> tuple[bool, Optional[str], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            cxn.execute(text("SELECT 1"))
        return True, None, warnings
    except Exception as exc:
        _warning(f"Database connectivity check failed: {exc}", warnings)
        return False, str(exc), warnings


def safe_count(schema: str, table: str) -> tuple[Optional[int], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.services.catalog_registry import get_engine_for_layer
        engine = get_engine_for_layer(schema if schema in ("bronze", "silver", "gold") else "gold")
        with engine.connect() as cxn:
            count = cxn.execute(
                text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
            ).scalar()
        return int(count or 0), warnings
    except Exception as exc:
        _warning(f"Count unavailable for {schema}.{table}: {exc}", warnings)
        return None, warnings


def fetch_entity_rows(
    schema: str,
    table: str,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], Optional[int], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.services.catalog_registry import get_engine_for_layer
        engine = get_engine_for_layer(schema if schema in ("bronze", "silver", "gold") else "gold")
        with engine.connect() as cxn:
            total = cxn.execute(
                text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
            ).scalar()
            rows = cxn.execute(
                text(f'SELECT * FROM "{schema}"."{table}" ORDER BY 1 LIMIT :limit OFFSET :offset'),
                {"limit": limit, "offset": offset},
            ).mappings().all()
        items = []
        for row in rows:
            item = {}
            for k, v in dict(row).items():
                if hasattr(v, "isoformat"):
                    item[k] = v.isoformat()
                else:
                    item[k] = v
            items.append(item)
        return items, int(total or 0), warnings
    except Exception as exc:
        _warning(f"Entity rows unavailable for {schema}.{table}: {exc}", warnings)
        return [], None, warnings


def get_catalog_summary() -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    result: dict[str, Any] = {
        "file_statistics": [],
        "source_statistics": [],
        "table_statistics": [],
    }
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            file_stats = cxn.execute(text("""
                SELECT download_status, COUNT(*) as count
                FROM data_catalog.downloaded_files
                GROUP BY download_status
            """)).mappings().all()
            source_stats = cxn.execute(text("""
                SELECT source_id, source_name, COUNT(*) as total_files
                FROM data_catalog.downloaded_files
                GROUP BY source_id, source_name
            """)).mappings().all()
            table_stats = cxn.execute(text("""
                SELECT table_type, COUNT(*) as table_count
                FROM data_catalog.available_tables
                GROUP BY table_type
            """)).mappings().all()
        result["file_statistics"] = [dict(r) for r in file_stats]
        result["source_statistics"] = [dict(r) for r in source_stats]
        result["table_statistics"] = [dict(r) for r in table_stats]
    except Exception as exc:
        _warning(f"Catalog summary unavailable: {exc}", warnings)
    return result, warnings


def get_schema_drift_count() -> tuple[Optional[int], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            exists = cxn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'silver' AND table_name = 'schema_drift'
                )
            """)).scalar()
            if not exists:
                return 0, warnings
            count = cxn.execute(text("SELECT COUNT(*) FROM silver.schema_drift")).scalar()
        return int(count or 0), warnings
    except Exception as exc:
        _warning(f"Schema drift count unavailable: {exc}", warnings)
        return None, warnings


def get_catalog_freshness_issues() -> tuple[list[dict[str, Any]], list[str]]:
    """Operational catalog freshness issues from data_catalog tables."""
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            failed_files = cxn.execute(text("""
                SELECT COUNT(*) FROM data_catalog.downloaded_files
                WHERE download_status = 'failed'
            """)).scalar() or 0
            if failed_files:
                issues.append({
                    "issue_key": "failed_downloads",
                    "severity": "warning",
                    "count": int(failed_files),
                    "description": f"{failed_files} downloaded file(s) with failed status.",
                })

            pending_bronze = cxn.execute(text("""
                SELECT COUNT(*) FROM data_catalog.downloaded_files
                WHERE download_status = 'downloaded' AND (bronze_loaded IS NOT TRUE)
            """)).scalar() or 0
            if pending_bronze:
                issues.append({
                    "issue_key": "pending_bronze_load",
                    "severity": "warning",
                    "count": int(pending_bronze),
                    "description": f"{pending_bronze} downloaded file(s) not yet loaded to bronze.",
                })

            table_count = cxn.execute(text("""
                SELECT COUNT(*) FROM data_catalog.available_tables
            """)).scalar() or 0
            if table_count == 0:
                issues.append({
                    "issue_key": "empty_available_tables",
                    "severity": "critical",
                    "count": 0,
                    "description": "data_catalog.available_tables is empty; catalog refresh may be incomplete.",
                })
    except Exception as exc:
        _warning(f"Catalog freshness issues unavailable: {exc}", warnings)
    return issues, warnings


def get_ingested_documents(limit: int, offset: int) -> tuple[list[dict[str, Any]], Optional[int], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            total = cxn.execute(text("SELECT COUNT(*) FROM data_catalog.downloaded_files")).scalar()
            rows = cxn.execute(text("""
                SELECT id, source_id, source_name, filename, file_sha256, download_status,
                       downloaded_at, bronze_loaded, silver_loaded, warehouse_loaded
                FROM data_catalog.downloaded_files
                ORDER BY downloaded_at DESC NULLS LAST
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset}).mappings().all()
        items = []
        for row in rows:
            item = {}
            for k, v in dict(row).items():
                item[k] = v.isoformat() if hasattr(v, "isoformat") else v
            items.append(item)
        return items, int(total or 0), warnings
    except Exception as exc:
        _warning(f"Ingested documents unavailable: {exc}", warnings)
        return [], None, warnings
