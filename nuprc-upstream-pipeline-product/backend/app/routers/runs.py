import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/runs", tags=["runs"])


def _mark_success(run_id: str, rows_loaded: int):
    with engine.begin() as cxn:
        cxn.execute(text("""
            UPDATE pipeline_run
            SET status='SUCCESS', ended_at=now(), rows_loaded=:rows, message=NULL
            WHERE run_id=:rid
        """), {"rid": run_id, "rows": int(rows_loaded or 0)})


def _mark_failed(run_id: str, err: Exception):
    msg = str(err)
    if len(msg) > 2000:
        msg = msg[:2000] + "…"
    with engine.begin() as cxn:
        cxn.execute(text("""
            UPDATE pipeline_run
            SET status='FAILED', ended_at=now(), message=:msg
            WHERE run_id=:rid
        """), {"rid": run_id, "msg": msg})


def _parse_meta(meta: Any) -> dict:
    if meta is None:
        return {}
    if isinstance(meta, dict):
        return meta
    if isinstance(meta, str):
        try:
            return json.loads(meta) if meta else {}
        except Exception:
            return {}
    return {}


def _serialize_run_row(row: dict) -> dict:
    item = dict(row)
    for key in ("started_at", "ended_at"):
        if item.get(key) is not None and hasattr(item[key], "isoformat"):
            item[key] = item[key].isoformat()
    meta = _parse_meta(item.pop("meta_json", None))
    item["rows_loaded"] = meta.get("rows_loaded") if isinstance(meta, dict) else None
    item["meta_json"] = meta
    return item


def _legacy_last_run_shape(row: Optional[dict]) -> Optional[dict]:
    if not row:
        return None
    item = _serialize_run_row(row)
    return {
        "run_id": item.get("run_id"),
        "pipeline_name": item.get("mode") or item.get("pipeline_name"),
        "status": (item.get("status") or "").upper(),
        "started_at": item.get("started_at"),
        "ended_at": item.get("ended_at"),
        "rows_loaded": item.get("rows_loaded") or 0,
        "message": item.get("message"),
        "mode": item.get("mode"),
    }


def _query_v1_summary() -> tuple[Optional[dict], list[str]]:
    warnings: list[str] = []
    try:
        from etl.config import get_etl_engine
        eng = get_etl_engine()
        with eng.connect() as cxn:
            total = int(cxn.execute(text("SELECT COUNT(*) FROM admin.etl_runs")).scalar() or 0)
            success = int(cxn.execute(text(
                "SELECT COUNT(*) FROM admin.etl_runs WHERE status = 'success'"
            )).scalar() or 0)
            failed = int(cxn.execute(text(
                "SELECT COUNT(*) FROM admin.etl_runs WHERE status = 'failed'"
            )).scalar() or 0)
            running = int(cxn.execute(text(
                "SELECT COUNT(*) FROM admin.etl_runs WHERE status = 'running'"
            )).scalar() or 0)
            last = cxn.execute(text("""
                SELECT run_id, mode, status, started_at, ended_at, meta_json, triggered_by
                FROM admin.etl_runs
                ORDER BY started_at DESC
                LIMIT 1
            """)).mappings().first()
        last_item = _serialize_run_row(dict(last)) if last else None
        return {
            "total_runs": total,
            "successful_runs": success,
            "failed_runs": failed,
            "running_runs": running,
            "success": success,
            "failed": failed,
            "running": running,
            "latest_run_id": last_item.get("run_id") if last_item else None,
            "latest_status": last_item.get("status") if last_item else None,
            "latest_started_at": last_item.get("started_at") if last_item else None,
            "latest_ended_at": last_item.get("ended_at") if last_item else None,
            "latest_rows_bronze": last_item.get("rows_loaded") if last_item else None,
            "last_run": _legacy_last_run_shape(dict(last)) if last else None,
            "source": "admin.etl_runs",
            "status": "ok",
        }, warnings
    except Exception as exc:
        warnings.append(f"admin.etl_runs unavailable: {exc}")
        return None, warnings


