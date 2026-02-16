# backend/app/routers/catalog.py
"""
Unified catalog API: files, tables by layer (bronze/silver/gold), diagnostics.
Single source of truth; no separate v1-catalog.
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from typing import Any, Dict, List, Optional

from app.core.db import engine
from app.models.data_catalog import refresh_available_tables

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _redact_url(url: str) -> str:
    if not url:
        return ""
    try:
        if "@" in url:
            pre, rest = url.split("@", 1)
            if "://" in pre:
                scheme = pre.split("://")[0] + "://"
                return f"{scheme}***:***@{rest}"
        return url.split("?")[0][:80] + ("..." if len(url) > 80 else "")
    except Exception:
        return "***"


@router.get("/diagnostics")
def catalog_diagnostics():
    """
    Return which DB URL (redacted) and schema is used per layer (bronze/silver/gold).
    Use to verify each layer points to the correct DB/schema.
    """
    layers = {}
    try:
        from etl.config import get_bronze_engine, get_silver_engine, get_gold_engine
        for name, getter in [("bronze", get_bronze_engine), ("silver", get_silver_engine), ("gold", get_gold_engine)]:
            eng = getter()
            url = (str(eng.url) if hasattr(eng, "url") and eng.url else "") or os.getenv(f"{name.upper()}_DB_URL") or os.getenv("DATABASE_URL") or ""
            layers[name] = {"schema": name, "url_redacted": _redact_url(url), "engine_same_as": None}
        urls = [layers[k].get("url_redacted") or "" for k in ["bronze", "silver", "gold"]]
        if len(set(urls)) == 1 and urls[0]:
            for k in layers:
                layers[k]["engine_same_as"] = "single_db"
    except Exception as e:
        layers["error"] = str(e)
    return {"ok": True, "layers": layers}


@router.get("/files")
def list_downloaded_files(
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List all downloaded files with their processing status.
    
    Query params:
    - source_id: Filter by source (e.g., 'oil_production_status')
    - status: Filter by download status ('downloaded', 'failed', 'duplicate')
    - limit: Number of results (1-1000, default 100)
    - offset: Pagination offset
    """
    where_clauses = []
    params = {'limit': limit, 'offset': offset}
    
    if source_id:
        where_clauses.append("source_id = :source_id")
        params['source_id'] = source_id
    
    if status:
        where_clauses.append("download_status = :status")
        params['status'] = status
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    with engine.connect() as cxn:
        # Get total count
        count_result = cxn.execute(text(f"""
            SELECT COUNT(*) FROM data_catalog.downloaded_files {where_sql}
        """), params)
        total = count_result.scalar() or 0
        
        # Get files
        files = cxn.execute(text(f"""
            SELECT 
                id, source_id, source_name, file_url, file_path, filename,
                file_sha256, file_type, file_size, report_period,
                download_status, downloaded_at, processed_at, run_id,
                bronze_loaded, bronze_table, bronze_rows,
                silver_loaded, silver_table, silver_rows,
                warehouse_loaded, warehouse_tables, warehouse_rows,
                error_message, created_at, updated_at
            FROM data_catalog.downloaded_files
            {where_sql}
            ORDER BY downloaded_at DESC
            LIMIT :limit OFFSET :offset
        """), params).mappings().all()
    
    return {
        "ok": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "files": [dict(f) for f in files]
    }


@router.get("/files/{file_sha256}")
def get_file_details(file_sha256: str):
    """Get detailed information about a specific downloaded file."""
    with engine.connect() as cxn:
        file = cxn.execute(text("""
            SELECT 
                id, source_id, source_name, file_url, file_path, filename,
                file_sha256, file_type, file_size, report_period,
                download_status, downloaded_at, processed_at, run_id,
                bronze_loaded, bronze_table, bronze_rows,
                silver_loaded, silver_table, silver_rows,
                warehouse_loaded, warehouse_tables, warehouse_rows,
                error_message, created_at, updated_at
            FROM data_catalog.downloaded_files
            WHERE file_sha256 = :hash
        """), {"hash": file_sha256}).mappings().first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
    
    return {"ok": True, "file": dict(file)}


