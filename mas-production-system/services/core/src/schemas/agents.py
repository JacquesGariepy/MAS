from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

class AgentCreate(BaseModel):
    name: str
    role: str
    agent_type: str
    capabilities: Optional[List[str]] = []
    initial_beliefs: Optional[Dict] = {}
    initial_desires: Optional[List[str]] = []
    configuration: Optional[Dict] = {}
    organization_id: Optional[UUID]

class AgentUpdate(BaseModel):
    name: Optional[str]
    role: Optional[str]
    capabilities: Optional[List[str]]
    configuration: Optional[Dict]

class AgentResponse(BaseModel):
    id: UUID
    name: str
    role: str
    agent_type: str
    status: str
    capabilities: List[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

class AgentDetail(BaseModel):
    id: UUID
    name: str
    role: str
    agent_type: str
    beliefs: Dict
    desires: List[str]
    intentions: List[str]
    metrics: Dict
    created_at: datetime
    last_active_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class AgentList(BaseModel):
    items: List[AgentResponse]
    total: int
    page: int
    per_page: int
    pages: int

class MemoryCreate(BaseModel):
    content: str
    memory_type: str
    importance: float = 0.5
    metadata: Optional[Dict] = {}

class MemoryResponse(BaseModel):
    id: UUID
    content: str
    memory_type: str
    importance: float
    metadata: Dict
    created_at: datetime
    last_accessed_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class MemoryList(BaseModel):
    items: List[MemoryResponse]
    total: int
    page: int
    per_page: int

class AgentMetrics(BaseModel):
    agent_id: UUID
    total_actions: int
    successful_actions: int
    success_rate: float
    total_messages: int
    uptime_hours: float
    memory_count: int
    task_completion_rate: float
    average_response_time: float