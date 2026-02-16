"""
ETL config: DB URLs and paths.
Supports BRONZE_DB_URL, SILVER_DB_URL, GOLD_DB_URL or single DATABASE_URL with bronze/silver/gold schemas.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine

# Default single DB (same as app)
_DEFAULT_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/nuprc",
)


def _get_engine(url, fallback_url: str):
    u = url or fallback_url
    if u and "postgresql" not in u.split(":")[0].lower():
        raise ValueError("Only PostgreSQL is supported. Use postgresql+psycopg:// or postgresql:// URL.")
    return create_engine(u, pool_pre_ping=True) if u else None


def get_bronze_engine():
    url = os.getenv("BRONZE_DB_URL") or _DEFAULT_URL
    return _get_engine(url, _DEFAULT_URL)


def get_silver_engine():
    url = os.getenv("SILVER_DB_URL") or _DEFAULT_URL
    return _get_engine(url, _DEFAULT_URL)


def get_gold_engine():
    url = os.getenv("GOLD_DB_URL") or _DEFAULT_URL
    return _get_engine(url, _DEFAULT_URL)


def get_etl_engine():
    """Single engine for observability + all layers when using one DB."""
    return get_bronze_engine()


# Storage: data/raw/{source}/{yyyy-mm-dd}/ (absolute so Bronze load finds files regardless of cwd)
_DATA_RAW_DEFAULT = (Path(__file__).resolve().parent.parent / "data" / "raw").as_posix()
DATA_RAW = Path(os.getenv("ETL_DATA_RAW", _DATA_RAW_DEFAULT))
CONNECT_TIMEOUT = float(os.getenv("ETL_CONNECT_TIMEOUT", "15"))
READ_TIMEOUT = float(os.getenv("ETL_READ_TIMEOUT", "120"))
MAX_FILE_SIZE = int(os.getenv("ETL_MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
