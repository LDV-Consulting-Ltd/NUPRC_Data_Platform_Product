"""Contract validation for PetroCore Tanna connector responses (v0.2.1)."""
from typing import Any

from pydantic import ValidationError

from app.tanna_connector.contract_schemas import (
    ConnectorEnvelopeSchema,
    DecisionProductItemSchema,
    ENDPOINT_OBJECT_TYPES,
    EntityItemSchema,
    EntityTypeSummarySchema,
    ITEM_SCHEMAS,
    VALID_IMPLEMENTATION_STATUSES,
)
from app.tanna_connector.external_ids import MODULE_PREFIX


def validate_envelope(payload: dict[str, Any]) -> ConnectorEnvelopeSchema:
    return ConnectorEnvelopeSchema.model_validate(payload)


def validate_items(object_type: str, items: list[Any], implementation_status: str) -> list[str]:
    """Validate items for object_type; return list of error messages (empty if valid)."""
    errors: list[str] = []

    if implementation_status == "not_implemented":
        if items:
            errors.append(f"{object_type}: not_implemented must return empty items")
        return errors

    if implementation_status == "placeholder":
        for i, item in enumerate(items):
            try:
                DecisionProductItemSchema.model_validate(item)
            except ValidationError as exc:
                errors.append(f"{object_type}[{i}] placeholder schema: {exc}")
        return errors

    schema = ITEM_SCHEMAS.get(object_type)
    if not schema:
        return errors

    for i, item in enumerate(items):
        try:
            if object_type == "entities":
                if item.get("id"):
                    EntityItemSchema.model_validate(item)
                else:
                    EntityTypeSummarySchema.model_validate(item)
            else:
                schema.model_validate(item)
        except ValidationError as exc:
            errors.append(f"{object_type}[{i}]: {exc}")

        ext_id = item.get("external_id")
        if ext_id and not str(ext_id).startswith(f"{MODULE_PREFIX}:"):
            errors.append(f"{object_type}[{i}]: external_id must start with '{MODULE_PREFIX}:'")

    return errors


def validate_full_response(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        envelope = validate_envelope(payload)
    except ValidationError as exc:
        return [f"envelope: {exc}"]

    if envelope.implementation_status not in VALID_IMPLEMENTATION_STATUSES:
        errors.append(f"invalid implementation_status: {envelope.implementation_status}")

    errors.extend(
        validate_items(
            envelope.object_type,
            envelope.items,
            envelope.implementation_status,
        )
    )
    return errors


def assert_external_id_prefix(external_id: str) -> bool:
    return str(external_id).startswith(f"{MODULE_PREFIX}:")
