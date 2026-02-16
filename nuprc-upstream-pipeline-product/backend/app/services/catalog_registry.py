"""
Canonical catalog: single source of truth for tables by layer.
Eliminates duplicates (etl_ vs legacy); business-friendly names for Gold and Silver.
Uses BRONZE_DB_URL / SILVER_DB_URL / GOLD_DB_URL when set, else DATABASE_URL (single DB).
"""
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_engine_for_layer(layer: str) -> Engine:
    """Return the DB engine for the given layer (bronze/silver/gold). Uses ETL config when available."""
    try:
        from etl.config import get_bronze_engine, get_silver_engine, get_gold_engine
        if layer == "bronze":
            return get_bronze_engine()
        if layer == "silver":
            return get_silver_engine()
        if layer == "gold":
            return get_gold_engine()
    except Exception:
        pass
    from app.core.db import engine
    return engine

# Canonical physical table names per layer (only these are shown by default)
CANONICAL_TABLES = {
    "bronze": [
        "etl_oil_production_raw",
        "etl_gas_production_raw",
        "etl_rig_disposition_raw",
        "etl_concessions_raw",
        "etl_concessions_sections",
    ],
    "silver": [
        "dim_date",
        "dim_operator",
        "fact_oil_production",
        "fact_gas_production",
        "fact_rig_disposition",
        "fact_concession_status",
    ],
    "gold": [
        "gold_dim_date",
        "gold_oil_dim_operator",
        "gold_oil_fact_production",
        "gold_gas_dim_operator",
        "gold_gas_fact_production",
        "gold_rig_dim_operator",
        "gold_rig_dim_rig",
        "gold_rig_dim_status",
        "gold_rig_fact_activity",
        "gold_concession_dim_concession",
        "gold_concession_fact_snapshot",
    ],
}

# Legacy/deprecated patterns: exclude if 0 rows and an etl_ equivalent exists
DEPRECATED_TABLE_PATTERNS = [
    re.compile(r"^oil_production", re.I),
    re.compile(r"^gas_production", re.I),
    re.compile(r"^rig_disposition", re.I),
    re.compile(r"^concession_situation", re.I),
    re.compile(r"^concession_", re.I),
]

# Business-friendly names for Gold (dataset-specific marts)
TABLE_DISPLAY: Dict[str, Dict[str, str]] = {
    "gold_dim_date": {
        "display_name": "Calendar (Conformed)",
        "subject_area": "Dimensions",
        "grain": "Daily",
    },
    "gold_oil_dim_operator": {
        "display_name": "Oil — Operators (Dimension)",
        "subject_area": "Oil",
        "grain": "By Operator",
    },
    "gold_oil_fact_production": {
        "display_name": "Oil — Production (Fact)",
        "subject_area": "Oil",
        "grain": "Date × Operator",
    },
    "gold_gas_dim_operator": {
        "display_name": "Gas — Operators (Dimension)",
        "subject_area": "Gas",
        "grain": "By Operator",
    },
    "gold_gas_fact_production": {
        "display_name": "Gas — Production (Fact)",
        "subject_area": "Gas",
        "grain": "Date × Operator",
    },
    "gold_rig_dim_operator": {
        "display_name": "Rig — Operators (Dimension)",
        "subject_area": "Rigs",
        "grain": "By Operator",
    },
    "gold_rig_dim_rig": {
        "display_name": "Rig — Rigs (Dimension)",
        "subject_area": "Rigs",
        "grain": "By Rig",
    },
    "gold_rig_dim_status": {
        "display_name": "Rig — Activity Status (Dimension)",
        "subject_area": "Rigs",
        "grain": "By Status",
    },
    "gold_rig_fact_activity": {
        "display_name": "Rig — Activity (Fact)",
        "subject_area": "Rigs",
        "grain": "Date × Operator × Rig × Status",
    },
    "gold_concession_dim_concession": {
        "display_name": "Concession — Register (Dimension)",
        "subject_area": "Concessions",
        "grain": "By Concession",
    },
    "gold_concession_fact_snapshot": {
        "display_name": "Concession — Snapshot (Fact)",
        "subject_area": "Concessions",
        "grain": "Report Date × Concession",
    },
    "etl_oil_production_raw": {"display_name": "Oil Production — Raw", "subject_area": "Oil", "grain": "By row"},
    "etl_gas_production_raw": {"display_name": "Gas Production — Raw", "subject_area": "Gas", "grain": "By row"},
    "etl_rig_disposition_raw": {"display_name": "Rig Disposition — Raw", "subject_area": "Rigs", "grain": "By row"},
    "etl_concessions_raw": {"display_name": "Concessions — Raw Extract", "subject_area": "Concessions", "grain": "By row"},
    "etl_concessions_sections": {"display_name": "Concession Sections (Headers)", "subject_area": "Concessions", "grain": "By section"},
    # Silver: business-friendly names for legacy UI
    "dim_date": {"display_name": "Silver Dim Date", "subject_area": "Dimensions", "grain": "Daily"},
    "dim_operator": {"display_name": "Silver Dim Operator", "subject_area": "Dimensions", "grain": "By Operator"},
    "fact_oil_production": {"display_name": "Silver Oil Production", "subject_area": "Oil", "grain": "By row"},
    "fact_gas_production": {"display_name": "Silver Gas Production", "subject_area": "Gas", "grain": "By row"},
    "fact_rig_disposition": {"display_name": "Silver Rig Disposition", "subject_area": "Rigs", "grain": "By row"},
    "fact_concession_status": {"display_name": "Silver Concessions", "subject_area": "Concessions", "grain": "By row"},
}


