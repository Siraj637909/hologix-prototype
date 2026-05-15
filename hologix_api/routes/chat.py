"""
Chat Completion Routes

OpenAI-compatible chat completion endpoints.
"""

import time
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from ..schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatMessage,
    Choice,
    ChunkChoice,
    UsageInfo,
)
from ..middleware.auth import get_current_user
from ..services.inference import InferenceService
from ..services.stream_manager import StreamManager

router = APIRouter()

# Service instances
inference_service = InferenceService()
stream_manager = StreamManager()


async def generate_stream(
    request: ChatCompletionRequest,
    request_id: str,
) -> AsyncGenerator[dict, None]:
    """Generate streaming response chunks."""
    created = int(time.time())
    
    # Send initial chunk with role
    if request.n and request.n > 1:
        for i in range(request.n):
            chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    ChunkChoice(
                        index=i,
                        delta=ChatMessage(role="assistant", content=""),
                        finish_reason=None,
                    )
                ],
            )
            yield {"data": chunk.model_dump_json()}
    else:
        chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=request.model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChatMessage(role="assistant", content=""),
                    finish_reason=None,
                )
            ],
        )
        yield {"data": chunk.model_dump_json()}
    
    # Generate content chunks
    try:
        async for token in inference_service.generate_stream(request):
            chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    ChunkChoice(
                        index=0,
                        delta=ChatMessage(content=token),
                        finish_reason=None,
                    )
                ],
            )
            yield {"data": chunk.model_dump_json()}
        
        # Send final chunk with finish reason
        final_chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=request.model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChatMessage(content=""),
                    finish_reason="stop",
                )
            ],
        )
        yield {"data": final_chunk.model_dump_json()}
        
    except Exception as e:
        yield {"data": f'{{"error": "{str(e)}"}}'}
    
    yield {"data": "[DONE]"}


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a chat completion.
    
    Generates a response from the specified model based on the conversation messages.
    Supports both regular and streaming responses.
    """
    request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    
    try:
        if request.stream:
            return EventSourceResponse(
                generate_stream(request, request_id),
                media_type="text/event-stream",
            )
        
        # Non-streaming: generate full response
        result = await inference_service.generate(request)
        
        choices = []
        for i, content in enumerate(result.get("choices", [result.get("content", "")])):
            message = ChatMessage(role="assistant", content=content)
            choice = Choice(
                index=i,
                message=message,
                finish_reason=result.get("finish_reason", "stop"),
            )
            choices.append(choice)
        
        usage = None
        if "usage" in result:
            usage = UsageInfo(**result["usage"])
        
        response = ChatCompletionResponse(
            id=request_id,
            created=created,
            model=request.model,
            choices=choices,
            usage=usage,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/completions")
async def list_chat_completions():
    """List available chat completion models (compatibility endpoint)."""
    return {"object": "list", "data": []}
