from app.tanna_connector.mocks.patterns_empty import FUTURE_CANDIDATES, MESSAGE
from app.tanna_connector.schemas.pattern import PatternsResponse


def build_patterns() -> PatternsResponse:
    return PatternsResponse(
        status="not_implemented",
        items=[],
        message=MESSAGE,
        future_candidates=FUTURE_CANDIDATES,
    )
