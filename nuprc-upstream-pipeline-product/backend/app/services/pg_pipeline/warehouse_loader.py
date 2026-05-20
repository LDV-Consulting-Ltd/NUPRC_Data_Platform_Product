"""Load silver into warehouse dimensions and fact_upstream_activity."""
from typing import Optional

from sqlalchemy import text

from app.core.db import engine


def load_silver_to_warehouse(run_id: str) -> int:
    count = 0
    with engine.connect() as cxn:
        rows = cxn.execute(
            text("""
                SELECT id, source_name, activity_type, report_period, operator_name,
                       asset_name, field_name, terminal_stream, product_type,
                       status, volume_value, volume_unit
                FROM silver.upstream_activity_standardized
                WHERE run_id = :run_id
            """),
            {"run_id": run_id},
        ).mappings().all()
    for row in rows:
        source_key = _upsert_source(row["source_name"], row["activity_type"])
        operator_key = _upsert_operator(row["operator_name"]) if row["operator_name"] else None
        asset_key = _upsert_asset(row["asset_name"], row["field_name"])
        product_key = _upsert_product(row["product_type"], row["terminal_stream"])
        date_key = _date_key_from_period(row["report_period"])
        with engine.begin() as cxn:
            cxn.execute(
                text("""
                    INSERT INTO warehouse.fact_upstream_activity (
                        date_key, source_key, operator_key, asset_key, product_key,
                        activity_type, report_period, status, volume_value, volume_unit,
                        source_row_id
                    ) VALUES (
                        :date_key, :source_key, :operator_key, :asset_key, :product_key,
                        :activity_type, :report_period, :status, :volume_value, :volume_unit,
                        :source_row_id
                    )
                """),
                {
                    "date_key": date_key,
                    "source_key": source_key,
                    "operator_key": operator_key,
                    "asset_key": asset_key,
                    "product_key": product_key,
                    "activity_type": row["activity_type"],
                    "report_period": row["report_period"],
                    "status": row["status"],
                    "volume_value": row["volume_value"],
                    "volume_unit": row["volume_unit"],
                    "source_row_id": row["id"],
                },
            )
        count += 1
    return count


def _upsert_source(source_name: str, activity_type: str) -> int:
    with engine.begin() as conn:
        r = conn.execute(
            text("""
                INSERT INTO warehouse.dim_source (source_name, activity_type)
                VALUES (:name, :atype)
                ON CONFLICT (source_name) DO UPDATE SET activity_type = EXCLUDED.activity_type
                RETURNING source_key
            """),
            {"name": source_name, "atype": activity_type},
        )
        return int(r.scalar_one())


def _upsert_operator(name: str) -> int:
    with engine.begin() as conn:
        r = conn.execute(
            text("""
                INSERT INTO warehouse.dim_operator (operator_name)
                VALUES (:name)
                ON CONFLICT (operator_name) DO UPDATE SET operator_name = EXCLUDED.operator_name
                RETURNING operator_key
            """),
            {"name": name},
        )
        return int(r.scalar_one())


def _upsert_asset(asset_name: Optional[str], field_name: Optional[str]) -> Optional[int]:
    if not asset_name:
        return None
    with engine.begin() as conn:
        r = conn.execute(
            text("""
                INSERT INTO warehouse.dim_asset (asset_name, field_name)
                VALUES (:asset, :field)
                ON CONFLICT (asset_name, field_name) DO UPDATE SET asset_name = EXCLUDED.asset_name
                RETURNING asset_key
            """),
            {"asset": asset_name, "field": field_name},
        )
        return int(r.scalar_one())


def _upsert_product(product_type: Optional[str], terminal_stream: Optional[str]) -> Optional[int]:
    pt = product_type or "unknown"
    with engine.begin() as conn:
        r = conn.execute(
            text("""
                INSERT INTO warehouse.dim_product (product_type, terminal_stream)
                VALUES (:pt, :ts)
                ON CONFLICT (product_type, terminal_stream) DO UPDATE SET product_type = EXCLUDED.product_type
                RETURNING product_key
            """),
            {"pt": pt, "ts": terminal_stream},
        )
        return int(r.scalar_one())


def _date_key_from_period(period: Optional[str]) -> Optional[int]:
    if not period:
        return None
    import re
    m = re.search(r"(20\d{2})", str(period))
    if m:
        y = int(m.group(1))
        return y * 10000 + 101
    return None
