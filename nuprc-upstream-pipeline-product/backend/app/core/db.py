import os
from sqlalchemy import create_engine

# Default to local SQLite for Windows dev (no Docker needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nuprc.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
