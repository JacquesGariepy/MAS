"""
Agents module exports
"""

from src.core.agents import AgentFactory, AgentRuntime, AGENT_TYPES
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.hybrid_agent import HybridAgent

# Create agent function using factory
def create_agent(agent_type: str, **kwargs):
    """Convenience function to create an agent using the factory."""
    return AgentFactory.create_agent(agent_type, **kwargs)

# Agent type mapping for backward compatibility
AGENT_TYPE_MAPPING = AGENT_TYPES

__all__ = [
    "AgentFactory",
    "AgentRuntime",
    "create_agent",
    "AGENT_TYPE_MAPPING",
    "AGENT_TYPES",
    "ReflexiveAgent", 
    "HybridAgent"
]