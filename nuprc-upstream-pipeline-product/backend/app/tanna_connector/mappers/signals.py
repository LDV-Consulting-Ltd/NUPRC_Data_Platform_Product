from app.tanna_connector.schemas.signal import SignalsResponse
from app.tanna_connector.services.signal_generator import generate_signals


def build_signals() -> SignalsResponse:
    items, warnings = generate_signals()
    status = "available" if items or not warnings else "degraded"
    return SignalsResponse(status=status, items=items, warnings=warnings)
