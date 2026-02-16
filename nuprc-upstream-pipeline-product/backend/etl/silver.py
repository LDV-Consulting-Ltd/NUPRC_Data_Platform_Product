"""
Silver: read from Bronze, transform (standardize/clean/dedupe), write to Silver DB/schema only.
Does NOT mirror Bronze: writes to silver.* tables in SILVER_DB_URL (or silver schema).
Mode-aware: only process bronze tables for the current run mode (oil|gas|rig|concession|full).
Reads ALL bronze rows (not just current run) so silver is populated; dedupes by row_hash.
"""
import hashlib
import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from etl.config import get_bronze_engine, get_silver_engine

logger = logging.getLogger(__name__)


def _redact_url(url: str) -> str:
    if not url:
        return ""
    try:
        return str(url).split("@")[-1].split("?")[0][:60] + "..." if "@" in str(url) else str(url)[:60]
    except Exception:
        return "***"

# Which bronze tables to process per mode (source_key / table)
MODE_TO_BRONZE_TABLES = {
    "full": [
        ("fact_oil_production", "etl_oil_production_raw"),
        ("fact_gas_production", "etl_gas_production_raw"),
        ("fact_rig_disposition", "etl_rig_disposition_raw"),
    ],
    "oil": [("fact_oil_production", "etl_oil_production_raw")],
    "gas": [("fact_gas_production", "etl_gas_production_raw")],
    "rig": [("fact_rig_disposition", "etl_rig_disposition_raw")],
    "concession": [],
}
CONCESSION_MODE = "concession"  # concession is separate (etl_concessions_raw)


def ensure_silver_schema(engine=None):
    engine = engine or get_silver_engine()
    with engine.begin() as cxn:
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        for stmt in [
            "CREATE TABLE IF NOT EXISTS silver.dim_date (date_key INT PRIMARY KEY, date_actual DATE NOT NULL, year INT, month INT, day INT)",
            "CREATE TABLE IF NOT EXISTS silver.dim_operator (operator_key SERIAL PRIMARY KEY, operator_name TEXT NOT NULL UNIQUE)",
            "CREATE TABLE IF NOT EXISTS silver.fact_oil_production (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, date_key INT, operator_key INT, payload JSONB, row_hash TEXT UNIQUE)",
            "CREATE TABLE IF NOT EXISTS silver.fact_gas_production (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, date_key INT, operator_key INT, payload JSONB, row_hash TEXT UNIQUE)",
            "CREATE TABLE IF NOT EXISTS silver.fact_rig_disposition (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, date_key INT, operator_key INT, payload JSONB, row_hash TEXT UNIQUE)",
            "CREATE TABLE IF NOT EXISTS silver.fact_concession_status (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, concession_category TEXT, payload JSONB, row_hash TEXT UNIQUE)",
        ]:
            cxn.execute(text(stmt))


def _date_key_from_payload(payload: Dict[str, Any], fallback: date) -> int:
    """Derive date_key (YYYYMMDD int) from payload; fallback to fallback date."""
    if not payload:
        d = fallback
    else:
        # Common Excel column names
        report_period = payload.get("report_period") or payload.get("report period") or payload.get("period")
        year = payload.get("year") or payload.get("year_")
        month = payload.get("month") or payload.get("month_")
        day = payload.get("day") or payload.get("day_")
        if report_period:
            try:
                s = str(report_period).strip()[:10]
                if len(s) >= 7:  # YYYY-MM or similar
                    parts = s.replace("-", " ").replace("/", " ").split()
                    y = int(parts[0]) if parts else fallback.year
                    m = int(parts[1]) if len(parts) > 1 else fallback.month
                    day_val = int(parts[2]) if len(parts) > 2 else 1
                    d = date(y, m, day_val)
                else:
                    d = fallback
            except (ValueError, IndexError, TypeError):
                d = fallback
        elif year is not None and month is not None:
            try:
                d = date(int(year), int(month), int(day) if day is not None else 1)
            except (ValueError, TypeError):
                d = fallback
        else:
            d = fallback
    return d.year * 10000 + d.month * 100 + d.day


def _ensure_date_in_dim(cxn, d: date, dk: int) -> None:
    cxn.execute(
        text("INSERT INTO silver.dim_date (date_key, date_actual, year, month, day) VALUES (:dk, :d, :y, :m, :day) ON CONFLICT (date_key) DO NOTHING"),
        {"dk": dk, "d": d, "y": d.year, "m": d.month, "day": d.day},
    )


