"""
Security middleware for production
"""

import time
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt

from src.config import settings
from src.utils.logger import get_logger
from src.cache import cache

logger = get_logger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:;"
        )
        
        # Remove server header
        response.headers.pop("server", None)
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        key = f"rate_limit:{client_id}"
        
        try:
            current = await cache.incr(key)
            if current == 1:
                await cache.expire(key, self.period)
            
            if current > self.calls:
                return Response(
                    content="Rate limit exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.period)
                    }
                )
            
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - current))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limit error: {str(e)}")
            # Fail open
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Try to get API key
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return f"token:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        
        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host
        
        return f"ip:{ip}"

class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            
            token = credentials.credentials
            
            # Verify token
            payload = self.verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired token"
                )
            
            # Store user info in request
            request.state.user_id = payload.get("sub")
            request.state.token_type = payload.get("type", "access")
            
            return token
        
        return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None

class APIKeyAuth:
    """API Key authentication"""
    
    async def __call__(self, request: Request) -> Optional[str]:
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key required"
            )
        
        # Verify API key
        key_data = await self.verify_api_key(api_key)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
        
        # Check if key is active
        if not key_data.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key is inactive"
            )
        
        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key has expired"
            )
        
        # Store key info in request
        request.state.api_key_id = key_data.get("id")
        request.state.user_id = key_data.get("user_id")
        request.state.permissions = key_data.get("permissions", [])
        
        # Update last used
        await self.update_last_used(api_key)
        
        return api_key
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key against database"""
        
        # Check cache first
        cache_key = f"api_key:{api_key[:8]}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Hash the key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Query database
        from src.database import get_db
        from src.database.models import APIKey
        
        db = next(get_db())
        try:
            api_key_obj = db.query(APIKey).filter(
                APIKey.key_hash == key_hash
            ).first()
            
            if not api_key_obj:
                return None
            
            key_data = {
                "id": str(api_key_obj.id),
                "user_id": str(api_key_obj.user_id),
                "is_active": api_key_obj.is_active,
                "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                "permissions": api_key_obj.permissions,
                "rate_limit": api_key_obj.rate_limit
            }
            
            # Cache for 5 minutes
            await cache.set(cache_key, key_data, expire=300)
            
            return key_data
            
        finally:
            db.close()
    
    async def update_last_used(self, api_key: str):
        """Update last used timestamp"""
        try:
            # Update in background
            from src.database import get_db
            from src.database.models import APIKey
            
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            db = next(get_db())
            try:
                db.query(APIKey).filter(
                    APIKey.key_hash == key_hash
                ).update({"last_used_at": datetime.utcnow()})
                db.commit()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to update API key last used: {str(e)}")

class SignatureVerification:
    """Webhook signature verification"""
    
    def __init__(self, secret: str):
        self.secret = secret.encode()
    
    async def verify(self, request: Request) -> bool:
        """Verify webhook signature"""
        
        signature = request.headers.get("X-Webhook-Signature")
        if not signature:
            return False
        
        # Get request body
        body = await request.body()
        
        # Calculate expected signature
        timestamp = request.headers.get("X-Webhook-Timestamp", "")
        payload = f"{timestamp}.{body.decode()}"
        
        expected = hmac.new(
            self.secret,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected)

def require_permissions(*permissions: str):
    """Decorator to require specific permissions"""
    
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_permissions = getattr(request.state, "permissions", [])
            
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator