# Pipeline Execution Steps

The pipeline follows these steps in order:

## Step 1: Scrape 4 NUPRC Sources & Download Files
- **Function**: `scrape_and_download_sources()`
- **What it does**:
  - Scrapes 4 sources: Concession, Oil, Gas, Rig
  - Downloads all available files (PDF/Excel)
  - Filters: Oil/Gas/Rig prefer Excel, Concession uses PDF
  - Skips duplicate files (already downloaded)
- **Output**: List of downloaded file info
- **Logs**: `📥 STEP 1: Scraping and downloading...`

## Step 2: Extract Tables & Load into Bronze Layer
- **Function**: `extract_and_load_bronze()`
- **What it does**:
  - Extracts tables from Excel/PDF files
  - Uses optimized loaders per source type
  - Loads structured data into `bronze` table (JSONB format)
  - Updates data catalog after each batch
- **Output**: Number of rows loaded
- **Logs**: `📦 STEP 2: Extracting and loading to bronze...`
- **Note**: Skipped if no new files downloaded (uses existing bronze data)

## Step 3: Transform to Silver with Fuzzy Column Matching
- **Function**: `transform_to_silver()`
- **What it does**:
  - Reads from bronze layer
  - Applies fuzzy column matching for schema drift
  - Standardizes column names and data types
  - Loads cleaned data into `silver` table
- **Output**: None (transforms in place)
- **Logs**: `✨ STEP 3: Transforming to silver...`

## Step 4: Load Warehouse Dimensional Model
- **Function**: `load_warehouse()`
- **What it does**:
  - Creates dimensional model (star schema)
  - Populates dimension tables (dim_date, dim_company, etc.)
  - Populates fact tables from silver data
  - Organizes data for analytics
- **Output**: None (loads into warehouse schema)
- **Logs**: `🏭 STEP 4: Loading warehouse...`

## Step 5: Generate Data Model Diagrams
- **Function**: `generate_diagrams()`
- **What it does**:
  - Generates Mermaid ER diagram
  - Saves diagram to file
  - Stores diagram in database for API access
- **Output**: Diagram file and database record
- **Logs**: `📊 STEP 5: Generating diagrams...`
- **Note**: Non-critical step (warnings logged if fails)

## Final Step: Refresh Data Catalog
- **Function**: `refresh_available_tables()`
- **What it does**:
  - Scans all tables (bronze, silver, warehouse)
  - Updates `data_catalog.available_tables` view
  - Makes tables visible in frontend
- **Output**: Updated catalog
- **Logs**: `Refreshing catalog with all tables...`

## Pipeline Completion
- Marks run as `SUCCESS` or `FAILED`
- Logs total rows loaded
- Returns run status

## Error Handling
- Each step has try/except with detailed error logging
- Pipeline continues even if Step 5 (diagrams) fails
- Timeout protection: 2 hours max execution time
- Cancellation support: Can cancel running pipeline

## Monitoring
Watch backend terminal for:
```
🔥🔥🔥 ENDPOINT CALLED: POST /pipeline/run 🔥🔥🔥
🚀 [MAIN] Starting pipeline thread...
🔥🔥🔥 THREAD EXECUTING - Pipeline starting! 🔥🔥🔥
🔥🔥🔥 execute_pipeline() FUNCTION CALLED! 🔥🔥🔥
📥 STEP 1: Scraping and downloading...
📦 STEP 2: Extracting and loading to bronze...
✨ STEP 3: Transforming to silver...
🏭 STEP 4: Loading warehouse...
📊 STEP 5: Generating diagrams...
✅✅✅ THREAD COMPLETE - Pipeline finished! ✅✅✅
```
