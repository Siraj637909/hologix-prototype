"""
Chat Completion Schemas

OpenAI-compatible chat completion request/response models.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message in a conversation."""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="Role of the message sender")
    content: Optional[Union[str, List[Dict[str, Any]]]] = Field(None, description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the participant")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls if any")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?"
            }
        }


class FunctionCall(BaseModel):
    """Function call definition."""
    name: str
    arguments: str


class ToolChoice(BaseModel):
    """Tool choice specification."""
    type: Literal["function", "none", "auto", "required"]
    function: Optional[FunctionCall] = None


class Tool(BaseModel):
    """Tool definition for function calling."""
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ResponseFormat(BaseModel):
    """Response format specification."""
    type: Literal["text", "json_object"] = "text"


class ChatCompletionRequest(BaseModel):
    """Chat completion request matching OpenAI API."""
    model: str = Field(..., description="Model identifier to use")
    messages: List[ChatMessage] = Field(..., description="List of conversation messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    n: Optional[int] = Field(1, ge=1, le=10, description="Number of completions to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream responses")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Logit bias for tokens")
    user: Optional[str] = Field(None, description="End user identifier")
    tools: Optional[List[Tool]] = Field(None, description="Available tools")
    tool_choice: Optional[Union[Literal["none", "auto", "required"], ToolChoice]] = Field(None)
    response_format: Optional[ResponseFormat] = Field(None)
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "llama-2-7b",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.7,
                "max_tokens": 512
            }
        }


class Choice(BaseModel):
    """Chat completion choice."""
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "function_call"]] = None


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @classmethod
    def from_counts(cls, prompt: int, completion: int) -> "UsageInfo":
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        )


class ChatCompletionResponse(BaseModel):
    """Chat completion response matching OpenAI API."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[UsageInfo] = None
    system_fingerprint: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123456",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "llama-2-7b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! How can I help you today?"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 15,
                    "total_tokens": 25
                }
            }
        }


class ChunkChoice(BaseModel):
    """Streaming chunk choice."""
    index: int = 0
    delta: ChatMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "function_call"]] = None


class ChatCompletionChunk(BaseModel):
    """Chat completion streaming chunk."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChunkChoice]
    system_fingerprint: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123456",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "llama-2-7b",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "Hello"
                        },
                        "finish_reason": None
                    }
                ]
            }
        }
