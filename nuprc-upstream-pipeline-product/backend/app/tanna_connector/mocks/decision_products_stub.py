STUB_DECISION_PRODUCTS = [
    {
        "decision_product_id": "monthly-oil-gas-regulatory-submission",
        "name": "Monthly Oil & Gas Regulatory Submission",
        "description": "Pre-packaged monthly oil and gas production submission dataset for regulatory reporting.",
        "source_data_products": [
            "petrocore.oil-production",
            "petrocore.gas-production",
        ],
        "missing_capabilities": [
            "export_bundle_generation",
            "regulatory_versioning",
            "approval_workflow",
        ],
        "next_steps": [
            "Define submission schema contract",
            "Add read-only export endpoint",
            "Attach audit metadata",
        ],
    },
    {
        "decision_product_id": "concession-compliance-snapshot",
        "name": "Concession Compliance Snapshot",
        "description": "Point-in-time concession register snapshot for compliance review.",
        "source_data_products": ["petrocore.concession-snapshot"],
        "missing_capabilities": [
            "snapshot_versioning",
            "compliance_rule_engine",
            "export_bundle_generation",
        ],
        "next_steps": [
            "Define compliance snapshot grain",
            "Add snapshot export format",
        ],
    },
    {
        "decision_product_id": "rig-activity-oversight-brief",
        "name": "Rig Activity Oversight Brief",
        "description": "Operational brief summarizing rig disposition and activity for oversight teams.",
        "source_data_products": ["petrocore.rig-activity"],
        "missing_capabilities": [
            "narrative_brief_generation",
            "export_bundle_generation",
            "scheduled_delivery",
        ],
        "next_steps": [
            "Define brief template",
            "Add aggregation queries over gold_rig_fact_activity",
        ],
    },
]
