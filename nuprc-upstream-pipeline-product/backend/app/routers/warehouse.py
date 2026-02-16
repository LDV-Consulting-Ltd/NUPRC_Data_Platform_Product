from fastapi import APIRouter
router = APIRouter(prefix="/warehouse", tags=["warehouse"])
@router.get("/tables")
def tables(): return {"ok": True, "tables": []}