@router.get("/tables")
def list_available_tables(
    layer: Optional[str] = Query(None, description="Layer: bronze | silver | gold (preferred; returns canonical tables only)"),
    schema: Optional[str] = Query(None, description="Alias for layer: bronze | silver | gold"),
    table_type: Optional[str] = None,
    source_id: Optional[str] = None,
    include_deprecated: bool = Query(False, description="Include deprecated/legacy tables (debug only)"),
):
    """
    List available tables. When layer (or schema) is bronze/silver/gold, returns canonical
    tables only (no etl_ vs legacy duplicates), with display_name, row_count, last_updated.
    Otherwise uses data_catalog.available_tables with table_type/source_id filters.
    """
    effective_layer = layer or schema
    if effective_layer and effective_layer in ("bronze", "silver", "gold"):
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
        layer_engine = get_engine_for_layer(effective_layer)
        tables = get_tables_for_layer(layer_engine, effective_layer, include_deprecated=include_deprecated)
        return {
            "ok": True,
            "layer": effective_layer,
            "schema": effective_layer,
            "tables": tables,
        }
    # Legacy Data Catalog: table_type bronze/silver/warehouse (or empty = all) → canonical layer data
    if not effective_layer and (not table_type or table_type in ("bronze", "silver", "warehouse", "catalog")):
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
        layers_to_fetch = []
        if not table_type or table_type == "bronze":
            layers_to_fetch.append(("bronze", "bronze"))
        if not table_type or table_type == "silver":
            layers_to_fetch.append(("silver", "silver"))
        if not table_type or table_type == "warehouse":
            layers_to_fetch.append(("gold", "warehouse"))
        if table_type == "catalog":
            layers_to_fetch = []  # catalog-only: fall through to data_catalog.available_tables
        legacy_tables = []
        idx = 0
        for layer, table_type_out in layers_to_fetch:
            try:
                layer_engine = get_engine_for_layer(layer)
                rows = get_tables_for_layer(layer_engine, layer, include_deprecated=False)
                for t in rows:
                    idx += 1
                    legacy_tables.append({
                        "id": idx,
                        "schema_name": layer,
                        "table_name": t["physical_name"],
                        "full_name": f"{layer}.{t['physical_name']}",
                        "table_type": table_type_out,
                        "source_id": None,
                        "description": t.get("description") or "",
                        "row_count": t.get("row_count", 0),
                        "last_updated": t.get("last_updated"),
                        "created_at": None,
                    })
            except Exception:
                pass
        if legacy_tables or (table_type and table_type != "catalog"):
            return {"ok": True, "tables": legacy_tables}
        # table_type == "catalog" with no v1 layers -> fall through

    # Legacy: data_catalog.available_tables (e.g. table_type=catalog only, or no match)
    where_clauses = []
    params = {}
    if table_type:
        where_clauses.append("table_type = :table_type")
        params["table_type"] = table_type
    if source_id:
        where_clauses.append("source_id = :source_id")
        params["source_id"] = source_id
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    with engine.connect() as cxn:
        tables = cxn.execute(text(f"""
            SELECT 
                id, schema_name, table_name, full_name, table_type,
                source_id, description, row_count, last_updated, created_at
            FROM data_catalog.available_tables
            {where_sql}
            ORDER BY table_type, schema_name, table_name
        """), params).mappings().all()
    return {
        "ok": True,
        "tables": [dict(t) for t in tables],
    }


