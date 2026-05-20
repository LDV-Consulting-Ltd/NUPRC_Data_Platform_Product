# Legacy run store — delegates to meta.pipeline_run (PostgreSQL).
from app.models.pg_schemas import init_pg_schemas


def init_run_tables():
    """Create meta pipeline tables (Postgres-only)."""
    init_pg_schemas()
