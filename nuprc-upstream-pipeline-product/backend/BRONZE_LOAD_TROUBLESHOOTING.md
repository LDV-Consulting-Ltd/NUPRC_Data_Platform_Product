# Bronze Load Failing — Troubleshooting

When the **Bronze Load** step fails in the Pipeline Lifecycle:

## 1. Get the actual error

- In the Control Panel, click **View Details** on the red error banner, or
- Call **GET /v1/pipeline/runs/{run_id}/diagnostics** and check `steps` for the `bronze` step’s `error_json.message` (and `traceback` if present).

The run’s `user_message` also contains the failure reason when the run has failed.

## 2. Common causes and fixes

| Cause | What you see | Fix |
|-------|----------------|-----|
| **File not found** | `Failed to read Excel ... No such file or directory` | Acquisition and Bronze must see the same `data/raw` path. Backend uses an absolute path (from `etl/config.py`). Restart the backend from the **backend** directory so `data/raw` is created there. Or set `ETL_DATA_RAW` to an absolute path. |
| **Excel read error** | `Failed to read Excel ...` (e.g. unsupported format, corrupted file) | Ensure the downloaded file is a valid `.xlsx` (or supported) Excel file. Check `data/raw/{source}/{date}/` for the file. |
| **Database / schema** | `relation "bronze.etl_*" does not exist` or column errors | Run migrations: `001_bronze_etl_tables.sql`, `005_bronze_report_year.sql`. The app runs them on first run; if you use a fresh DB, ensure the backend has created the `bronze` schema and tables. |
| **Connection** | `could not connect to server` / connection timeout | Check `DATABASE_URL` (or `BRONZE_DB_URL`). Ensure PostgreSQL is running and reachable. |
| **Concession only** | PDF extract or insert error | For concession runs, the failure may be in `extract_concession_pdf` or concession table insert. Check `error_json` for the exact exception. |

## 3. Paths

- **Storage**: Files are written to `ETL_DATA_RAW` (default: `backend/data/raw/{source}/{yyyy-mm-dd}/`).
- **Absolute path**: The ETL resolves this to an absolute path so Bronze load finds files even if the server was started from another directory. If you override `ETL_DATA_RAW`, use an absolute path for consistency.

## 4. After fixing

Restart the pipeline (e.g. **Run Full Pipeline** or the same mode that failed). If the failure was path-related, restart the backend from the `backend` folder so `data/raw` is correct.
