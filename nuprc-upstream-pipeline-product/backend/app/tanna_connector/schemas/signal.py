from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SignalItem(BaseModel):
    signal_id: str
    signal_type: str
    severity: Literal["info", "warning", "critical"]
    title: str
    description: str
    source: str
    detected_at: str
    confidence: float = Field(ge=0.0, le=1.0)
    backing_data: dict[str, Any] = Field(default_factory=dict)
    related_entities: list[str] = Field(default_factory=list)
    related_data_products: list[str] = Field(default_factory=list)


class SignalsResponse(BaseModel):
    status: str = "available"
    items: list[SignalItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
