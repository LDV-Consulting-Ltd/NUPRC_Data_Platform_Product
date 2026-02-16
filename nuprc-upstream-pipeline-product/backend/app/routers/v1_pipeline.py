"""
V1 Pipeline API: ETL-backed runs with observability.
Canonical namespace: /v1/pipeline/...
Structured errors: user_message, technical_details.
Six canonical steps: source_scraping, file_acquisition, bronze_load, silver_transformation, warehouse_modeling, data_product_generation.
"""
import json
import uuid
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.db import engine
from sqlalchemy import text

router = APIRouter(prefix="/v1/pipeline", tags=["v1-pipeline"])

# Canonical step keys matching UI lifecycle (1–6)
CANONICAL_STEP_KEYS = [
    "source_scraping",
    "file_acquisition",
    "bronze_load",
    "silver_transformation",
    "warehouse_modeling",
    "data_product_generation",
]
CANONICAL_LABELS = [
    "1) Source Scraping",
    "2) File Acquisition",
    "3) Bronze Load",
    "4) Silver Transformation",
    "5) Warehouse Modeling",
    "6) Data Product Generation",
]

# Map ETL step_key to canonical index (0–5). ETL has: acquire, acquire_*, bronze, silver, gold, data_product_generation.
ETL_STEP_TO_CANONICAL = {
    "acquire": (0, 1),  # covers 1 and 2
    "acquire_oil": (0, 1),
    "acquire_gas": (0, 1),
    "acquire_rig": (0, 1),
    "acquire_concession": (0, 1),
    "bronze": (2, 2),
    "silver": (3, 3),
    "gold": (4, 4),
    "data_product_generation": (5, 5),
}
STUCK_RUN_HOURS = 3


class StartRunBody(BaseModel):
    mode: str = "full"  # full | oil | gas | rig | concession | retry_failed_sources


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


def _build_canonical_steps(run: dict, raw_steps: List[dict]) -> List[dict]:
    """Build 6 canonical steps from run status and ETL raw steps. status: waiting|running|done|failed|cancelled."""
    run_status = (run.get("status") or "running").lower()
    steps = []
    step_done_up_to = -1  # index of last step that is done
    failed_step = None  # index of first failed step
    for raw in raw_steps:
        sk = (raw.get("step_key") or "").lower()
        st = (raw.get("status") or "").lower()
        if sk in ETL_STEP_TO_CANONICAL:
            start_idx, end_idx = ETL_STEP_TO_CANONICAL[sk]
            if st == "success":
                for i in range(start_idx, end_idx + 1):
                    step_done_up_to = max(step_done_up_to, i)
            elif st == "failed":
                if failed_step is None:
                    failed_step = end_idx
    # data_product_generation (index 5) is done only when run is success
    if run_status == "success":
        step_done_up_to = max(step_done_up_to, 5)
    if run_status == "cancelled":
        pass  # leave step_done_up_to as is
    if run_status == "failed" and failed_step is None:
        failed_step = step_done_up_to + 1 if step_done_up_to < 5 else None
    for i in range(6):
        step_key = CANONICAL_STEP_KEYS[i]
        label = CANONICAL_LABELS[i]
        if failed_step is not None and i == failed_step:
            status = "failed"
        elif i <= step_done_up_to:
            status = "done"
        elif i == step_done_up_to + 1 and run_status == "running":
            status = "running"
        elif run_status == "cancelled" and i > step_done_up_to:
            status = "cancelled"
        else:
            status = "waiting"
        # Find raw step for started_at/ended_at/duration/metrics/error
        started_at = None
        ended_at = None
        duration_seconds = None
        metrics = {}
        error = None
        for raw in raw_steps:
            sk = (raw.get("step_key") or "").lower()
            if sk in ETL_STEP_TO_CANONICAL:
                start_idx, end_idx = ETL_STEP_TO_CANONICAL[sk]
                if start_idx <= i <= end_idx:
                    started_at = raw.get("started_at")
                    ended_at = raw.get("ended_at")
                    if started_at and ended_at:
                        try:
                            if hasattr(ended_at, "timestamp") and hasattr(started_at, "timestamp"):
                                duration_seconds = int(ended_at.timestamp() - started_at.timestamp())
                            else:
                                end_ts = ended_at if isinstance(ended_at, (int, float)) else None
                                start_ts = started_at if isinstance(started_at, (int, float)) else None
                                if end_ts is not None and start_ts is not None:
                                    duration_seconds = int(end_ts - start_ts)
                        except Exception:
                            pass
                    m = raw.get("metrics_json")
                    if m and isinstance(m, dict):
                        metrics = m
                    elif isinstance(m, str):
                        try:
                            metrics = json.loads(m) if m else {}
                        except Exception:
                            pass
                    err = raw.get("error_json")
                    if err and isinstance(err, dict):
                        error = err.get("message", str(err))
                    elif isinstance(err, str):
                        try:
                            err_d = json.loads(err) if err else {}
                            error = err_d.get("message", err) if isinstance(err_d, dict) else err
                        except Exception:
                            error = err
                    break
        steps.append({
            "step_key": step_key,
            "label": label,
            "status": status,
            "started_at": str(started_at) if started_at else None,
            "ended_at": str(ended_at) if ended_at else None,
            "duration_seconds": duration_seconds,
            "metrics": metrics,
            "error": error,
        })
    return steps


