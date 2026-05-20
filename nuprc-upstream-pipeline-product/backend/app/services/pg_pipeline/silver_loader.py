"""Silver standardization from bronze JSONB."""
import json
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.db import engine
from app.services.pg_pipeline.sources import ACTIVITY_TYPE, BRONZE_TABLE

BATCH = 1000


def standardize_bronze_to_silver(run_id: str) -> int:
    total = 0
    for source_key, table in BRONZE_TABLE.items():
        activity = ACTIVITY_TYPE[source_key]
        with engine.connect() as cxn:
            rows = cxn.execute(
                text(f"""
                    SELECT id, source_name, canonical_payload, row_payload, report_period
                    FROM {table}
                    WHERE run_id = :run_id
                """),
                {"run_id": run_id},
            ).mappings().all()
        batch: List[Dict[str, Any]] = []
        for row in rows:
            canon = row["canonical_payload"]
            if isinstance(canon, str):
                canon = json.loads(canon)
            raw = row["row_payload"]
            if isinstance(raw, str):
                raw = json.loads(raw)
            rec = _to_silver_row(run_id, row["source_name"], activity, row["report_period"], canon or raw, raw)
            batch.append(rec)
            if len(batch) >= BATCH:
                _insert_batch(batch)
                total += len(batch)
                batch = []
        if batch:
            _insert_batch(batch)
            total += len(batch)
    return total


def _to_silver_row(
    run_id: str,
    source_name: str,
    activity_type: str,
    report_period: str | None,
    canon: Dict[str, Any],
    raw: Dict[str, Any],
) -> Dict[str, Any]:
    def g(*keys: str):
        for k in keys:
            if k in canon and canon[k] is not None:
                return canon[k]
            if k in raw and raw[k] is not None:
                return raw[k]
        return None

    vol = g("production_volume", "gas_volume", "volume", "quantity")
    try:
        vol_f = float(vol) if vol is not None else None
    except (TypeError, ValueError):
        vol_f = None

    return {
        "run_id": run_id,
        "source_name": source_name,
        "activity_type": activity_type,
        "report_period": report_period or str(g("report_period", "period", "year") or ""),
        "operator_name": g("operator_name", "operator"),
        "asset_name": g("asset_name", "facility_or_field", "field_name"),
        "field_name": g("field_name", "facility_or_field"),
        "terminal_stream": g("terminal_stream"),
        "product_type": g("product_type", "liquid_type"),
        "rig_name": g("rig_name", "rig"),
        "concession_name": g("concession_name", "concession"),
        "concession_type": g("concession_type"),
        "status": g("status"),
        "volume_value": vol_f,
        "volume_unit": g("unit"),
        "row_payload": json.dumps(raw),
    }


def _insert_batch(batch: List[Dict[str, Any]]) -> None:
    import pandas as pd
    df = pd.DataFrame(batch)
    df.to_sql(
        "upstream_activity_standardized",
        engine,
        schema="silver",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=BATCH,
    )
