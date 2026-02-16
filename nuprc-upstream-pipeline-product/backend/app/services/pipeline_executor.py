# backend/app/services/pipeline_executor.py
"""
Main pipeline execution logic that orchestrates all steps.
Uses async implementations for concurrent processing.
"""
import asyncio
from typing import List, Optional

from app.services.bronze_loader import load_to_bronze
from app.services.fuzzy_matcher import detect_schema_drift, log_schema_drift


def scrape_and_download_sources(run_id: str, log_func, source_ids: Optional[List[str]] = None) -> List[dict]:
    """
    Step 1: Scrape sources and download files (async wrapper).
    Uses async implementation for concurrent processing.
    
    Args:
        run_id: Run identifier
        log_func: Logging function
        source_ids: Optional list of source IDs to process. If None, processes all sources.
    """
    print(f"   [scrape_and_download_sources] Starting...")
    from app.services.async_pipeline_executor import scrape_and_download_sources_async
    
    # Create new event loop for background task (FastAPI runs in thread pool)
    print(f"   [scrape_and_download_sources] Creating event loop...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print(f"   [scrape_and_download_sources] Running async function...")
        # Add overall timeout (10 minutes max for scraping + downloading)
        result = loop.run_until_complete(
            asyncio.wait_for(
                scrape_and_download_sources_async(run_id, log_func, source_ids),
                timeout=600.0  # 10 minutes max
            )
        )
        print(f"   [scrape_and_download_sources] Complete: {len(result) if result else 0} files")
        return result
    except asyncio.TimeoutError:
        print(f"   [scrape_and_download_sources] TIMEOUT after 10 minutes")
        log_func(run_id, "ERROR", "Scraping/downloading timed out after 10 minutes")
        return []
    except Exception as e:
        print(f"   [scrape_and_download_sources] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        log_func(run_id, "ERROR", f"Scraping/downloading failed: {str(e)}")
        return []
    finally:
        loop.close()
        print(f"   [scrape_and_download_sources] Event loop closed")


def extract_and_load_bronze(downloaded_files: List[dict], run_id: str, log_func) -> int:
    """
    Step 2: Extract tables from files and load into bronze layer (async wrapper).
    Uses async implementation for concurrent processing.
    """
    from app.services.async_pipeline_executor import extract_and_load_bronze_async
    
    # Create new event loop for background task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Add overall timeout (30 minutes max for extraction + loading)
        return loop.run_until_complete(
            asyncio.wait_for(
                extract_and_load_bronze_async(downloaded_files, run_id, log_func),
                timeout=1800.0  # 30 minutes max
            )
        )
    except asyncio.TimeoutError:
        log_func(run_id, "ERROR", "Extraction/loading timed out after 30 minutes")
        return 0
    finally:
        loop.close()


def transform_to_silver(run_id: str, log_func):
    """
    Step 3: Transform bronze data to silver layer with fuzzy matching.
    """
    from app.services.silver_transformer import transform_bronze_to_silver
    
    transform_bronze_to_silver(run_id, log_func)


def load_warehouse(run_id: str, log_func):
    """
    Step 4: Load warehouse dimensional model from silver.
    """
    from app.services.warehouse_loader import populate_dimensions, populate_fact_tables
    from sqlalchemy import text
    from app.core.db import engine
    
    log_func(run_id, "INFO", "Loading warehouse dimensional model...")
    
    # Ensure dim_date is populated
    with engine.begin() as cxn:
        cxn.execute(text("""
            INSERT INTO warehouse.dim_date (date_key, date_actual, day_of_week, day_name, month, month_name, quarter, year)
            SELECT 
                TO_CHAR(d, 'YYYYMMDD')::INTEGER as date_key,
                d as date_actual,
                EXTRACT(DOW FROM d)::INTEGER as day_of_week,
                TO_CHAR(d, 'Day') as day_name,
                EXTRACT(MONTH FROM d)::INTEGER as month,
                TO_CHAR(d, 'Month') as month_name,
                EXTRACT(QUARTER FROM d)::INTEGER as quarter,
                EXTRACT(YEAR FROM d)::INTEGER as year
            FROM generate_series('2020-01-01'::date, '2030-12-31'::date, '1 day'::interval) d
            ON CONFLICT (date_key) DO NOTHING
        """))
    
    # Populate dimensions from bronze/silver
    populate_dimensions(run_id, log_func)
    
    # Populate fact tables from silver
    populate_fact_tables(run_id, log_func)
    
    log_func(run_id, "INFO", "Warehouse loading completed")


def generate_diagrams(run_id: str, log_func):
    """
    Step 5: Generate data model diagrams.
    """
    from app.services.diagram_generator import generate_mermaid_er_diagram, save_diagram
    from sqlalchemy import text
    from app.core.db import engine
    
    log_func(run_id, "INFO", "Generating diagrams...")
    
    try:
        # Generate Mermaid ER diagram
        diagram = generate_mermaid_er_diagram()
        
        # Save to file
        diagram_path = save_diagram(diagram, "data_model.mmd")
        log_func(run_id, "INFO", f"Diagram saved to {diagram_path}")
        
        # Also store in database for API access
        with engine.begin() as cxn:
            # Create diagrams table if it doesn't exist
            cxn.execute(text("""
                CREATE TABLE IF NOT EXISTS pipeline_diagrams (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    diagram_type TEXT NOT NULL,
                    diagram_content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
            """))
            
            # Store diagram
            cxn.execute(text("""
                INSERT INTO pipeline_diagrams (diagram_type, diagram_content)
                VALUES ('mermaid_er', :content)
            """), {"content": diagram})
        
        log_func(run_id, "INFO", "Diagrams generated and stored")
        
    except Exception as e:
        log_func(run_id, "WARN", f"Failed to generate diagrams: {str(e)}")