@router.get("/test", response_model=Dict[str, Any])
def pipeline_test():
    """Health/test endpoint. Returns ok, timestamp, version."""
    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
    }


@router.get("/status", response_model=Dict[str, Any])
def get_status_alias():
    """Alias for GET /v1/pipeline/platform/status."""
    return get_platform_status()


@router.post("/runs", response_model=Dict[str, Any])
def start_run(body: Optional[StartRunBody] = None):
    """Start an ETL run. Mode: full | oil | gas | rig | concession."""
    mode = (body and body.mode) or "full"
    if mode not in ("full", "oil", "gas", "rig", "concession", "retry_failed_sources"):
        raise HTTPException(status_code=400, detail={"user_message": "Invalid mode.", "technical_details": {"mode": mode}})
    etl_mode = "full" if mode == "retry_failed_sources" else mode
    run_id = str(uuid.uuid4())
    try:
        from etl import observability
        from etl.run import run_etl
        observability.init_observability_schema()
        observability.create_run(run_id, etl_mode, triggered_by="api")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "user_message": "Failed to start pipeline run.",
                "technical_details": {"error": str(e)},
            },
        )
    def run():
        from etl.run import run_etl
        run_etl(etl_mode, triggered_by="api", run_id=run_id)
    t = threading.Thread(target=run, daemon=False)
    t.start()
    return {"ok": True, "run_id": run_id, "status": "running", "mode": mode}


