"""Meta-schema pipeline API helpers (PostgreSQL-first runs)."""
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.core.db import engine
from app.services.pg_pipeline import meta_log

META_STEP_TO_UI = {
    "source_discovery": ("source_scraping", "1) Source Scraping"),
    "file_acquisition": ("file_acquisition", "2) File Acquisition"),
    "bronze_load": ("bronze_load", "3) Bronze Load"),
    "silver_standardization": ("silver_transformation", "4) Silver Transformation"),
    "warehouse_load": ("warehouse_modeling", "5) Warehouse Modeling"),
    "data_product_refresh": ("data_product_generation", "6) Data Product Generation"),
}


def meta_run_exists(run_id: str) -> bool:
    with engine.connect() as cxn:
        row = cxn.execute(
            text("SELECT 1 FROM meta.pipeline_run WHERE run_id = :id"),
            {"id": run_id},
        ).first()
    return row is not None


def get_meta_run_response(run_id: str) -> Optional[Dict[str, Any]]:
    data = meta_log.get_run(run_id)
    if not data:
        return None
    run = data["run"]
    raw_steps = data["steps"]
    run_status = (run.get("status") or "RUNNING").lower()
    if run_status == "success":
        run_status = "success"
    elif run_status == "failed":
        run_status = "failed"
    elif run_status in ("queued", "running"):
        run_status = "running"
    else:
        run_status = run_status.lower()

    steps_by_name = {s["step_name"]: s for s in raw_steps}
    steps_out: List[Dict[str, Any]] = []
    running_idx = None
    done_up_to = -1
    for i, (meta_name, (ui_key, label)) in enumerate(META_STEP_TO_UI.items()):
        st = steps_by_name.get(meta_name, {})
        st_status = (st.get("status") or "").upper()
        if st_status == "SUCCESS":
            ui_status = "done"
            done_up_to = i
        elif st_status == "FAILED":
            ui_status = "failed"
        elif st_status == "RUNNING":
            ui_status = "running"
            running_idx = i
        else:
            ui_status = "waiting"
        steps_out.append({
            "step_key": ui_key,
            "label": label,
            "status": ui_status,
            "started_at": str(st.get("started_at")) if st.get("started_at") else None,
            "ended_at": str(st.get("ended_at")) if st.get("ended_at") else None,
            "duration_seconds": int(st["duration_seconds"]) if st.get("duration_seconds") else None,
            "metrics": {
                "rows_processed": st.get("rows_processed"),
                "files_processed": st.get("files_processed"),
            },
            "error": st.get("message"),
        })

    if run_status == "running" and running_idx is None:
        for i, s in enumerate(steps_out):
            if s["status"] == "waiting":
                s["status"] = "running"
                break

    return {
        "ok": True,
        "run_id": run_id,
        "mode": "full",
        "status": run_status,
        "started_at": str(run.get("started_at")) if run.get("started_at") else None,
        "ended_at": str(run.get("ended_at")) if run.get("ended_at") else None,
        "steps": steps_out,
        "meta": {"rows_loaded": run.get("rows_loaded"), "pipeline": "pg"},
        "user_message": run.get("message"),
    }


def get_meta_diagnostics(run_id: str) -> Optional[Dict[str, Any]]:
    data = meta_log.get_run(run_id)
    if not data:
        return None
    return {
        "ok": True,
        "run_id": run_id,
        "run": dict(data["run"]),
        "steps": data["steps"],
        "schema_drift": data["schema_drift"],
        "current_step": _current_step(data["steps"]),
        "user_message": data["run"].get("message"),
    }


def _current_step(steps: List[dict]) -> Optional[str]:
    for s in steps:
        if (s.get("status") or "").upper() == "RUNNING":
            return s.get("step_name")
    return None


