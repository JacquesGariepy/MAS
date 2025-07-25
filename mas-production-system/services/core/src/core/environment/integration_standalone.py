"""
Standalone Integration module for Software Environment
Works without requiring the full agent infrastructure
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .software_environment import (
    SoftwareEnvironment, SoftwareLocation, TopologyType, 
    VisibilityLevel
)

logger = logging.getLogger(__name__)

@dataclass
class SimpleAgent:
    """Simple agent representation for integration"""
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    agent_type: str = "reflexive"

class StandaloneEnvironmentAdapter:
    """Standalone adapter that works without full MAS dependencies"""
    
    def __init__(self, environment: Optional[SoftwareEnvironment] = None):
        self.environment = environment or SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
        self.agent_locations: Dict[str, SoftwareLocation] = {}
        self.registered_agents: Dict[str, SimpleAgent] = {}
        
    async def register_agent(self, agent: Any, namespace: str = "default"):
        """Register any agent-like object with software environment"""
        # Extract agent properties flexibly
        agent_id = str(getattr(agent, 'agent_id', getattr(agent, 'id', id(agent))))
        name = getattr(agent, 'name', f'Agent-{agent_id[:8]}')
        role = getattr(agent, 'role', 'generic')
        capabilities = getattr(agent, 'capabilities', [])
        agent_type = getattr(agent, 'agent_type', 'reflexive')
        
        # Create location for agent
        location = SoftwareLocation(
            host="localhost",
            process_id=asyncio.get_running_loop().__hash__(),
            namespace=f"mas/{namespace}/{role}",
            coordinates={'x': len(self.agent_locations) * 10, 'y': 0}
        )
        
        # Add to environment
        self.environment.add_agent(agent_id, location)
        
        self.agent_locations[agent_id] = location
        self.registered_agents[agent_id] = SimpleAgent(
            agent_id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities,
            agent_type=agent_type
        )
        
        # Set visibility based on agent type
        if agent_type == "cognitive":
            visibility = VisibilityLevel.FULL
        elif agent_type == "hybrid":
            visibility = VisibilityLevel.NAMESPACE
        else:  # reflexive
            visibility = VisibilityLevel.PROCESS
            
        self.environment.observability.set_visibility(agent_id, visibility)
        
        logger.info(f"Registered agent {name} in software environment at {namespace}")
        return True
        
    async def update_agent_context(self, agent: Any):
        """Update agent's context with environment perception"""
        agent_id = str(getattr(agent, 'agent_id', getattr(agent, 'id', id(agent))))
        
        if agent_id not in self.registered_agents:
            return
            
        # Get filtered perception
        perception = self.environment.perceive(agent_id)
        
        # Update agent's environment if it has a context attribute
        if hasattr(agent, 'context') and hasattr(agent.context, 'environment'):
            agent.context.environment.update({
                'spatial': {
                    'location': self.agent_locations.get(agent_id),
                    'nearby_agents': perception.get('entities', {})
                },
                'resources': perception.get('resources', {}),
                'dynamics': perception.get('dynamics', {}),
                'events': perception.get('events', [])
            })
            
            # Also update new fields if they exist
            if hasattr(agent.context, 'software_location'):
                agent.context.software_location = self.agent_locations.get(agent_id)
            if hasattr(agent.context, 'resource_allocation'):
                agent.context.resource_allocation = self.environment.resource_manager.allocations.get(agent_id, {})
                
    async def execute_agent_action(self, agent: Any, action: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute agent action through environment"""
        agent_id = str(getattr(agent, 'agent_id', getattr(agent, 'id', id(agent))))
        
        if agent_id not in self.registered_agents:
            return False, {'error': 'Agent not registered'}
        
        # Map common agent actions to environment actions
        if action.get('type') == 'send_message' and 'target' in action:
            env_action = {
                'type': 'communicate',
                'target': str(action['target']),
                'message': action.get('message', {})
            }
        elif action.get('type') == 'request_resources':
            env_action = {
                'type': 'allocate_resource',
                'resources': action.get('resources', {})
            }
        elif action.get('type') == 'release_resources':
            env_action = {
                'type': 'release_resource',
                'resources': action.get('resources', {})
            }
        else:
            env_action = action
            
        # Execute through environment
        return await self.environment.execute_action(agent_id, env_action)
        
    def get_agent_perception(self, agent: Any) -> Dict[str, Any]:
        """Get what an agent can perceive from the environment"""
        agent_id = str(getattr(agent, 'agent_id', getattr(agent, 'id', id(agent))))
        
        if agent_id not in self.registered_agents:
            return {}
            
        return self.environment.perceive(agent_id)
        
    async def create_agent_network(self, agents: List[Any], topology: str = "full_mesh"):
        """Create network connections between agents"""
        agent_ids = []
        for agent in agents:
            agent_id = str(getattr(agent, 'agent_id', getattr(agent, 'id', id(agent))))
            if agent_id in self.registered_agents:
                agent_ids.append(agent_id)
        
        if topology == "full_mesh":
            for i, agent1_id in enumerate(agent_ids):
                for agent2_id in agent_ids[i+1:]:
                    self.environment.spatial_model.add_connection(
                        agent1_id, agent2_id, "network"
                    )
                    
        elif topology == "star" and len(agent_ids) > 1:
            hub_id = agent_ids[0]
            for agent_id in agent_ids[1:]:
                self.environment.spatial_model.add_connection(
                    hub_id, agent_id, "network"
                )
                
        elif topology == "ring":
            for i in range(len(agent_ids)):
                next_i = (i + 1) % len(agent_ids)
                self.environment.spatial_model.add_connection(
                    agent_ids[i], agent_ids[next_i], "network"
                )
                
        logger.info(f"Created {topology} network topology for {len(agent_ids)} agents")

async def integrate_mas_with_environment(runtime: Any = None) -> StandaloneEnvironmentAdapter:
    """
    Integrate MAS with software environment
    Works with or without a runtime object
    """
    # Create environment
    env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
    
    # Create adapter
    adapter = StandaloneEnvironmentAdapter(env)
    
    # If runtime provided, register its agents
    if runtime and hasattr(runtime, 'list_agents'):
        agents = runtime.list_agents()
        for agent in agents:
            await adapter.register_agent(agent)
            
        # Create default network
        if len(agents) > 1:
            await adapter.create_agent_network(agents, topology="full_mesh")
    
    # Start environment update loop
    async def environment_update_loop():
        while True:
            try:
                await env.update(1.0)
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Environment update error: {e}")
                
    # Start background task
    update_task = asyncio.create_task(environment_update_loop())
    
    # Store task reference for cleanup
    adapter._update_task = update_task
    
    logger.info("Software environment integration ready")
    return adapter

def enhance_agent_perception(agent_class):
    """
    Class decorator to enhance agent with environment perception
    Can be applied to any agent class
    """
    original_perceive = getattr(agent_class, 'perceive', None)
    
    if original_perceive:
        async def enhanced_perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
            # Call original perceive
            perception = await original_perceive(self, environment)
            
            # Enhance with software environment data if available
            if 'spatial' in environment:
                perception['location'] = environment['spatial'].get('location', {})
                perception['nearby_entities'] = environment['spatial'].get('nearby_agents', {})
                
            if 'resources' in environment:
                perception['system_resources'] = environment['resources']
                
            if 'dynamics' in environment:
                perception['environmental_state'] = environment['dynamics']
                
            return perception
            
        agent_class.perceive = enhanced_perceive
        
    return agent_class