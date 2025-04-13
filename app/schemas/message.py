from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    """Base message model with common attributes"""
    content: str = Field(..., description="Content of the message")

class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    sender_id: int = Field(..., description="ID of the sender")
    receiver_id: int = Field(..., description="ID of the receiver")

class MessageResponse(MessageBase):
    """Schema for message response"""
    message_id: str = Field(..., description="Unique identifier for the message")
    sender_id: int = Field(..., description="ID of the sender")
    receiver_id: int = Field(..., description="ID of the receiver")
    conversation_id: int = Field(..., description="ID of the conversation")
    timestamp: str = Field(..., description="Timestamp of message creation")

    class Config:
        orm_mode = True

class PaginatedMessageResponse(BaseModel):
    """Schema for paginated message responses"""
    messages: List[MessageResponse] = Field(default_factory=list, description="List of messages")
    has_more: bool = Field(default=False, description="Whether there are more messages to fetch")