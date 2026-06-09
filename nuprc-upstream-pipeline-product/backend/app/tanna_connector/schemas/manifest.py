from typing import Any, Optional

from pydantic import BaseModel, Field


class ManifestResponse(BaseModel):
    product_id: str
    name: str
    connector_id: str
    connector_version: str
    source_system: str
    api_version: str
    domains: list[str]
    capabilities: list[str]
    canonical_layers: list[str]
    canonical_pipeline: str
    endpoints: list[str]
    backing_assets: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: str = "available"
