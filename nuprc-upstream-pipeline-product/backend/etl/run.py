"""
Orchestrate ETL: full | oil | gas | rig | concession.
Uses observability (start_run, end_run, start_step, end_step) and structured errors.
"""
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from etl import observability
from etl.acquire import download_file, download_concession_pdf
from etl.scrape import get_excel_links_for_source
from etl.bronze import load_excel_to_bronze, load_concession_to_bronze
from etl.silver import transform_to_silver
from etl.gold import transform_to_gold
from etl.sources import CONCESSION_PDF_URL


def _run_acquisition(
    run_id: str,
    modes: List[str],
) -> Tuple[List[Tuple[Path, str, str]], Optional[str]]:
    """
    Acquire files for given modes (oil, gas, rig, concession).
    Returns (list of (path, source_key, file_url), error_message).
    """
    results = []
    for mode in modes:
        if mode == "concession":
            observability.start_step(run_id, "acquire_concession")
            path, sha, err = download_concession_pdf(CONCESSION_PDF_URL, "concession")
            if err:
                observability.end_step(run_id, "acquire_concession", status="failed", error={"message": err})
                return results, f"Concession download failed: {err}"
            results.append((path, "concession", CONCESSION_PDF_URL))
            observability.end_step(run_id, "acquire_concession", status="success", metrics={"files": 1, "sha256": sha})
            continue
        if mode not in ("oil", "gas", "rig"):
            continue
        observability.start_step(run_id, f"acquire_{mode}")
        links, err = get_excel_links_for_source(mode)
        if err:
            observability.end_step(run_id, f"acquire_{mode}", status="failed", error={"message": err})
            return results, f"Scrape {mode} failed: {err}"
        if not links:
            observability.end_step(run_id, f"acquire_{mode}", status="success", metrics={"files": 0})
            continue
        downloaded = 0
        for link in links:
            path, sha, size, ct, download_err = download_file(
                link["url"], mode, link.get("filename"),
                allowed_content_types=[
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel",
                    "application/octet-stream",
                    "",
                ],
            )
            if download_err:
                observability.end_step(run_id, f"acquire_{mode}", status="failed", error={"message": download_err, "url": link["url"]})
                return results, f"Download failed for {link.get('filename', link['url'])}: {download_err}"
            if path:
                results.append((path, mode, link["url"]))
                downloaded += 1
        observability.end_step(run_id, f"acquire_{mode}", status="success", metrics={"files": downloaded})
    return results, None


