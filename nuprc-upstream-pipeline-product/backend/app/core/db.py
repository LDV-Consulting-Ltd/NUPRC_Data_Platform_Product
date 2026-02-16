"""
Database connection: PostgreSQL only.
This application uses only PostgreSQL. SQLite is not supported (schema uses
JSONB, TIMESTAMPTZ, GENERATED ALWAYS AS IDENTITY, CREATE SCHEMA).
"""
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/nuprc",
)

# Enforce PostgreSQL only
if DATABASE_URL and "postgresql" not in DATABASE_URL.split(":")[0].lower():
    raise ValueError(
        "Only PostgreSQL is supported. Set DATABASE_URL to a postgresql:// URL "
        "(e.g. postgresql+psycopg://user:pass@localhost:5432/nuprc). SQLite is not supported."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
