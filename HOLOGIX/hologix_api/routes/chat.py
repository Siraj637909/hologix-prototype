from fastapi import APIRouter
from hologix_api.schemas.chat import ChatRequest
router=APIRouter(prefix="/v1/chat")
@router.post("/completions")
async def completions(req: ChatRequest): return {"id":"hgx_mock","model":req.model,"message":"placeholder"}
