from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_id: Optional[str] = Field(None, description="User ID")
    location: Optional[str] = Field(None, description="User location for context")
    crop_context: Optional[str] = Field(None, description="Current crop context")

class ToolCall(BaseModel):
    tool_name: str
    parameters: dict
    result: dict

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tool_calls_made: List[ToolCall]
    sources: List[str]
    suggestions: List[str]
    confidence: float = Field(..., ge=0, le=1)
    success: bool = True
    message: str = "Chat response generated successfully"
