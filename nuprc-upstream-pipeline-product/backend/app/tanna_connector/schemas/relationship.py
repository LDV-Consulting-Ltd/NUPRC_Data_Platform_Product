from typing import Literal, Optional

from pydantic import BaseModel, Field


class RelationshipItem(BaseModel):
    relationship_id: str
    source_type: str
    relationship_type: str
    target_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    backing_source: str
    status: Literal["available", "unavailable", "stub"] = "available"
    description: Optional[str] = None


class RelationshipsResponse(BaseModel):
    status: str = "available"
    items: list[RelationshipItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
