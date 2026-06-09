"""Bearer service-token authentication for /api/v1/tanna/* endpoints."""
import logging
import os
import secrets
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)
TOKEN_ENV_VAR = "TANNA_CONNECTOR_TOKEN"
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
_env_loaded = False


def _ensure_env_loaded() -> None:
    """Load backend/.env so TANNA_CONNECTOR_TOKEN is available at request time."""
    global _env_loaded
    if _env_loaded:
        return
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=False)
    _env_loaded = True


def _expected_token() -> str:
    _ensure_env_loaded()
    return os.environ.get(TOKEN_ENV_VAR, "").strip()


def log_token_configuration_status() -> None:
    """Safe startup log: configured or not, never the token value."""
    configured = bool(_expected_token())
    logger.info(
        "Tanna connector auth: %s configured via %s",
        "is" if configured else "is not",
        TOKEN_ENV_VAR,
    )


def require_connector_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing connector service token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected = _expected_token()
    if not expected:
        logger.warning("Tanna connector auth rejected: %s is not configured", TOKEN_ENV_VAR)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Connector auth not configured. Set {TOKEN_ENV_VAR} environment variable.",
        )

    received = credentials.credentials.strip()
    if not secrets.compare_digest(received, expected):
        logger.warning(
            "Tanna connector auth rejected: bearer token mismatch (%s is configured)",
            TOKEN_ENV_VAR,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid connector service token",
        )
    return received
