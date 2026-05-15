"""
HOLOGIX API Schemas

Pydantic models for OpenAI-compatible request/response handling.
"""

from .chat import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    Choice,
    ChunkChoice,
    UsageInfo,
)
from .completions import (
    CompletionRequest,
    CompletionResponse,
    CompletionChoice,
)
from .models import ModelInfo, ModelsList
from .embeddings import EmbeddingRequest, EmbeddingResponse, EmbeddingData

__all__ = [
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChunk",
    "Choice",
    "ChunkChoice",
    "UsageInfo",
    "CompletionRequest",
    "CompletionResponse",
    "CompletionChoice",
    "ModelInfo",
    "ModelsList",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingData",
]
