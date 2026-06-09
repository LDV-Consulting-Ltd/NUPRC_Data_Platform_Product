"""Decision product service — placeholder shells only."""
from app.tanna_connector.config import MODULE_ID, PRIMARY_GOLD_TABLES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import decision_product_id

PLACEHOLDER_NOTE = (
    "Decision product shell only. No export bundle or approval workflow exists yet."
)

OIL_DP = PRIMARY_GOLD_TABLES["gold_oil_fact_production"]["id"]
GAS_DP = PRIMARY_GOLD_TABLES["gold_gas_fact_production"]["id"]
CON_DP = PRIMARY_GOLD_TABLES["gold_concession_fact_snapshot"]["id"]


def get_decision_products() -> dict:
    stubs = [
        {
            "slug": "monthly_upstream_production_review",
            "name": "Monthly Upstream Production Review",
            "description": "Draft placeholder for monthly upstream production oversight review.",
            "decision_type": "operational",
            "related": [OIL_DP, GAS_DP],
        },
        {
            "slug": "regulatory_production_oversight_brief",
            "name": "Regulatory Production Oversight Brief",
            "description": "Draft placeholder for regulatory production oversight brief.",
            "decision_type": "regulatory",
            "related": [OIL_DP, GAS_DP, CON_DP],
        },
        {
            "slug": "data_quality_remediation_review",
            "name": "Data Quality Remediation Review",
            "description": "Draft placeholder for data quality remediation review.",
            "decision_type": "data_quality",
            "related": [],
        },
    ]
    items = []
    for stub in stubs:
        eid = decision_product_id(stub["slug"])
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "name": stub["name"],
            "description": stub["description"],
            "decision_type": stub["decision_type"],
            "status": "draft",
            "placeholder": True,
            "note": PLACEHOLDER_NOTE,
            "related_intelligence_products": stub["related"],
            "owner": "LDV",
        })

    return build_envelope(
        object_type="decision_products",
        implementation_status="placeholder",
        items=items,
        source="petrocore.tanna_connector.decision_product_service",
        notes=PLACEHOLDER_NOTE,
        sync_ready=False,
    )
