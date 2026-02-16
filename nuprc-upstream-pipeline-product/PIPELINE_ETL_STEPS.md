# Pipeline ETL Steps (1–6) and Run Response

## Steps (Control Panel lifecycle)

| Step | Key | ETL step_key | Description |
|------|-----|--------------|-------------|
| 1 | source_scraping | acquire / acquire_* | Scrape source pages for file links |
| 2 | file_acquisition | acquire / acquire_* | Download files |
| 3 | bronze_load | bronze | Ingest into bronze.etl_*_raw |
| 4 | silver_transformation | silver | Transform to silver dim_* / fact_* |
| 5 | warehouse_modeling | gold | Build gold_* star schema |
| 6 | data_product_generation | data_product_generation | Refresh catalog metadata |

## Modes

- **full**: oil + gas + rig + concession (all sources)
- **oil** | **gas** | **rig** | **concession**: single source

Silver and Gold are mode-aware: only tables for the run mode are populated (e.g. `oil` → silver fact_oil_production, gold_fact_upstream_production with source_type=oil).

## Example run response

`GET /v1/pipeline/runs/{run_id}` after a successful **oil** run:

```json
{
  "ok": true,
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "oil",
  "status": "success",
  "started_at": "2025-02-08T12:00:00",
  "ended_at": "2025-02-08T12:05:00",
  "steps": [
    { "step_key": "source_scraping", "label": "1) Source Scraping", "status": "done", "metrics": {} },
    { "step_key": "file_acquisition", "label": "2) File Acquisition", "status": "done", "metrics": { "file_count": 1 } },
    { "step_key": "bronze_load", "label": "3) Bronze Load", "status": "done", "metrics": { "rows_loaded": 150, "tables_written": ["etl_oil_production_raw"], "mode": "oil" } },
    { "step_key": "silver_transformation", "label": "4) Silver Transformation", "status": "done", "metrics": { "tables_written": ["fact_oil_production"], "rows_written": 150, "mode": "oil" } },
    { "step_key": "warehouse_modeling", "label": "5) Warehouse Modeling", "status": "done", "metrics": { "tables_written": ["gold_fact_upstream_production"], "rows_written": 150, "mode": "oil" } },
    { "step_key": "data_product_generation", "label": "6) Data Product Generation", "status": "done", "metrics": { "catalog_refreshed": true } }
  ],
  "meta": { "rows_loaded": 150, "tables_written": { "bronze": [...], "silver": [...], "gold": [...] } }
}
```

## How to run locally

1. **Env vars** (optional; default single DB):
   - `DATABASE_URL` — single DB for all layers (default: `postgresql+psycopg://postgres:postgres@localhost:5432/nuprc`)
   - Or separate: `BRONZE_DB_URL`, `SILVER_DB_URL`, `GOLD_DB_URL`

2. **Start run**:
   - API: `POST /v1/pipeline/runs` with body `{"mode": "oil"}` or `{"mode": "full"}`
   - CLI: `python -m etl.cli run --mode oil` (if available)

3. **Poll status**: `GET /v1/pipeline/runs/{run_id}`

4. **Cancel**: `POST /v1/pipeline/runs/{run_id}/cancel`

## Catalog after run

- `GET /catalog/tables?layer=bronze` — etl_*_raw tables
- `GET /catalog/tables?layer=silver` — dim_date, dim_operator, fact_*
- `GET /catalog/tables?layer=gold` — gold_dim_*, gold_fact_* with business-friendly display names
