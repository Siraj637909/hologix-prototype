"""
Model Routes

OpenAI-compatible model listing endpoints.
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..schemas.models import ModelInfo, ModelsList
from ..middleware.auth import get_current_user
from ..services.model_manager import ModelManager

router = APIRouter()

model_manager = ModelManager()


@router.get("/models", response_model=ModelsList)
async def list_models(current_user: dict = Depends(get_current_user)):
    """
    List available models.
    
    Returns a list of all models available in the HOLOGIX system.
    """
    try:
        models = await model_manager.list_models()
        
        model_infos = []
        for model in models:
            info = ModelInfo(
                id=model["id"],
                created=model.get("created", int(time.time())),
                owned_by="hologix",
                model_type=model.get("type"),
                format=model.get("format"),
                quantization=model.get("quantization"),
                size_bytes=model.get("size_bytes"),
                status=model.get("status", "ready"),
            )
            model_infos.append(info)
        
        return ModelsList(data=model_infos)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get information about a specific model.
    
    Returns detailed information about the specified model.
    """
    try:
        model = await model_manager.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        return ModelInfo(
            id=model["id"],
            created=model.get("created", int(time.time())),
            owned_by="hologix",
            model_type=model.get("type"),
            format=model.get("format"),
            quantization=model.get("quantization"),
            size_bytes=model.get("size_bytes"),
            status=model.get("status", "ready"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{model_id}")
async def unload_model(model_id: str, current_user: dict = Depends(get_current_user)):
    """
    Unload a model from memory.
    
    Removes the specified model from active memory (does not delete from disk).
    """
    try:
        success = await model_manager.unload_model(model_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found or not loaded")
        
        return {"object": "model", "id": model_id, "deleted": True}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
