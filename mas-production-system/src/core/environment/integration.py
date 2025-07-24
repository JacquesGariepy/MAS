"""
Integration module for Software Environment with existing MAS system
Bridges the new software environment with existing agent infrastructure
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from src.core.environment.software_environment import (
    SoftwareEnvironment, SoftwareLocation, TopologyType, 
    VisibilityLevel, EnvironmentEvent
)

if TYPE_CHECKING:
    from src.core.agents.base_agent import BaseAgent, AgentContext
    from src.core.runtime.agent_runtime import AgentRuntime
else:
    # Runtime types for when modules aren't available
    BaseAgent = Any
    AgentContext = Any
    AgentRuntime = Any
import logging

logger = logging.getLogger(__name__)

class EnvironmentAdapter:
    """Adapts the software environment for existing MAS agents"""
    
    def __init__(self, environment: SoftwareEnvironment):
        self.environment = environment
        self.agent_locations: Dict[str, SoftwareLocation] = {}
        self.runtime: Optional[AgentRuntime] = None
        
    def set_runtime(self, runtime: AgentRuntime):
        """Set the agent runtime for integration"""
        self.runtime = runtime
        
    async def register_agent(self, agent: BaseAgent, namespace: str = "default"):
        """Register existing agent with software environment"""
        # Create location for agent
        location = SoftwareLocation(
            host="localhost",
            process_id=asyncio.get_running_loop().__hash__(),
            container_id=None,
            namespace=f"mas/{namespace}/{agent.role}",
            coordinates={'x': len(self.agent_locations) * 10, 'y': 0}
        )
        
        # Add to environment
        self.environment.add_agent(str(agent.agent_id), location, {
            'name': agent.name,
            'role': agent.role,
            'capabilities': agent.capabilities,
            'agent_type': agent.agent_type
        })
        
        self.agent_locations[str(agent.agent_id)] = location
        
        # Set visibility based on agent type
        if agent.agent_type == "cognitive":
            self.environment.observability.set_visibility(
                str(agent.agent_id), VisibilityLevel.FULL
            )
        elif agent.agent_type == "hybrid":
            self.environment.observability.set_visibility(
                str(agent.agent_id), VisibilityLevel.NETWORK
            )
        else:  # reflexive
            self.environment.observability.set_visibility(
                str(agent.agent_id), VisibilityLevel.NAMESPACE
            )
            
        logger.info(f"Registered agent {agent.name} in software environment at {namespace}")
        
    async def update_agent_context(self, agent: BaseAgent):
        """Update agent's context with environment perception"""
        agent_id = str(agent.agent_id)
        
        # Get filtered perception
        perception = self.environment.perceive(agent_id)
        
        # Update agent's environment in context
        if hasattr(agent, 'context') and agent.context:
            agent.context.environment.update({
                'spatial': {
                    'location': self.agent_locations.get(agent_id).__dict__ if agent_id in self.agent_locations else {},
                    'nearby_agents': perception.get('entities', {})
                },
                'resources': perception.get('resources', {}),
                'dynamics': perception.get('dynamics', {}),
                'events': perception.get('events', [])
            })
            
    async def execute_agent_action(self, agent: BaseAgent, action: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute agent action through environment"""
        agent_id = str(agent.agent_id)
        
        # Map agent actions to environment actions
        if action.get('type') == 'send_message' and 'target' in action:
            # Convert to environment communication
            env_action = {
                'type': 'communicate',
                'target': str(action['target']),
                'message': action.get('message', {})
            }
        elif action.get('type') == 'request_resources':
            # Resource allocation
            env_action = {
                'type': 'allocate_resource',
                'resources': action.get('resources', {})
            }
        elif action.get('type') == 'move':
            # Location change
            env_action = {
                'type': 'move',
                'target_location': action.get('target_location')
            }
        else:
            # Pass through
            env_action = action
            
        # Execute through environment
        success, result = await self.environment.execute_action(agent_id, env_action)
        
        # Log environment events
        if success and env_action['type'] == 'communicate':
            event = EnvironmentEvent(
                'agent_communication',
                agent_id,
                {'target': env_action['target'], 'success': True}
            )
            await self.environment.dynamics.add_event(event)
            
        return success, result
        
    async def create_agent_network(self, agents: List[BaseAgent], topology: str = "full_mesh"):
        """Create network connections between agents"""
        agent_ids = [str(agent.agent_id) for agent in agents]
        
        if topology == "full_mesh":
            # Connect all agents to each other
            for i, agent1_id in enumerate(agent_ids):
                for agent2_id in agent_ids[i+1:]:
                    self.environment.spatial_model.add_connection(
                        agent1_id, agent2_id, "network"
                    )
                    
        elif topology == "star":
            # First agent is hub
            if len(agent_ids) > 1:
                hub_id = agent_ids[0]
                for agent_id in agent_ids[1:]:
                    self.environment.spatial_model.add_connection(
                        hub_id, agent_id, "network"
                    )
                    
        elif topology == "ring":
            # Connect in a ring
            for i in range(len(agent_ids)):
                next_i = (i + 1) % len(agent_ids)
                self.environment.spatial_model.add_connection(
                    agent_ids[i], agent_ids[next_i], "network"
                )

class EnhancedAgentContext(AgentContext):
    """Enhanced context with software environment integration"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.software_location: Optional[SoftwareLocation] = None
        self.resource_allocation: Dict[str, float] = {}
        self.visibility_level: VisibilityLevel = VisibilityLevel.NAMESPACE
        
    def update_from_environment(self, env_perception: Dict[str, Any]):
        """Update context from environment perception"""
        # Update environment with spatial and resource info
        self.environment.update({
            'spatial': env_perception.get('spatial', {}),
            'resources': env_perception.get('resources', {}),
            'dynamics': env_perception.get('dynamics', {}),
            'system_events': env_perception.get('events', [])
        })

async def integrate_mas_with_environment(runtime: AgentRuntime) -> EnvironmentAdapter:
    """Main integration function"""
    # Create software environment
    env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
    
    # Create adapter
    adapter = EnvironmentAdapter(env)
    adapter.set_runtime(runtime)
    
    # Register all existing agents
    agents = runtime.list_agents()
    for agent in agents:
        await adapter.register_agent(agent)
        
    # Create network topology
    await adapter.create_agent_network(agents, topology="full_mesh")
    
    # Start environment update loop
    async def environment_update_loop():
        while True:
            try:
                # Update environment
                await env.update(1.0)  # 1 second delta
                
                # Update all agent contexts
                for agent in runtime.list_agents():
                    await adapter.update_agent_context(agent)
                    
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Environment update error: {e}")
                
    # Start background task
    asyncio.create_task(environment_update_loop())
    
    logger.info("MAS integrated with software environment")
    return adapter

# Hook into existing agent perceive method
def enhance_agent_perception(original_perceive):
    """Decorator to enhance agent perception with software environment"""
    async def enhanced_perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        # Call original perceive
        perception = await original_perceive(environment)
        
        # Enhance with software environment data if available
        if 'spatial' in environment:
            perception['location'] = environment['spatial'].get('location', {})
            perception['nearby_entities'] = environment['spatial'].get('nearby_agents', {})
            
        if 'resources' in environment:
            perception['system_resources'] = environment['resources']
            
        if 'dynamics' in environment:
            perception['environmental_state'] = environment['dynamics']
            
        return perception
        
    return enhanced_perceive

# Example usage showing integration
async def demonstrate_integration():
    """Demonstrate the integrated system"""
    from src.core.agents import AgentFactory
    
    # Create runtime
    runtime = AgentRuntime()
    
    # Create some agents
    factory = AgentFactory()
    
    # Cognitive agent with full visibility
    cognitive_agent = await factory.create_agent(
        agent_type="cognitive",
        name="Observer",
        role="monitor",
        capabilities=["analysis", "monitoring"]
    )
    await runtime.register_agent(cognitive_agent)
    await runtime.start_agent(cognitive_agent)
    
    # Reflexive agent with limited visibility
    reflexive_agent = await factory.create_agent(
        agent_type="reflexive",
        name="Worker",
        role="executor",
        capabilities=["execution", "response"]
    )
    await runtime.register_agent(reflexive_agent)
    await runtime.start_agent(reflexive_agent)
    
    # Integrate with environment
    adapter = await integrate_mas_with_environment(runtime)
    
    # Test resource allocation
    success, result = await adapter.execute_agent_action(cognitive_agent, {
        'type': 'request_resources',
        'resources': {'cpu': 10, 'memory': 1024*1024*50}  # 50MB
    })
    print(f"Resource allocation for {cognitive_agent.name}: {success}")
    
    # Test communication with visibility
    success, result = await adapter.execute_agent_action(cognitive_agent, {
        'type': 'send_message',
        'target': reflexive_agent.agent_id,
        'message': {'content': 'Task assignment', 'priority': 'high'}
    })
    print(f"Communication result: {success}")
    
    # Let system run for a bit
    await asyncio.sleep(5)
    
    # Check agent perceptions
    cognitive_perception = adapter.environment.perceive(str(cognitive_agent.agent_id))
    reflexive_perception = adapter.environment.perceive(str(reflexive_agent.agent_id))
    
    print(f"\nCognitive agent sees: {len(cognitive_perception.get('entities', {}))} entities")
    print(f"Reflexive agent sees: {len(reflexive_perception.get('entities', {}))} entities")
    print(f"\nSystem resources: {cognitive_perception.get('resources', {})}")

if __name__ == "__main__":
    asyncio.run(demonstrate_integration())