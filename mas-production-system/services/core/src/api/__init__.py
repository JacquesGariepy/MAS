"""
API module initialization
"""
from fastapi import APIRouter

from src.api.agents import router as agents_router
from src.api.v1.endpoints.tasks import router as tasks_router

# Create main API router
router = APIRouter()

# Include sub-routers
router.include_router(agents_router, prefix="/agents", tags=["agents"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])

# TODO: Add more routers as they are created
# router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
# router.include_router(messages_router, prefix="/messages", tags=["messages"])
# router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])

__all__ = ["router"]