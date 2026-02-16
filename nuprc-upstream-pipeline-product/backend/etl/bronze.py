"""
Load acquired data into Bronze: payload JSONB + metadata columns.
Excel: read with pandas, normalize column names, compute row_hash, insert.
Concession: insert raw rows and section events from concession extractor.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text

from etl.config import get_bronze_engine
from etl.concession import extract_concession_pdf


def init_bronze_etl_tables(engine=None):
    """Create bronze ETL tables if they do not exist."""
    engine = engine or get_bronze_engine()
    path = Path(__file__).parent / "migrations" / "001_bronze_etl_tables.sql"
    if not path.exists():
        return
    ddl = path.read_text()
    # Run each statement: split by newline+semicolon to avoid splitting inside (...)
    statements = []
    current = []
    depth = 0
    for line in ddl.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        depth += line.count("(") - line.count(")")
        if ";" in line and depth <= 0:
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            depth = 0
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)
    for stmt in statements:
        if not stmt.strip():
            continue
        with engine.begin() as cxn:
            cxn.execute(text(stmt))
    # Migration 005: report_year column
    path_005 = Path(__file__).parent / "migrations" / "005_bronze_report_year.sql"
    if path_005.exists():
        ddl_005 = path_005.read_text()
        for stmt in ddl_005.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    with engine.begin() as cxn:
                        cxn.execute(text(stmt))
                except Exception:
                    pass


def _report_year_from_payload_and_file(payload: Dict[str, Any], file_name: str, downloaded_at: datetime) -> int:
    """Derive report_year from payload (year, report_period), file name (e.g. 2024), or downloaded_at year."""
    import re
    if payload:
        year = payload.get("year") or payload.get("year_") or payload.get("report_year")
        if year is not None:
            try:
                return int(year)
            except (ValueError, TypeError):
                pass
        rp = payload.get("report_period") or payload.get("report period") or payload.get("period")
        if rp is not None:
            s = str(rp).strip()
            m = re.search(r"20\d{2}", s)
            if m:
                return int(m.group(0))
    if file_name:
        m = re.search(r"20\d{2}", file_name)
        if m:
            return int(m.group(0))
    return downloaded_at.year if downloaded_at else datetime.now(timezone.utc).year


def _normalize_key(s: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in (s or "").strip().lower()).strip("_") or "col"


def _row_hash(row: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:32]


def load_excel_to_bronze(
    file_path: Path,
    source_key: str,
    file_url: str,
    ingest_run_id: str,
    table_name: str,
    downloaded_at: Optional[datetime] = None,
) -> int:
    """
    Read Excel file, normalize columns to payload JSONB, add metadata, insert into bronze.<table_name>.
    table_name: etl_oil_production_raw | etl_gas_production_raw | etl_rig_disposition_raw
    Returns rows inserted.
    """
    downloaded_at = downloaded_at or datetime.now(timezone.utc)
    engine = get_bronze_engine()
    full_table = f"bronze.{table_name}"

    try:
        xl = pd.ExcelFile(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel {file_path}: {e}") from e

    total = 0
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=0)
        if df.empty or len(df.columns) == 0:
            continue
        df = df.astype(str).fillna("")
        cols = [str(c).strip() for c in df.columns]
        normalized = [_normalize_key(c) or f"col_{i}" for i, c in enumerate(cols)]
        rows = []
        report_year_fallback = _report_year_from_payload_and_file({}, file_path.name, downloaded_at)
        for idx, r in df.iterrows():
            payload = {normalized[i]: (r.iloc[i] if i < len(r) else None) for i in range(len(cols))}
            payload = {k: (None if v == "" else v) for k, v in payload.items()}
            row_hash = _row_hash(payload)
            report_year = _report_year_from_payload_and_file(payload, file_path.name, downloaded_at)
            if report_year is None:
                report_year = report_year_fallback
            rows.append({
                "ingest_run_id": ingest_run_id,
                "source_key": source_key,
                "file_url": file_url,
                "file_name": file_path.name,
                "downloaded_at": downloaded_at,
                "sheet_name": sheet_name,
                "row_number": int(idx) + 1,
                "row_hash": row_hash,
                "payload": json.dumps(payload, default=str),
                "report_year": report_year,
            })
        if not rows:
            continue
        for row in rows:
            # Use a separate transaction per row so a failed INSERT doesn't abort the connection.
            # Otherwise the fallback INSERT would hit "current transaction is aborted".
            try:
                with engine.begin() as cxn:
                    cxn.execute(
                        text(f"""
                            INSERT INTO {full_table}
                            (ingest_run_id, source_key, file_url, file_name, downloaded_at, sheet_name, row_number, row_hash, payload, report_year)
                            VALUES (:ingest_run_id, :source_key, :file_url, :file_name, :downloaded_at, :sheet_name, :row_number, :row_hash, CAST(:payload AS jsonb), :report_year)
                        """),
                        row,
                    )
            except Exception as e:
                if "report_year" in str(e) or "column" in str(e).lower():
                    with engine.begin() as cxn:
                        cxn.execute(
                            text(f"""
                                INSERT INTO {full_table}
                                (ingest_run_id, source_key, file_url, file_name, downloaded_at, sheet_name, row_number, row_hash, payload)
                                VALUES (:ingest_run_id, :source_key, :file_url, :file_name, :downloaded_at, :sheet_name, :row_number, :row_hash, CAST(:payload AS jsonb))
                            """),
                            {k: v for k, v in row.items() if k != "report_year"},
                        )
                else:
                    raise
            total += 1
    return total


def load_concession_to_bronze(
    file_path: Path,
    file_url: str,
    ingest_run_id: str,
    source_key: str = "concession",
    downloaded_at: Optional[datetime] = None,
) -> int:
    """Extract PDF with section headers, insert into bronze.etl_concessions_raw and bronze.etl_concessions_sections. Returns total raw rows inserted."""
    downloaded_at = downloaded_at or datetime.now(timezone.utc)
    engine = get_bronze_engine()
    raw_rows, section_events = extract_concession_pdf(str(file_path))

    report_year = downloaded_at.year if downloaded_at else datetime.now(timezone.utc).year
    with engine.begin() as cxn:
        for ev in section_events:
            cxn.execute(
                text("""
                    INSERT INTO bronze.etl_concessions_sections
                    (ingest_run_id, source_key, file_url, file_name, page_number, header_text, concession_category, line_index, report_year)
                    VALUES (:ingest_run_id, :source_key, :file_url, :file_name, :page_number, :header_text, :concession_category, :line_index, :report_year)
                """),
                {
                    "ingest_run_id": ingest_run_id,
                    "source_key": source_key,
                    "file_url": file_url,
                    "file_name": file_path.name,
                    "page_number": ev["page_number"],
                    "header_text": ev.get("header_text"),
                    "concession_category": ev["concession_category"],
                    "line_index": ev.get("line_index"),
                    "report_year": report_year,
                },
            )
        # Ensure concession_category_full column exists (migration 003)
        try:
            cxn.execute(text("ALTER TABLE bronze.etl_concessions_raw ADD COLUMN IF NOT EXISTS concession_category_full TEXT"))
        except Exception:
            pass
        count = 0
        for r in raw_rows:
            category_full = r.get("concession_category_full") or r.get("concession_category") or "UNKNOWN"
            cxn.execute(
                text("""
                    INSERT INTO bronze.etl_concessions_raw
                    (ingest_run_id, source_key, file_url, file_name, downloaded_at, page_number, row_number_on_page, concession_category, concession_category_full, payload, report_year)
                    VALUES (:ingest_run_id, :source_key, :file_url, :file_name, :downloaded_at, :page_number, :row_number_on_page, :concession_category, :concession_category_full, CAST(:payload AS jsonb), :report_year)
                """),
                {
                    "ingest_run_id": ingest_run_id,
                    "source_key": source_key,
                    "file_url": file_url,
                    "file_name": file_path.name,
                    "downloaded_at": downloaded_at,
                    "page_number": r["page_number"],
                    "row_number_on_page": r["row_number_on_page"],
                    "concession_category": category_full,
                    "concession_category_full": category_full,
                    "payload": json.dumps(r["payload"], default=str),
                    "report_year": report_year,
                },
            )
            count += 1
    return count
