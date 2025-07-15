"""
Database module initialization
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from src.config import settings

# Create base class for models
Base = declarative_base()

# Import all models to ensure they are registered
from src.database.models import *

# Sync engine for Alembic migrations
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+psycopg2://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async engine for application
engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factories
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False
)

async def init_db():
    """Initialize database"""
    # In production, use Alembic migrations
    # This is just for development
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Get synchronous database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = [
    "Base",
    "engine", 
    "init_db",
    "get_db",
    "get_sync_db",
    "sync_engine"
]