"""
Agent API endpoints with full CRUD operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database import get_db
from src.database.models import Agent, User, Organization
from src.auth import get_current_user
from src.schemas import agents as schemas
from src.services.agent_service import AgentService
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.utils.pagination import paginate
from src.cache import cache
from src.message_broker import publish_event

router = APIRouter(prefix="/agents", tags=["agents"])
logger = get_logger(__name__)

@router.post("", response_model=schemas.AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: schemas.AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends(),
    llm_service: LLMService = Depends()
):
    """Create a new agent"""
    
    # Check user quota
    agent_count = db.query(Agent).filter(
        and_(Agent.owner_id == current_user.id, Agent.is_active == True)
    ).count()
    
    if agent_count >= current_user.agent_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent quota exceeded. Maximum allowed: {current_user.agent_quota}"
        )
    
    # Validate organization membership if specified
    if agent_data.organization_id:
        org = db.query(Organization).filter(
            and_(
                Organization.id == agent_data.organization_id,
                Organization.owner_id == current_user.id,
                Organization.is_active == True
            )
        ).first()
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or access denied"
            )
    
    try:
        # Create agent
        agent = await agent_service.create_agent(
            owner_id=current_user.id,
            agent_data=agent_data,
            llm_service=llm_service
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        # Publish event
        await publish_event("agent.created", {
            "agent_id": str(agent.id),
            "owner_id": str(current_user.id),
            "agent_type": agent.agent_type
        })
        
        # Clear cache
        await cache.delete(f"user_agents:{current_user.id}")
        
        logger.info(f"Agent {agent.id} created by user {current_user.id}")
        
        return schemas.AgentResponse.from_orm(agent)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )

@router.get("", response_model=schemas.AgentList)
async def list_agents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's agents with filtering and pagination"""
    
    # Try cache first
    cache_key = f"user_agents:{current_user.id}:{page}:{per_page}:{agent_type}:{status}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Build query
    query = db.query(Agent).filter(
        and_(Agent.owner_id == current_user.id, Agent.is_active == True)
    )
    
    # Apply filters
    if agent_type:
        query = query.filter(Agent.agent_type == agent_type)
    
    if status:
        query = query.filter(Agent.status == status)
    
    if organization_id:
        query = query.join(Agent.organizations).filter(
            Organization.id == organization_id
        )
    
    if search:
        query = query.filter(
            or_(
                Agent.name.ilike(f"%{search}%"),
                Agent.role.ilike(f"%{search}%")
            )
        )
    
    # Order by last active
    query = query.order_by(Agent.last_active_at.desc().nullsfirst(), Agent.created_at.desc())
    
    # Paginate
    result = paginate(query, page, per_page, schemas.AgentResponse)
    
    # Cache result
    await cache.set(cache_key, result, expire=300)  # 5 minutes
    
    return result

@router.get("/{agent_id}", response_model=schemas.AgentDetail)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent details"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update last accessed
    agent.last_active_at = datetime.utcnow()
    db.commit()
    
    return schemas.AgentDetail.from_orm(agent)

@router.patch("/{agent_id}", response_model=schemas.AgentResponse)
async def update_agent(
    agent_id: UUID,
    update_data: schemas.AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Update agent properties"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Update agent
        updated_agent = await agent_service.update_agent(agent, update_data)
        
        db.commit()
        db.refresh(updated_agent)
        
        # Publish event
        await publish_event("agent.updated", {
            "agent_id": str(agent.id),
            "updated_fields": update_data.dict(exclude_unset=True).keys()
        })
        
        # Clear cache
        await cache.delete(f"user_agents:{current_user.id}")
        
        return schemas.AgentResponse.from_orm(updated_agent)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Delete an agent (soft delete)"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Stop agent if running
        await agent_service.stop_agent(agent)
        
        # Soft delete
        agent.is_active = False
        agent.status = 'deleted'
        
        db.commit()
        
        # Publish event
        await publish_event("agent.deleted", {
            "agent_id": str(agent.id),
            "owner_id": str(current_user.id)
        })
        
        # Clear cache
        await cache.delete(f"user_agents:{current_user.id}")
        
        logger.info(f"Agent {agent_id} deleted by user {current_user.id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )

@router.post("/{agent_id}/start", response_model=schemas.AgentResponse)
async def start_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Start an agent"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    if agent.status not in ['idle', 'error']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is already {agent.status}"
        )
    
    try:
        # Start agent
        await agent_service.start_agent(agent)
        
        agent.status = 'working'
        agent.last_active_at = datetime.utcnow()
        
        db.commit()
        
        # Publish event
        await publish_event("agent.started", {
            "agent_id": str(agent.id)
        })
        
        return schemas.AgentResponse.from_orm(agent)
        
    except Exception as e:
        logger.error(f"Failed to start agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start agent"
        )

@router.post("/{agent_id}/stop", response_model=schemas.AgentResponse)
async def stop_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Stop a running agent"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    if agent.status == 'idle':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not running"
        )
    
    try:
        # Stop agent
        await agent_service.stop_agent(agent)
        
        agent.status = 'idle'
        
        db.commit()
        
        # Publish event
        await publish_event("agent.stopped", {
            "agent_id": str(agent.id)
        })
        
        return schemas.AgentResponse.from_orm(agent)
        
    except Exception as e:
        logger.error(f"Failed to stop agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop agent"
        )

@router.get("/{agent_id}/memories", response_model=schemas.MemoryList)
async def get_agent_memories(
    agent_id: UUID,
    memory_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent's memories"""
    
    # Verify agent ownership
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Query memories
    query = agent.memories
    
    if memory_type:
        query = query.filter(Memory.memory_type == memory_type)
    
    query = query.order_by(Memory.importance.desc(), Memory.created_at.desc())
    
    return paginate(query, page, per_page, schemas.MemoryResponse)

@router.post("/{agent_id}/memories", response_model=schemas.MemoryResponse)
async def add_agent_memory(
    agent_id: UUID,
    memory_data: schemas.MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Add memory to agent"""
    
    # Verify agent ownership
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Create memory
        memory = await agent_service.add_memory(agent, memory_data)
        
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        return schemas.MemoryResponse.from_orm(memory)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add memory"
        )

@router.get("/{agent_id}/metrics", response_model=schemas.AgentMetrics)
async def get_agent_metrics(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Get agent performance metrics"""
    
    agent = db.query(Agent).filter(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get metrics
    metrics = await agent_service.get_agent_metrics(agent)
    
    return metrics