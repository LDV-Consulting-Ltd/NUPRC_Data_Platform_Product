"""Stable external_id generation for PetroCore Tanna connector objects."""
import hashlib
import re

MODULE_PREFIX = "petrocore"


def _slug(value: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return slug[:max_len] if slug else "unknown"


def external_id(object_type: str, *parts: str) -> str:
    """Build petrocore:{object_type}:{stable_parts...} external_id."""
    safe = [_slug(p) for p in parts if p is not None and str(p).strip()]
    return f"{MODULE_PREFIX}:{object_type}:{':'.join(safe)}"


def data_product_id(table_name: str) -> str:
    return external_id("data_product", table_name)


def entity_id(entity_type: str, key: str) -> str:
    return external_id("entity", entity_type, key)


def relationship_id(source: str, relationship_type: str, target: str) -> str:
    return external_id("relationship", source, relationship_type, target)


def signal_id(signal_type: str, stable_key: str) -> str:
    return external_id("signal", signal_type.lower(), stable_key)


def illumination_id(signal_external_id: str) -> str:
    suffix = signal_external_id.split(":", 2)[-1] if ":" in signal_external_id else signal_external_id
    return external_id("illumination", suffix)


def decision_product_id(slug: str) -> str:
    return external_id("decision_product", slug)


def knowledge_asset_id(category: str, name: str) -> str:
    return external_id("knowledge_asset", category, name)


def pattern_id(name: str = "reserved") -> str:
    return external_id("pattern", name)


def stable_hash_key(*parts: str) -> str:
    """Deterministic short key from stable inputs (not a random UUID)."""
    raw = ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]
