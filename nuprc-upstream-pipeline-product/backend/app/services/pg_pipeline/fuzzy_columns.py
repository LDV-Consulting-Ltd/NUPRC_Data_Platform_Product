"""Fuzzy column mapping with rapidfuzz; log drift to meta.schema_drift."""
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process
from sqlalchemy import text

from app.core.db import engine

MATCH_THRESHOLD = 72
HIGH_DRIFT_THRESHOLD = 50

CANONICAL_BY_ACTIVITY = {
    "oil_production": [
        "terminal_stream", "liquid_type", "report_period", "production_volume",
        "unit", "operator_name", "field_name", "asset_name",
    ],
    "gas_production": [
        "facility_or_field", "product_type", "report_period", "gas_volume",
        "unit", "operator_name", "field_name",
    ],
    "rig_disposition": [
        "rig_name", "operator_name", "status", "location", "report_period",
    ],
    "concession": [
        "concession_name", "operator_name", "concession_type", "terrain",
        "status", "award_date", "expiry_date", "area",
    ],
}


def map_columns(
    run_id: str,
    source_name: str,
    activity_type: str,
    file_url: str,
    source_columns: List[str],
) -> Tuple[Dict[str, str], bool]:
    """
    Map source column names to canonical names.
    Returns (mapping source_col -> canonical, has_high_drift).
    """
    canonical = CANONICAL_BY_ACTIVITY.get(activity_type, [])
    mapping: Dict[str, str] = {}
    high_drift = False
    for col in source_columns:
        if not col or not str(col).strip():
            continue
        col_s = str(col).strip()
        match = process.extractOne(
            col_s,
            canonical,
            scorer=fuzz.token_sort_ratio,
        )
        if match and match[1] >= MATCH_THRESHOLD:
            mapping[col_s] = match[0]
            _log_drift(run_id, source_name, file_url, col_s, match[0], match[1], "COLUMN_MAPPED", "INFO")
        else:
            score = match[1] if match else 0
            severity = "HIGH" if score < HIGH_DRIFT_THRESHOLD else "WARN"
            if severity == "HIGH":
                high_drift = True
            _log_drift(
                run_id, source_name, file_url, col_s,
                match[0] if match else None, score,
                "UNMAPPED_COLUMN", severity,
                f"No confident match for column '{col_s}'",
            )
    return mapping, high_drift


def _log_drift(
    run_id: str,
    source_name: str,
    file_url: str,
    original: str,
    mapped: Optional[str],
    score: float,
    drift_type: str,
    severity: str,
    message: str = "",
) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO meta.schema_drift (
                    run_id, source_name, file_url, drift_type,
                    original_column, mapped_column, match_score, message, severity
                ) VALUES (
                    :run_id, :source_name, :file_url, :drift_type,
                    :original, :mapped, :score, :message, :severity
                )
            """),
            {
                "run_id": run_id,
                "source_name": source_name,
                "file_url": file_url,
                "drift_type": drift_type,
                "original": original,
                "mapped": mapped,
                "score": float(score),
                "message": message or f"{original} -> {mapped} ({score:.0f})",
                "severity": severity,
            },
        )


def apply_mapping(row: Dict[str, Any], col_map: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in row.items():
        key = col_map.get(str(k).strip(), str(k).strip())
        out[key] = v
    return out
