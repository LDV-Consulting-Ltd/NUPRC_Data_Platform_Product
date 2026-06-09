"""Mount PetroCore Tanna Connector using the official SDK router factory."""
from tanna_connector_sdk.router import create_tanna_router

from tanna_connector.connector import PetroCoreTannaConnector

_connector = PetroCoreTannaConnector()

router = create_tanna_router(
    _connector,
    prefix="/api/v1/tanna",
    tags=["Tanna Connector"],
    token_env_var="TANNA_CONNECTOR_TOKEN",
)
