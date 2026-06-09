from typing import Literal, Optional

from pydantic import BaseModel, Field


class DataProductItem(BaseModel):
    product_id: str
    name: str
    display_name: Optional[str] = None
    subject_area: Optional[str] = None
    grain: Optional[str] = None
    description: Optional[str] = None
    schema_name: str = "gold"
    table_name: str
    layer: str = "gold"
    product_type: str = "analytical_data_product"
    status: Literal["available", "unavailable", "degraded"] = "unavailable"
    row_count: Optional[int] = None
    last_updated: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class DataProductsResponse(BaseModel):
    status: str = "available"
    items: list[DataProductItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
