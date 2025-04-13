from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationBase(BaseModel):
    """Base conversation model with common attributes"""
    pass

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    participant_ids: List[int] = Field(..., description="IDs of conversation participants")

class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    conversation_id: int = Field(..., description="Unique identifier for the conversation")
    participant_ids: List[int] = Field(..., description="IDs of conversation participants")
    created_at: str = Field(..., description="Timestamp of conversation creation")
    last_updated: str = Field(..., description="Timestamp of last message")
    class Config:
        orm_mode = True

class ConversationListItem(BaseModel):
    """Schema for conversation list item"""
    conversation_id: int = Field(..., description="Unique identifier for the conversation")
    other_user_id: int = Field(..., description="ID of the other user in 1-1 conversations")
    last_updated: str = Field(..., description="Timestamp of last message")
    last_message: str = Field(..., description="Preview of the last message")

class PaginatedConversationResponse(BaseModel):
    """Schema for paginated conversation responses"""
    conversations: List[ConversationListItem] = Field(default_factory=list, description="List of conversations")
    has_more: bool = Field(default=False, description="Whether there are more conversations to fetch")