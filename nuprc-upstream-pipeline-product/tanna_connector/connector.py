"""PetroCore Tanna Connector v1 — read-only SDK implementation."""

from tanna_connector_sdk.base_connector import TannaConnector
from tanna_connector_sdk.schemas import (
    ConnectorDataProduct,
    ConnectorDecisionProduct,
    ConnectorEntity,
    ConnectorHealthResponse,
    ConnectorIllumination,
    ConnectorKnowledgeAsset,
    ConnectorManifest,
    ConnectorPattern,
    ConnectorRelationship,
    ConnectorSignal,
)

from tanna_connector import mapper


class PetroCoreTannaConnector(TannaConnector):
    """Exposes confirmed PetroCore intelligence objects to Tanna Core via the SDK contract."""

    def get_health(self) -> ConnectorHealthResponse:
        return mapper.map_health()

    def get_manifest(self) -> ConnectorManifest:
        return mapper.map_manifest()

    def get_data_products(self) -> list[ConnectorDataProduct]:
        return mapper.map_data_products()

    def get_entities(self) -> list[ConnectorEntity]:
        return mapper.map_entities()

    def get_relationships(self) -> list[ConnectorRelationship]:
        return mapper.map_relationships()

    def get_signals(self) -> list[ConnectorSignal]:
        return mapper.map_signals()

    def get_patterns(self) -> list[ConnectorPattern]:
        return mapper.map_patterns()

    def get_illuminations(self) -> list[ConnectorIllumination]:
        return mapper.map_illuminations()

    def get_decision_products(self) -> list[ConnectorDecisionProduct]:
        return mapper.map_decision_products()

    def get_knowledge_assets(self) -> list[ConnectorKnowledgeAsset]:
        return mapper.map_knowledge_assets()
