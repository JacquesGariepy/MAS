"""
Agents module initialization
"""
from typing import Type, Dict, Any, Optional
from uuid import UUID
import asyncio

from src.core.agents.base_agent import BaseAgent
from src.core.agents.cognitive_agent import CognitiveAgent
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.hybrid_agent import HybridAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Agent type registry
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    "cognitive": CognitiveAgent,  # Cognitive agents use LLM for complex reasoning
    "reactive": CognitiveAgent,   # Reactive is an alias for cognitive (for backward compatibility)
    "reflexive": ReflexiveAgent,  # Reflexive agents use rule-based processing
    "hybrid": HybridAgent         # Hybrid agents combine both approaches
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
        """Create an agent of the specified type
        
        Args:
            agent_type: Type of agent ("reactive", "reflexive", or "hybrid")
            agent_id: Unique identifier for the agent
            name: Agent name
            role: Agent role/purpose
            capabilities: List of agent capabilities
            llm_service: LLM service for cognitive processing
            **kwargs: Additional parameters:
                - reactive_rules: Dict of rules for reflexive agents
                - cognitive_threshold: Float threshold for hybrid agents
                - beliefs: Initial beliefs
                - desires: Initial desires
                - intentions: Initial intentions
        
        Returns:
            BaseAgent instance of the specified type
        """
        
        logger.info(f"Creating {agent_type} agent: {name} (ID: {agent_id})")
        logger.debug(f"Agent parameters: role={role}, capabilities={capabilities}, kwargs={kwargs.keys()}")
        
        agent_class = AGENT_TYPES.get(agent_type)
        if not agent_class:
            logger.error(f"Unknown agent type: {agent_type}. Available types: {list(AGENT_TYPES.keys())}")
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {list(AGENT_TYPES.keys())}")
        
        try:
            # Extract type-specific parameters
            if agent_type == "reflexive":
                # Reflexive agents need reactive_rules
                reactive_rules = kwargs.get("reactive_rules", {})
                logger.debug(f"Creating reflexive agent with {len(reactive_rules)} rules")
                
            elif agent_type == "hybrid":
                # Hybrid agents need both reactive_rules and cognitive_threshold
                reactive_rules = kwargs.get("reactive_rules", {})
                cognitive_threshold = kwargs.get("cognitive_threshold", 0.7)
                logger.debug(f"Creating hybrid agent with {len(reactive_rules)} rules and threshold {cognitive_threshold}")
                
            elif agent_type == "reactive":
                # Reactive (cognitive) agents primarily use the LLM
                logger.debug(f"Creating reactive agent with LLM service: {llm_service is not None}")
            
            # Create the agent
            agent = agent_class(
                agent_id=agent_id,
                name=name,
                role=role,
                capabilities=capabilities,
                llm_service=llm_service,
                **kwargs
            )
            
            logger.info(f"Successfully created {agent_type} agent: {name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent {name}: {str(e)}", exc_info=True)
            raise
    
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
        # Agent should already be registered, just verify it exists
        if agent.agent_id not in self.running_agents:
            raise ValueError(f"Agent {agent.agent_id} is not registered")
        
        # Don't add again, it's already in running_agents from register_agent
        
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
    
    async def is_agent_running(self, agent_id: UUID) -> bool:
        """Check if an agent is running"""
        return agent_id in self.running_agents

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
    "ReflexiveAgent",
    "HybridAgent",
    "AgentFactory",
    "AgentRuntime",
    "get_agent_runtime",
    "AGENT_TYPES"
]