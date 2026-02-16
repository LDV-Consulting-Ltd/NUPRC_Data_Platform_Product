# Legacy UI Rewired to v1 Catalog

Legacy Data Catalog and Datawarehouse Tables UIs now use the same canonical tables and counts as the v1 pipeline (etl_* for bronze, gold_* for warehouse). No legacy pages or links were removed. **V2 Catalog UI is unchanged.**

---

## 1) Legacy pages rewired (data source only)

| Page | Path | Data source change |
|------|------|--------------------|
| **Legacy Data Catalog** | `frontend/app/showcase/catalog/page.tsx` | No code change. Backend `/catalog/tables` and `/catalog/tables/{schema}/{table}` now proxy to v1 catalog when `table_type` is bronze/silver/warehouse (or empty = all). |
| **Legacy Datawarehouse Tables** | `frontend/app/showcase/warehouse/page.tsx` | No code change. Backend `GET /warehouse/tables` now returns v1 catalog data (bronze + gold as "warehouse") instead of hardcoded legacy table names. |

**V2 Catalog (unchanged):** `frontend/app/catalog/page.tsx` — still uses `GET /catalog/tables?layer=bronze|silver|gold` via `fetchCatalogTables(layer)`.

---

## 2) Backend changes

### 2.1 Catalog registry (`app/services/catalog_registry.py`)

- **`get_engine_for_layer(layer)`**  
  Returns the DB engine for the given layer using `etl.config` (BRONZE_DB_URL / SILVER_DB_URL / GOLD_DB_URL when set), else `app.core.db.engine`, so row counts and `last_updated` use the correct DB/schema per layer.
- **Silver display names**  
  `TABLE_DISPLAY` entries for silver: `dim_date`, `dim_operator`, `fact_oil_production`, `fact_gas_production`, `fact_rig_disposition`, `fact_concession_status` with business-friendly `display_name` and `subject_area`/`grain`.

### 2.2 Catalog router (`app/routers/catalog.py`)

- **`GET /catalog/tables`**  
  - When `layer` or `schema` is bronze/silver/gold: unchanged; uses `get_engine_for_layer` + `get_tables_for_layer` (already canonical).  
  - When **no** `layer`/`schema` (legacy Data Catalog): if `table_type` is bronze, silver, warehouse, or empty, response is built from v1 catalog (canonical tables only). Mapping: `table_type=warehouse` → layer `gold`. Returns legacy shape: `id`, `schema_name`, `table_name`, `full_name`, `table_type`, `description`, `row_count`, `last_updated`.  
  - When `table_type=catalog`: still uses `data_catalog.available_tables`.
- **`GET /catalog/tables/{schema_name}/{table_name}`**  
  For `schema_name` in bronze/silver/gold: uses `get_tables_for_layer` and layer engine for that schema; returns legacy table detail shape and columns from `information_schema`. Deprecated tables are not returned (canonical only).

### 2.3 v1 catalog router (`app/routers/v1_catalog.py`)

- **`GET /v1/catalog/tables?layer=`**  
  Uses `get_engine_for_layer(layer)` instead of a single app engine, so counts and `last_updated` are correct per layer.

### 2.4 Warehouse router (`app/routers/warehouse.py`)

- **`GET /warehouse/tables`**  
  No longer uses hardcoded legacy table names. Calls `get_tables_for_layer` for **bronze** and **gold** (gold exposed as layer `"warehouse"` for legacy UI). Returns `{ ok, tables: [{ schema, table_name, full_name, row_count, layer }] }` with canonical names only (e.g. `etl_oil_production_raw`, `gold_fact_upstream_production`). No `oil_production_status_raw` etc. unless `include_deprecated=true` (not used by this endpoint).

---

## 3) Example API responses

### `GET /v1/catalog/tables?layer=bronze`

