from fastapi import APIRouter
router=APIRouter(prefix="/v1/system")
@router.get("/health")
async def health(): return {"status":"ok"}
