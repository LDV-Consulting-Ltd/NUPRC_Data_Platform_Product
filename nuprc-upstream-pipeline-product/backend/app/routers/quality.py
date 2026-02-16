from fastapi import APIRouter
router = APIRouter(prefix="/quality", tags=["quality"])
@router.get("/summary")
def summary(): return {"ok": True, "kpis": {}}
