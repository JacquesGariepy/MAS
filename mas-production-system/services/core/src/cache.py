"""
Cache module with async Redis support
"""
import redis.asyncio as aioredis
from typing import Optional, Union
import json

from src.config import settings

# Async Redis client
cache = None

async def init_cache():
    """Initialize async Redis connection"""
    global cache
    redis_url = str(settings.REDIS_URL) if settings.REDIS_URL else "redis://redis:6379/0"
    cache = await aioredis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    return cache

async def get_cache():
    """Get cache instance"""
    if cache is None:
        await init_cache()
    return cache

async def get(key: str) -> Optional[str]:
    """Get value from cache"""
    if cache is None:
        await init_cache()
    return await cache.get(key)

async def set(key: str, value: Union[str, dict, list], expire: Optional[int] = None) -> bool:
    """Set value in cache with optional expiration"""
    if cache is None:
        await init_cache()
    
    # Convert complex types to JSON
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    
    if expire:
        return await cache.setex(key, expire, value)
    return await cache.set(key, value)

async def delete(key: str) -> bool:
    """Delete key from cache"""
    if cache is None:
        await init_cache()
    return await cache.delete(key) > 0

async def exists(key: str) -> bool:
    """Check if key exists"""
    if cache is None:
        await init_cache()
    return await cache.exists(key) > 0

async def incr(key: str) -> int:
    """Increment counter"""
    if cache is None:
        await init_cache()
    return await cache.incr(key)

async def expire(key: str, seconds: int) -> bool:
    """Set expiration on key"""
    if cache is None:
        await init_cache()
    return await cache.expire(key, seconds)

async def close():
    """Close Redis connection"""
    global cache
    if cache:
        await cache.close()
        cache = None

__all__ = [
    "cache",
    "init_cache",
    "get",
    "set",
    "delete",
    "exists",
    "incr",
    "expire",
    "close"
]