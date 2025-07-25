"""
Middleware module initialization
"""
from src.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    JWTBearer,
    APIKeyAuth,
    SignatureVerification,
    require_permissions
)

# Additional middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
import time

from src.utils.logger import get_logger
from src.monitoring import track_request

logger = get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} "
                f"{request.url.path} in {duration:.3f}s"
            )
            
            # Track metrics
            track_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {duration:.3f}s - {str(e)}"
            )
            
            # Track failed request
            track_request(
                method=request.method,
                endpoint=request.url.path,
                status=500,
                duration=duration
            )
            
            raise

__all__ = [
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "RequestIDMiddleware",
    "LoggingMiddleware",
    "JWTBearer",
    "APIKeyAuth",
    "SignatureVerification",
    "require_permissions"
]