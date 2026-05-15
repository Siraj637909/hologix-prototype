"""
Embedding Schemas

OpenAI-compatible embedding request/response models.
"""

from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Embedding request matching OpenAI API."""
    model: str = Field(..., description="Model identifier to use")
    input: Union[str, List[str], List[int], List[List[int]]] = Field(
        ..., 
        description="Input text or tokens to embed"
    )
    encoding_format: Optional[Literal["float", "base64"]] = Field("float")
    dimensions: Optional[int] = Field(None, ge=1, description="Output embedding dimensions")
    user: Optional[str] = Field(None, description="End user identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "all-minilm-l6-v2",
                "input": "The quick brown fox jumps over the lazy dog",
                "encoding_format": "float"
            }
        }


class EmbeddingData(BaseModel):
    """Single embedding data."""
    object: str = "embedding"
    index: int
    embedding: List[float]


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """Embedding response matching OpenAI API."""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Optional[UsageInfo] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "index": 0,
                        "embedding": [0.1, -0.2, 0.3, "..."]
                    }
                ],
                "model": "all-minilm-l6-v2",
                "usage": {
                    "prompt_tokens": 9,
                    "total_tokens": 9
                }
            }
        }
