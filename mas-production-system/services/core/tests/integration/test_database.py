"""
Integration tests for database operations
"""
import pytest
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, init_db, Base, engine
from src.database.models import User, Agent, Organization

@pytest.fixture
async def db_session():
    """Create a test database session"""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Get session
    async with AsyncSessionLocal() as session:
        yield session
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.created_at is not None

@pytest.mark.asyncio
async def test_create_agent(db_session: AsyncSession):
    """Test creating an agent"""
    # Create user first
    user = User(
        id=uuid4(),
        email="agent_owner@example.com",
        username="agentowner",
        password_hash="hashed"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create agent
    agent = Agent(
        id=uuid4(),
        name="Test Agent",
        role="assistant",
        agent_type="cognitive",
        capabilities=["test", "analyze"],
        owner_id=user.id
    )
    
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.status == "idle"
    assert len(agent.capabilities) == 2

@pytest.mark.asyncio
async def test_create_organization(db_session: AsyncSession):
    """Test creating an organization"""
    org = Organization(
        id=uuid4(),
        name="Test Org",
        org_type="team",
        metadata={"description": "Test organization"}
    )
    
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    
    assert org.id is not None
    assert org.name == "Test Org"
    assert org.metadata["description"] == "Test organization"