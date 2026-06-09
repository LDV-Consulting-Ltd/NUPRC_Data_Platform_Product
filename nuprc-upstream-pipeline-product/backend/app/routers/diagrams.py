from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine
from app.services.v1_diagram_service import PIPELINE_FLOW_MERMAID

router = APIRouter(prefix="/diagrams", tags=["diagrams"])

FALLBACK_MERMAID = PIPELINE_FLOW_MERMAID


def _fallback_payload(status: str, message: str, table_source: str) -> dict:
    return {
        "ok": True,
        "status": status,
        "message": message,
        "diagram": None,
        "source": "generated_fallback",
        "table_source": table_source,
        "is_fallback": True,
        "fallback_diagram": {
            "diagram_type": "pipeline_flow",
            "diagram_content": FALLBACK_MERMAID,
            "created_at": None,
        },
        "suggested_action": "Run diagram generation or use static lineage from catalog metadata.",
    }


@router.post("/generate")
def generate_diagrams():
    """Generate and store v1 pipeline diagrams without running a full ETL."""
    from app.services.v1_diagram_service import store_v1_diagrams_after_run
    result = store_v1_diagrams_after_run(run_id=None)
    if not result.get("ok"):
        return {
            "ok": True,
            "status": "degraded",
            "message": result.get("warning") or "Diagram generation failed.",
            "diagram": None,
            "source": "pipeline_diagrams",
            "is_fallback": False,
            "technical_details": result,
        }
    return {
        "ok": True,
        "status": "available",
        "message": "Diagrams generated and stored.",
        "stored": result.get("stored", []),
        "source": "pipeline_diagrams",
        "is_fallback": False,
    }


@router.get("/latest")
def get_latest_diagram():
    """Return latest stored diagram or a graceful empty/fallback response. Never raises."""
    try:
        with engine.connect() as cxn:
            table_reg = cxn.execute(
                text("SELECT to_regclass('public.pipeline_diagrams')")
            ).scalar()
            if not table_reg:
                return _fallback_payload(
                    "unavailable",
                    "pipeline_diagrams table is not present. Run the v1 pipeline once to generate diagrams.",
                    "pipeline_diagrams",
                )

            row = cxn.execute(text("""
                SELECT id, diagram_type, diagram_content, created_at
                FROM pipeline_diagrams
                ORDER BY
                    CASE diagram_type
                        WHEN 'pipeline_flow' THEN 0
                        WHEN 'v1_data_model' THEN 1
                        ELSE 2
                    END,
                    created_at DESC
                LIMIT 1
            """)).mappings().first()
    except Exception as exc:
        return _fallback_payload(
            "unavailable",
            f"Could not read pipeline_diagrams: {exc}",
            "pipeline_diagrams",
        )

    if not row:
        return _fallback_payload(
            "empty",
            "No generated pipeline diagram is available yet.",
            "pipeline_diagrams",
        )

    item = dict(row)
    if item.get("created_at") is not None:
        item["created_at"] = str(item["created_at"])
    return {
        "ok": True,
        "status": "available",
        "message": None,
        "diagram": item,
        "source": "pipeline_diagrams",
        "is_fallback": False,
    }
