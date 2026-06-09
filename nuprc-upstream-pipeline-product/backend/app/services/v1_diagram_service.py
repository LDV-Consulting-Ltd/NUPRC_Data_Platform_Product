"""
Generate and store v1 pipeline diagrams after successful ETL runs.
Failure-tolerant: never raises; logs warnings only.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from app.core.db import engine

logger = logging.getLogger(__name__)

PIPELINE_FLOW_MERMAID = """flowchart LR
    A[POST /v1/pipeline/runs] --> B[etl/scrape.py]
    B --> C[etl/acquire.py]
    C --> D[bronze.etl_oil_production_raw]
    C --> E[bronze.etl_gas_production_raw]
    C --> F[bronze.etl_rig_disposition_raw]
    C --> G[bronze.etl_concessions_raw]
    D --> H[silver.fact_oil_production]
    E --> I[silver.fact_gas_production]
    F --> J[silver.fact_rig_disposition]
    G --> K[silver.fact_concession_status]
    H --> L[gold.gold_oil_fact_production]
    I --> M[gold.gold_gas_fact_production]
    J --> N[gold.gold_rig_fact_activity]
    K --> O[gold.gold_concession_fact_snapshot]
    L --> P[data_catalog.available_tables]
    M --> P
    N --> P
    O --> P
    P --> Q[/catalog and /warehouse APIs/]
    Q --> R[Frontend pages]
"""

V1_DATA_MODEL_MERMAID = """erDiagram
    ETL_OIL_RAW ||--o{ FACT_OIL : transforms_to
    ETL_GAS_RAW ||--o{ FACT_GAS : transforms_to
    ETL_RIG_RAW ||--o{ FACT_RIG : transforms_to
    ETL_CONC_RAW ||--o{ FACT_CONC : transforms_to
    FACT_OIL ||--o{ GOLD_OIL : loads_to
    FACT_GAS ||--o{ GOLD_GAS : loads_to
    FACT_RIG ||--o{ GOLD_RIG : loads_to
    FACT_CONC ||--o{ GOLD_CONC : loads_to
    GOLD_OIL ||--o{ AVAILABLE_TABLES : registers_in
    GOLD_GAS ||--o{ AVAILABLE_TABLES : registers_in
    GOLD_RIG ||--o{ AVAILABLE_TABLES : registers_in
    GOLD_CONC ||--o{ AVAILABLE_TABLES : registers_in

    ETL_OIL_RAW {
        text source_key
        text file_url
        text file_sha256
        timestamptz downloaded_at
        jsonb row_data
    }
    ETL_GAS_RAW {
        text source_key
        text file_url
        jsonb row_data
    }
    ETL_RIG_RAW {
        text source_key
        text file_url
        jsonb row_data
    }
    ETL_CONC_RAW {
        text source_key
        text file_url
        jsonb row_data
    }
    FACT_OIL {
        bigint id PK
        date report_period
        text operator_name
        numeric production_volume
    }
    FACT_GAS {
        bigint id PK
        date report_period
        numeric production_volume
    }
    FACT_RIG {
        bigint id PK
        date report_date
        text rig_name
        text rig_status
    }
    FACT_CONC {
        bigint id PK
        date report_period
        text concession_status
    }
    GOLD_OIL {
        bigint id PK
        int date_key FK
        numeric production_volume
    }
    GOLD_GAS {
        bigint id PK
        int date_key FK
        numeric production_volume
    }
    GOLD_RIG {
        bigint id PK
        int date_key FK
        text rig_status
    }
    GOLD_CONC {
        bigint id PK
        int report_date_key FK
        text concession_status
    }
    AVAILABLE_TABLES {
        text schema_name
        text table_name
        text table_type
        bigint row_count
    }
"""

_DIAGRAM_SPECS: list[tuple[str, str]] = [
    ("pipeline_flow", PIPELINE_FLOW_MERMAID),
    ("v1_data_model", V1_DATA_MODEL_MERMAID),
]

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_diagrams (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    diagram_type TEXT NOT NULL,
    diagram_content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""


def store_v1_diagrams_after_run(run_id: str | None = None) -> dict[str, Any]:
    """
    Create pipeline_diagrams if needed and insert v1 flow + data-model diagrams.
    Safe to call after successful ETL; failures are logged and returned, never raised.
    """
    stored: list[str] = []
    try:
        with engine.begin() as cxn:
            cxn.execute(text(_CREATE_TABLE_SQL))
            for diagram_type, content in _DIAGRAM_SPECS:
                cxn.execute(
                    text("""
                        INSERT INTO pipeline_diagrams (diagram_type, diagram_content)
                        VALUES (:diagram_type, :content)
                    """),
                    {"diagram_type": diagram_type, "content": content},
                )
                stored.append(diagram_type)
        logger.info("Stored v1 diagrams after run %s: %s", run_id, ", ".join(stored))
        return {"ok": True, "stored": stored, "run_id": run_id}
    except Exception as exc:
        logger.warning("v1 diagram storage skipped for run %s: %s", run_id, exc)
        return {"ok": False, "stored": stored, "run_id": run_id, "warning": str(exc)}
