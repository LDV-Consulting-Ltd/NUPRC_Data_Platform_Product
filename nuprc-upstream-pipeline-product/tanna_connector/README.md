# PetroCore Tanna Connector v1

Read-only connector layer that exposes PetroCore (NUPRC upstream pipeline product) intelligence objects to **Tanna Core** using the official **Tanna Connector SDK**.

PetroCore remains a standalone product. Tanna must **not** access PetroCore databases or internal APIs directly — only this connector surface.

## Purpose

- Standardize PetroCore outputs for Tanna consumption
- Expose gold marts, entities, operational signals, and knowledge assets
- Preserve existing ingestion, ETL, and internal APIs unchanged

## Prerequisites

1. **Tanna Connector SDK** on `PYTHONPATH`:

```bash
export TANNA_SDK_PACKAGES_PATH="/path/to/TANNA by LDV/packages"
export PYTHONPATH="${TANNA_SDK_PACKAGES_PATH}:${PYTHONPATH}"
```

Default resolution (sibling repo): `../../TANNA by LDV/packages`

2. **Service token** (required for connector endpoints):

```bash
export TANNA_CONNECTOR_TOKEN=your-secret-service-token
```

| Response | Condition |
|----------|-----------|
| `401` | Missing `Authorization: Bearer` header |
| `403` | Invalid token |
| `503` | `TANNA_CONNECTOR_TOKEN` not set |

## Endpoints

All require `Authorization: Bearer <TANNA_CONNECTOR_TOKEN>`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/tanna/health` | Connector health |
| `GET /api/v1/tanna/manifest` | Module manifest (`module_id: petrocore`) |
| `GET /api/v1/tanna/data-products` | Gold mart data products |
| `GET /api/v1/tanna/entities` | Operators, concessions, rigs, sources, documents |
| `GET /api/v1/tanna/relationships` | Structural relationships |
| `GET /api/v1/tanna/signals` | Operational signals (freshness, pipeline, drift) |
| `GET /api/v1/tanna/patterns` | Empty — analytical patterns not implemented |
| `GET /api/v1/tanna/illuminations` | Rule-based operational illuminations |
| `GET /api/v1/tanna/decision-products` | Metadata-only stubs (`status: draft`) |
| `GET /api/v1/tanna/knowledge-assets` | Docs, glossaries, ER diagram index |

## Exposed Objects (confirmed backing only)

| Object | Source |
|--------|--------|
| Data products | `catalog_registry` gold marts + `TABLE_DISPLAY` |
| Entities | Gold dimensions, `sources.py`, `data_catalog.downloaded_files`, `warehouse.dim_asset` |
| Relationships | Gold FK structure, catalog lineage |
| Signals | `admin.etl_*`, freshness, `silver.schema_drift` |
| Patterns | **Not implemented** — returns `[]` |
| Illuminations | Pipeline status, freshness, schema drift |
| Decision products | Placeholder stubs only |
| Knowledge assets | Markdown docs, `TABLE_DISPLAY`, `CANONICAL_COLUMNS`, diagrams |

## Security

- Bearer service token only (`TANNA_CONNECTOR_TOKEN`)
- No user sessions on connector routes
- No direct database exposure to Tanna
- Read-only SQL inside connector mappers only

## Package Layout

```
tanna_connector/
  connector.py   # PetroCoreTannaConnector (subclasses TannaConnector)
  mapper.py      # PetroCore → SDK schema mapping
  router.py      # SDK create_tanna_router() mount
  config.py      # Module constants + SDK path bootstrap
  README.md
```

Read-only adapters live in `backend/app/tanna_connector/adapters/` (reused, not duplicated).

## Future Tanna Synchronization

This release exposes the connector contract only. Tanna Core sync (pull schedules, traceability, governance workflows) is **not** implemented here.
