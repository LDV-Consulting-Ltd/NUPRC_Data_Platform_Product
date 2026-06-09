from typing import Literal, Optional

from pydantic import BaseModel, Field


class KnowledgeAssetItem(BaseModel):
    asset_id: str
    title: str
    asset_type: str
    path: Optional[str] = None
    summary: Optional[str] = None
    source: str
    status: Literal["available", "unavailable", "stub"] = "available"


class KnowledgeAssetsResponse(BaseModel):
    status: str = "available"
    items: list[KnowledgeAssetItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