@router.get("/tables/{schema_name}/{table_name}")
def get_table_details(schema_name: str, table_name: str):
    """Get detailed information about a specific table. Canonical tables (bronze/silver/gold) use v1 catalog."""
    full_name = f"{schema_name}.{table_name}"
    # Canonical layers: serve from v1 catalog (correct counts, no legacy table names)
    if schema_name in ("bronze", "silver", "gold"):
        from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer
        layer_engine = get_engine_for_layer(schema_name)
        tables = get_tables_for_layer(layer_engine, schema_name, include_deprecated=False)
        match = next((t for t in tables if t["physical_name"] == table_name), None)
        if not match:
            raise HTTPException(status_code=404, detail="Table not found in catalog")
        table_type = "warehouse" if schema_name == "gold" else schema_name
        table_info = {
            "id": 0,
            "schema_name": schema_name,
            "table_name": table_name,
            "full_name": full_name,
            "table_type": table_type,
            "source_id": None,
            "description": match.get("description") or "",
            "row_count": match.get("row_count", 0),
            "last_updated": match.get("last_updated"),
            "created_at": None,
        }
        try:
            with layer_engine.connect() as cxn:
                row_count = cxn.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                ).scalar() or 0
        except Exception:
            row_count = match.get("row_count", 0)
        try:
            with layer_engine.connect() as cxn:
                columns = cxn.execute(
                    text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = :schema AND table_name = :table
                        ORDER BY ordinal_position
                    """),
                    {"schema": schema_name, "table": table_name},
                ).mappings().all()
        except Exception:
            columns = []
        return {
            "ok": True,
            "table": table_info,
            "actual_row_count": row_count,
            "columns": [dict(c) for c in columns],
        }

    # Legacy: resolve from data_catalog.available_tables
    with engine.connect() as cxn:
        table_info = cxn.execute(text("""
            SELECT id, schema_name, table_name, full_name, table_type,
                source_id, description, row_count, last_updated, created_at
            FROM data_catalog.available_tables
            WHERE full_name = :full_name
        """), {"full_name": full_name}).mappings().first()
        if not table_info:
            raise HTTPException(status_code=404, detail="Table not found in catalog")
        try:
            row_count = cxn.execute(text(f"SELECT COUNT(*) FROM {full_name}")).scalar() or 0
        except Exception:
            row_count = 0
        try:
            columns = cxn.execute(
                text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """),
                {"schema": schema_name, "table": table_name},
            ).mappings().all()
        except Exception:
            columns = []
    return {
        "ok": True,
        "table": dict(table_info),
        "actual_row_count": row_count,
        "columns": [dict(c) for c in columns],
    }


@router.post("/refresh")
def refresh_catalog():
    """Refresh the available_tables catalog from actual database tables."""
    try:
        refresh_available_tables()
        return {"ok": True, "message": "Catalog refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh catalog: {str(e)}")


# Canonical bronze tables for backfill (no deprecated legacy tables)
BACKFILL_BRONZE_SOURCE_TABLES = {
    "oil_production_status": "bronze.etl_oil_production_raw",
    "gas_production_status": "bronze.etl_gas_production_raw",
    "rig_disposition": "bronze.etl_rig_disposition_raw",
    "concession_situation": "bronze.etl_concessions_raw",  # primary; etl_concessions_sections has no file_sha256 typically
}