def _query_legacy_summary() -> tuple[Optional[dict], list[str]]:
    warnings: list[str] = []
    try:
        with engine.connect() as cxn:
            total = int(cxn.execute(text("SELECT COUNT(*) FROM pipeline_run")).scalar() or 0)
            success = int(cxn.execute(text(
                "SELECT COUNT(*) FROM pipeline_run WHERE status='SUCCESS'"
            )).scalar() or 0)
            failed = int(cxn.execute(text(
                "SELECT COUNT(*) FROM pipeline_run WHERE status='FAILED'"
            )).scalar() or 0)
            running = int(cxn.execute(text(
                "SELECT COUNT(*) FROM pipeline_run WHERE status='RUNNING'"
            )).scalar() or 0)
            last = cxn.execute(text("""
                SELECT run_id, pipeline_name, status, started_at, ended_at, rows_loaded, message
                FROM pipeline_run
                ORDER BY started_at DESC
                LIMIT 1
            """)).mappings().first()
        last_dict = dict(last) if last else None
        return {
            "total_runs": total,
            "successful_runs": success,
            "failed_runs": failed,
            "running_runs": running,
            "success": success,
            "failed": failed,
            "running": running,
            "latest_run_id": last_dict.get("run_id") if last_dict else None,
            "latest_status": (last_dict.get("status") or "").lower() if last_dict else None,
            "latest_started_at": str(last_dict.get("started_at")) if last_dict and last_dict.get("started_at") else None,
            "latest_ended_at": str(last_dict.get("ended_at")) if last_dict and last_dict.get("ended_at") else None,
            "latest_rows_bronze": last_dict.get("rows_loaded") if last_dict else None,
            "last_run": last_dict,
            "source": "pipeline_run",
            "status": "ok",
        }, warnings
    except Exception as exc:
        warnings.append(f"pipeline_run unavailable: {exc}")
        return None, warnings


def _build_summary_response() -> dict:
    warnings: list[str] = []
    payload, w = _query_v1_summary()
    warnings.extend(w)
    if payload:
        return {"ok": True, "warnings": warnings, **payload}

    legacy, w2 = _query_legacy_summary()
    warnings.extend(w2)
    if legacy:
        warnings.append("Fell back to legacy pipeline_run counts.")
        return {"ok": True, "warnings": warnings, **legacy}

    return {
        "ok": True,
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "running_runs": 0,
        "success": 0,
        "failed": 0,
        "running": 0,
        "latest_run_id": None,
        "latest_status": None,
        "latest_started_at": None,
        "latest_ended_at": None,
        "latest_rows_bronze": None,
        "last_run": None,
        "source": "unavailable",
        "status": "degraded",
        "warnings": warnings or ["No run data available from admin.etl_runs or pipeline_run."],
    }


@router.get("/summary/v1")
def runs_summary_v1():
    """Explicit v1 run summary from admin.etl_runs only."""
    payload, warnings = _query_v1_summary()
    if not payload:
        return {
            "ok": True,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "running_runs": 0,
            "latest_run_id": None,
            "latest_status": None,
            "latest_started_at": None,
            "latest_ended_at": None,
            "latest_rows_bronze": None,
            "source": "admin.etl_runs",
            "status": "degraded",
            "warnings": warnings,
        }
    return {"ok": True, "warnings": warnings, **payload}


@router.get("/summary")
def runs_summary():
    """Run summary — primarily admin.etl_runs (v1), with legacy pipeline_run fallback."""
    return _build_summary_response()


@router.get("/")
def list_runs():
    """Legacy list from pipeline_run. Use GET /v1/pipeline/runs for v1 history."""
    with engine.connect() as cxn:
        rows = cxn.execute(text("""
            SELECT run_id, pipeline_name, status, started_at, ended_at, rows_loaded, message
            FROM pipeline_run
            ORDER BY started_at DESC
            LIMIT 50
        """)).mappings().all()
    return {"ok": True, "runs": rows}
