"""
Message broker module with async Redis pub/sub support
"""
import redis.asyncio as aioredis
import json
from typing import Dict, Any, Callable, Optional
import asyncio

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Async Redis client for pub/sub
broker = None
pubsub = None
subscribers = {}

async def init_message_broker():
    """Initialize async Redis connection for message broker"""
    global broker, pubsub
    broker = await aioredis.from_url(
        settings.REDIS_URL or "redis://redis:6379/1",
        encoding="utf-8",
        decode_responses=True
    )
    pubsub = broker.pubsub()
    return broker

async def get_broker():
    """Get broker instance"""
    if broker is None:
        await init_message_broker()
    return broker

async def publish_event(event_type: str, data: Dict[str, Any]):
    """Publish event to channel"""
    if broker is None:
        await init_message_broker()
    
    message = {
        "event_type": event_type,
        "data": data,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await broker.publish(event_type, json.dumps(message))
    logger.debug(f"Published event {event_type}: {data}")

async def subscribe(channel: str, handler: Callable):
    """Subscribe to channel with handler"""
    if pubsub is None:
        await init_message_broker()
    
    await pubsub.subscribe(channel)
    subscribers[channel] = handler
    logger.info(f"Subscribed to channel: {channel}")

async def unsubscribe(channel: str):
    """Unsubscribe from channel"""
    if pubsub is None:
        return
    
    await pubsub.unsubscribe(channel)
    subscribers.pop(channel, None)
    logger.info(f"Unsubscribed from channel: {channel}")

async def listen():
    """Listen for messages on subscribed channels"""
    if pubsub is None:
        await init_message_broker()
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            channel = message["channel"]
            if channel in subscribers:
                try:
                    data = json.loads(message["data"])
                    await subscribers[channel](data)
                except Exception as e:
                    logger.error(f"Error handling message on {channel}: {e}")

async def broadcast(event_type: str, data: Dict[str, Any], channels: list[str]):
    """Broadcast event to multiple channels"""
    tasks = []
    for channel in channels:
        task = publish_event(f"{channel}:{event_type}", data)
        tasks.append(task)
    
    await asyncio.gather(*tasks)

async def close():
    """Close Redis connections"""
    global broker, pubsub
    if pubsub:
        await pubsub.close()
        pubsub = None
    if broker:
        await broker.close()
        broker = None

__all__ = [
    "init_message_broker",
    "publish_event",
    "subscribe",
    "unsubscribe",
    "listen",
    "broadcast",
    "close"
]