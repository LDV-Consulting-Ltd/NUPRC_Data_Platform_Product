"""Relationship service — structural relationships from confirmed metadata only."""
from app.tanna_connector.config import MODULE_ID, PRIMARY_GOLD_TABLES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import relationship_id


def get_relationships() -> dict:
    oil_dp = PRIMARY_GOLD_TABLES["gold_oil_fact_production"]["id"]
    gas_dp = PRIMARY_GOLD_TABLES["gold_gas_fact_production"]["id"]
    rig_dp = PRIMARY_GOLD_TABLES["gold_rig_fact_activity"]["id"]
    con_dp = PRIMARY_GOLD_TABLES["gold_concession_fact_snapshot"]["id"]

    items = [
        {
            "id": relationship_id("gold_oil_fact_production", "depends_on", "gold_oil_dim_operator"),
            "external_id": relationship_id("gold_oil_fact_production", "depends_on", "gold_oil_dim_operator"),
            "module_id": MODULE_ID,
            "source_object_id": oil_dp,
            "source_object_type": "data_product",
            "relationship_type": "depends_on",
            "target_object_id": "gold.gold_oil_dim_operator",
            "target_object_type": "dimension_table",
            "description": "gold_oil_fact_production depends_on gold_oil_dim_operator (FK)",
            "confidence": 0.95,
            "status": "active",
        },
        {
            "id": relationship_id("gold_gas_fact_production", "depends_on", "gold_gas_dim_operator"),
            "external_id": relationship_id("gold_gas_fact_production", "depends_on", "gold_gas_dim_operator"),
            "module_id": MODULE_ID,
            "source_object_id": gas_dp,
            "source_object_type": "data_product",
            "relationship_type": "depends_on",
            "target_object_id": "gold.gold_gas_dim_operator",
            "target_object_type": "dimension_table",
            "description": "gold_gas_fact_production depends_on gold_gas_dim_operator (FK)",
            "confidence": 0.95,
            "status": "active",
        },
        {
            "id": relationship_id("gold_rig_fact_activity", "depends_on", "gold_rig_dim_operator"),
            "external_id": relationship_id("gold_rig_fact_activity", "depends_on", "gold_rig_dim_operator"),
            "module_id": MODULE_ID,
            "source_object_id": rig_dp,
            "source_object_type": "data_product",
            "relationship_type": "depends_on",
            "target_object_id": "gold.gold_rig_dim_operator",
            "target_object_type": "dimension_table",
            "description": "gold_rig_fact_activity depends_on gold_rig_dim_operator (FK)",
            "confidence": 0.95,
            "status": "active",
        },
        {
            "id": relationship_id("gold_concession_fact_snapshot", "depends_on", "gold_concession_dim_concession"),
            "external_id": relationship_id("gold_concession_fact_snapshot", "depends_on", "gold_concession_dim_concession"),
            "module_id": MODULE_ID,
            "source_object_id": con_dp,
            "source_object_type": "data_product",
            "relationship_type": "depends_on",
            "target_object_id": "gold.gold_concession_dim_concession",
            "target_object_type": "dimension_table",
            "description": "gold_concession_fact_snapshot depends_on gold_concession_dim_concession (FK)",
            "confidence": 0.95,
            "status": "active",
        },
        {
            "id": relationship_id("ingested_document", "produces", "bronze_etl_oil_production_raw"),
            "external_id": relationship_id("ingested_document", "produces", "bronze_etl_oil_production_raw"),
            "module_id": MODULE_ID,
            "source_object_id": "petrocore:entity:ingested_document:lineage",
            "source_object_type": "ingested_document",
            "relationship_type": "produces",
            "target_object_id": "bronze.etl_oil_production_raw",
            "target_object_type": "bronze_table",
            "description": "Downloaded file ingested into bronze (catalog lineage)",
            "confidence": 0.85,
            "status": "active",
        },
        {
            "id": relationship_id("bronze_etl_oil_production_raw", "produces", "gold_oil_fact_production"),
            "external_id": relationship_id("bronze_etl_oil_production_raw", "produces", "gold_oil_fact_production"),
            "module_id": MODULE_ID,
            "source_object_id": "bronze.etl_oil_production_raw",
            "source_object_type": "bronze_table",
            "relationship_type": "produces",
            "target_object_id": oil_dp,
            "target_object_type": "data_product",
            "description": "Bronze ETL transforms to gold oil production mart",
            "confidence": 0.85,
            "status": "active",
        },
    ]

    return build_envelope(
        object_type="relationships",
        implementation_status="partial",
        items=items,
        source="gold FK structure, catalog lineage, ETL medallion mapping",
        notes="Structural relationships only. No graph database.",
    )
