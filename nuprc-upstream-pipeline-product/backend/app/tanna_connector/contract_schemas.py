"""Tanna connector contract schemas for envelope and item validation (v0.2.1)."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

ImplementationStatus = Literal[
    "implemented", "partial", "placeholder", "not_implemented"
]

VALID_IMPLEMENTATION_STATUSES = frozenset({
    "implemented", "partial", "placeholder", "not_implemented",
})


class ConnectorMetadataSchema(BaseModel):
    source: str
    notes: str = ""
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
    sync_ready: bool
    sync_notes: str
    external_id_strategy: str
    duplicate_handling_notes: str


class ConnectorEnvelopeSchema(BaseModel):
    module_id: Literal["petrocore"]
    module_name: Literal["PetroCore"]
    object_type: str
    implementation_status: ImplementationStatus
    items: list[Any] = Field(default_factory=list)
    metadata: ConnectorMetadataSchema


class ManifestItemSchema(BaseModel):
    module_id: str
    module_name: str
    connector_version: str
    api_version: str
    supported_object_types: list[str]


class HealthComponentSchema(BaseModel):
    name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthItemSchema(BaseModel):
    status: str
    components: list[HealthComponentSchema]


class StatusMatrixEntrySchema(BaseModel):
    object_type: str
    implementation_status: ImplementationStatus
    notes: str


class StatusItemSchema(BaseModel):
    connector_version: str
    module_id: str
    module_name: str
    overall_status: str
    endpoint_maturity_matrix: list[StatusMatrixEntrySchema]
    implemented_objects: list[str]
    partial_objects: list[str]
    placeholder_objects: list[str]
    not_implemented_objects: list[str]
    last_generated_at: str


class DataProductItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    name: str


class EntityItemSchema(BaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    module_id: Optional[str] = None
    entity_type: str


class EntityTypeSummarySchema(BaseModel):
    entity_type: str
    backing_table: Optional[str] = None
    count: Optional[int] = None


class RelationshipItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    source_object_id: str
    relationship_type: str
    target_object_id: str
    confidence: float = Field(ge=0.0, le=1.0)


class SignalItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    name: str
    signal_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    detected_at: str


class IlluminationItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    title: str
    summary: str
    related_signals: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class DecisionProductItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    name: str
    status: Literal["draft"]
    placeholder: Literal[True]
    note: str


class KnowledgeAssetItemSchema(BaseModel):
    id: str
    external_id: str
    module_id: str
    title: str
    asset_type: str


ITEM_SCHEMAS: dict[str, type[BaseModel]] = {
    "manifest": ManifestItemSchema,
    "health": HealthItemSchema,
    "status": StatusItemSchema,
    "data_products": DataProductItemSchema,
    "entities": EntityItemSchema,
    "relationships": RelationshipItemSchema,
    "signals": SignalItemSchema,
    "illuminations": IlluminationItemSchema,
    "decision_products": DecisionProductItemSchema,
    "knowledge_assets": KnowledgeAssetItemSchema,
}

ENDPOINT_OBJECT_TYPES = [
    "manifest",
    "health",
    "data_products",
    "entities",
    "relationships",
    "signals",
    "patterns",
    "illuminations",
    "decision_products",
    "knowledge_assets",
]