def list_meta_runs(limit: int, offset: int) -> Dict[str, Any]:
    with engine.connect() as cxn:
        total = cxn.execute(text("SELECT COUNT(*) FROM meta.pipeline_run")).scalar() or 0
        rows = cxn.execute(
            text("""
                SELECT run_id, pipeline_name, status, started_at, ended_at, rows_loaded, message
                FROM meta.pipeline_run
                ORDER BY started_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        ).mappings().all()
    return {
        "ok": True,
        "runs": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def _normalize_status(status: str | None) -> str:
    s = (status or "").lower()
    if s in ("success", "succeeded"):
        return "success"
    if s in ("failed", "failure"):
        return "failed"
    if s in ("running", "queued"):
        return "running"
    if s == "cancelled":
        return "cancelled"
    return s or "unknown"


def _parse_rows_loaded(run: dict) -> int:
    if run.get("rows_loaded") is not None:
        try:
            return int(run["rows_loaded"])
        except (TypeError, ValueError):
            pass
    meta = run.get("meta_json")
    if isinstance(meta, dict) and "rows_loaded" in meta:
        try:
            return int(meta["rows_loaded"])
        except (TypeError, ValueError):
            pass
    if isinstance(meta, str):
        import json
        try:
            m = json.loads(meta)
            if isinstance(m, dict) and "rows_loaded" in m:
                return int(m["rows_loaded"])
        except Exception:
            pass
    return 0


def list_all_pipeline_runs(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Merge meta.pipeline_run and admin.etl_runs (dedupe by run_id, newest first)."""
    merged: Dict[str, dict] = {}

    with engine.connect() as cxn:
        try:
            meta_rows = cxn.execute(
                text("""
                    SELECT run_id, pipeline_name AS mode, status, started_at, ended_at,
                           rows_loaded, message, NULL::jsonb AS meta_json, 'meta' AS source
                    FROM meta.pipeline_run
                    ORDER BY started_at DESC NULLS LAST
                """)
            ).mappings().all()
            for r in meta_rows:
                d = dict(r)
                d["status"] = _normalize_status(d.get("status"))
                merged[d["run_id"]] = d
        except Exception:
            pass

        try:
            admin_rows = cxn.execute(
                text("""
                    SELECT run_id, mode, status, started_at, ended_at, meta_json,
                           NULL::bigint AS rows_loaded, NULL::text AS message, 'admin' AS source
                    FROM admin.etl_runs
                    ORDER BY started_at DESC NULLS LAST
                """)
            ).mappings().all()
            for r in admin_rows:
                d = dict(r)
                d["status"] = _normalize_status(d.get("status"))
                rid = d["run_id"]
                if rid in merged:
                    continue
                if d.get("rows_loaded") is None:
                    d["rows_loaded"] = _parse_rows_loaded(d)
                merged[rid] = d
        except Exception:
            pass

    runs = sorted(
        merged.values(),
        key=lambda x: x.get("started_at") or "",
        reverse=True,
    )
    total = len(runs)
    page = runs[offset : offset + limit]
    for r in page:
        if r.get("rows_loaded") is None:
            r["rows_loaded"] = _parse_rows_loaded(r)
        if isinstance(r.get("started_at"), object) and hasattr(r["started_at"], "isoformat"):
            r["started_at"] = r["started_at"].isoformat()
        if isinstance(r.get("ended_at"), object) and r.get("ended_at") and hasattr(r["ended_at"], "isoformat"):
            r["ended_at"] = r["ended_at"].isoformat()

    return {"ok": True, "runs": page, "total": total, "limit": limit, "offset": offset}


def get_platform_status_payload() -> Dict[str, Any]:
    """Latest run + last successful run + today's row counts from all run stores."""
    from datetime import datetime, timezone

    listed = list_all_pipeline_runs(limit=200, offset=0)
    runs = listed.get("runs") or []
    latest = runs[0] if runs else None
    last_success = next((r for r in runs if r.get("status") == "success"), None)

    today = datetime.now(timezone.utc).date()
    records_today = 0
    for r in runs:
        st = r.get("started_at")
        if not st:
            continue
        try:
            d = datetime.fromisoformat(str(st).replace("Z", "+00:00")).date()
        except Exception:
            continue
        if d == today and r.get("status") == "success":
            records_today += _parse_rows_loaded(r)

    if records_today == 0 and last_success:
        records_today = _parse_rows_loaded(last_success)

    latest_run = None
    if latest:
        latest_run = {
            "run_id": latest.get("run_id"),
            "mode": latest.get("mode") or "full",
            "status": latest.get("status"),
            "started_at": latest.get("started_at"),
            "ended_at": latest.get("ended_at"),
            "meta_json": {"rows_loaded": _parse_rows_loaded(latest)},
        }

    return {
        "ok": True,
        "latest_run": latest_run,
        "last_successful_run": last_success,
        "records_today": records_today,
        "system_health": "degraded" if latest and latest.get("status") == "failed" else "healthy",
    }
