# Data Catalog System - All Sources

## Overview

The data catalog system tracks **all 4 sources** (Oil, Gas, Concession, Rig) throughout the entire pipeline:
- **Oil Production Status** (`oil_production_status`)
- **Gas Production Status** (`gas_production_status`)
- **Concession Situation** (`concession_situation`)
- **Rig Disposition** (`rig_disposition`)

## Automatic Tracking

The catalog automatically tracks files at every stage:

### 1. Download Stage
- Files are registered when downloaded (all sources)
- Tracks: file URL, hash, size, type, source, download status
- Location: `data_catalog.downloaded_files`

### 2. Bronze Stage
- Updated when files are loaded to bronze tables
- Tracks: bronze table, row count, processing timestamp
- Works for: All sources (via `bronze_loader.py`)

### 3. Silver Stage
- Updated when files are transformed to silver
- Tracks: silver table, row count
- Works for: All sources (via `silver_transformer.py`)

### 4. Warehouse Stage
- Updated when facts are loaded to warehouse
- Tracks: warehouse tables, row counts
- Works for: All sources (via `warehouse_loader.py`)
  - Oil → `warehouse.fact_oil_production`
  - Gas → `warehouse.fact_gas_production`
  - Rig → `warehouse.fact_rig_activity`
  - Concession → `warehouse.fact_concession_status`

## API Endpoints

All endpoints work for all sources:

```bash
# List all downloaded files (all sources)
GET /catalog/files

# Filter by source
GET /catalog/files?source_id=oil_production_status
GET /catalog/files?source_id=gas_production_status
GET /catalog/files?source_id=concession_situation
GET /catalog/files?source_id=rig_disposition

# Get file details
GET /catalog/files/{file_sha256}

# List all tables (all sources)
GET /catalog/tables

# Filter by table type
GET /catalog/tables?table_type=bronze
GET /catalog/tables?table_type=silver
GET /catalog/tables?table_type=warehouse

# Filter by source
GET /catalog/tables?source_id=oil_production_status

# Get table details
GET /catalog/tables/{schema}/{table_name}

# Get summary statistics (all sources)
GET /catalog/summary

# Refresh catalog
POST /catalog/refresh
```

## Catalog Tables

### `data_catalog.downloaded_files`
Tracks all downloaded files with processing status:
- File metadata (URL, hash, size, type)
- Source information
- Processing status (bronze, silver, warehouse)
- Row counts at each stage
- Timestamps

### `data_catalog.available_tables`
Lists all tables in the system:
- Bronze tables (4 sources)
- Silver tables (4 sources)
- Warehouse tables (dimensions + facts)
- Row counts
- Last updated timestamps

## Summary Statistics

The `/catalog/summary` endpoint provides:
- **File statistics**: Count by status (downloaded, failed, duplicate)
- **Source statistics**: Per-source breakdown with row counts
- **Table statistics**: Count by type (bronze, silver, warehouse)

## Example Response

```json
{
  "ok": true,
  "file_statistics": [
    {"download_status": "downloaded", "count": 45, "bronze_count": 45, "silver_count": 40, "warehouse_count": 40},
    {"download_status": "duplicate", "count": 12, ...}
  ],
  "source_statistics": [
    {
      "source_id": "oil_production_status",
      "source_name": "Oil Production Status",
      "total_files": 15,
      "downloaded": 12,
      "total_bronze_rows": 125000,
      "total_silver_rows": 120000,
      "total_warehouse_rows": 120000
    },
    {
      "source_id": "gas_production_status",
      ...
    },
    {
      "source_id": "concession_situation",
      ...
    },
    {
      "source_id": "rig_disposition",
      ...
    }
  ],
  "table_statistics": [
    {"table_type": "bronze", "table_count": 4, "total_rows": 500000},
    {"table_type": "silver", "table_count": 4, "total_rows": 480000},
    {"table_type": "warehouse", "table_count": 11, "total_rows": 450000}
  ]
}
```

## Notes

- The catalog is **automatically updated** during pipeline execution
- All 4 sources are tracked equally
- Oil production has an optimized direct-to-warehouse path, but still tracked in catalog
- Catalog updates are non-blocking (failures don't stop pipeline)
