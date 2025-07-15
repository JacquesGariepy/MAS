"""
Tasks endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.database import get_db
from src.database.models import Task, User, Agent
from src.schemas.tasks import TaskCreate, TaskUpdate, TaskResponse, TaskList
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    # Verify agent exists and belongs to user if assigned
    if task_data.assigned_to:
        stmt = select(Agent).where(
            and_(
                Agent.id == task_data.assigned_to,
                Agent.owner_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or does not belong to you"
            )
    
    # Create task
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        priority=task_data.priority or "medium",
        status="pending",
        owner_id=current_user.id,
        assigned_to=task_data.assigned_to,
        metadata=task_data.metadata or {},
        created_at=datetime.utcnow()
    )
    
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        task_type=db_task.task_type,
        priority=db_task.priority,
        status=db_task.status,
        owner_id=db_task.owner_id,
        assigned_to=db_task.assigned_to,
        result=db_task.result,
        metadata=db_task.metadata,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        completed_at=db_task.completed_at
    )

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    stmt = select(Task).where(
        and_(
            Task.id == task_id,
            Task.owner_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        priority=task.priority,
        status=task.status,
        owner_id=task.owner_id,
        assigned_to=task.assigned_to,
        result=task.result,
        metadata=task.metadata,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at
    )

@router.get("/tasks", response_model=TaskList)
async def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's tasks with filtering"""
    # Build query
    conditions = [Task.owner_id == current_user.id]
    
    if status:
        conditions.append(Task.status == status)
    if task_type:
        conditions.append(Task.task_type == task_type)
    if assigned_to:
        conditions.append(Task.assigned_to == assigned_to)
    
    # Count total
    count_stmt = select(Task).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = len(count_result.all())
    
    # Get paginated results
    stmt = (
        select(Task)
        .where(and_(*conditions))
        .order_by(Task.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    return TaskList(
        items=[
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                task_type=task.task_type,
                priority=task.priority,
                status=task.status,
                owner_id=task.owner_id,
                assigned_to=task.assigned_to,
                result=task.result,
                metadata=task.metadata,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at
            )
            for task in tasks
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update task"""
    stmt = select(Task).where(
        and_(
            Task.id == task_id,
            Task.owner_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    
    # Mark completion time if status changed to completed
    if task_update.status == "completed" and task.status != "completed":
        task.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        priority=task.priority,
        status=task.status,
        owner_id=task.owner_id,
        assigned_to=task.assigned_to,
        result=task.result,
        metadata=task.metadata,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at
    )