def transform_to_silver(run_id: str, mode: str = "full") -> dict:
    """
    Read from Bronze (all rows, not just current run), transform and dedupe by row_hash, write to Silver DB only.
    Silver schema/tables are in SILVER_DB_URL or silver schema; never writes to bronze.
    Returns metrics: rows_written per table, tables_written list, mode. Logs silver engine (redacted) and counts.
    """
    ensure_silver_schema()
    bronze = get_bronze_engine()
    silver = get_silver_engine()
    try:
        silver_url = _redact_url(str(silver.url))
        logger.info("Silver transform: writing to schema=silver, url_redacted=%s", silver_url)
    except Exception:
        logger.info("Silver transform: writing to schema=silver")
    today = date.today()
    default_dk = today.year * 10000 + today.month * 100 + today.day
    metrics = {"mode": mode, "tables_written": [], "rows_read": 0, "rows_written": 0}

    # Ensure default date in dim_date (Silver DB/schema only)
    with silver.begin() as cxn:
        _ensure_date_in_dim(cxn, today, default_dk)

    tables_to_process = MODE_TO_BRONZE_TABLES.get(mode, MODE_TO_BRONZE_TABLES["full"])

    # Read ALL rows from bronze (no run_id filter) so silver is fully populated; dedupe by row_hash on insert
    for table, bronze_table in tables_to_process:
        with bronze.connect() as bcxn:
            rows = bcxn.execute(
                text(f"SELECT row_hash, payload, ingest_run_id FROM bronze.{bronze_table}"),
            ).mappings().all()
        if not rows:
            metrics[table] = 0
            continue
        metrics["rows_read"] = metrics.get("rows_read", 0) + len(rows)
        inserted = 0
        with silver.begin() as scxn:
            for r in rows:
                payload = r["payload"] if isinstance(r["payload"], dict) else {}
                op_name = (payload.get("operator") or payload.get("operator_name") or payload.get("company") or "Unknown")
                if isinstance(op_name, dict):
                    op_name = "Unknown"
                op_name = str(op_name).strip()[:200] if op_name else "Unknown"
                scxn.execute(text("INSERT INTO silver.dim_operator (operator_name) VALUES (:n) ON CONFLICT (operator_name) DO NOTHING"), {"n": op_name})
                res = scxn.execute(text("SELECT operator_key FROM silver.dim_operator WHERE operator_name = :n"), {"n": op_name}).fetchone()
                op_key = res[0] if res else 1
                dk = _date_key_from_payload(payload, today)
                y, rest = dk // 10000, dk % 10000
                m, d = max(1, rest // 100), max(1, rest % 100)
                try:
                    _ensure_date_in_dim(scxn, date(y, m, d), dk)
                except ValueError:
                    _ensure_date_in_dim(scxn, today, default_dk)
                payload_json = json.dumps(payload, default=str) if isinstance(payload, dict) else payload
                try:
                    scxn.execute(
                        text(f"INSERT INTO silver.{table} (date_key, operator_key, payload, row_hash) VALUES (:dk, :ok, CAST(:payload AS jsonb), :rh) ON CONFLICT (row_hash) DO NOTHING"),
                        {"dk": dk, "ok": op_key, "payload": payload_json, "rh": r["row_hash"]},
                    )
                    inserted += 1
                except Exception:
                    pass
        metrics[table] = inserted
        metrics["rows_written"] = metrics.get("rows_written", 0) + inserted
        if inserted > 0:
            metrics["tables_written"] = list(set(metrics.get("tables_written", []) + [table]))

    # Concession (when mode is full or concession) — read ALL from bronze, dedupe by row_hash
    if mode in ("full", "concession"):
        with bronze.connect() as bcxn:
            rows = bcxn.execute(
                text("SELECT payload, concession_category FROM bronze.etl_concessions_raw"),
            ).mappings().all()
        concession_inserted = 0
        with silver.begin() as scxn:
            for r in rows:
                payload = r["payload"] if isinstance(r["payload"], dict) else {}
                cat = (r.get("concession_category") or "UNKNOWN")[:500]
                rh = hashlib.sha256(json.dumps({"cat": cat, "p": payload}, sort_keys=True, default=str).encode()).hexdigest()[:32]
                try:
                    scxn.execute(
                        text("INSERT INTO silver.fact_concession_status (concession_category, payload, row_hash) VALUES (:cat, CAST(:payload AS jsonb), :rh) ON CONFLICT (row_hash) DO NOTHING"),
                        {"cat": cat, "payload": json.dumps(payload, default=str) if isinstance(payload, dict) else "{}", "rh": rh},
                    )
                    concession_inserted += 1
                except Exception:
                    pass
        metrics["fact_concession_status"] = concession_inserted
        metrics["rows_read"] = metrics.get("rows_read", 0) + len(rows)
        metrics["rows_written"] = metrics.get("rows_written", 0) + concession_inserted
        if concession_inserted > 0:
            metrics["tables_written"] = list(set(metrics.get("tables_written", []) + ["fact_concession_status"]))

    if "fact_concession_status" not in metrics:
        metrics["fact_concession_status"] = 0
    logger.info(
        "Silver transform done: schema=silver tables_written=%s rows_written=%s",
        metrics.get("tables_written", []),
        metrics.get("rows_written", 0),
    )
    return metrics
