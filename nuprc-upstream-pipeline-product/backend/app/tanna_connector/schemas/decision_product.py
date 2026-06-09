from typing import Literal

from pydantic import BaseModel, Field


class DecisionProductItem(BaseModel):
    decision_product_id: str
    name: str
    status: Literal["stub"] = "stub"
    implementation_status: Literal["metadata_only"] = "metadata_only"
    source_data_products: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    description: str = ""


class DecisionProductsResponse(BaseModel):
    status: str = "stub"
    items: list[DecisionProductItem] = Field(default_factory=list)
    message: str = "Decision products are metadata-only stubs. Export bundles are not implemented."
    warnings: list[str] = Field(default_factory=list)
