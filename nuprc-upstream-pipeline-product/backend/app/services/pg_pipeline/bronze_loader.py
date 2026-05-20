"""Bronze load: parse files and bulk insert JSONB rows."""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from sqlalchemy import text

from app.core.db import engine
from app.services.pg_pipeline.fuzzy_columns import apply_mapping, map_columns
from app.services.pg_pipeline.sources import ACTIVITY_TYPE, BRONZE_TABLE

CHUNKSIZE = 500


def load_file_to_bronze(
    run_id: str,
    source_key: str,
    source_name: str,
    file_path: Path,
    file_url: str,
    file_hash: str,
) -> Tuple[int, bool]:
    """Load one file into the appropriate bronze table. Returns (row_count, drift_flag)."""
    activity = ACTIVITY_TYPE[source_key]
    table = BRONZE_TABLE[source_key]
    if file_path.suffix.lower() == ".pdf":
        rows = _load_pdf_rows(file_path)
    else:
        rows = _load_excel_rows(file_path)
    if not rows:
        return 0, False
    col_map, high_drift = map_columns(
        run_id, source_name, activity, file_url, list(rows[0].keys())
    )
    records = []
    for raw in rows:
        canonical = apply_mapping(raw, col_map)
        records.append({
            "run_id": run_id,
            "source_name": source_name,
            "file_url": file_url,
            "file_hash": file_hash,
            "report_period": _extract_period(canonical),
            "row_payload": json.dumps(raw),
            "canonical_payload": json.dumps(canonical),
            "schema_version": "v1",
            "drift_flag": high_drift,
        })
    df = pd.DataFrame(records)
    df.to_sql(
        table.split(".")[-1],
        engine,
        schema=table.split(".")[0],
        if_exists="append",
        index=False,
        method="multi",
        chunksize=CHUNKSIZE,
    )
    return len(records), high_drift


def _load_excel_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        xls = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    except Exception:
        df = pd.read_excel(path, engine="openpyxl")
        xls = {"Sheet1": df}
    rows: List[Dict[str, Any]] = []
    for _name, df in xls.items():
        if df is None or df.empty:
            continue
        df = df.where(pd.notnull(df), None)
        for rec in df.to_dict(orient="records"):
            rows.append({str(k): v for k, v in rec.items() if k is not None})
    return rows


def _load_pdf_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        import pdfplumber
        rows: List[Dict[str, Any]] = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables() or []
                for ti, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    headers = [str(h or f"col_{j}") for j, h in enumerate(table[0])]
                    for data_row in table[1:]:
                        row = {headers[j]: (data_row[j] if j < len(data_row) else None) for j in range(len(headers))}
                        rows.append(row)
        return rows
    except Exception:
        return [{"raw_path": str(path), "note": "pdf_parse_failed"}]


def _extract_period(canonical: Dict[str, Any]) -> str | None:
    for key in ("report_period", "period", "year"):
        v = canonical.get(key)
        if v is not None:
            return str(v)
    return None
