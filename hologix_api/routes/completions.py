"""
Completion Routes

OpenAI-compatible text completion endpoints.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from ..schemas.completions import (
    CompletionRequest,
    CompletionResponse,
    CompletionChoice,
    UsageInfo,
)
from ..middleware.auth import get_current_user
from ..services.inference import InferenceService

router = APIRouter()

inference_service = InferenceService()


@router.post("/completions")
async def create_completion(
    request: CompletionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a text completion.
    
    Generates a completion from the specified model based on the prompt.
    """
    request_id = f"cmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    
    try:
        result = await inference_service.generate_completion(request)
        
        choices = []
        for i, text in enumerate(result.get("choices", [result.get("text", "")])):
            choice = CompletionChoice(
                index=i,
                text=text,
                logprobs=result.get("logprobs"),
                finish_reason=result.get("finish_reason", "stop"),
            )
            choices.append(choice)
        
        usage = None
        if "usage" in result:
            usage = UsageInfo(**result["usage"])
        
        response = CompletionResponse(
            id=request_id,
            created=created,
            model=request.model,
            choices=choices,
            usage=usage,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
