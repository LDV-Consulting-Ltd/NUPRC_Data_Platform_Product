# Unified Catalog and Pipeline (v1 Only)

## One catalog

There is a **single catalog API** at **`/catalog/*`**:

- **`GET /catalog/tables?layer=bronze|silver|gold`** — Canonical tables per layer (etl_* / silver.* / gold_*), correct row counts and display names.
- **`GET /catalog/diagnostics`** — Which DB/schema is used per layer (redacted URLs).
- **`GET /catalog/files`**, **`GET /catalog/files/{file_sha256}`**, **`GET /catalog/tables/{schema}/{table}`**, **`POST /catalog/refresh`**, **`POST /catalog/backfill`**, **`GET /catalog/summary`**, **`GET /catalog/quick-summary`** — All other catalog endpoints.

**Deprecated alias (still supported):** **`/v1/catalog/tables`** and **`/v1/catalog/diagnostics`** are thin aliases to the same logic. Prefer **`/catalog/*`**.

---

## One pipeline (v1)

The **canonical pipeline** is **`/v1/pipeline/*`**:

- **`POST /v1/pipeline/runs`** — Start run (body: `{ "mode": "full" | "oil" | "gas" | "rig" | "concession" }`).
- **`GET /v1/pipeline/runs`** — List runs.
- **`GET /v1/pipeline/runs/{run_id}`** — Run detail and 6 steps.
- **`GET /v1/pipeline/runs/{run_id}/diagnostics`** — Diagnostics.
- **`POST /v1/pipeline/runs/{run_id}/cancel`** — Cancel run.
- **`GET /v1/pipeline/platform/status`** — Platform status.
- **`GET /v1/pipeline/sources/health`** — Source health.
- **`POST /v1/pipeline/runs/clear-stuck`** — Clear stuck runs.
- **`GET /v1/pipeline/runs/blocking`** — Blocking runs.

**Old pipeline (`/pipeline/*`) is deactivated as the main path:** all `/pipeline/*` endpoints now **forward to v1**. Callers can keep using `/pipeline/run`, `/pipeline/runs`, etc.; they are served by the same v1 pipeline (admin.etl_runs, run_etl). New code should use **`/v1/pipeline/*`** only.

---

## Summary

| Area    | Single API              | Deprecated / alias              |
|---------|-------------------------|----------------------------------|
| Catalog | **`/catalog/*`**        | `/v1/catalog/tables`, `/v1/catalog/diagnostics` (alias) |
| Pipeline| **`/v1/pipeline/*`**    | `/pipeline/*` (facade to v1)    |
