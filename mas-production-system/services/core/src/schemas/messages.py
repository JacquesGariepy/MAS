"""
Message schemas for API validation
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    receiver_id: UUID = Field(..., description="ID of the receiving agent")
    performative: str = Field(..., description="FIPA-ACL performative (inform, request, propose, etc.)")
    content: Dict[str, Any] = Field(..., description="Message content as JSON")
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID for tracking")
    in_reply_to: Optional[UUID] = Field(None, description="ID of message being replied to")
    
    @validator('performative')
    def validate_performative(cls, v):
        valid_performatives = ['inform', 'request', 'propose', 'accept', 'reject', 'query', 'subscribe']
        if v not in valid_performatives:
            raise ValueError(f"Performative must be one of: {', '.join(valid_performatives)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "receiver_id": "123e4567-e89b-12d3-a456-426614174000",
                "performative": "request",
                "content": {
                    "action": "analyze_data",
                    "params": {"dataset": "sales_2024"}
                },
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    performative: str
    content: Dict[str, Any]
    protocol: str = "fipa-acl"
    conversation_id: UUID
    in_reply_to: Optional[UUID]
    is_read: bool
    created_at: datetime
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "sender_id": "550e8400-e29b-41d4-a716-446655440000",
                "receiver_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "performative": "inform",
                "content": {"status": "task_completed", "result": {"analysis": "completed"}},
                "protocol": "fipa-acl",
                "conversation_id": "8a5b4c6d-e78f-91a2-b345-567890123456",
                "in_reply_to": None,
                "is_read": False,
                "created_at": "2024-01-15T10:30:00"
            }
        }


class MessageList(BaseModel):
    """Schema for paginated message list"""
    items: list[MessageResponse]
    total: int
    page: int
    per_page: int
    pages: int