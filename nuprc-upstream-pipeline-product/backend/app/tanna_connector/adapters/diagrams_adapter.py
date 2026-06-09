"""Read-only adapter for pipeline diagrams."""
from typing import Any, Optional


def get_latest_diagram() -> tuple[Optional[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import text
        from app.core.db import engine
        with engine.connect() as cxn:
            exists = cxn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'pipeline_diagrams'
                )
            """)).scalar()
            if not exists:
                warnings.append("pipeline_diagrams table does not exist")
                return None, warnings
            row = cxn.execute(text("""
                SELECT id, diagram_type, diagram_content, created_at
                FROM pipeline_diagrams
                ORDER BY created_at DESC
                LIMIT 1
            """)).mappings().first()
        if not row:
            warnings.append("No diagrams found in pipeline_diagrams")
            return None, warnings
        diagram = dict(row)
        if hasattr(diagram.get("created_at"), "isoformat"):
            diagram["created_at"] = diagram["created_at"].isoformat()
        return diagram, warnings
    except Exception as exc:
        warnings.append(f"Latest diagram unavailable: {exc}")
        return None, warnings


def get_static_mermaid_fallback() -> tuple[Optional[str], list[str]]:
    warnings: list[str] = []
    try:
        from app.services.diagram_generator import generate_mermaid_er_diagram
        return generate_mermaid_er_diagram(), warnings
    except Exception as exc:
        warnings.append(f"Static Mermaid fallback unavailable: {exc}")
        return None, warnings