@router.post("/backfill")
def backfill_catalog_from_bronze():
    """
    Backfill the catalog with files from canonical bronze tables only.
    Does not resurrect deprecated legacy tables.
    """
    from app.models.data_catalog import register_downloaded_file, update_file_processing_status
    from app.services.sources import get_all_sources

    sources = get_all_sources()
    source_map = {s.source_id: s for s in sources}
    bronze_tables = BACKFILL_BRONZE_SOURCE_TABLES

    total_registered = 0
    total_updated = 0

    with engine.connect() as cxn:
        for source_id, bronze_table in bronze_tables.items():
            try:
                # Get all unique files from bronze table
                files = cxn.execute(text(f"""
                    SELECT DISTINCT 
                        source_id, source_url, file_url, file_sha256, 
                        report_period, extracted_at
                    FROM {bronze_table}
                    WHERE file_sha256 IS NOT NULL
                """)).mappings().all()
                
                source = source_map.get(source_id)
                source_name = source.name if source else source_id
                
                for file in files:
                    # Register file in catalog if not exists
                    try:
                        register_downloaded_file(
                            source_id=source_id,
                            source_name=source_name,
                            file_url=file['file_url'],
                            file_path=None,  # We don't have the path for old files
                            filename=file['file_url'].split('/')[-1],
                            file_sha256=file['file_sha256'],
                            file_type=file['file_url'].split('.')[-1] if '.' in file['file_url'] else 'unknown',
                            file_size=None,
                            report_period=str(file['report_period']) if file['report_period'] else None,
                            download_status='downloaded'
                        )
                        total_registered += 1
                    except Exception:
                        pass  # File might already exist
                    
                    # Update bronze status
                    try:
                        # Count rows for this file
                        row_count = cxn.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM {bronze_table}
                            WHERE file_sha256 = :hash
                        """), {"hash": file['file_sha256']}).scalar() or 0
                        
                        update_file_processing_status(
                            file_sha256=file['file_sha256'],
                            bronze_loaded=True,
                            bronze_table=bronze_table,
                            bronze_rows=row_count,
                            processed_at=str(file['extracted_at']) if file['extracted_at'] else None
                        )
                        total_updated += 1
                    except Exception:
                        pass
                        
            except Exception as e:
                # Table might not exist or have no data
                continue
    
    # Also refresh available tables
    try:
        refresh_available_tables()
    except Exception:
        pass
    
    return {
        "ok": True,
        "message": f"Backfilled catalog: {total_registered} files registered, {total_updated} files updated with bronze status"
    }


@router.get("/summary")
def get_catalog_summary():
    """Get a summary of the data catalog."""
    with engine.connect() as cxn:
        # File statistics
        file_stats = cxn.execute(text("""
            SELECT 
                download_status,
                COUNT(*) as count,
                SUM(CASE WHEN bronze_loaded THEN 1 ELSE 0 END) as bronze_count,
                SUM(CASE WHEN silver_loaded THEN 1 ELSE 0 END) as silver_count,
                SUM(CASE WHEN warehouse_loaded THEN 1 ELSE 0 END) as warehouse_count
            FROM data_catalog.downloaded_files
            GROUP BY download_status
        """)).mappings().all()
        
        # Source statistics
        source_stats = cxn.execute(text("""
            SELECT 
                source_id,
                source_name,
                COUNT(*) as total_files,
                SUM(CASE WHEN download_status = 'downloaded' THEN 1 ELSE 0 END) as downloaded,
                SUM(CASE WHEN download_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN download_status = 'duplicate' THEN 1 ELSE 0 END) as duplicates,
                SUM(bronze_rows) as total_bronze_rows,
                SUM(silver_rows) as total_silver_rows,
                SUM(warehouse_rows) as total_warehouse_rows
            FROM data_catalog.downloaded_files
            GROUP BY source_id, source_name
            ORDER BY source_id
        """)).mappings().all()
        
        # Table statistics
        table_stats = cxn.execute(text("""
            SELECT 
                table_type,
                COUNT(*) as table_count,
                SUM(row_count) as total_rows
            FROM data_catalog.available_tables
            GROUP BY table_type
        """)).mappings().all()
    
    return {
        "ok": True,
        "file_statistics": [dict(f) for f in file_stats],
        "source_statistics": [dict(s) for s in source_stats],
        "table_statistics": [dict(t) for t in table_stats]
    }


@router.get("/quick-summary")
def get_quick_summary():
    """
    Quick summary endpoint - optimized for fast response during/after downloads.
    Returns basic counts without heavy aggregations.
    """
    with engine.connect() as cxn:
        # Quick counts - no heavy GROUP BY
        total_files = cxn.execute(text("""
            SELECT COUNT(*) FROM data_catalog.downloaded_files
        """)).scalar() or 0
        
        downloaded_count = cxn.execute(text("""
            SELECT COUNT(*) FROM data_catalog.downloaded_files 
            WHERE download_status = 'downloaded'
        """)).scalar() or 0
        
        # Count by source (simple, fast)
        source_counts = {}
        for source_id in ['oil_production_status', 'gas_production_status', 'concession_situation', 'rig_disposition']:
            count = cxn.execute(text("""
                SELECT COUNT(*) FROM data_catalog.downloaded_files 
                WHERE source_id = :source_id AND download_status = 'downloaded'
            """), {"source_id": source_id}).scalar() or 0
            source_counts[source_id] = count
        
        # Recent downloads (last 5 minutes)
        recent_count = cxn.execute(text("""
            SELECT COUNT(*) FROM data_catalog.downloaded_files 
            WHERE downloaded_at > now() - INTERVAL '5 minutes'
        """)).scalar() or 0
    
    return {
        "ok": True,
        "total_files": total_files,
        "downloaded_files": downloaded_count,
        "recent_downloads_5min": recent_count,
        "by_source": source_counts,
        "timestamp": datetime.now().isoformat()
    }
