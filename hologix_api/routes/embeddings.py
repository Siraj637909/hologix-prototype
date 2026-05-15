"""
Embedding Routes

OpenAI-compatible embedding endpoints.
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..schemas.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingData,
    UsageInfo,
)
from ..middleware.auth import get_current_user
from ..services.inference import InferenceService

router = APIRouter()

inference_service = InferenceService()


@router.post("/embeddings")
async def create_embeddings(
    request: EmbeddingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create embeddings for the given input.
    
    Generates embeddings from the specified model.
    """
    try:
        result = await inference_service.generate_embeddings(request)
        
        embeddings_data = []
        for i, embedding in enumerate(result.get("embeddings", [])):
            data = EmbeddingData(
                object="embedding",
                index=i,
                embedding=embedding,
            )
            embeddings_data.append(data)
        
        usage = None
        if "usage" in result:
            usage = UsageInfo(**result["usage"])
        
        response = EmbeddingResponse(
            object="list",
            data=embeddings_data,
            model=request.model,
            usage=usage,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