```json
{
  "ok": true,
  "layer": "bronze",
  "schema": "bronze",
  "tables": [
    {
      "physical_name": "etl_concessions_raw",
      "display_name": "Concessions — Raw Extract",
      "description": "Raw extracted data: etl_concessions_raw",
      "row_count": 42,
      "last_updated": "2025-02-08 12:00:00",
      "subject_area": "Concessions",
      "grain": "By row"
    },
    {
      "physical_name": "etl_oil_production_raw",
      "display_name": "Oil Production — Raw",
      "description": "Raw extracted data: etl_oil_production_raw",
      "row_count": 150,
      "last_updated": "2025-02-08 12:00:00",
      "subject_area": "Oil",
      "grain": "By row"
    }
  ]
}
```

### `GET /v1/catalog/tables?layer=gold`

```json
{
  "ok": true,
  "layer": "gold",
  "schema": "gold",
  "tables": [
    {
      "physical_name": "gold_dim_date",
      "display_name": "Calendar (Dimension)",
      "description": "Warehouse table: gold_dim_date",
      "row_count": 365,
      "last_updated": "2025-02-08 12:00:00",
      "subject_area": "Dimensions",
      "grain": "Daily"
    },
    {
      "physical_name": "gold_fact_upstream_production",
      "display_name": "Upstream Production — Oil & Gas (Fact)",
      "description": "Warehouse table: gold_fact_upstream_production",
      "row_count": 1200,
      "last_updated": "2025-02-08 12:00:00",
      "subject_area": "Upstream Production",
      "grain": "Daily"
    }
  ]
}
```

### `GET /warehouse/tables` (legacy Datawarehouse Tables)

```json
{
  "ok": true,
  "tables": [
    { "schema": "bronze", "table_name": "etl_oil_production_raw", "full_name": "bronze.etl_oil_production_raw", "row_count": 150, "layer": "bronze" },
    { "schema": "gold", "table_name": "gold_fact_upstream_production", "full_name": "gold.gold_fact_upstream_production", "row_count": 1200, "layer": "warehouse" }
  ]
}
```

---

## 4) Manual test steps

1. **Run pipeline (optional)**  
   - `POST /v1/pipeline/runs` with `{"mode": "oil"}` or `"full"` so bronze/silver/gold have data.

2. **v1 catalog vs legacy screens**  
   - `GET /v1/catalog/tables?layer=bronze`: confirm only canonical bronze tables (etl_*), non-zero counts where data exists, no `oil_production_status_raw`.  
   - Open **Legacy Datawarehouse Tables** (`/showcase/warehouse`): Bronze section should list same etl_* tables and counts; Warehouse section should list gold_* tables with same counts as v1 gold.  
   - `GET /v1/catalog/tables?layer=gold`: confirm gold_dim_* and gold_fact_* with business-friendly display names and correct counts.  
   - Open **Legacy Data Catalog** (`/showcase/catalog`) → Tables tab: select Bronze / Silver / Warehouse and “All Types”. Confirm same canonical names and counts, no legacy table names. Click a table: details should match (row count, columns).

3. **V2 Catalog unchanged**  
   - Open **Data Catalog** (`/catalog`): layer selector Bronze/Silver/Gold still works and shows the same tables/counts as before (via `GET /catalog/tables?layer=`).

4. **No deletions**  
   - All legacy and new catalog/warehouse routes and pages remain; only data sources for legacy UIs were switched to v1 catalog (via backend proxy).

---

## 5) Acceptance criteria (reference)

- Legacy **Datawarehouse Tables**: Bronze = etl_* with correct counts; Warehouse = gold_* with business-friendly names and correct counts.  
- Legacy **Data Catalog**: Same canonical tables and counts for selected layer (bronze/silver/warehouse); table details work for canonical tables.  
- **V2 Catalog**: Unchanged and still works.  
- No table named `oil_production_status_raw` (or similar deprecated names) on legacy pages unless `include_deprecated=true`.  
- Counts are non-zero where tables have data (correct DB/schema per layer).  
- All pages and links remain available.