def run_etl(
    mode: str,
    triggered_by: str = "cli",
    run_id: Optional[str] = None,
) -> Tuple[str, bool, Optional[str], dict]:
    """
    Run ETL for mode in (full, oil, gas, rig, concession).
    If run_id is provided (e.g. from API), use it; otherwise create new run.
    Returns (run_id, success, user_message, technical_details).
    """
    modes = ["oil", "gas", "rig", "concession"] if mode == "full" else [mode]
    user_message = None
    technical = {"run_id": None, "mode": mode, "steps": []}

    try:
        observability.init_observability_schema()
    except Exception as e:
        return "", False, "Database setup failed.", {"error": str(e), "traceback": traceback.format_exc()}

    if run_id is None:
        run_id = observability.start_run(mode, triggered_by=triggered_by, meta={})
    technical["run_id"] = run_id

    try:
        from etl.config import get_etl_engine
        from etl.bronze import init_bronze_etl_tables
        engine = get_etl_engine()
        for schema in ["bronze", "silver", "gold", "admin"]:
            with engine.begin() as cxn:
                from sqlalchemy import text
                cxn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        init_bronze_etl_tables()
    except Exception as e:
        observability.end_run(run_id, status="failed", meta={**technical, "error": str(e)})
        return run_id, False, "Schema creation failed.", {"error": str(e)}

    observability.start_step(run_id, "acquire")
    files_info, acq_err = _run_acquisition(run_id, modes)
    if acq_err:
        observability.end_step(run_id, "acquire", status="failed", error={"message": acq_err})
        observability.end_run(run_id, status="failed", meta={**technical, "error": acq_err})
        return run_id, False, "Data acquisition failed. Check source URLs and network.", {"acquisition_error": acq_err}
    observability.end_step(run_id, "acquire", status="success", metrics={"file_count": len(files_info)})

    if not files_info:
        observability.end_run(run_id, status="success", meta={**technical, "rows_loaded": 0})
        return run_id, True, "No new files to process.", technical

    observability.start_step(run_id, "bronze")
    downloaded_at = datetime.now(timezone.utc)
    total_bronze = 0
    bronze_tables_written = []
    try:
        for path, source_key, file_url in files_info:
            # Resolve to absolute path so Bronze load finds files regardless of process cwd
            abs_path = Path(path).resolve()
            if source_key == "concession":
                n = load_concession_to_bronze(abs_path, file_url, run_id, source_key, downloaded_at)
                if n > 0:
                    bronze_tables_written.append("etl_concessions_raw")
                    bronze_tables_written.append("etl_concessions_sections")
            else:
                table = {"oil": "etl_oil_production_raw", "gas": "etl_gas_production_raw", "rig": "etl_rig_disposition_raw"}[source_key]
                n = load_excel_to_bronze(abs_path, source_key, file_url, run_id, table, downloaded_at)
                total_bronze += n
                if n > 0 and table not in bronze_tables_written:
                    bronze_tables_written.append(table)
        observability.end_step(
            run_id,
            "bronze",
            status="success",
            metrics={
                "rows_loaded": total_bronze,
                "tables_written": list(dict.fromkeys(bronze_tables_written)),
                "mode": mode,
            },
        )
    except Exception as e:
        observability.end_step(run_id, "bronze", status="failed", error={"message": str(e), "traceback": traceback.format_exc()})
        observability.end_run(run_id, status="failed", meta={**technical, "error": str(e)})
        return run_id, False, "Bronze load failed.", {"error": str(e), "traceback": traceback.format_exc()}

    observability.start_step(run_id, "silver")
    try:
        silver_metrics = transform_to_silver(run_id, mode=mode)
    except Exception as e:
        observability.end_step(run_id, "silver", status="failed", error={"message": str(e)})
        observability.end_run(run_id, status="failed", meta={**technical, "error": str(e)})
        return run_id, False, "Silver transform failed.", {"error": str(e)}
    silver_rows = silver_metrics.get("rows_written", 0)
    if total_bronze > 0 and silver_rows == 0:
        observability.end_step(run_id, "silver", status="failed", error={"message": "Silver wrote 0 rows but bronze had data. Check Silver DB/schema and transform."}, metrics=silver_metrics)
        observability.end_run(run_id, status="failed", meta={**technical, "error": "Silver rows_written=0"})
        return run_id, False, "Silver transformation wrote no rows despite bronze data. Check Silver DB connection and schema.", {"silver_rows_written": 0, "bronze_rows": total_bronze}
    observability.end_step(run_id, "silver", status="success", metrics=silver_metrics)

    observability.start_step(run_id, "gold")
    try:
        gold_metrics = transform_to_gold(run_id, mode=mode)
    except Exception as e:
        observability.end_step(run_id, "gold", status="failed", error={"message": str(e)})
        observability.end_run(run_id, status="failed", meta={**technical, "error": str(e)})
        return run_id, False, "Gold load failed.", {"error": str(e)}
    gold_rows = gold_metrics.get("rows_written", 0)
    if silver_rows > 0 and gold_rows == 0:
        observability.end_step(run_id, "gold", status="failed", error={"message": "Gold wrote 0 rows but silver had data. Check Gold DB/schema and transform."}, metrics=gold_metrics)
        observability.end_run(run_id, status="failed", meta={**technical, "error": "Gold rows_written=0"})
        return run_id, False, "Warehouse (Gold) wrote no rows despite silver data. Check Gold DB connection and schema.", {"gold_rows_written": 0, "silver_rows": silver_rows}
    observability.end_step(run_id, "gold", status="success", metrics=gold_metrics)

    # Step 6: data_product_generation — refresh catalog
    observability.start_step(run_id, "data_product_generation")
    try:
        from app.models.data_catalog import refresh_available_tables
        refresh_available_tables()
        observability.end_step(run_id, "data_product_generation", status="success", metrics={"catalog_refreshed": True})
    except Exception as e:
        observability.end_step(run_id, "data_product_generation", status="failed", error={"message": str(e)})
        observability.end_run(run_id, status="failed", meta={**technical, "error": str(e)})
        return run_id, False, "Catalog refresh failed.", {"error": str(e)}
    try:
        from app.services.catalog_registry import CANONICAL_TABLES
        tables_written = {k: list(v) for k, v in CANONICAL_TABLES.items()}
    except Exception:
        tables_written = {}

    # Optional post-run hook: store pipeline diagrams (failure-tolerant).
    try:
        from app.services.v1_diagram_service import store_v1_diagrams_after_run
        diagram_result = store_v1_diagrams_after_run(run_id)
        if diagram_result.get("ok"):
            technical["diagrams_stored"] = diagram_result.get("stored", [])
    except Exception:
        pass

    observability.end_run(
        run_id,
        status="success",
        meta={**technical, "rows_loaded": total_bronze, "tables_written": tables_written},
    )
    return run_id, True, None, {**technical, "rows_loaded": total_bronze}
