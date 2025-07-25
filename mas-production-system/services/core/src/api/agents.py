"""
Agent API endpoints with async SQLAlchemy
"""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from src.database import get_db
from src.database.models import Agent, User, Organization, Message
from src.api.dependencies import get_current_user
from src.schemas import agents as schemas
from src.schemas import messages as message_schemas
from src.services.agent_service import AgentService
from src.services.llm_service import LLMService
from src.services.message_delivery import get_delivery_service
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
        # Map reactive to cognitive for database compatibility
        if agent_data.agent_type == "reactive":
            agent_data.agent_type = "cognitive"
        
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

@router.post("/{agent_id}/messages", response_model=message_schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    agent_id: UUID,
    message_data: message_schemas.MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message from an agent to another agent.
    
    The endpoint:
    1. Verifies that the sender agent belongs to the current user
    2. Verifies that the receiver agent exists
    3. Creates a message with FIPA-ACL performative
    4. Saves it to the database
    5. Returns the created message
    
    Args:
        agent_id: ID of the sending agent (from URL)
        message_data: Message creation data including receiver_id, performative, and content
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        The created message with all fields
        
    Raises:
        404: If sender or receiver agent not found
        403: If sender agent doesn't belong to current user
        400: If invalid performative or other validation error
    """
    
    # Step 1: Verify that the sender agent belongs to the current user
    stmt = select(Agent).where(
        and_(
            Agent.id == agent_id,
            Agent.owner_id == current_user.id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    sender = result.scalar_one_or_none()
    
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender agent not found or you don't have permission to send messages from this agent"
        )
    
    # Step 2: Verify that the receiver agent exists
    stmt = select(Agent).where(
        and_(
            Agent.id == message_data.receiver_id,
            Agent.is_active == True
        )
    )
    result = await db.execute(stmt)
    receiver = result.scalar_one_or_none()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver agent not found"
        )
    
    # Prevent sending messages to self
    if agent_id == message_data.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent cannot send messages to itself"
        )
    
    try:
        # Step 3 & 4: Create message with FIPA-ACL performative and save to database
        message = Message(
            sender_id=agent_id,
            receiver_id=message_data.receiver_id,
            performative=message_data.performative,
            content=message_data.content,
            protocol='fipa-acl',
            conversation_id=message_data.conversation_id or uuid4(),
            in_reply_to=message_data.in_reply_to,
            is_read=False
        )
        
        db.add(message)
        
        # Update sender metrics
        if hasattr(sender, 'total_messages'):
            sender.total_messages = (sender.total_messages or 0) + 1
        sender.last_active_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        
        # Publish event for real-time notifications
        await publish_event("message.sent", {
            "message_id": str(message.id),
            "sender_id": str(agent_id),
            "receiver_id": str(message_data.receiver_id),
            "performative": message.performative,
            "conversation_id": str(message.conversation_id)
        })
        
        # Clear receiver's cache to ensure they see new messages
        await cache_delete(f"agent_messages:{message_data.receiver_id}")
        
        # Deliver message to running agent
        delivery_service = get_delivery_service()
        delivered = await delivery_service.deliver_message_from_db(db, message.id)
        
        if delivered:
            logger.info(f"Message {message.id} sent and delivered to agent {message_data.receiver_id}")
        else:
            logger.info(f"Message {message.id} sent from agent {agent_id} to {message_data.receiver_id} (queued for delivery)")
        
        # Step 5: Return the created message
        return message_schemas.MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            performative=message.performative,
            content=message.content,
            protocol=message.protocol,
            conversation_id=message.conversation_id,
            in_reply_to=message.in_reply_to,
            is_read=message.is_read,
            created_at=message.created_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to send message from agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/{agent_id}/messages", response_model=message_schemas.MessageList)
async def get_agent_messages(
    agent_id: UUID,
    message_type: str = Query("received", regex="^(sent|received|all)$", description="Filter by message type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conversation_id: Optional[UUID] = Query(None, description="Filter by conversation ID"),
    performative: Optional[str] = Query(None, description="Filter by performative"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for an agent (sent, received, or all).
    
    Args:
        agent_id: ID of the agent
        message_type: Filter by sent, received, or all messages
        page: Page number for pagination
        per_page: Number of items per page
        conversation_id: Optional filter by conversation
        performative: Optional filter by performative type
        
    Returns:
        Paginated list of messages
    """
    
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
            detail="Agent not found or you don't have permission to view its messages"
        )
    
    # Build base query
    stmt = select(Message)
    
    # Apply message type filter
    if message_type == "sent":
        stmt = stmt.where(Message.sender_id == agent_id)
    elif message_type == "received":
        stmt = stmt.where(Message.receiver_id == agent_id)
    else:  # all
        stmt = stmt.where(or_(Message.sender_id == agent_id, Message.receiver_id == agent_id))
    
    # Apply additional filters
    if conversation_id:
        stmt = stmt.where(Message.conversation_id == conversation_id)
    
    if performative:
        stmt = stmt.where(Message.performative == performative)
    
    # Order by creation date (newest first)
    stmt = stmt.order_by(Message.created_at.desc())
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Paginate
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Build response
    return message_schemas.MessageList(
        items=[
            message_schemas.MessageResponse(
                id=msg.id,
                sender_id=msg.sender_id,
                receiver_id=msg.receiver_id,
                performative=msg.performative,
                content=msg.content,
                protocol=msg.protocol,
                conversation_id=msg.conversation_id,
                in_reply_to=msg.in_reply_to,
                is_read=msg.is_read,
                created_at=msg.created_at
            )
            for msg in messages
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if per_page > 0 else 0
    )

@router.patch("/{agent_id}/messages/{message_id}/read", response_model=message_schemas.MessageResponse)
async def mark_message_as_read(
    agent_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a message as read. Only the receiver agent can mark a message as read.
    
    Args:
        agent_id: ID of the agent (must be the receiver)
        message_id: ID of the message to mark as read
        
    Returns:
        Updated message
    """
    
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
            detail="Agent not found or you don't have permission"
        )
    
    # Get the message and verify the agent is the receiver
    stmt = select(Message).where(
        and_(
            Message.id == message_id,
            Message.receiver_id == agent_id
        )
    )
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or this agent is not the receiver"
        )
    
    # Mark as read
    message.is_read = True
    
    try:
        await db.commit()
        await db.refresh(message)
        
        # Clear cache
        await cache_delete(f"agent_messages:{agent_id}")
        
        # Publish event
        await publish_event("message.read", {
            "message_id": str(message_id),
            "agent_id": str(agent_id)
        })
        
        return message_schemas.MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            performative=message.performative,
            content=message.content,
            protocol=message.protocol,
            conversation_id=message.conversation_id,
            in_reply_to=message.in_reply_to,
            is_read=message.is_read,
            created_at=message.created_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to mark message as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark message as read"
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