from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.db import engine
from app.services.pg_pipeline.diagrams import MERMAID, get_latest_diagrams

router = APIRouter(prefix="/diagrams", tags=["diagrams"])


@router.get("")
def list_diagrams():
    with engine.connect() as cxn:
        try:
            rows = cxn.execute(text("""
                SELECT id, diagram_type, created_at
                FROM meta.pipeline_diagrams
                ORDER BY created_at DESC
                LIMIT 20
            """)).mappings().all()
            if rows:
                return {"ok": True, "diagrams": [dict(row) for row in rows]}
        except Exception:
            pass
    return {
        "ok": True,
        "diagrams": [{"diagram_type": k, "created_at": None} for k in MERMAID],
    }


@router.get("/latest")
def get_latest_diagram():
    try:
        diagrams = get_latest_diagrams()
    except Exception:
        diagrams = {k: {"mermaid": v, "created_at": None} for k, v in MERMAID.items()}
    return {
        "ok": True,
        "conceptual": diagrams.get("conceptual", {}),
        "logical": diagrams.get("logical", {}),
        "physical": diagrams.get("physical", {}),
        "lineage": diagrams.get("lineage", {}),
        "diagram": {
            "diagram_type": "lineage",
            "diagram_content": diagrams.get("lineage", {}).get("mermaid", MERMAID["lineage"]),
        },
    }


@router.get("/{diagram_id}")
def get_diagram(diagram_id: int):
    with engine.connect() as cxn:
        diagram = cxn.execute(text("""
            SELECT id, diagram_type, diagram_content, created_at
            FROM meta.pipeline_diagrams
            WHERE id = :id
        """), {"id": diagram_id}).mappings().first()
        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")
    return {"ok": True, "diagram": dict(diagram)}
