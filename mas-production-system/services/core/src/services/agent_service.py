"""
Agent service with complete lifecycle management
"""

import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session

from src.database.models import Agent, Memory, Message, Task
from src.schemas.agents import AgentCreate, AgentUpdate, MemoryCreate
from src.core.agents import AgentFactory, get_agent_runtime
from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.utils.logger import get_logger
from src.config import settings
from src.cache import cache
from src.message_broker import publish_event

logger = get_logger(__name__)

class AgentService:
    """Service for managing agent lifecycle"""
    
    def __init__(self):
        self.agent_factory = AgentFactory()
        self.runtime = get_agent_runtime()  # Use global runtime instance
        # self.embedding_service = EmbeddingService()  # TODO: fix initialization
        
    async def create_agent(
        self,
        owner_id: UUID,
        agent_data: AgentCreate,
        llm_service: LLMService
    ) -> Agent:
        """Create a new agent"""
        
        # Create database model
        agent = Agent(
            id=uuid4(),  # Explicitly generate UUID
            owner_id=owner_id,
            name=agent_data.name,
            role=agent_data.role,
            agent_type=agent_data.agent_type,
            beliefs=agent_data.initial_beliefs or {},
            desires=agent_data.initial_desires or [],
            intentions=[],
            capabilities=agent_data.capabilities or [],
            reactive_rules=agent_data.reactive_rules or {},
            configuration=agent_data.configuration or {}
        )
        
        # Create runtime instance with all necessary parameters
        factory_params = {
            "agent_type": agent_data.agent_type,
            "agent_id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "capabilities": agent.capabilities,
            "llm_service": llm_service,
            "reactive_rules": agent_data.reactive_rules or {}
        }
        
        # Add configuration parameters
        if agent_data.configuration:
            factory_params.update(agent_data.configuration)
        
        runtime_agent = self.agent_factory.create_agent(**factory_params)
        
        # Register with runtime
        await self.runtime.register_agent(runtime_agent)
        
        logger.info(f"Created agent {agent.id} of type {agent.agent_type}")
        
        return agent
        
    async def update_agent(
        self,
        agent: Agent,
        update_data: AgentUpdate
    ) -> Agent:
        """Update agent properties"""
        
        # Update database fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(agent, field):
                setattr(agent, field, value)
        
        agent.updated_at = datetime.utcnow()
        
        # Update runtime instance if running
        if agent.status != 'idle':
            runtime_agent = self.runtime.get_running_agent(agent.id)
            if runtime_agent:
                await runtime_agent.update_configuration(update_dict)
        
        logger.info(f"Updated agent {agent.id}")
        
        return agent
        
    async def start_agent(self, agent: Agent):
        """Start agent execution"""
        
        # Check if already running
        if await self.runtime.is_agent_running(agent.id):
            logger.warning(f"Agent {agent.id} is already running")
            return
        
        # Create runtime instance if not exists
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if not runtime_agent:
            # Create LLM service with proper configuration
            llm_service = LLMService()
            runtime_agent = self.agent_factory.create_agent(
                agent_type=agent.agent_type,
                agent_id=agent.id,
                name=agent.name,
                role=agent.role,
                capabilities=agent.capabilities,
                llm_service=llm_service,
                **agent.configuration
            )
            await self.runtime.register_agent(runtime_agent)
        
        # Start agent
        await self.runtime.start_agent(runtime_agent)
        
        logger.info(f"Started agent {agent.id}")
        
    async def stop_agent(self, agent: Agent):
        """Stop agent execution"""
        
        if not await self.runtime.is_agent_running(agent.id):
            logger.warning(f"Agent {agent.id} is not running")
            return
        
        await self.runtime.stop_agent(agent.id)
        
        logger.info(f"Stopped agent {agent.id}")
        
    async def add_memory(
        self,
        agent: Agent,
        memory_data: MemoryCreate
    ) -> Memory:
        """Add memory to agent"""
        
        # Generate embedding (TODO: uncomment when EmbeddingService is fixed)
        # embedding = await self.embedding_service.create_embedding(memory_data.content)
        embedding = None  # Temporary
        
        # Create memory
        memory = Memory(
            agent_id=agent.id,
            content=memory_data.content,
            embedding=embedding,
            metadata=memory_data.metadata or {},
            memory_type=memory_data.memory_type,
            importance=memory_data.importance
        )
        
        # Update agent's memory in runtime
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if runtime_agent:
            await runtime_agent.add_memory(memory)
        
        return memory
        
    async def search_memories(
        self,
        agent: Agent,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search agent's memories"""
        
        # Generate query embedding
        query_embedding = await self.embedding_service.create_embedding(query)
        
        # Search in vector store
        results = await self.embedding_service.search_similar(
            query_embedding,
            filter_conditions={
                "agent_id": str(agent.id),
                "memory_type": memory_type
            } if memory_type else {"agent_id": str(agent.id)},
            limit=limit
        )
        
        return results
        
    async def get_agent_metrics(self, agent: Agent) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        # Check cache
        cache_key = f"agent_metrics:{agent.id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Calculate metrics
        metrics = {
            "agent_id": str(agent.id),
            "total_actions": agent.total_actions,
            "successful_actions": agent.successful_actions,
            "success_rate": (
                agent.successful_actions / agent.total_actions 
                if agent.total_actions > 0 else 0
            ),
            "total_messages": agent.total_messages,
            "uptime_hours": 0,
            "memory_count": len(agent.memories),
            "task_completion_rate": 0,
            "average_response_time": 0
        }
        
        # Get runtime metrics if available
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if runtime_agent:
            runtime_metrics = await runtime_agent.get_metrics()
            metrics.update(runtime_metrics)
        
        # Cache for 1 minute
        await cache.set(cache_key, metrics, expire=60)
        
        return metrics
        
    async def execute_action(
        self,
        agent: Agent,
        action_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an agent action"""
        
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if not runtime_agent:
            raise ValueError(f"Agent {agent.id} is not running")
        
        try:
            result = await runtime_agent.execute_action(action_type, params)
            
            # Update metrics
            agent.total_actions += 1
            if result.get("success"):
                agent.successful_actions += 1
            
            # Publish event
            await publish_event("agent.action_executed", {
                "agent_id": str(agent.id),
                "action_type": action_type,
                "success": result.get("success", False)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute action for agent {agent.id}: {str(e)}")
            agent.total_actions += 1
            raise
            
    async def handle_message(
        self,
        agent: Agent,
        message: Message
    ) -> Optional[Message]:
        """Handle incoming message for agent"""
        
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if not runtime_agent:
            logger.warning(f"Agent {agent.id} is not running, queueing message")
            # Queue message for later processing
            await cache.rpush(f"agent_message_queue:{agent.id}", message.json())
            return None
        
        try:
            # Process message
            response = await runtime_agent.handle_message(message)
            
            # Update metrics
            agent.total_messages += 1
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to handle message for agent {agent.id}: {str(e)}")
            raise
            
    async def assign_task(
        self,
        agent: Agent,
        task: Task
    ):
        """Assign task to agent"""
        
        runtime_agent = self.runtime.get_running_agent(agent.id)
        if not runtime_agent:
            raise ValueError(f"Agent {agent.id} is not running")
        
        await runtime_agent.add_task(task)
        
        # Update task assignment
        if not task.assigned_agents:
            task.assigned_agents = []
        task.assigned_agents.append(agent.id)
        task.status = 'assigned'
        
        logger.info(f"Assigned task {task.id} to agent {agent.id}")