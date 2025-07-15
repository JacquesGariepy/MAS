"""
Agent API endpoints with async SQLAlchemy
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.database.models import Agent, User, Organization
from src.api.dependencies import get_current_user
from src.schemas import agents as schemas
from src.services.agent_service import AgentService
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.cache import delete as cache_delete, get as cache_get, set as cache_set
from src.message_broker import publish_event

router = APIRouter(prefix="/agents", tags=["agents"])
logger = get_logger(__name__)

@router.post("", response_model=schemas.AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: schemas.AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(),
    llm_service: LLMService = Depends()
):
    """Create a new agent"""
    
    # Check user quota
    stmt = select(func.count()).select_from(Agent).where(
        and_(Agent.owner_id == current_user.id, Agent.is_active == True)
    )
    result = await db.execute(stmt)
    agent_count = result.scalar()
    
    if agent_count >= current_user.agent_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent quota exceeded. Maximum allowed: {current_user.agent_quota}"
        )
    
    # Validate organization membership if specified
    if agent_data.organization_id:
        stmt = select(Organization).where(
            and_(
                Organization.id == agent_data.organization_id,
                Organization.owner_id == current_user.id,
                Organization.is_active == True
            )
        )
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        
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
        await db.commit()
        await db.refresh(agent)
        
        # Publish event
        await publish_event("agent.created", {
            "agent_id": str(agent.id),
            "owner_id": str(current_user.id),
            "agent_type": agent.agent_type
        })
        
        # Clear cache
        await cache_delete(f"user_agents:{current_user.id}")
        
        logger.info(f"Agent {agent.id} created by user {current_user.id}")
        
        return schemas.AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            agent_type=agent.agent_type,
            status=agent.status,
            capabilities=agent.capabilities if hasattr(agent, 'capabilities') else [],
            created_at=agent.created_at
        )
        
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_db)
):
    """List user's agents with filtering and pagination"""
    
    # Try cache first
    cache_key = f"user_agents:{current_user.id}:{page}:{per_page}:{agent_type}:{status}"
    cached = await cache_get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # Build query
    stmt = select(Agent).where(
        and_(Agent.owner_id == current_user.id, Agent.is_active == True)
    )
    
    # Apply filters
    if agent_type:
        stmt = stmt.where(Agent.agent_type == agent_type)
    
    if status:
        stmt = stmt.where(Agent.status == status)
    
    if organization_id:
        stmt = stmt.join(Agent.organizations).where(
            Organization.id == organization_id
        )
    
    if search:
        stmt = stmt.where(
            or_(
                Agent.name.ilike(f"%{search}%"),
                Agent.role.ilike(f"%{search}%")
            )
        )
    
    # Order by last active
    stmt = stmt.order_by(Agent.last_active_at.desc().nullsfirst(), Agent.created_at.desc())
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Paginate
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    agents = result.scalars().all()
    
    # Build response
    agent_list = schemas.AgentList(
        items=[
            schemas.AgentResponse(
                id=agent.id,
                name=agent.name,
                role=agent.role,
                agent_type=agent.agent_type,
                status=agent.status,
                capabilities=agent.capabilities if hasattr(agent, 'capabilities') else [],
                created_at=agent.created_at
            )
            for agent in agents
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if per_page > 0 else 0
    )
    
    # Cache result
    import json
    # Convert to dict with JSON serialization support (mode='json' converts UUID to str)
    agent_list_dict = {
        "items": [item.model_dump(mode='json') for item in agent_list.items],
        "total": agent_list.total,
        "page": agent_list.page,
        "per_page": agent_list.per_page,
        "pages": agent_list.pages
    }
    await cache_set(cache_key, agent_list_dict, expire=300)  # 5 minutes
    
    return agent_list

@router.get("/{agent_id}", response_model=schemas.AgentDetail)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent details"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update last accessed
    agent.last_active_at = datetime.utcnow()
    await db.commit()
    
    return schemas.AgentDetail(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        agent_type=agent.agent_type,
        beliefs=agent.beliefs if hasattr(agent, 'beliefs') else {},
        desires=agent.desires if hasattr(agent, 'desires') else [],
        intentions=agent.intentions if hasattr(agent, 'intentions') else [],
        metrics=agent.metrics if hasattr(agent, 'metrics') else {},
        created_at=agent.created_at,
        last_active_at=agent.last_active_at
    )

@router.patch("/{agent_id}", response_model=schemas.AgentResponse)
async def update_agent(
    agent_id: UUID,
    update_data: schemas.AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Update agent properties"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Update agent
        updated_agent = await agent_service.update_agent(agent, update_data)
        
        await db.commit()
        await db.refresh(updated_agent)
        
        # Publish event
        await publish_event("agent.updated", {
            "agent_id": str(agent.id),
            "updated_fields": list(update_data.dict(exclude_unset=True).keys())
        })
        
        # Clear cache
        await cache_delete(f"user_agents:{current_user.id}")
        
        return schemas.AgentResponse(
            id=updated_agent.id,
            name=updated_agent.name,
            role=updated_agent.role,
            agent_type=updated_agent.agent_type,
            status=updated_agent.status,
            capabilities=updated_agent.capabilities if hasattr(updated_agent, 'capabilities') else [],
            created_at=updated_agent.created_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Delete an agent (soft delete)"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Stop agent if running
        await agent_service.stop_agent(agent)
        
        # Soft delete - mark as inactive with idle status
        agent.is_active = False
        agent.status = 'idle'  # Use valid status instead of 'deleted'
        
        await db.commit()
        
        # Publish event
        await publish_event("agent.deleted", {
            "agent_id": str(agent.id),
            "owner_id": str(current_user.id)
        })
        
        # Clear cache
        await cache_delete(f"user_agents:{current_user.id}")
        
        logger.info(f"Agent {agent_id} deleted by user {current_user.id}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )

@router.post("/{agent_id}/start", response_model=schemas.AgentResponse)
async def start_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Start an agent"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
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
        
        await db.commit()
        
        # Publish event
        await publish_event("agent.started", {
            "agent_id": str(agent.id)
        })
        
        return schemas.AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            agent_type=agent.agent_type,
            status=agent.status,
            capabilities=agent.capabilities if hasattr(agent, 'capabilities') else [],
            created_at=agent.created_at
        )
        
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
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Stop a running agent"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
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
        
        await db.commit()
        
        # Publish event
        await publish_event("agent.stopped", {
            "agent_id": str(agent.id)
        })
        
        return schemas.AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            agent_type=agent.agent_type,
            status=agent.status,
            capabilities=agent.capabilities if hasattr(agent, 'capabilities') else [],
            created_at=agent.created_at
        )
        
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
    db: AsyncSession = Depends(get_db)
):
    """Get agent's memories"""
    
    # Verify agent ownership
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # For now, return empty list
    # In real implementation, would query Memory table
    return schemas.MemoryList(
        items=[],
        total=0,
        page=page,
        per_page=per_page
    )

@router.post("/{agent_id}/memories", response_model=schemas.MemoryResponse)
async def add_agent_memory(
    agent_id: UUID,
    memory_data: schemas.MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Add memory to agent"""
    
    # Verify agent ownership
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    try:
        # Create memory
        memory = await agent_service.add_memory(agent, memory_data)
        
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        return schemas.MemoryResponse(
            id=memory.id,
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
            metadata=memory.memory_metadata if hasattr(memory, 'memory_metadata') else {},
            created_at=memory.created_at,
            last_accessed_at=memory.last_accessed_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to add memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add memory"
        )

@router.get("/{agent_id}/metrics", response_model=schemas.AgentMetrics)
async def get_agent_metrics(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Get agent performance metrics"""
    
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get metrics
    metrics = await agent_service.get_agent_metrics(agent)
    return metrics

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends()
):
    """Delete an agent"""
    
    # Get agent
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Stop agent if running
    runtime = agent_service.runtime
    if await runtime.is_agent_running(agent.id):
        await runtime.stop_agent(agent.id)
    
    # Delete agent from database
    await db.delete(agent)
    await db.commit()
    
    # Clear cache
    await cache_delete(f"user_agents:{current_user.id}")
    
    logger.info(f"Deleted agent {agent_id} for user {current_user.id}")