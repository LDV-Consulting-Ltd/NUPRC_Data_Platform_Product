"""Standard Tanna connector response envelope with sync readiness (v0.2.1)."""
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.tanna_connector.contract_validation import validate_full_response
from app.tanna_connector.sync_readiness import get_sync_readiness

ImplementationStatus = Literal[
    "implemented", "partial", "placeholder", "not_implemented"
]


class ConnectorMetadata(BaseModel):
    source: str
    notes: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    warnings: list[str] = Field(default_factory=list)
    sync_ready: bool = False
    sync_notes: str = ""
    external_id_strategy: str = ""
    duplicate_handling_notes: str = ""


class ConnectorEnvelope(BaseModel):
    module_id: str = "petrocore"
    module_name: str = "PetroCore"
    object_type: str
    implementation_status: ImplementationStatus
    items: list[Any] = Field(default_factory=list)
    metadata: ConnectorMetadata


def build_envelope(
    object_type: str,
    implementation_status: ImplementationStatus,
    items: list[Any],
    source: str,
    notes: str = "",
    warnings: list[str] | None = None,
    sync_ready: bool | None = None,
    sync_notes: str = "",
    external_id_strategy: str = "",
    duplicate_handling_notes: str = "",
    validate: bool = True,
) -> dict[str, Any]:
    readiness = get_sync_readiness(object_type)
    payload = ConnectorEnvelope(
        object_type=object_type,
        implementation_status=implementation_status,
        items=items,
        metadata=ConnectorMetadata(
            source=source,
            notes=notes,
            warnings=warnings or [],
            sync_ready=sync_ready if sync_ready is not None else readiness["sync_ready"],
            sync_notes=sync_notes or readiness["sync_notes"],
            external_id_strategy=external_id_strategy or readiness["external_id_strategy"],
            duplicate_handling_notes=(
                duplicate_handling_notes or readiness["duplicate_handling_notes"]
            ),
        ),
    ).model_dump()

    if validate:
        errors = validate_full_response(payload)
        if errors:
            payload["metadata"]["warnings"] = list(payload["metadata"]["warnings"]) + [
                f"contract_validation: {e}" for e in errors[:5]
            ]
    return payload
