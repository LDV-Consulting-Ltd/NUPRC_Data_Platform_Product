from fastapi import APIRouter
router = APIRouter(prefix="/health", tags=["health"])
@router.get("/summary")
def health(): return {"ok": True, "status": "green"}