@router.get("/runs", response_model=Dict[str, Any])
def list_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
):
    """List pipeline runs (newest first). Query: limit, offset, status, mode."""
    try:
        from etl.config import get_etl_engine
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL not available.", "technical_details": {}})
    eng = get_etl_engine()
    where = []
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if status:
        where.append("status = :status")
        params["status"] = status
    if mode:
        where.append("mode = :mode")
        params["mode"] = mode
    where_sql = " AND ".join(where) if where else "1=1"
    with eng.connect() as cxn:
        total = cxn.execute(
            text(f"SELECT COUNT(*) FROM admin.etl_runs WHERE {where_sql}"),
            params,
        ).scalar() or 0
        rows = cxn.execute(
            text(f"""
                SELECT run_id, mode, status, started_at, ended_at, triggered_by, meta_json
                FROM admin.etl_runs WHERE {where_sql}
                ORDER BY started_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).mappings().all()
    runs = [dict(r) for r in rows]
    return {"ok": True, "runs": runs, "total": total, "limit": limit, "offset": offset}


@router.post("/runs/clear-stuck", response_model=Dict[str, Any])
def clear_stuck_runs():
    """Mark runs stuck in 'running' for > threshold hours as failed. Returns count cleared."""
    try:
        from etl.config import get_etl_engine
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL not available.", "technical_details": {}})
    threshold = datetime.now(timezone.utc) - timedelta(hours=STUCK_RUN_HOURS)
    eng = get_etl_engine()
    with eng.begin() as cxn:
        rows = cxn.execute(
            text("""
                SELECT run_id FROM admin.etl_runs
                WHERE status = 'running' AND started_at < :threshold
            """),
            {"threshold": threshold},
        ).mappings().all()
        run_ids = [r["run_id"] for r in rows]
        if not run_ids:
            return {"ok": True, "cleared": 0, "run_ids": [], "user_message": None}
        cxn.execute(
            text("""
                UPDATE admin.etl_runs
                SET status = 'failed', ended_at = now(),
                    meta_json = COALESCE(meta_json, '{}'::jsonb) || '{"reason": "stuck"}'::jsonb
                WHERE status = 'running' AND started_at < :threshold
            """),
            {"threshold": threshold},
        )
    return {"ok": True, "cleared": len(run_ids), "run_ids": run_ids, "user_message": None}


@router.get("/runs/blocking", response_model=Dict[str, Any])
def check_blocking_runs():
    """Return whether any run is blocking (single-run lock)."""
    try:
        from etl.config import get_etl_engine
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL not available.", "technical_details": {}})
    eng = get_etl_engine()
    blocking = []
    with eng.connect() as cxn:
        rows = cxn.execute(text("""
            SELECT run_id, mode, status, started_at
            FROM admin.etl_runs WHERE status = 'running'
            ORDER BY started_at DESC
        """)).mappings().all()
        for r in rows:
            blocking.append({
                "run_id": r["run_id"],
                "mode": r["mode"],
                "status": r["status"],
                "started_at": str(r["started_at"]) if r.get("started_at") else None,
            })
    return {
        "ok": True,
        "blocking_runs": blocking,
        "blocking": len(blocking) > 0,
        "user_message": None,
    }


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
def get_run(run_id: str):
    """Get run status and steps (progress). Returns 6 canonical steps for UI lifecycle."""
    try:
        from etl.observability import get_run as get_etl_run, get_run_steps
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL observability not available.", "technical_details": {}})
    run = get_etl_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"user_message": "Run not found.", "technical_details": {"run_id": run_id}})
    raw_steps = get_run_steps(run_id)
    steps = _build_canonical_steps(run, raw_steps)
    status = run.get("status") or "running"
    meta = _parse_meta(run.get("meta_json"))
    error = meta.get("error") if isinstance(meta, dict) else None
    return {
        "ok": True,
        "run_id": run_id,
        "mode": run.get("mode"),
        "status": status,
        "started_at": str(run.get("started_at")) if run.get("started_at") else None,
        "ended_at": str(run.get("ended_at")) if run.get("ended_at") else None,
        "steps": steps,
        "meta": meta,
        "user_message": error or (meta.get("message") if isinstance(meta, dict) else None),
        "technical_details": {"run_id": run_id, "steps_count": len(steps)},
    }


@router.post("/runs/{run_id}/cancel", response_model=Dict[str, Any])
def cancel_run(run_id: str):
    """Cancel a running run. Marks run as cancelled."""
    try:
        from etl.observability import get_run as get_etl_run, cancel_run as obs_cancel_run
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL observability not available.", "technical_details": {}})
    run = get_etl_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"user_message": "Run not found.", "technical_details": {"run_id": run_id}})
    if (run.get("status") or "").lower() != "running":
        raise HTTPException(status_code=400, detail={"user_message": "Run is not running.", "technical_details": {"status": run.get("status")}})
    cancelled = obs_cancel_run(run_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail={"user_message": "Run could not be cancelled (already finished?).", "technical_details": {}})
    updated = get_etl_run(run_id)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "cancelled",
        "run": dict(updated) if updated else None,
        "user_message": None,
    }


@router.get("/runs/{run_id}/diagnostics", response_model=Dict[str, Any])
def get_run_diagnostics(run_id: str):
    """Get run diagnostics for failure analysis."""
    try:
        from etl.observability import get_run_diagnostics
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL observability not available.", "technical_details": {}})
    diag = get_run_diagnostics(run_id)
    if not diag.get("found"):
        raise HTTPException(status_code=404, detail={"user_message": "Run not found.", "technical_details": {"run_id": run_id}})
    run = diag.get("run") or {}
    meta = run.get("meta_json") or {}
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta) if meta else {}
        except Exception:
            meta = {}
    error = meta.get("error") if isinstance(meta, dict) else None
    return {
        "ok": True,
        "run_id": run_id,
        "run": diag.get("run"),
        "steps": diag.get("steps", []),
        "user_message": error or "See steps for details.",
        "technical_details": diag,
    }


@router.get("/platform/status", response_model=Dict[str, Any])
def get_platform_status():
    """Platform status and latest run summary."""
    try:
        from etl.observability import get_run
        from etl.config import get_etl_engine
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL not available.", "technical_details": {}})
    latest_run = None
    try:
        eng = get_etl_engine()
        with eng.connect() as cxn:
            row = cxn.execute(text("""
                SELECT run_id, mode, status, started_at, ended_at, meta_json
                FROM admin.etl_runs ORDER BY started_at DESC LIMIT 1
            """)).mappings().first()
            if row:
                latest_run = dict(row)
    except Exception as e:
        pass
    return {
        "ok": True,
        "latest_run": latest_run,
        "user_message": None,
        "technical_details": {},
    }


@router.get("/sources/health", response_model=Dict[str, Any])
def get_sources_health():
    """Source health (bronze row counts as proxy for freshness)."""
    try:
        from etl.config import get_etl_engine
    except ImportError:
        raise HTTPException(status_code=503, detail={"user_message": "ETL not available.", "technical_details": {}})
    eng = get_etl_engine()
    sources = []
    tables = [
        ("oil_production_status", "Oil Production", "bronze.etl_oil_production_raw"),
        ("gas_production_status", "Gas Production", "bronze.etl_gas_production_raw"),
        ("rig_disposition", "Rig Disposition", "bronze.etl_rig_disposition_raw"),
        ("concession_situation", "Concession Status", "bronze.etl_concessions_raw"),
    ]
    for source_key, label, table in tables:
        try:
            with eng.connect() as cxn:
                count = cxn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
        except Exception:
            count = 0
        score = min(100, 50 + (count // 100)) if count else 40
        status = "fresh" if score >= 85 else "stable" if score >= 70 else "degraded" if score >= 50 else "down"
        sources.append({
            "source_key": source_key,
            "label": label,
            "status": status,
            "freshness_score": score,
            "row_count": count,
        })
    return {
        "ok": True,
        "sources": sources,
        "user_message": None,
        "technical_details": {},
    }


@router.get("/freshness", response_model=Dict[str, Any])
def get_gold_freshness():
    """Data freshness from Warehouse (Gold) layer only. Used by Control Panel Data Freshness cards."""
    try:
        from app.services.catalog_registry import get_engine_for_layer
        eng = get_engine_for_layer("gold")
    except Exception:
        raise HTTPException(status_code=503, detail={"user_message": "Gold layer not available.", "technical_details": {}})
    from datetime import datetime, timezone
    # Dataset-specific marts: gold_oil_fact_production, gold_gas_fact_production, gold_rig_fact_activity, gold_concession_fact_snapshot
    with eng.connect() as cxn:
        try:
            oil_cnt = cxn.execute(text("SELECT COUNT(*) FROM gold.gold_oil_fact_production")).scalar() or 0
            oil_max = cxn.execute(text(
                "SELECT MAX(d.date_actual) FROM gold.gold_oil_fact_production t JOIN gold.gold_dim_date d ON t.date_key = d.date_key"
            )).scalar()
        except Exception:
            oil_cnt = 0
            oil_max = None
        try:
            gas_cnt = cxn.execute(text("SELECT COUNT(*) FROM gold.gold_gas_fact_production")).scalar() or 0
            gas_max = cxn.execute(text(
                "SELECT MAX(d.date_actual) FROM gold.gold_gas_fact_production t JOIN gold.gold_dim_date d ON t.date_key = d.date_key"
            )).scalar()
        except Exception:
            gas_cnt = 0
            gas_max = None
        try:
            rig_cnt = cxn.execute(text("SELECT COUNT(*) FROM gold.gold_rig_fact_activity")).scalar() or 0
            rig_max = cxn.execute(text(
                "SELECT MAX(d.date_actual) FROM gold.gold_rig_fact_activity t JOIN gold.gold_dim_date d ON t.date_key = d.date_key"
            )).scalar()
        except Exception:
            rig_cnt = 0
            rig_max = None
        try:
            conc_cnt = cxn.execute(text("SELECT COUNT(*) FROM gold.gold_concession_fact_snapshot")).scalar() or 0
            conc_max = cxn.execute(text(
                "SELECT MAX(d.date_actual) FROM gold.gold_concession_fact_snapshot t JOIN gold.gold_dim_date d ON t.report_date_key = d.date_key"
            )).scalar()
        except Exception:
            conc_cnt = 0
            conc_max = None

    def freshness_score(count: int, max_date_iso: Optional[str], expected_hours: float) -> int:
        if count == 0:
            return 40
        base = min(100, 50 + (count // 100))
        if max_date_iso:
            try:
                dt = datetime.fromisoformat(max_date_iso.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if dt.tzinfo:
                    age_h = (now - dt).total_seconds() / 3600
                else:
                    age_h = (datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if age_h <= expected_hours * 0.5:
                    base = min(100, base + 25)
                elif age_h <= expected_hours:
                    base = min(100, base + 10)
                elif age_h <= expected_hours * 2:
                    base = max(50, base - 10)
                else:
                    base = max(40, base - 20)
            except Exception:
                pass
        return max(40, min(100, base))

    expected_oil_gas = 2 * 60  # 2h in minutes for expected_interval
    expected_rig = 6 * 60
    expected_conc = 24 * 60  # daily

    oil_iso = oil_max.isoformat() if oil_max and hasattr(oil_max, "isoformat") else (str(oil_max) if oil_max else None)
    gas_iso = gas_max.isoformat() if gas_max and hasattr(gas_max, "isoformat") else (str(gas_max) if gas_max else None)
    rig_iso = rig_max.isoformat() if rig_max and hasattr(rig_max, "isoformat") else (str(rig_max) if rig_max else None)

    conc_iso = conc_max.isoformat() if conc_max and hasattr(conc_max, "isoformat") else (str(conc_max) if conc_max else None)
    items = []
    for source_key, label, count, max_iso, expected_m in [
        ("oil_production_status", "Oil Production", oil_cnt, oil_iso, expected_oil_gas),
        ("gas_production_status", "Gas Production", gas_cnt, gas_iso, expected_oil_gas),
        ("rig_disposition", "Rig Disposition", rig_cnt, rig_iso, expected_rig),
        ("concession_situation", "Concession Status", conc_cnt, conc_iso, expected_conc),
    ]:
        score = freshness_score(count, max_iso, expected_m / 60)
        status = "fresh" if score >= 85 else "stable" if score >= 70 else "degraded" if score >= 50 else "down"
        items.append({
            "source_key": source_key,
            "label": label,
            "status": status,
            "freshness_score": score,
            "row_count": count,
            "last_updated": max_iso,
            "expected_interval_minutes": int(expected_m),
        })
    return {"ok": True, "sources": items}
