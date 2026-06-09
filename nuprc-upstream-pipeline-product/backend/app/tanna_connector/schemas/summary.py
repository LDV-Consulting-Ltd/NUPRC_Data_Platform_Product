from typing import Any

from pydantic import BaseModel, Field


class ConnectorSummaryResponse(BaseModel):
    product_id: str
    product_name: str
    connector_version: str
    health_status: str
    health_score: int
    data_product_count: int
    entity_type_count: int
    relationship_count: int
    active_signal_count: int
    implementation_gaps: list[str] = Field(default_factory=list)
    connector_readiness: str
    manifest_summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    generated_at: str
