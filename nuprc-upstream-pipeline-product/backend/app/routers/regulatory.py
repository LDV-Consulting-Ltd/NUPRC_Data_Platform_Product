"""
Regulatory export downloads: CSV / ZIP from silver layer tables.
"""
import csv
import io
import zipfile
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.services.catalog_registry import get_engine_for_layer

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

# export_id -> tables in silver schema
_EXPORT_DEFS: Dict[str, Dict[str, Any]] = {
    "submission_monthly_oil_gas": {
        "name": "Monthly Oil & Gas Report",
        "category": "submission",
        "tables": ["silver.fact_oil_production", "silver.fact_gas_production"],
        "version": "v2026.1",
    },
    "submission_quarterly_concession": {
        "name": "Quarterly Concession Snapshot",
        "category": "submission",
        "tables": ["silver.fact_concession_status"],
        "version": "v2026.Q1",
    },
    "bundle_audit_dec_2025": {
        "name": "Audit export bundle — Dec 2025",
        "category": "bundle",
        "tables": [
            "silver.fact_oil_production",
            "silver.fact_gas_production",
            "silver.fact_rig_disposition",
            "silver.fact_concession_status",
            "silver.dim_date",
            "silver.dim_operator",
        ],
        "version": "2025-12",
    },
    "bundle_snapshot_jan_2026": {
        "name": "Regulatory snapshot — Jan 2026",
        "category": "bundle",
        "tables": [
            "silver.fact_oil_production",
            "silver.fact_gas_production",
            "silver.fact_rig_disposition",
            "silver.fact_concession_status",
        ],
        "version": "2026-01",
    },
    "snapshot_v2026_1": {
        "name": "Regulatory snapshot v2026.1",
        "category": "snapshot",
        "tables": [
            "silver.fact_oil_production",
            "silver.fact_gas_production",
            "silver.fact_rig_disposition",
            "silver.fact_concession_status",
            "silver.dim_date",
            "silver.dim_operator",
        ],
        "version": "v2026.1",
    },
    "snapshot_v2025_12": {
        "name": "Regulatory snapshot v2025.12",
        "category": "snapshot",
        "tables": [
            "silver.fact_oil_production",
            "silver.fact_gas_production",
            "silver.fact_rig_disposition",
            "silver.fact_concession_status",
        ],
        "version": "v2025.12",
    },
    "snapshot_v2025_q4": {
        "name": "Regulatory snapshot v2025.Q4",
        "category": "snapshot",
        "tables": [
            "silver.fact_oil_production",
            "silver.fact_gas_production",
            "silver.fact_concession_status",
        ],
        "version": "v2025.Q4",
    },
}


def _serialize_cell(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        import json
        return json.dumps(value, default=str)
    return str(value)


def _table_to_csv_bytes(cxn, full_table: str, max_rows: int = 500_000) -> bytes:
    """Export a table to CSV bytes."""
    buf = io.StringIO()
    try:
        result = cxn.execute(
            text(f"SELECT * FROM {full_table} LIMIT :limit"),
            {"limit": max_rows},
        )
        rows = result.mappings().all()
        if not rows:
            writer = csv.writer(buf)
            writer.writerow(["message"])
            writer.writerow(["No rows in table"])
            return buf.getvalue().encode("utf-8-sig")

        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _serialize_cell(row[k]) for k in fieldnames})
    except Exception as e:
        writer = csv.writer(buf)
        writer.writerow(["error"])
        writer.writerow([str(e)])
    return buf.getvalue().encode("utf-8-sig")


def _table_row_count(cxn, full_table: str) -> int:
    try:
        return int(cxn.execute(text(f"SELECT COUNT(*) FROM {full_table}")).scalar() or 0)
    except Exception:
        return 0


def _estimate_size_mb(row_count: int) -> str:
    if row_count == 0:
        return "—"
    approx_kb = max(1, row_count * 0.5)
    if approx_kb >= 1024:
        return f"{approx_kb / 1024:.1f} MB"
    return f"{int(approx_kb)} KB"


@router.get("/exports")
def list_regulatory_exports():
    """List downloadable regulatory datasets with live row counts."""
    eng = get_engine_for_layer("silver")
    items = []
    with eng.connect() as cxn:
        for export_id, meta in _EXPORT_DEFS.items():
            tables = meta["tables"]
            total_rows = sum(_table_row_count(cxn, t) for t in tables)
            items.append({
                "export_id": export_id,
                "name": meta["name"],
                "category": meta["category"],
                "version": meta.get("version"),
                "tables": [t.split(".", 1)[-1] for t in tables],
                "row_count": total_rows,
                "size_label": _estimate_size_mb(total_rows),
                "download_url": f"/regulatory/download/{export_id}",
            })
    return {"ok": True, "exports": items}


@router.get("/download/{export_id}")
def download_regulatory_export(export_id: str):
    """Download a regulatory dataset as CSV (single table) or ZIP (multiple tables)."""
    meta = _EXPORT_DEFS.get(export_id)
    if not meta:
        raise HTTPException(status_code=404, detail={"user_message": "Export not found.", "technical_details": {"export_id": export_id}})

    tables: List[str] = meta["tables"]
    version = meta.get("version", "export")
    safe_name = export_id.replace(" ", "_")
    eng = get_engine_for_layer("silver")

    with eng.connect() as cxn:
        if len(tables) == 1:
            csv_bytes = _table_to_csv_bytes(cxn, tables[0])
            table_short = tables[0].split(".")[-1]
            filename = f"nuprc_{safe_name}_{table_short}_{version}.csv"
            return StreamingResponse(
                iter([csv_bytes]),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for full_table in tables:
                table_short = full_table.split(".")[-1]
                csv_bytes = _table_to_csv_bytes(cxn, full_table)
                zf.writestr(f"{table_short}.csv", csv_bytes)
        zip_buffer.seek(0)
        filename = f"nuprc_{safe_name}_{version}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
