"""
Monitoring module with Prometheus metrics
"""
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from functools import wraps
from typing import Callable, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create a custom registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    'mas_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

request_duration = Histogram(
    'mas_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=registry
)

active_agents = Gauge(
    'mas_active_agents',
    'Number of active agents',
    ['agent_type'],
    registry=registry
)

agent_actions = Counter(
    'mas_agent_actions_total',
    'Total agent actions',
    ['agent_type', 'action_type', 'status'],
    registry=registry
)

task_queue_size = Gauge(
    'mas_task_queue_size',
    'Size of task queue',
    ['queue_name'],
    registry=registry
)

db_connections = Gauge(
    'mas_db_connections',
    'Database connection pool stats',
    ['pool_name', 'state'],
    registry=registry
)

cache_operations = Counter(
    'mas_cache_operations_total',
    'Cache operations',
    ['operation', 'status'],
    registry=registry
)

llm_requests = Counter(
    'mas_llm_requests_total',
    'LLM API requests',
    ['model', 'status'],
    registry=registry
)

llm_tokens = Counter(
    'mas_llm_tokens_total',
    'LLM tokens used',
    ['model', 'token_type'],
    registry=registry
)

system_info = Info(
    'mas_system_info',
    'System information',
    registry=registry
)

def init_monitoring():
    """Initialize monitoring with system info"""
    system_info.info({
        'version': '2.0.0',
        'environment': 'production',
        'service': 'mas-core'
    })
    logger.info("Monitoring initialized")

def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def track_agent_action(agent_type: str, action_type: str, success: bool):
    """Track agent action metrics"""
    status = "success" if success else "failure"
    agent_actions.labels(
        agent_type=agent_type,
        action_type=action_type,
        status=status
    ).inc()

def update_active_agents(agent_type: str, count: int):
    """Update active agents gauge"""
    active_agents.labels(agent_type=agent_type).set(count)

def track_cache_operation(operation: str, success: bool):
    """Track cache operation metrics"""
    status = "success" if success else "failure"
    cache_operations.labels(operation=operation, status=status).inc()

def track_llm_request(model: str, success: bool, input_tokens: int = 0, output_tokens: int = 0):
    """Track LLM request metrics"""
    status = "success" if success else "failure"
    llm_requests.labels(model=model, status=status).inc()
    
    if success and input_tokens > 0:
        llm_tokens.labels(model=model, token_type="input").inc(input_tokens)
    
    if success and output_tokens > 0:
        llm_tokens.labels(model=model, token_type="output").inc(output_tokens)

def update_task_queue_size(queue_name: str, size: int):
    """Update task queue size gauge"""
    task_queue_size.labels(queue_name=queue_name).set(size)

def update_db_connections(pool_name: str, active: int, idle: int, total: int):
    """Update database connection pool metrics"""
    db_connections.labels(pool_name=pool_name, state="active").set(active)
    db_connections.labels(pool_name=pool_name, state="idle").set(idle)
    db_connections.labels(pool_name=pool_name, state="total").set(total)

def timing_decorator(metric_name: str):
    """Decorator to time function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                request_duration.labels(
                    method="function",
                    endpoint=metric_name
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                request_duration.labels(
                    method="function",
                    endpoint=metric_name
                ).observe(duration)
                raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                request_duration.labels(
                    method="function",
                    endpoint=metric_name
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                request_duration.labels(
                    method="function",
                    endpoint=metric_name
                ).observe(duration)
                raise e
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

async def get_metrics() -> Response:
    """Get Prometheus metrics"""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# Import asyncio for decorator
import asyncio

__all__ = [
    "init_monitoring",
    "track_request",
    "track_agent_action",
    "update_active_agents",
    "track_cache_operation",
    "track_llm_request",
    "update_task_queue_size",
    "update_db_connections",
    "timing_decorator",
    "get_metrics"
]