def _default_display(schema: str, physical: str) -> str:
    if "oil" in physical:
        return "Oil Production — Raw" if schema == "bronze" else "Oil Production"
    if "gas" in physical:
        return "Gas Production — Raw" if schema == "bronze" else "Gas Production"
    if "rig" in physical:
        return "Rig Disposition — Raw" if schema == "bronze" else "Rig Disposition"
    if "concession" in physical:
        return "Concessions — Raw Extract" if schema == "bronze" else "Concession Status"
    return physical.replace("_", " ").title()


def _default_description(schema: str, physical: str) -> str:
    if schema == "bronze":
        return f"Raw extracted data: {physical}"
    if schema == "silver":
        return f"Cleaned and conformed: {physical}"
    return f"Warehouse table: {physical}"


def _is_deprecated(physical_name: str) -> bool:
    return any(p.search(physical_name) for p in DEPRECATED_TABLE_PATTERNS)


def get_tables_for_layer(
    engine: Engine,
    layer: str,
    include_deprecated: bool = False,
) -> List[Dict[str, Any]]:
    """
    Return list of tables for the given layer (bronze | silver | gold).
    Only canonical tables are included unless include_deprecated=True.
    Each table has: physical_name, display_name, description, row_count, last_updated, subject_area, grain.
    """
    if layer not in ("bronze", "silver", "gold"):
        return []
    schema = layer
    canonical_set = set(CANONICAL_TABLES.get(layer, []))
    tables_out: List[Dict[str, Any]] = []

    with engine.connect() as cxn:
        # Last successful ETL run per schema (proxy for last_updated)
        last_updated: Optional[str] = None
        try:
            row = cxn.execute(
                text("""
                    SELECT max(ended_at)::text
                    FROM admin.etl_runs
                    WHERE status = 'success' AND ended_at IS NOT NULL
                """)
            ).scalar()
            if row:
                last_updated = str(row)
        except Exception:
            pass

        # Which physical tables exist in this schema
        existing = set()
        for (tname,) in cxn.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            """),
            {"schema": schema},
        ).fetchall():
            existing.add(tname)

        # Build list: prefer canonical; if include_deprecated add others (excluding 0-row deprecated when etl_ exists)
        to_show = set()
        for t in canonical_set:
            if t in existing:
                to_show.add(t)
        if include_deprecated:
            for t in existing:
                if t in to_show:
                    continue
                if _is_deprecated(t):
                    # Include only if it has rows (else skip - duplicate of etl_)
                    try:
                        n = cxn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{t}"')).scalar() or 0
                        if n > 0:
                            to_show.add(t)
                    except Exception:
                        pass
                else:
                    to_show.add(t)

        for physical_name in sorted(to_show):
            info = TABLE_DISPLAY.get(physical_name) or {}
            display_name = info.get("display_name") or _default_display(schema, physical_name)
            subject_area = info.get("subject_area", "")
            grain = info.get("grain", "")
            description = _default_description(schema, physical_name)
            row_count = 0
            try:
                row_count = cxn.execute(
                    text(f'SELECT COUNT(*) FROM "{schema}"."{physical_name}"')
                ).scalar() or 0
            except Exception:
                pass
            tables_out.append({
                "physical_name": physical_name,
                "display_name": display_name,
                "description": description,
                "row_count": row_count,
                "last_updated": last_updated,
                "subject_area": subject_area or None,
                "grain": grain or None,
            })

    return tables_out
