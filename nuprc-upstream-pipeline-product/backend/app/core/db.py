"""
Database connection: PostgreSQL only.

Local dev: Docker Postgres (`docker compose up -d` in repo root).
Production: Supabase Postgres via `DATABASE_URL` (Project Settings → Database).

Schema uses JSONB, TIMESTAMPTZ, GENERATED ALWAYS AS IDENTITY, and CREATE SCHEMA —
not compatible with SQLite.
"""
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/nuprc",
)

_scheme = (DATABASE_URL or "").split(":", 1)[0].lower()
if DATABASE_URL and _scheme not in ("postgresql", "postgresql+psycopg", "postgresql+psycopg2"):
    raise ValueError(
        "Only PostgreSQL is supported. Set DATABASE_URL to a postgresql:// or "
        "postgresql+psycopg:// URL (local Docker or Supabase). SQLite is not supported."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
