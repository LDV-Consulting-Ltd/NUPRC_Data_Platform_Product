from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class HealthComponent(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "down", "unknown"]
    score: Optional[int] = None
    message: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "down"]
    score: int = Field(ge=0, le=100)
    components: list[HealthComponent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: str
