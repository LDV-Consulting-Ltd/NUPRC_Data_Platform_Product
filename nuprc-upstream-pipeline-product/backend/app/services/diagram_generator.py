# backend/app/services/diagram_generator.py
"""
Generate data model diagrams (Mermaid format).
"""
from sqlalchemy import text
from typing import Dict, List


def generate_mermaid_er_diagram() -> str:
    """
    Generate a Mermaid ER diagram of the data model.
    """
    diagram = """erDiagram
    %% Bronze Layer
    BRONZE_CONCESSION {
        bigint id PK
        text source_id
        text file_url
        text file_sha256
        date report_period
        jsonb raw_data
    }
    
    BRONZE_OIL {
        bigint id PK
        text source_id
        text file_url
        text file_sha256
        date report_period
        jsonb raw_data
    }
    
    BRONZE_GAS {
        bigint id PK
        text source_id
        text file_url
        text file_sha256
        date report_period
        jsonb raw_data
    }
    
    BRONZE_RIG {
        bigint id PK
        text source_id
        text file_url
        text file_sha256
        date report_period
        jsonb raw_data
    }
    
    %% Silver Layer
    SILVER_SCHEMA_DRIFT {
        bigint id PK
        text source_id
        text table_name
        text column_name
        text canonical_name
        numeric similarity_score
        text drift_type
    }
    
    %% Warehouse Dimensions
    DIM_DATE {
        integer date_key PK
        date date_actual
        integer year
        integer month
        integer quarter
    }
    
    DIM_OPERATOR {
        bigint operator_key PK
        text operator_name
        text operator_code
    }
    
    DIM_ASSET {
        bigint asset_key PK
        text asset_name
        text asset_type
        text block_name
        text field_name
    }
    
    %% Warehouse Facts
    FACT_OIL_PRODUCTION {
        bigint id PK
        integer date_key FK
        bigint operator_key FK
        bigint asset_key FK
        numeric production_volume
        text production_unit
    }
    
    FACT_GAS_PRODUCTION {
        bigint id PK
        integer date_key FK
        bigint operator_key FK
        bigint asset_key FK
        numeric production_volume
        text production_unit
    }
    
    FACT_RIG_ACTIVITY {
        bigint id PK
        integer date_key FK
        bigint operator_key FK
        bigint asset_key FK
        text rig_name
        text rig_status
    }
    
    FACT_CONCESSION_STATUS {
        bigint id PK
        integer date_key FK
        bigint operator_key FK
        bigint asset_key FK
        text concession_status
    }
    
    %% Relationships
    DIM_DATE ||--o{ FACT_OIL_PRODUCTION : "has"
    DIM_DATE ||--o{ FACT_GAS_PRODUCTION : "has"
    DIM_DATE ||--o{ FACT_RIG_ACTIVITY : "has"
    DIM_DATE ||--o{ FACT_CONCESSION_STATUS : "has"
    
    DIM_OPERATOR ||--o{ FACT_OIL_PRODUCTION : "operates"
    DIM_OPERATOR ||--o{ FACT_GAS_PRODUCTION : "operates"
    DIM_OPERATOR ||--o{ FACT_RIG_ACTIVITY : "operates"
    DIM_OPERATOR ||--o{ FACT_CONCESSION_STATUS : "holds"
    
    DIM_ASSET ||--o{ FACT_OIL_PRODUCTION : "produces"
    DIM_ASSET ||--o{ FACT_GAS_PRODUCTION : "produces"
    DIM_ASSET ||--o{ FACT_RIG_ACTIVITY : "hosts"
    DIM_ASSET ||--o{ FACT_CONCESSION_STATUS : "covers"
"""
    return diagram


def save_diagram(diagram_text: str, filename: str = "data_model.mmd"):
    """Save diagram to file."""
    from pathlib import Path
    diagram_dir = Path("data/diagrams")
    diagram_dir.mkdir(parents=True, exist_ok=True)
    
    diagram_path = diagram_dir / filename
    diagram_path.write_text(diagram_text, encoding='utf-8')
    
    return str(diagram_path)
