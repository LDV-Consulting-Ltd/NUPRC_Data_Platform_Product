# About this project

## What it is

**NUPRC Upstream Pipeline Product** is part of the **NUPRC Data Platform**. It provides a backend API and web frontend for managing and monitoring **upstream pipeline** runs, quality metrics, warehouse metadata, and related diagrams.

## Purpose

- **Pipeline run tracking** — Record and query pipeline executions (run ID, name, status, started/ended times, rows loaded, error messages). Runs are stored in a database and exposed via REST endpoints.
- **Quality** — Placeholder for quality KPIs and checks tied to upstream data.
- **Warehouse** — Placeholder for listing and describing warehouse/dataset tables used by the platform.
- **Diagrams** — Placeholder for pipeline or process diagrams (e.g. lineage or flow visuals).
- **Health** — Simple health endpoint for uptime and integration checks.

## Who it’s for

- **NUPRC** (Nigerian Upstream Petroleum Regulatory Commission) and its data platform teams.
- Developers and operators who need to run, monitor, and inspect upstream data pipelines and related metadata.

## Main components

1. **Backend (FastAPI)**  
   - REST API for runs, quality, warehouse, diagrams, and health.  
   - Persistence via SQLAlchemy on **PostgreSQL** (medallion schemas: bronze, silver, gold, admin).  
   - Tables: `pipeline_run`, `pipeline_log` for run history and logs; ETL observability in `admin.etl_runs`.

2. **Frontend (Next.js)**  
   - Web UI built with Next.js 16 and React 19 (TypeScript).  
   - Consumes the backend API for runs, quality, warehouse, and diagrams.

## Design choices

- **PostgreSQL only** — Local development uses **Docker Postgres** (`docker compose up -d`). Production target is **Supabase Postgres** via `DATABASE_URL`. SQLite is not supported (JSONB, `TIMESTAMPTZ`, `GENERATED ALWAYS AS IDENTITY`, `CREATE SCHEMA`).
- **Modular routers** — Separate routers for runs, quality, warehouse, diagrams, and health to keep the API clear and extensible.
- **Run store** — Centralized run and log storage so pipeline jobs can register runs and update status (e.g. success/failed, rows loaded).

## Relation to the wider platform

This repo is the **upstream pipeline product** within the larger NUPRC Data Platform. It focuses on pipeline execution, run history, and the metadata/quality/warehouse/diagram surfaces needed to operate and understand upstream data flows.

For setup and usage, see the main [README.md](./README.md).
