"""
API v1 module initialization
"""
from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.tasks import router as tasks_router

# Create v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(auth_router)
router.include_router(tasks_router)

__all__ = ["router"]