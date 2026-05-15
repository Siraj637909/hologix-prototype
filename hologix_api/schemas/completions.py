"""
Completion Schemas

OpenAI-compatible text completion request/response models.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """Text completion request matching OpenAI API."""
    model: str = Field(..., description="Model identifier to use")
    prompt: Union[str, List[str], List[int], List[List[int]]] = Field(..., description="Prompt text or tokens")
    suffix: Optional[str] = Field(None, description="Suffix to append after completion")
    max_tokens: Optional[int] = Field(16, ge=1, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1, le=10, description="Number of completions")
    stream: Optional[bool] = Field(False, description="Whether to stream responses")
    logprobs: Optional[int] = Field(None, ge=0, le=5, description="Number of log probabilities to return")
    echo: Optional[bool] = Field(False, description="Echo back the prompt")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    best_of: Optional[int] = Field(1, ge=1, le=20)
    logit_bias: Optional[Dict[str, float]] = Field(None)
    user: Optional[str] = Field(None, description="End user identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "llama-2-7b",
                "prompt": "Once upon a time",
                "max_tokens": 100,
                "temperature": 0.7
            }
        }


class CompletionChoice(BaseModel):
    """Completion choice."""
    index: int
    text: str
    logprobs: Optional[Dict[str, Any]] = None
    finish_reason: Optional[Literal["stop", "length"]] = None


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    """Text completion response matching OpenAI API."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: Optional[UsageInfo] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cmpl-123456",
                "object": "text_completion",
                "created": 1234567890,
                "model": "llama-2-7b",
                "choices": [
                    {
                        "index": 0,
                        "text": ", there lived a brave knight...",
                        "logprobs": None,
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 10,
                    "total_tokens": 14
                }
            }
        }
