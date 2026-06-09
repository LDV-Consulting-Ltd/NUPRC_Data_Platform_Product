from contextlib import asynccontextmanager
import logging
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import runs, quality, diagrams, warehouse, health, pipeline, catalog, v1_pipeline
from app.routers import v1_catalog  # alias only: /v1/catalog/* -> same as /catalog/*
from app.tanna_connector.router import router as petrocore_tanna_router
from .models.run_store import init_run_tables
from .models.schemas import init_all_schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from app.tanna_connector.security import log_token_configuration_status
    log_token_configuration_status()
    init_run_tables()
    init_all_schemas()
    yield
    # Shutdown (if needed in the future)


app = FastAPI(title="NUPRC Upstream Pipeline API", lifespan=lifespan)


def _safe_detail(exc: Exception) -> str:
    """Build error detail string using ASCII replacement to avoid Windows UnicodeEncodeError."""
    try:
        msg = str(exc) if exc is not None else "None"
    except Exception:
        msg = "<error message could not be stringified>"
    try:
        tb = traceback.format_exc()
    except Exception:
        tb = ""
    raw = f"{type(exc).__name__}: {msg}\n{tb}"
    return raw.encode("ascii", errors="replace").decode("ascii")


@app.exception_handler(Exception)
def unhandled_exception_handler(request, exc):
    """Return 500 with error detail so the frontend can show the real cause."""
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": _safe_detail(exc)},
    )


# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router)
app.include_router(quality.router)
app.include_router(diagrams.router)
app.include_router(warehouse.router)
app.include_router(health.router)
app.include_router(pipeline.router)
app.include_router(catalog.router)
app.include_router(v1_catalog.router)  # deprecated alias; use /catalog/*
app.include_router(v1_pipeline.router)
app.include_router(petrocore_tanna_router)

@app.get("/")
def root():
    return {"ok": True, "service": "nuprc-upstream-pipeline-api"}
