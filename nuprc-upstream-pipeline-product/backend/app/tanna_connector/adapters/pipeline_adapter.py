"""Read-only adapter for v1 pipeline / admin.etl observability tables."""
from typing import Any, Optional


def _warning(msg: str, warnings: list[str]) -> None:
    if msg not in warnings:
        warnings.append(msg)


def get_latest_run() -> tuple[Optional[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from etl.config import get_etl_engine
        eng = get_etl_engine()
        with eng.connect() as cxn:
            row = cxn.execute(text("""
                SELECT run_id, mode, status, started_at, ended_at, triggered_by, meta_json
                FROM admin.etl_runs
                ORDER BY started_at DESC
                LIMIT 1
            """)).mappings().first()
        return dict(row) if row else None, warnings
    except Exception as exc:
        _warning(f"Latest ETL run unavailable: {exc}", warnings)
        return None, warnings


def get_blocking_runs() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from etl.config import get_etl_engine
        eng = get_etl_engine()
        with eng.connect() as cxn:
            rows = cxn.execute(text("""
                SELECT run_id, mode, status, started_at
                FROM admin.etl_runs
                WHERE status = 'running'
                ORDER BY started_at DESC
            """)).mappings().all()
        return [dict(r) for r in rows], warnings
    except Exception as exc:
        _warning(f"Blocking runs unavailable: {exc}", warnings)
        return [], warnings


def get_failed_steps_for_latest_run() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from etl.config import get_etl_engine
        eng = get_etl_engine()
        with eng.connect() as cxn:
            run = cxn.execute(text("""
                SELECT run_id, status FROM admin.etl_runs
                ORDER BY started_at DESC LIMIT 1
            """)).mappings().first()
            if not run:
                return [], warnings
            rows = cxn.execute(text("""
                SELECT step_key, status, started_at, ended_at, error_json
                FROM admin.etl_run_steps
                WHERE run_id = :run_id AND status = 'failed'
                ORDER BY started_at
            """), {"run_id": run["run_id"]}).mappings().all()
        return [dict(r) for r in rows], warnings
    except Exception as exc:
        _warning(f"Failed ETL steps unavailable: {exc}", warnings)
        return [], warnings


def get_sources_health() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    tables = [
        ("oil_production_status", "Oil Production", "bronze.etl_oil_production_raw"),
        ("gas_production_status", "Gas Production", "bronze.etl_gas_production_raw"),
        ("rig_disposition", "Rig Disposition", "bronze.etl_rig_disposition_raw"),
        ("concession_situation", "Concession Status", "bronze.etl_concessions_raw"),
    ]
    sources: list[dict[str, Any]] = []
    try:
        from sqlalchemy import text
        from etl.config import get_etl_engine
        eng = get_etl_engine()
        for source_key, label, table in tables:
            count = 0
            try:
                with eng.connect() as cxn:
                    count = cxn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
            except Exception:
                pass
            score = min(100, 50 + (count // 100)) if count else 40
            status = "fresh" if score >= 85 else "stable" if score >= 70 else "degraded" if score >= 50 else "down"
            sources.append({
                "source_key": source_key,
                "label": label,
                "status": status,
                "freshness_score": score,
                "row_count": count,
            })
    except Exception as exc:
        _warning(f"Source health unavailable: {exc}", warnings)
    return sources, warnings


def get_gold_freshness() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from datetime import datetime, timezone
        from sqlalchemy import text
        from app.services.catalog_registry import get_engine_for_layer
        eng = get_engine_for_layer("gold")
        datasets = [
            ("oil_production_status", "Oil Production", "gold.gold_oil_fact_production", "date_key"),
            ("gas_production_status", "Gas Production", "gold.gold_gas_fact_production", "date_key"),
            ("rig_disposition", "Rig Disposition", "gold.gold_rig_fact_activity", "date_key"),
            (
                "concession_situation",
                "Concession Status",
                "gold.gold_concession_fact_snapshot",
                "report_date_key",
            ),
        ]
        items = []
        with eng.connect() as cxn:
            for source_key, label, fact_table, date_col in datasets:
                count = 0
                max_date = None
                try:
                    count = cxn.execute(text(f"SELECT COUNT(*) FROM {fact_table}")).scalar() or 0
                    max_date = cxn.execute(text(f"""
                        SELECT MAX(d.date_actual)
                        FROM {fact_table} t
                        JOIN gold.gold_dim_date d ON t.{date_col} = d.date_key
                    """)).scalar()
                except Exception:
                    pass
                score = 40 if count == 0 else min(100, 50 + (count // 100))
                status = "fresh" if score >= 85 else "stable" if score >= 70 else "degraded" if score >= 50 else "down"
                max_iso = max_date.isoformat() if max_date and hasattr(max_date, "isoformat") else (
                    str(max_date) if max_date else None
                )
                items.append({
                    "source_key": source_key,
                    "label": label,
                    "status": status,
                    "freshness_score": score,
                    "row_count": count,
                    "last_updated": max_iso,
                })
    except Exception as exc:
        _warning(f"Gold freshness unavailable: {exc}", warnings)
    return items, warnings


def get_run_diagnostics() -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        from etl.observability import get_run_diagnostics as obs_diag
        latest, w = get_latest_run()
        warnings.extend(w)
        if not latest:
            return {"found": False}, warnings
        return obs_diag(latest["run_id"]), warnings
    except Exception as exc:
        _warning(f"Run diagnostics unavailable: {exc}", warnings)
        return {"found": False}, warnings
