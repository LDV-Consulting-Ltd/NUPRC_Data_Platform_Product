from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.core.db import engine

router = APIRouter(prefix="/diagrams", tags=["diagrams"])


@router.get("")
def list_diagrams():
    """List all available diagrams."""
    with engine.connect() as cxn:
        rows = cxn.execute(text("""
            SELECT id, diagram_type, created_at
            FROM pipeline_diagrams
            ORDER BY created_at DESC
            LIMIT 10
        """)).mappings().all()
    return {"ok": True, "diagrams": [dict(row) for row in rows]}


@router.get("/latest")
def get_latest_diagram():
    """Get the most recent diagram."""
    with engine.connect() as cxn:
        diagram = cxn.execute(text("""
            SELECT id, diagram_type, diagram_content, created_at
            FROM pipeline_diagrams
            ORDER BY created_at DESC
            LIMIT 1
        """)).mappings().first()
        
        if not diagram:
            raise HTTPException(status_code=404, detail="No diagrams found. Run the pipeline first.")
        
    return {"ok": True, "diagram": dict(diagram)}


@router.get("/{diagram_id}")
def get_diagram(diagram_id: int):
    """Get a specific diagram by ID."""
    with engine.connect() as cxn:
        diagram = cxn.execute(text("""
            SELECT id, diagram_type, diagram_content, created_at
            FROM pipeline_diagrams
            WHERE id = :id
        """), {"id": diagram_id}).mappings().first()
        
        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")
        
    return {"ok": True, "diagram": dict(diagram)}
