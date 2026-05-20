# Quick start

From this folder (`nuprc-upstream-pipeline-product`):

1. Start Postgres: `docker compose up -d`
2. Run backend commands from **`backend`** (set `DATABASE_URL` if not using the default Docker URL).

## Run ETL (concession / full / oil / gas / rig)

```powershell
cd backend
python -m etl.cli run --mode concession
```

Or from anywhere (absolute path):

```powershell
cd "C:\Users\alann\OneDrive\Documents\Python Projects\NUPRC data platform Product\nuprc-upstream-pipeline-product\backend"
python -m etl.cli run --mode concession
```

## Healthcheck

```powershell
cd backend
python -m etl.cli healthcheck
```

## Run tests

```powershell
cd backend
pip install pytest
python -m pytest tests/test_concession_header_and_explode.py tests/test_etl_acquisition.py -v
```

## If you're in the wrong folder

- **Wrong:** `NUPRC data platform Product` (no `backend` here)
- **Right:** `NUPRC data platform Product\nuprc-upstream-pipeline-product\backend`

So first run: `cd nuprc-upstream-pipeline-product\backend`
