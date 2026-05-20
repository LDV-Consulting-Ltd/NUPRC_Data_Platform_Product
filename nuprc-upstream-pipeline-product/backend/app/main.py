from contextlib import asynccontextmanager
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import runs, quality, diagrams, warehouse, health, pipeline, catalog, v1_pipeline, regulatory, governance
from app.routers import v1_catalog  # alias only: /v1/catalog/* -> same as /catalog/*
from app.models.pg_schemas import init_pg_schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pg_schemas()
    yield


app = FastAPI(title="NUPRC Upstream Pipeline API", lifespan=lifespan)


def _safe_detail(exc: Exception) -> str:
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
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": _safe_detail(exc)},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
app.include_router(v1_catalog.router)
app.include_router(v1_pipeline.router)
app.include_router(regulatory.router)
app.include_router(governance.router)


@app.get("/")
def root():
    return {"ok": True, "service": "nuprc-upstream-pipeline-api"}
