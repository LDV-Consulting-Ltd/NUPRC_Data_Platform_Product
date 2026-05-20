"""Generate and store Mermaid diagram definitions."""
from sqlalchemy import text

from app.core.db import engine

MERMAID = {
    "conceptual": """flowchart LR
  Sources[NUPRC Sources] --> Bronze[Bronze JSONB]
  Bronze --> Silver[Silver Standardized]
  Silver --> Warehouse[Warehouse Facts]
  Warehouse --> Products[Data Products]
""",
    "logical": """erDiagram
  OIL ||--o{ FACT : feeds
  GAS ||--o{ FACT : feeds
  RIG ||--o{ FACT : feeds
  CONCESSION ||--o{ FACT : feeds
  FACT }o--|| DIM_OPERATOR : has
  FACT }o--|| DIM_ASSET : has
""",
    "physical": """flowchart TB
  subgraph bronze
    oil[oil_production_status_raw]
    gas[gas_production_status_raw]
    rig[rig_disposition_raw]
    con[concession_situation_raw]
  end
  subgraph silver
    std[upstream_activity_standardized]
  end
  subgraph warehouse
    fact[fact_upstream_activity]
  end
  oil --> std
  gas --> std
  rig --> std
  con --> std
  std --> fact
""",
    "lineage": """flowchart LR
  S1[Oil Page] --> A1[Acquire]
  S2[Gas Page] --> A2[Acquire]
  S3[Rig Page] --> A3[Acquire]
  S4[Concession PDF] --> A4[Acquire]
  A1 --> B[Bronze Load]
  A2 --> B
  A3 --> B
  A4 --> B
  B --> SL[Silver]
  SL --> WH[Warehouse]
  WH --> CAT[Catalog Refresh]
""",
}


def save_diagrams(run_id: str) -> None:
    with engine.begin() as cxn:
        for dtype, content in MERMAID.items():
            cxn.execute(
                text("""
                    INSERT INTO meta.pipeline_diagrams (run_id, diagram_type, diagram_content)
                    VALUES (:run_id, :dtype, :content)
                """),
                {"run_id": run_id, "dtype": dtype, "content": content},
            )


def get_latest_diagrams() -> dict:
    out = {}
    with engine.connect() as cxn:
        for dtype in MERMAID:
            row = cxn.execute(
                text("""
                    SELECT diagram_content, created_at
                    FROM meta.pipeline_diagrams
                    WHERE diagram_type = :dtype
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"dtype": dtype},
            ).mappings().first()
            out[dtype] = {
                "mermaid": row["diagram_content"] if row else MERMAID[dtype],
                "created_at": str(row["created_at"]) if row else None,
            }
    return out
