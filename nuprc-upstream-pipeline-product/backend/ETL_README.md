# NUPRC ETL Pipeline (Rebuild)

Production-grade ETL: **Acquire → Bronze → Silver → Gold** with reliable acquisition (httpx, retries), observability, and v1 API.

## File tree (key modules)

```
backend/
  etl/
    __init__.py
    config.py          # DB URLs, paths, timeouts
    observability.py   # etl_runs, etl_run_steps
    acquire.py         # httpx download (retries, backoff, sha256, data/raw/{source}/{date})
    scrape.py          # Oil/Gas/Rig: Excel links only
    sources.py         # Source URLs (concession PDF direct URL)
    concession.py      # PDF section parser: strict header (PEL/PPL/PML), full header text, explode multi-value rows
    bronze.py          # Load to bronze (payload JSONB + metadata)
    silver.py          # Conformed dims/facts
    gold.py            # Star schema (gold_*)
    run.py             # Orchestration (full | oil | gas | rig | concession)
    cli.py             # CLI entry
    healthcheck.py     # NUPRC + DB health
    migrations/
      001_bronze_etl_tables.sql
      002_silver_gold_tables.sql
      003_concession_category_full.sql
  app/routers/
    v1_pipeline.py    # POST/GET /v1/pipeline/runs, diagnostics, platform/status, sources/health
  tests/
    test_etl_acquisition.py
    test_etl_bronze_silver_gold.py
```

## Env vars

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL URL (single DB for all layers) | `postgresql+psycopg://postgres:postgres@localhost:5432/nuprc` |
| `BRONZE_DB_URL` | Optional separate Bronze DB | same as DATABASE_URL |
| `SILVER_DB_URL` | Optional separate Silver DB | same as DATABASE_URL |
| `GOLD_DB_URL` | Optional separate Gold DB | same as DATABASE_URL |
| `ETL_DATA_RAW` | Directory for raw downloads | `data/raw` |
| `ETL_CONNECT_TIMEOUT` | HTTP connect timeout (s) | 15 |
| `ETL_READ_TIMEOUT` | HTTP read timeout (s) | 120 |
| `ETL_MAX_FILE_SIZE` | Max download size (bytes) | 100MB |

## How to run

### CLI (from backend directory)

```bash
cd backend
pip install -r requirements.txt
# Optional: set DATABASE_URL if not using default

# Full pipeline
python -m etl.cli run --mode full

# Per-source
python -m etl.cli run --mode oil
python -m etl.cli run --mode gas
python -m etl.cli run --mode rig
python -m etl.cli run --mode concession

# Healthcheck (NUPRC pages + concession PDF + DB)
python -m etl.cli healthcheck
```

### API (v1)

Start the FastAPI backend, then:

- **Start run:** `POST /v1/pipeline/runs` body `{"mode": "full"}` or `"oil"` | `"gas"` | `"rig"` | `"concession"`
- **Poll run:** `GET /v1/pipeline/runs/{run_id}`
- **Diagnostics:** `GET /v1/pipeline/runs/{run_id}/diagnostics`
- **Platform status:** `GET /v1/pipeline/platform/status`
- **Sources health:** `GET /v1/pipeline/sources/health`

Error responses include `user_message` and `technical_details` for the frontend.

### Migrations

Bronze/Silver/Gold tables are created automatically on first run. To apply SQL manually:

```bash
psql "$DATABASE_URL" -f etl/migrations/001_bronze_etl_tables.sql
psql "$DATABASE_URL" -f etl/migrations/002_silver_gold_tables.sql
```

Observability tables (`admin.etl_runs`, `admin.etl_run_steps`) are created by `observability.init_observability_schema()` at startup.

## Source rules

- **Oil / Gas / Rig:** Scrape HTML from NUPRC pages; keep **Excel only** (`.xlsx`, `.xls`); ignore PDFs. Download with httpx (retries, User-Agent, redirects), store under `data/raw/{source}/{yyyy-mm-dd}/`.
- **Concession:** Single direct PDF URL (Feb 2026). Download same way. Parse with pdfplumber; detect section headers (PEL, PPL, PML, OML, OPL) and set `concession_category` per row. Load into `bronze.concessions_raw` and `bronze.concessions_sections`.

## Troubleshooting acquisition failures

1. **Healthcheck:** Run `python -m etl.cli healthcheck`. Fix any failing check (DB, oil/gas/rig page, concession PDF).
2. **Network:** Ensure the host can reach `https://www.nuprc.gov.ng`. Try `curl -I "https://www.nuprc.gov.ng/oil-production-status-report/"`.
3. **Concession URL:** Use the exact HTTPS URL (no `chrome-extension://`). If the PDF moved, update `etl/sources.py` `CONCESSION_PDF_URL`.
4. **Timeouts:** Increase `ETL_READ_TIMEOUT` or `ETL_CONNECT_TIMEOUT` if downloads are slow.
5. **Logs:** Check `admin.etl_run_steps` for the run (step_key, status, error_json, metrics_json).

## Tests

```bash
cd backend
pip install pytest
pytest tests/ -v
```

- `test_etl_acquisition.py`: Excel link extraction (oil/gas/rig), concession PDF download, concession parser assigns category.
- `test_concession_header_and_explode.py`: Header whitelist/blacklist, explode multi-value rows, parser returns `concession_category_full` and payload `row_split_*`.
- `test_etl_bronze_silver_gold.py`: Bronze write (with DB), silver/gold build without crashing (requires DB).
