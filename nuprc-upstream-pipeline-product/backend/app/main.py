from fastapi import FastAPI
from app.routers import runs, quality, diagrams, warehouse, health

app = FastAPI(title="NUPRC Upstream Pipeline API")

app.include_router(runs.router)
app.include_router(quality.router)
app.include_router(diagrams.router)
app.include_router(warehouse.router)
app.include_router(health.router)

@app.get("/")
def root():
    return {"ok": True, "service": "nuprc-upstream-pipeline-api"}
