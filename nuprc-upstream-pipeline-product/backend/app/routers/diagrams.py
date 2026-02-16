from fastapi import APIRouter
router = APIRouter(prefix="/diagrams", tags=["diagrams"])
@router.get("")
def list_diagrams(): return {"ok": True, "items": []}
