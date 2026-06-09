from typing import Literal


def score_to_status(score: int) -> Literal["healthy", "degraded", "down"]:
    if score >= 80:
        return "healthy"
    if score >= 50:
        return "degraded"
    return "down"
