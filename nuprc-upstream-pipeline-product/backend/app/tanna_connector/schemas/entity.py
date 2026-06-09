from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EntityTypeItem(BaseModel):
    entity_type: str
    slug: str
    status: Literal["available", "unavailable", "degraded"] = "unavailable"
    count: Optional[int] = None
    backing_tables: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class EntitiesResponse(BaseModel):
    status: str = "available"
    items: list[EntityTypeItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EntitySampleResponse(BaseModel):
    entity_type: str
    slug: str
    status: Literal["available", "unavailable", "degraded"] = "unavailable"
    limit: int
    offset: int
    total: Optional[int] = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
