"""
Agent Factory for creating different types of agents
"""

from typing import Type, Dict, Any, Optional
from uuid import UUID

from src.core.agents.base_agent import BaseAgent
from src.core.agents.cognitive_agent import CognitiveAgent
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.hybrid_agent import HybridAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Agent type registry mapping
AGENT_TYPE_MAPPING: Dict[str, Type[BaseAgent]] = {
    "reactive": CognitiveAgent,   # Reactive agents use cognitive processing (LLM-based)
    "reflexive": ReflexiveAgent,  # Reflexive agents use rule-based processing
    "hybrid": HybridAgent         # Hybrid agents combine both approaches
}


class AgentFactory:
    """
    Factory class for creating different types of agents.
    
    This factory supports three types of agents:
    - Reactive (Cognitive): Uses LLM for reasoning and decision-making
    - Reflexive: Uses predefined rules for quick responses
    - Hybrid: Combines both reactive and reflexive capabilities
    """
    
    @staticmethod
    def create_agent(
        agent_type: str,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: list,
        llm_service: Optional[Any] = None,
        **kwargs
    ) -> BaseAgent:
        """
        Create an agent of the specified type.
        
        Args:
            agent_type: Type of agent ("reactive", "reflexive", or "hybrid")
            agent_id: Unique identifier for the agent
            name: Agent name
            role: Agent role/purpose
            capabilities: List of agent capabilities
            llm_service: LLM service for cognitive processing (required for reactive/hybrid)
            **kwargs: Additional type-specific parameters:
                - reactive_rules: Dict[str, Any] - Rules for reflexive/hybrid agents
                - cognitive_threshold: float - Threshold for hybrid agent mode switching (default: 0.7)
                - beliefs: Dict[str, Any] - Initial beliefs
                - desires: List[str] - Initial desires
                - intentions: List[Dict] - Initial intentions
        
        Returns:
            BaseAgent: Instance of the specified agent type
            
        Raises:
            ValueError: If agent_type is not recognized
            TypeError: If required parameters are missing for the agent type
        """
        logger.info(f"Creating agent: type={agent_type}, name={name}, id={agent_id}")
        logger.debug(f"Agent configuration: role={role}, capabilities={capabilities}, extra_params={list(kwargs.keys())}")
        
        # Validate agent type
        if agent_type not in AGENT_TYPE_MAPPING:
            available_types = list(AGENT_TYPE_MAPPING.keys())
            logger.error(f"Invalid agent type '{agent_type}'. Available types: {available_types}")
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {available_types}")
        
        agent_class = AGENT_TYPE_MAPPING[agent_type]
        
        # Validate type-specific requirements
        if agent_type == "reactive" and not llm_service:
            logger.warning("Creating reactive agent without LLM service - limited capabilities")
        
        if agent_type == "reflexive":
            reactive_rules = kwargs.get("reactive_rules", {})
            if not reactive_rules:
                logger.warning(f"Creating reflexive agent '{name}' without any rules")
            else:
                logger.info(f"Creating reflexive agent '{name}' with {len(reactive_rules)} rules")
        
        if agent_type == "hybrid":
            reactive_rules = kwargs.get("reactive_rules", {})
            cognitive_threshold = kwargs.get("cognitive_threshold", 0.7)
            logger.info(f"Creating hybrid agent '{name}' with {len(reactive_rules)} rules and threshold={cognitive_threshold}")
            
            if not llm_service:
                logger.warning("Creating hybrid agent without LLM service - will only use reflexive mode")
        
        try:
            # Create the agent instance
            agent = agent_class(
                agent_id=agent_id,
                name=name,
                role=role,
                capabilities=capabilities,
                llm_service=llm_service,
                **kwargs
            )
            
            logger.info(f"Successfully created {agent_type} agent '{name}' with ID {agent_id}")
            
            # Log agent configuration for debugging
            if hasattr(agent, 'reactive_rules'):
                logger.debug(f"Agent '{name}' has {len(getattr(agent, 'reactive_rules', {}))} reactive rules")
            if hasattr(agent, 'cognitive_threshold'):
                logger.debug(f"Agent '{name}' cognitive threshold: {getattr(agent, 'cognitive_threshold', 'N/A')}")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent '{name}': {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available agent types."""
        return list(AGENT_TYPE_MAPPING.keys())
    
    @staticmethod
    def get_agent_class(agent_type: str) -> Type[BaseAgent]:
        """Get the agent class for a given type."""
        if agent_type not in AGENT_TYPE_MAPPING:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return AGENT_TYPE_MAPPING[agent_type]
    
    @staticmethod
    def register_custom_type(type_name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register a custom agent type.
        
        Args:
            type_name: Name for the new agent type
            agent_class: Class that extends BaseAgent
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class} must be a subclass of BaseAgent")
        
        if type_name in AGENT_TYPE_MAPPING:
            logger.warning(f"Overriding existing agent type '{type_name}'")
        
        AGENT_TYPE_MAPPING[type_name] = agent_class
        logger.info(f"Registered custom agent type '{type_name}' -> {agent_class.__name__}")


# Convenience function for quick agent creation
def create_agent(agent_type: str, **kwargs) -> BaseAgent:
    """Convenience function to create an agent using the factory."""
    return AgentFactory.create_agent(agent_type, **kwargs)