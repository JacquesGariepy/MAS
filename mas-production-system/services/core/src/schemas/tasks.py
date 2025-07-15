"""
Task schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    task_type: str = Field(..., min_length=1, max_length=50)
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")

class TaskCreate(TaskBase):
    assigned_to: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|failed|cancelled)$")
    assigned_to: Optional[UUID] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(TaskBase):
    id: UUID
    status: str
    owner_id: UUID
    assigned_to: Optional[UUID]
    result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

class TaskList(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    per_page: int
    pages: int