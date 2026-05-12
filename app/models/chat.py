from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: str | None = Field(None, description="Conversation ID for context")
    user_id: str | None = Field(None, description="User ID")
    location: str | None = Field(None, description="User location for context")
    crop_context: str | None = Field(None, description="Current crop context")

class ToolCall(BaseModel):
    tool_name: str
    parameters: dict
    result: dict

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tool_calls_made: list[ToolCall]
    sources: list[str]
    suggestions: list[str]
    confidence: float = Field(..., ge=0, le=1)
    success: bool = True
    message: str = "Chat response generated successfully"
