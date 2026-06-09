from app.tanna_connector.schemas.relationship import RelationshipItem, RelationshipsResponse

STATIC_RELATIONSHIPS = [
    ("rel:oil-operated-by", "OilProduction", "OPERATED_BY", "Operator", "gold_oil_fact_production FK", 0.95),
    ("rel:oil-observed-on", "OilProduction", "OBSERVED_ON", "CalendarDate", "gold_oil_fact_production.date_key", 0.95),
    ("rel:gas-operated-by", "GasProduction", "OPERATED_BY", "Operator", "gold_gas_fact_production FK", 0.95),
    ("rel:gas-observed-on", "GasProduction", "OBSERVED_ON", "CalendarDate", "gold_gas_fact_production.date_key", 0.95),
    ("rel:rig-operated-by", "RigActivity", "OPERATED_BY", "Operator", "gold_rig_fact_activity FK", 0.95),
    ("rel:rig-uses-rig", "RigActivity", "USES_RIG", "Rig", "gold_rig_fact_activity.rig_sk", 0.95),
    ("rel:rig-observed-on", "RigActivity", "OBSERVED_ON", "CalendarDate", "gold_rig_fact_activity.date_key", 0.95),
    ("rel:conc-describes", "ConcessionSnapshot", "DESCRIBES", "Concession", "gold_concession_fact_snapshot FK", 0.95),
    ("rel:conc-observed-on", "ConcessionSnapshot", "OBSERVED_ON", "CalendarDate", "gold_concession_fact_snapshot.report_date_key", 0.95),
    ("rel:doc-ingested-bronze", "IngestedDocument", "INGESTED_INTO", "BronzeTable", "data_catalog.downloaded_files.bronze_table", 0.9),
    ("rel:bronze-transformed-gold", "BronzeTable", "TRANSFORMED_TO", "GoldMart", "catalog_registry canonical pipeline", 0.85),
]


def build_relationships() -> RelationshipsResponse:
    items = [
        RelationshipItem(
            relationship_id=rid,
            source_type=src,
            relationship_type=rel,
            target_type=tgt,
            confidence=conf,
            backing_source=backing,
            status="available",
            description=f"{src} {rel} {tgt}",
        )
        for rid, src, rel, tgt, backing, conf in STATIC_RELATIONSHIPS
    ]
    return RelationshipsResponse(status="available", items=items)
