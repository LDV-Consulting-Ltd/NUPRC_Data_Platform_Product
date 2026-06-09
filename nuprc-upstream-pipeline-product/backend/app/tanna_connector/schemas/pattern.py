from pydantic import BaseModel, Field


class PatternsResponse(BaseModel):
    status: str = "not_implemented"
    items: list = Field(default_factory=list)
    message: str
    future_candidates: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
