"""
Legacy Environment wrapper for backward compatibility
Redirects to the new SoftwareEnvironment implementation
"""

from .software_environment import SoftwareEnvironment, TopologyType
from .integration import EnvironmentAdapter
import logging

logger = logging.getLogger(__name__)

class Environment:
    """
    Legacy Environment class that wraps the new SoftwareEnvironment
    Maintains backward compatibility while using the new implementation
    """
    
    def __init__(self):
        # Create new software environment with default network topology
        self._software_env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
        self._adapter = EnvironmentAdapter(self._software_env)
        self.agents = []  # For backward compatibility
        
        logger.info("Legacy Environment created with SoftwareEnvironment backend")
        
    def add_agent(self, agent):
        """Add agent to environment (backward compatible)"""
        self.agents.append(agent)
        
        # Also register in software environment
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._adapter.register_agent(agent))
            else:
                loop.run_until_complete(self._adapter.register_agent(agent))
        except Exception as e:
            logger.warning(f"Could not register agent in software environment: {e}")
            
    def remove_agent(self, agent):
        """Remove agent from environment"""
        if agent in self.agents:
            self.agents.remove(agent)
            
        # Also remove from software environment
        try:
            self._software_env.remove_agent(str(agent.agent_id))
        except Exception as e:
            logger.warning(f"Could not remove agent from software environment: {e}")
            
    def get_agents(self):
        """Get all agents in environment"""
        return self.agents
        
    def get_state(self):
        """Get environment state"""
        return {
            'agents': [{'id': str(a.agent_id), 'name': a.name} for a in self.agents],
            'software_state': self._software_env.global_state
        }
        
    @property
    def software_environment(self):
        """Access to the underlying software environment"""
        return self._software_env
        
    @property
    def adapter(self):
        """Access to the environment adapter"""
        return self._adapter