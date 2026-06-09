# PetroCore Tanna Connector Backend v0.2.1

Read-only connector surface exposing PetroCore intelligence objects to **Tanna Core** at `/api/v1/tanna/*`.

PetroCore remains a standalone product (`nuprc-upstream-pipeline-product`). The **PetroCore** name is used only at this connector boundary.

## v0.2.1 — Contract Validation & Sync Readiness

This release hardens the connector for safe Tanna Core consumption:

- **Standard response envelope** on every endpoint (validated at build time)
- **Schema validation** for items per object type
- **`GET /api/v1/tanna/status`** — maturity matrix and sync planning metadata
- **Sync readiness metadata** on every endpoint (`sync_ready`, `sync_notes`, `external_id_strategy`, `duplicate_handling_notes`)
- **Stable external_ids** using `petrocore:{object_type}:{stable_key}` pattern
- **Expanded contract test suite**

No new analytical intelligence is added in this release.

## Maturity Matrix

| Object type | Status | Sync-ready |
|-------------|--------|------------|
| manifest | implemented | yes |
| health | partial | yes |
| data_products | implemented | yes |
| entities | partial | yes (limited instances) |
| relationships | partial | yes |
| signals | partial | yes |
| patterns | not_implemented | no |
| illuminations | partial | yes |
| decision_products | placeholder | no |
| knowledge_assets | partial | yes |

Query `GET /api/v1/tanna/status` for the full matrix with notes.

## What Tanna Core Can Safely Sync Today

| Object type | Safe to sync | Caveats |
|-------------|--------------|---------|
| manifest | yes | Single module registration document |
| health | yes | Point-in-time snapshot; replace each cycle |
| data_products | yes | Stable table-backed external_ids |
| entities | yes | Sampled instances (max 100/type); may change |
| relationships | yes | Structural only; 6 confirmed relationships |
| signals | yes | Operational only; deterministic external_ids |
| illuminations | yes | Rule-based; derived from signals |
| knowledge_assets | yes | Read-only index; content_text is excerpt |
| decision_products | **no** | Placeholder shells only |
| patterns | **no** | Empty; not implemented |

## Sync Readiness Rules

| implementation_status | sync_ready |
|----------------------|------------|
| implemented | `true` when stable external_ids exist |
| partial | `true` when external_ids are stable and limitations documented |
| placeholder | `false` |
| not_implemented | `false` |

## External ID Strategy

All connector objects use stable, deterministic external_ids:

```
petrocore:data_product:gold_oil_fact_production
petrocore:entity:operator:{operator_name}
petrocore:relationship:gold_oil_fact_production:depends_on:gold_oil_dim_operator
petrocore:signal:pipeline_run_failed:{run_id}
petrocore:illumination:{signal_key}
petrocore:knowledge_asset:documentation:README
petrocore:decision_product:monthly_upstream_production_review
```

No random UUIDs unless backed by persisted identifiers (e.g. file SHA for ingested documents).

## Response Envelope

Every endpoint returns:

```json
{
  "module_id": "petrocore",
  "module_name": "PetroCore",
  "object_type": "...",
  "implementation_status": "implemented | partial | placeholder | not_implemented",
  "items": [],
  "metadata": {
    "source": "...",
    "notes": "...",
    "generated_at": "ISO-8601",
    "warnings": [],
    "sync_ready": true,
    "sync_notes": "...",
    "external_id_strategy": "...",
    "duplicate_handling_notes": "..."
  }
}
```

## Endpoints

| Endpoint | implementation_status |
|----------|----------------------|
| `GET /api/v1/tanna/manifest` | implemented |
| `GET /api/v1/tanna/health` | partial |
| `GET /api/v1/tanna/status` | implemented |
| `GET /api/v1/tanna/data-products` | implemented |
| `GET /api/v1/tanna/entities` | partial |
| `GET /api/v1/tanna/relationships` | partial |
| `GET /api/v1/tanna/signals` | partial |
| `GET /api/v1/tanna/patterns` | not_implemented |
| `GET /api/v1/tanna/illuminations` | partial |
| `GET /api/v1/tanna/decision-products` | placeholder |
| `GET /api/v1/tanna/knowledge-assets` | partial |

## Authentication

```
Authorization: Bearer <TANNA_CONNECTOR_TOKEN>
```

| Response | Condition |
|----------|-----------|
| `401` | Missing Bearer token |
| `403` | Invalid token |
| `503` | Token not configured |

## Operational Signals (v0.2)

Allowed signal types only — no analytical production intelligence:

`PIPELINE_RUN_FAILED`, `PIPELINE_STEP_FAILED`, `PIPELINE_RUN_BLOCKED`, `PIPELINE_RUN_RUNNING`, `DATA_FRESHNESS_DEGRADED`, `SOURCE_UNAVAILABLE`, `SCHEMA_DRIFT_DETECTED`, `CATALOG_FRESHNESS_ISSUE`

## What Is Not Implemented

- Tanna Core sync engine (this connector exposes readiness metadata only)
- Analytical patterns (`/patterns` returns empty items)
- Production-ready decision products
- LLM illuminations
- Production decline / operator performance / field performance signals
- Field, Terminal, License, Operator Group entities

## Roadmap

| Version | Focus |
|---------|-------|
| v0.1 | Connector surface |
| v0.2 | Operational intelligence (signals, illuminations, health) |
| v0.2.1 | Contract validation & sync readiness |
| v0.3 | Analytical intelligence (only when backed by real PetroCore logic) |
| v0.4+ | Decision product exports and approval workflows |

## Unchanged by Design

- Ingestion and ETL (`backend/etl/*`)
- Database schema
- Existing `/catalog/*`, `/v1/pipeline/*`, and all other APIs
- Frontend pages
