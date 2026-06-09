from app.tanna_connector.mocks.decision_products_stub import STUB_DECISION_PRODUCTS
from app.tanna_connector.schemas.decision_product import DecisionProductItem, DecisionProductsResponse


def build_decision_products() -> DecisionProductsResponse:
    items = [
        DecisionProductItem(
            decision_product_id=stub["decision_product_id"],
            name=stub["name"],
            description=stub["description"],
            source_data_products=stub["source_data_products"],
            missing_capabilities=stub["missing_capabilities"],
            next_steps=stub["next_steps"],
        )
        for stub in STUB_DECISION_PRODUCTS
    ]
    return DecisionProductsResponse(
        status="stub",
        items=items,
        message="Decision products are metadata-only stubs. Export bundles are not implemented.",
        warnings=["All decision products are clearly labeled stub/metadata_only responses."],
    )
