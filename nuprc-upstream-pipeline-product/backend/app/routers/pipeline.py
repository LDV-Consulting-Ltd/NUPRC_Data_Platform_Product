# backend/app/routers/pipeline.py
"""
Deprecated: old pipeline API. All endpoints forward to v1-pipeline (/v1/pipeline/*).
Use v1-pipeline directly. This facade keeps old callers working.
"""
import uuid
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _v1_start_run(mode: str = "full") -> Dict[str, Any]:
    """Start a v1 pipeline run. Returns { ok, run_id, status, mode }."""
    run_id = str(uuid.uuid4())
    try:
        from etl import observability
        observability.init_observability_schema()
        observability.create_run(run_id, mode, triggered_by="api")
    except Exception as e:
        raise HTTPException(status_code=500, detail={"user_message": "Failed to start pipeline run.", "technical_details": {"error": str(e)}})

    def run():
        from etl.run import run_etl
        run_etl(mode, triggered_by="api", run_id=run_id)

    t = threading.Thread(target=run, daemon=False)
    t.start()
    return {"ok": True, "run_id": run_id, "status": "running", "mode": mode}


@router.get("/test")
def test_pipeline_endpoint():
    """Forward to v1 pipeline test. Use GET /v1/pipeline/test."""
    try:
        from app.routers.v1_pipeline import pipeline_test
        return pipeline_test()
    except Exception as e:
        return {"ok": False, "checks": {"error": str(e)}}


@router.post("/run")
def run_pipeline(
    source_ids: Optional[List[str]] = Query(None),
):
    """
    Deprecated: use POST /v1/pipeline/runs with body { "mode": "full" }.
    Starts a full pipeline run via v1 and returns old response shape.
    """
    # Map source_ids to mode: all or specific -> always "full" for compatibility
    mode = "full"
    data = _v1_start_run(mode=mode)
    return {
        "ok": True,
        "run_id": data["run_id"],
        "status": "RUNNING",
        "message": f"Pipeline started (v1). Use GET /v1/pipeline/runs/{data['run_id']} for status.",
        "requested_sources": source_ids or ["all"],
    }


@router.get("/runs")
def list_pipeline_runs():
    """Deprecated: use GET /v1/pipeline/runs. Returns runs from v1 (admin.etl_runs)."""
    try:
        from etl.config import get_etl_engine
        from sqlalchemy import text
    except ImportError:
        raise HTTPException(status_code=503, detail="ETL not available.")
    eng = get_etl_engine()
    with eng.connect() as cxn:
        rows = cxn.execute(text("""
            SELECT run_id, mode, status, started_at, ended_at, meta_json
            FROM admin.etl_runs
            ORDER BY started_at DESC
            LIMIT 50
        """)).mappings().all()
    runs = []
    for r in rows:
        meta = r.get("meta_json") or {}
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta) if meta else {}
            except Exception:
                meta = {}
        rows_loaded = meta.get("rows_loaded") if isinstance(meta, dict) else None
        runs.append({
            "run_id": r["run_id"],
            "pipeline_name": f"pipeline_{r.get('mode') or 'full'}",
            "status": (r.get("status") or "running").upper(),
            "started_at": r["started_at"],
            "ended_at": r["ended_at"],
            "rows_loaded": rows_loaded,
            "message": meta.get("message") if isinstance(meta, dict) else None,
        })
    return {"ok": True, "runs": runs}


@router.get("/runs/{run_id}")
def get_pipeline_run(run_id: str):
    """Deprecated: use GET /v1/pipeline/runs/{run_id}. Returns run and empty logs (v1 has steps instead)."""
    try:
        from etl.observability import get_run as get_etl_run
    except ImportError:
        raise HTTPException(status_code=503, detail="ETL not available.")
    run = get_etl_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    status = (run.get("status") or "running").upper()
    meta = run.get("meta_json") or {}
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta) if meta else {}
        except Exception:
            meta = {}
    return {
        "ok": True,
        "run": {
            "run_id": run_id,
            "pipeline_name": f"pipeline_{run.get('mode') or 'full'}",
            "status": status,
            "started_at": run.get("started_at"),
            "ended_at": run.get("ended_at"),
            "rows_loaded": meta.get("rows_loaded") if isinstance(meta, dict) else None,
            "message": meta.get("message") or meta.get("error") if isinstance(meta, dict) else None,
        },
        "requested_sources": [run.get("mode") or "full"],
        "logs": [],  # v1 uses steps; no legacy log table
    }


@router.post("/runs/{run_id}/cancel")
def cancel_pipeline_run(run_id: str):
    """Deprecated: use POST /v1/pipeline/runs/{run_id}/cancel."""
    try:
        from etl.observability import get_run as get_etl_run, cancel_run as obs_cancel_run
    except ImportError:
        raise HTTPException(status_code=503, detail="ETL not available.")
    run = get_etl_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if (run.get("status") or "").lower() != "running":
        raise HTTPException(status_code=400, detail=f"Run is not running (current status: {run.get('status')})")
    cancelled = obs_cancel_run(run_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail="Run could not be cancelled")
    return {"ok": True, "message": f"Run {run_id} cancelled successfully"}


@router.post("/clear-stuck-runs")
def clear_stuck_runs():
    """Deprecated: use POST /v1/pipeline/runs/clear-stuck."""
    try:
        from app.routers.v1_pipeline import clear_stuck_runs as v1_clear
        r = v1_clear()
        return {"ok": True, "message": f"Cleared {r.get('cleared', 0)} stuck run(s)", "cleared": r.get("cleared", 0), "run_ids": r.get("run_ids", [])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-blocking")
def check_blocking_runs(source_ids: Optional[List[str]] = Query(None)):
    """Deprecated: use GET /v1/pipeline/runs/blocking."""
    try:
        from app.routers.v1_pipeline import check_blocking_runs as v1_blocking
        r = v1_blocking()
        return {
            "ok": True,
            "requested_sources": source_ids or ["all"],
            "blocking_runs": [{"run_id": b["run_id"], "sources": [b.get("mode", "full")], "started_at": b.get("started_at"), "reason": "v1 single-run lock"} for b in r.get("blocking_runs", [])],
            "can_run": not r.get("blocking", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_pipeline_status():
    """Deprecated: use GET /v1/pipeline/platform/status. Returns status from v1 (admin.etl_runs + canonical tables)."""
    try:
        from app.routers.v1_pipeline import get_platform_status
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    plat = get_platform_status()
    latest = plat.get("latest_run")
    if latest:
        latest = dict(latest)
        meta = latest.get("meta_json")
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta) if meta else {}
            except Exception:
                meta = {}
        latest["rows_loaded"] = meta.get("rows_loaded") if isinstance(meta, dict) else None
    bronze_counts = {}
    gold_counts = {}
    try:
        eng_b = get_engine_for_layer("bronze")
        for t in get_tables_for_layer(eng_b, "bronze", include_deprecated=False):
            bronze_counts[f"bronze.{t['physical_name']}"] = t.get("row_count", 0)
        eng_g = get_engine_for_layer("gold")
        for t in get_tables_for_layer(eng_g, "gold", include_deprecated=False):
            gold_counts[f"gold.{t['physical_name']}"] = t.get("row_count", 0)
    except Exception:
        pass
    return {
        "ok": True,
        "latest_run": latest,
        "bronze_counts": bronze_counts,
        "warehouse_counts": gold_counts,
    }
