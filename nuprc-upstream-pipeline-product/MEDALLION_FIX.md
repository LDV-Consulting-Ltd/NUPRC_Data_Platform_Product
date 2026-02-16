# Medallion Architecture Fix — Bronze → Silver → Gold

## Summary of changes

1. **Catalog** — Each layer reads from the correct DB/schema; diagnostics endpoint added.
2. **Bronze** — `report_year` column added and populated (from payload, file name, or `downloaded_at`).
3. **Silver** — Reads **all** Bronze rows (no run_id filter), dedupes by `row_hash`, writes **only** to Silver DB/schema. Logs schema and row counts.
4. **Gold** — Reads from Silver only, writes to Gold only. Logs schema and row counts.
5. **Orchestrator** — Step 4/5 fail loudly if Bronze had rows but Silver wrote 0, or Silver had rows but Gold wrote 0. Step 6 (data_product_generation) runs catalog refresh.

---

## 1) Catalog: correct DB per layer + diagnostics

- **`get_engine_for_layer(layer)`** (in `catalog_registry`) already uses `BRONZE_DB_URL` / `SILVER_DB_URL` / `GOLD_DB_URL` (or `DATABASE_URL` for a single DB). No change needed; each layer uses the correct engine.
- **`GET /catalog/diagnostics`** — Returns per layer:
  - `schema`: bronze | silver | gold
  - `url_redacted`: DB URL with credentials redacted
  - `engine_same_as`: `"single_db"` when all three use the same URL

**Example response:**

```json
{
  "ok": true,
  "layers": {
    "bronze": { "schema": "bronze", "url_redacted": "***:***@localhost:5432/nuprc", "engine_same_as": "single_db" },
    "silver": { "schema": "silver", "url_redacted": "***:***@localhost:5432/nuprc", "engine_same_as": "single_db" },
    "gold":   { "schema": "gold",   "url_redacted": "***:***@localhost:5432/nuprc", "engine_same_as": "single_db" }
  }
}
```

---

## 2) Bronze: report_year

- **Migration** `etl/migrations/005_bronze_report_year.sql`: adds `report_year INT` and indexes to all five bronze tables.
- **Loaders**:
  - `load_excel_to_bronze`: derives `report_year` from payload (`year`, `report_period`), file name (e.g. `2024`), or `downloaded_at.year`; inserts with `report_year`. Fallback INSERT without `report_year` if column is missing.
  - `load_concession_to_bronze`: sets `report_year = downloaded_at.year` for sections and raw rows.
- **Init** — `init_bronze_etl_tables()` runs 001 and 005 so new and existing DBs get the column.

---

## 3) Silver: stop mirroring Bronze

- **Read** — `SELECT ... FROM bronze.{bronze_table}` **with no** `WHERE ingest_run_id = :rid`. All bronze rows are read so silver is fully populated; repeated runs dedupe by `row_hash`.
- **Write** — Only to `silver.*` (Silver DB or silver schema). Uses `get_silver_engine()`; never writes to bronze.
- **Logging** — Logs `schema=silver`, redacted URL, and `tables_written` / `rows_written` at the end.

Silver tables remain: `dim_date`, `dim_operator`, `fact_oil_production`, `fact_gas_production`, `fact_rig_disposition`, `fact_concession_status`.

---

## 4) Gold: populate from Silver

- **Read** — From `silver.dim_date`, `silver.dim_operator`, `silver.fact_*` only (Silver engine).
- **Write** — Only to `gold.*` (Gold engine). Never writes to bronze or silver.
- **Logging** — Logs reading from silver, writing to schema=gold, and final `tables_written` / `rows_written`.

---

## 5) Orchestrator: steps 4–6 and fail-loud

- **Step 4 (Silver)** — After `transform_to_silver(run_id, mode)`:
  - If `total_bronze > 0` and `silver_metrics["rows_written"] == 0`: mark step failed, end run failed, return error message.
  - Otherwise mark step success.
- **Step 5 (Gold)** — After `transform_to_gold(run_id, mode)`:
  - If `silver_rows > 0` and `gold_metrics["rows_written"] == 0`: mark step failed, end run failed, return error message.
  - Otherwise mark step success.
- **Step 6 (data_product_generation)** — `start_step` → `refresh_available_tables()` → `end_step(success)`. On refresh failure, run fails.

---

## 6) Example run step metrics (after full run)

```json
{
  "steps": [
    { "step_key": "source_scraping", "status": "done", "metrics": {} },
    { "step_key": "file_acquisition", "status": "done", "metrics": { "file_count": 4 } },
    { "step_key": "bronze_load", "status": "done", "metrics": { "rows_loaded": 500, "tables_written": ["etl_oil_production_raw", "etl_gas_production_raw", "etl_rig_disposition_raw", "etl_concessions_raw"], "mode": "full" } },
    { "step_key": "silver_transformation", "status": "done", "metrics": { "mode": "full", "tables_written": ["fact_oil_production", "fact_gas_production", "fact_rig_disposition", "fact_concession_status"], "rows_read": 500, "rows_written": 500 } },
    { "step_key": "warehouse_modeling", "status": "done", "metrics": { "mode": "full", "tables_written": ["gold_fact_upstream_production", "gold_fact_rig_activity", "gold_fact_concessions"], "rows_written": 450 } },
    { "step_key": "data_product_generation", "status": "done", "metrics": { "catalog_refreshed": true } }
  ]
}
```

---

## 7) Verification

1. **Catalog diagnostics** — `GET /v1/catalog/diagnostics` shows the correct schema and (redacted) URL per layer.
2. **Silver ≠ Bronze** — After a run, `GET /v1/catalog/tables?layer=silver` shows `fact_*` / `dim_*` with nonzero counts when bronze has data; `layer=bronze` shows `etl_*` only.
3. **Gold populated** — `GET /catalog/tables?layer=gold` shows `gold_dim_*` and `gold_fact_*` with nonzero counts when silver has data.
4. **Control Panel** — Steps 4 and 5 show “done” only when `rows_written` > 0 (or when there was no data to move). If bronze had data and silver wrote 0, step 4 fails with a clear error.

---

## 8) Files changed

| Area | File |
|------|------|
| Catalog | `app/routers/catalog.py` — added `GET /catalog/diagnostics` |
| Bronze | `etl/migrations/005_bronze_report_year.sql` — new; `etl/bronze.py` — report_year extraction + INSERT |
| Silver | `etl/silver.py` — read all bronze (no run_id filter), logging |
| Gold | `etl/gold.py` — logging only (already reads silver, writes gold) |
| Orchestrator | `etl/run.py` — pass mode to silver; validate silver/gold rows_written; step 6 with catalog refresh |
