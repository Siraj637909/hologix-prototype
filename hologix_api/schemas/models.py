"""
Model Schemas

OpenAI-compatible model listing schemas.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Information about a single model."""
    id: str = Field(..., description="Model identifier")
    object: str = "model"
    created: int = Field(..., description="Unix timestamp of model creation/loading")
    owned_by: str = Field("hologix", description="Owner of the model")
    permission: List = Field(default_factory=list)
    root: Optional[str] = None
    parent: Optional[str] = None
    
    # HOLOGIX-specific fields
    model_type: Optional[Literal["llm", "embedding", "vision", "audio", "multimodal"]] = None
    format: Optional[str] = None
    quantization: Optional[str] = None
    size_bytes: Optional[int] = None
    status: Optional[Literal["loading", "ready", "error", "unloaded"]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "llama-2-7b-q4_0",
                "object": "model",
                "created": 1234567890,
                "owned_by": "hologix",
                "model_type": "llm",
                "format": "gguf",
                "quantization": "q4_0",
                "status": "ready"
            }
        }


class ModelsList(BaseModel):
    """List of available models."""
    object: str = "list"
    data: List[ModelInfo] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "object": "list",
                "data": [
                    {
                        "id": "llama-2-7b-q4_0",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "hologix",
                        "status": "ready"
                    },
                    {
                        "id": "mistral-7b-q5_0",
                        "object": "model",
                        "created": 1234567891,
                        "owned_by": "hologix",
                        "status": "ready"
                    }
                ]
            }
        }
