# Live UI Wiring Verification

Manual checks after wiring frontend pages to v1 ETL (`admin.etl_runs`) and medallion tables.

## Prerequisites

- Postgres: `petrocore-nuprc-db` on port **5434**
- Backend: `http://127.0.0.1:8001`
- Frontend: `http://localhost:3001` (local dev port)

## Backend endpoints

| URL | Expected |
|-----|----------|
| `GET /runs/summary` | `source: admin.etl_runs`, non-zero counts when v1 runs exist |
| `GET /runs/summary/v1` | Same source, explicit v1-only summary |
| `GET /v1/pipeline/runs/history` | `source: admin.etl_runs`, run list with `duration_seconds`, `rows_bronze` |
| `GET /v1/pipeline/sources/health` | Each source has `reachability_status`, `data_presence_status`, `explanation` |
| `GET /v1/pipeline/platform/status` | Latest run from `admin.etl_runs` |
| `GET /pipeline/status` | Latest run + bronze/gold row counts |
| `GET /catalog/summary` | `file_registry_status.status: empty` when no downloaded files |
| `GET /catalog/tables?layer=gold` | Live gold tables |
| `GET /warehouse/tables` | Live warehouse tables |
| `GET /diagrams/latest` | HTTP 200; `status: available` after v1 run or `POST /diagrams/generate` |
| `POST /diagrams/generate` | Stores `pipeline_flow` + `v1_data_model` in `pipeline_diagrams` |

Quick curl examples:

```bash
curl -s http://127.0.0.1:8001/runs/summary | jq .source,.total_runs
curl -s http://127.0.0.1:8001/diagrams/latest | jq .status,.is_fallback
curl -s http://127.0.0.1:8001/v1/pipeline/sources/health | jq '.sources[0] | {status,data_presence_status,explanation}'
```

## Frontend pages

| Page | What to verify |
|------|----------------|
| `/control-panel` | Critical banner only when `status === down`; degraded shows advisory copy |
| `/showcase` | Latest run badge works with lowercase `success`; bronze/gold counts visible |
| `/showcase/runs` | Total/success/failed from v1; latest run status and time |
| `/run-history` | Live runs from API, not hardcoded IDs |
| `/lineage` | Canonical v1 table names (`bronze.etl_*`, `silver.fact_*`, `gold.gold_*`) |
| `/showcase/catalog` Files tab | Honest empty message when no `downloaded_files`; Tables tab still live |
| `/showcase/diagrams` | No 500; empty state or fallback Mermaid diagram |
| `/catalog` | Tables tab unchanged, live medallion metadata |

## Automated smoke tests

```bash
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests/test_live_ui_wiring.py -v
```

## Intentionally placeholder / empty

- `data_catalog.downloaded_files` — v1 ETL does not populate file registry
- `pipeline_diagrams` — v1 ETL does not generate stored diagrams (fallback structural diagram only)
- `pipeline_run` — legacy table; used only as fallback for `/runs/summary`
- Run history cost / SLA columns — not tracked in v1 observability yet
