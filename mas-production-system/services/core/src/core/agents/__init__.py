"""
Agents module initialization
"""
from typing import Type, Dict, Any, Optional
from uuid import UUID
import asyncio

from src.core.agents.base_agent import BaseAgent
from src.core.agents.cognitive_agent import CognitiveAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Agent type registry
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    "cognitive": CognitiveAgent,
    # TODO: Add ReflexiveAgent and HybridAgent when implemented
}

class AgentFactory:
    """Factory for creating agents"""
    
    @staticmethod
    def create_agent(
        agent_type: str,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: list,
        llm_service: Any,  # Pass as parameter instead of getting it here
        **kwargs
    ) -> BaseAgent:
        """Create an agent of the specified type"""
        
        agent_class = AGENT_TYPES.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return agent_class(
            agent_id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities,
            llm_service=llm_service,
            **kwargs
        )
    
    @staticmethod
    def register_agent_type(name: str, agent_class: Type[BaseAgent]):
        """Register a new agent type"""
        AGENT_TYPES[name] = agent_class
        logger.info(f"Registered agent type: {name}")

class AgentRuntime:
    """Runtime manager for agents"""
    
    def __init__(self):
        self.running_agents: Dict[UUID, BaseAgent] = {}
        self.agent_tasks: Dict[UUID, asyncio.Task] = {}
    
    async def register_agent(self, agent: BaseAgent):
        """Register an agent without starting it"""
        if agent.agent_id in self.running_agents:
            raise ValueError(f"Agent {agent.agent_id} is already registered")
        
        self.running_agents[agent.agent_id] = agent
        logger.info(f"Registered agent {agent.name} ({agent.agent_id})")
    
    async def start_agent(self, agent: BaseAgent):
        """Start an agent"""
        if agent.agent_id in self.running_agents:
            raise ValueError(f"Agent {agent.agent_id} is already running")
        
        self.running_agents[agent.agent_id] = agent
        
        # Create and start agent task
        task = asyncio.create_task(agent.run())
        self.agent_tasks[agent.agent_id] = task
        
        logger.info(f"Started agent {agent.name} ({agent.agent_id})")
    
    async def stop_agent(self, agent_id: UUID):
        """Stop an agent"""
        agent = self.running_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} is not running")
        
        # Stop the agent
        await agent.stop()
        
        # Cancel task if still running
        task = self.agent_tasks.get(agent_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Remove from tracking
        del self.running_agents[agent_id]
        del self.agent_tasks[agent_id]
        
        logger.info(f"Stopped agent {agent_id}")
    
    async def stop_all_agents(self):
        """Stop all running agents"""
        agent_ids = list(self.running_agents.keys())
        
        for agent_id in agent_ids:
            try:
                await self.stop_agent(agent_id)
            except Exception as e:
                logger.error(f"Error stopping agent {agent_id}: {e}")
    
    def get_running_agent(self, agent_id: UUID) -> Optional[BaseAgent]:
        """Get a running agent by ID"""
        return self.running_agents.get(agent_id)
    
    def list_running_agents(self) -> list[UUID]:
        """List all running agent IDs"""
        return list(self.running_agents.keys())

# Global runtime instance
_agent_runtime: Optional[AgentRuntime] = None

def get_agent_runtime() -> AgentRuntime:
    """Get or create agent runtime instance"""
    global _agent_runtime
    if _agent_runtime is None:
        _agent_runtime = AgentRuntime()
    return _agent_runtime

__all__ = [
    "BaseAgent",
    "CognitiveAgent",
    "AgentFactory",
    "AgentRuntime",
    "get_agent_runtime",
    "AGENT_TYPES"
]