from typing import Literal

from pydantic import BaseModel, Field


class IlluminationItem(BaseModel):
    illumination_id: str
    title: str
    narrative: str
    category: Literal["operational", "data_quality", "catalog", "freshness", "pipeline"]
    confidence: float = Field(ge=0.0, le=1.0)
    generated_from: list[str] = Field(default_factory=list)
    generated_at: str


class IlluminationsResponse(BaseModel):
    status: str = "available"
    items: list[IlluminationItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
