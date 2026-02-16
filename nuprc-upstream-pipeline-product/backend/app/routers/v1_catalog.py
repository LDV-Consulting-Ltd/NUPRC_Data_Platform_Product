"""
Deprecated: use /catalog/* instead. This module provides /v1/catalog/* as an alias
so existing callers do not break. All logic lives in the unified catalog (catalog router + catalog_registry).
"""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


@router.get("/diagnostics", response_model=Dict[str, Any])
def catalog_diagnostics_alias():
    """Alias for GET /catalog/diagnostics. Use /catalog/diagnostics."""
    from app.routers.catalog import catalog_diagnostics
    return catalog_diagnostics()


@router.get("/tables", response_model=Dict[str, Any])
def list_tables_by_layer_alias(
    layer: str = Query(..., description="Layer: bronze | silver | gold"),
    include_deprecated: bool = Query(False, description="Include deprecated tables (debug only)"),
):
    """Alias for GET /catalog/tables?layer=. Use /catalog/tables?layer=bronze|silver|gold."""
    if layer not in ("bronze", "silver", "gold"):
        raise HTTPException(
            status_code=400,
            detail={"user_message": "Invalid layer. Use bronze, silver, or gold.", "technical_details": {"layer": layer}},
        )
    from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
    layer_engine = get_engine_for_layer(layer)
    tables = get_tables_for_layer(layer_engine, layer, include_deprecated=include_deprecated)
    return {"ok": True, "layer": layer, "schema": layer, "tables": tables}
