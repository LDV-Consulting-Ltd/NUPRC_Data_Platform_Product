"""
PostgreSQL-first schema initialization: meta, bronze, silver, warehouse.
Handles legacy bronze tables by adding missing columns before indexes.
"""
from pathlib import Path
from sqlalchemy import text
from app.core.db import engine

_MIGRATION = Path(__file__).resolve().parents[2] / "etl" / "migrations" / "007_postgres_first.sql"

_BRONZE_TABLES = [
    "bronze.oil_production_status_raw",
    "bronze.gas_production_status_raw",
    "bronze.rig_disposition_raw",
    "bronze.concession_situation_raw",
]

_BRONZE_COLUMNS = [
    ("run_id", "TEXT"),
    ("source_name", "TEXT"),
    ("file_url", "TEXT"),
    ("file_hash", "TEXT"),
    ("report_period", "TEXT"),
    ("extracted_at", "TIMESTAMPTZ DEFAULT now()"),
    ("row_payload", "JSONB DEFAULT '{}'::jsonb"),
    ("canonical_payload", "JSONB"),
    ("schema_version", "TEXT"),
    ("drift_flag", "BOOLEAN DEFAULT FALSE"),
]


def init_pg_schemas() -> None:
    if not _MIGRATION.exists():
        raise FileNotFoundError(f"Missing migration: {_MIGRATION}")
    ddl = _MIGRATION.read_text(encoding="utf-8")
    statements = _split_sql(ddl)
    index_stmts = []
    other_stmts = []
    for stmt in statements:
        if stmt.upper().startswith("CREATE INDEX"):
            index_stmts.append(stmt)
        else:
            other_stmts.append(stmt)

    with engine.begin() as cxn:
        for stmt in other_stmts:
            cxn.execute(text(stmt))
        _upgrade_legacy_bronze(cxn)
        for stmt in index_stmts:
            try:
                cxn.execute(text(stmt))
            except Exception:
                pass  # index may already exist or column still missing


def _upgrade_legacy_bronze(cxn) -> None:
    """Add Postgres-first columns to bronze tables created under older schemas."""
    for table in _BRONZE_TABLES:
        for col, col_type in _BRONZE_COLUMNS:
            try:
                cxn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            except Exception:
                pass
        # Backfill source_name from legacy source_id when present
        try:
            cxn.execute(text(f"""
                UPDATE {table}
                SET source_name = COALESCE(source_name, source_id)
                WHERE source_name IS NULL AND source_id IS NOT NULL
            """))
        except Exception:
            pass
        # Map legacy raw_data into row_payload when empty
        try:
            cxn.execute(text(f"""
                UPDATE {table}
                SET row_payload = COALESCE(row_payload, raw_data, '{{}}'::jsonb)
                WHERE row_payload IS NULL
            """))
        except Exception:
            pass


def _split_sql(ddl: str) -> list:
    statements = []
    current = []
    for line in ddl.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if ";" in line:
            stmt = "\n".join(current).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1].strip()
            if stmt:
                statements.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip().rstrip(";")
        if stmt:
            statements.append(stmt)
    return statements
