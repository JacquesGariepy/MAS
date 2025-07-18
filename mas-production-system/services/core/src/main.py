"""
Multi-Agent System Core Service
Production-ready implementation
"""

import asyncio
import signal
import sys
from typing import Optional
import uvloop

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.config import settings
from src.api import router as api_router
from src.api.v1.endpoints.auth import router as auth_router
from src.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    LoggingMiddleware
)
from src.database import engine, init_db
from src.cache import init_cache
from src.message_broker import init_message_broker
from src.monitoring import init_monitoring
from src.utils.logger import get_logger
from src.services.message_delivery import get_delivery_service

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize Sentry for error tracking
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT,
        )
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Performance middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_CALLS, period=settings.RATE_LIMIT_PERIOD)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Prometheus metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    
    # Include routers
    app.include_router(auth_router)  # Auth at root level
    app.include_router(api_router, prefix="/api/v1")
    
    return app

app = create_app()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize database
    await init_db()
    
    # Initialize cache
    await init_cache()
    
    # Initialize message broker
    await init_message_broker()
    
    # Initialize monitoring
    init_monitoring()
    
    # Start message delivery service
    delivery_service = get_delivery_service()
    await delivery_service.start()
    
    logger.info("All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down services...")
    
    # Stop message delivery service
    delivery_service = get_delivery_service()
    await delivery_service.stop()
    
    # Close database connections
    await engine.dispose()
    
    # Close cache connections
    # Close message broker connections
    
    logger.info("Shutdown complete")

def handle_signal(sig, frame):
    """Handle system signals gracefully"""
    logger.info(f"Received signal {sig}")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        loop="uvloop",
        log_config=None,  # Use custom logging
        access_log=False,  # Handled by middleware
        server_header=False,  # Security
        date_header=False,  # Security
    )