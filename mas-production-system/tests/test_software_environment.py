"""
Tests for Software Environment integration
"""

import pytest
import asyncio
from uuid import uuid4
import os

from src.core.environment import (
    SoftwareEnvironment,
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    EnvironmentAdapter,
    SystemConstraint,
    ConstraintType
)

from src.core.agents import AgentFactory
from src.services.llm_service import LLMService

class TestSoftwareEnvironment:
    """Test software environment functionality"""
    
    @pytest.fixture
    async def environment(self):
        """Create test environment"""
        env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
        yield env
        
    @pytest.fixture
    async def agent_factory(self):
        """Create agent factory"""
        factory = AgentFactory()
        llm_service = LLMService()
        return factory, llm_service
        
    def test_spatial_representation(self, environment):
        """Test spatial model"""
        # Add entities at different locations
        loc1 = SoftwareLocation(
            host="server1",
            process_id=1234,
            namespace="app/service1",
            coordinates={'x': 0, 'y': 0}
        )
        
        loc2 = SoftwareLocation(
            host="server1",
            process_id=1234,
            namespace="app/service2", 
            coordinates={'x': 10, 'y': 10}
        )
        
        loc3 = SoftwareLocation(
            host="server2",
            process_id=5678,
            namespace="app/service3",
            coordinates={'x': 100, 'y': 100}
        )
        
        environment.add_agent("agent1", loc1)
        environment.add_agent("agent2", loc2)
        environment.add_agent("agent3", loc3)
        
        # Test distance calculations
        assert loc1.distance_to(loc2) < loc1.distance_to(loc3)
        assert loc1.distance_to(loc1) == 0.0
        
        # Test neighbors
        neighbors = environment.spatial_model.get_neighbors("agent1", 50.0)
        assert "agent2" in neighbors
        assert "agent3" not in neighbors
        
    def test_resource_management(self, environment):
        """Test resource allocation"""
        # Request resources
        success = environment.resource_manager.request_resources(
            "agent1",
            {'cpu': 25, 'memory': 1024*1024*100}
        )
        assert success
        
        # Check allocation
        cpu_usage = environment.resource_manager.get_resource_usage()['cpu']
        assert cpu_usage['used'] >= 25
        
        # Release resources
        environment.resource_manager.release_resources(
            "agent1",
            {'cpu': 25, 'memory': 1024*1024*100}
        )
        
        # Check release
        cpu_usage_after = environment.resource_manager.get_resource_usage()['cpu']
        assert cpu_usage_after['used'] < cpu_usage['used']
        
    @pytest.mark.asyncio
    async def test_constraints(self, environment):
        """Test constraint enforcement"""
        # Add agent
        location = SoftwareLocation(
            host="localhost",
            process_id=os.getpid(),
            namespace="test"
        )
        environment.add_agent("test_agent", location)
        
        # Try to allocate excessive CPU
        success, result = await environment.execute_action("test_agent", {
            'type': 'allocate_resource',
            'resources': {'cpu': 95}  # Over 90% threshold
        })
        
        assert not success
        assert 'violations' in result
        assert any('CPU' in v for v in result['violations'])
        
    def test_partial_observability(self, environment):
        """Test visibility filtering"""
        # Add agents with different visibility
        loc1 = SoftwareLocation(host="localhost", process_id=1, namespace="ns1")
        loc2 = SoftwareLocation(host="localhost", process_id=1, namespace="ns2")
        loc3 = SoftwareLocation(host="localhost", process_id=2, namespace="ns1")
        
        environment.add_agent("observer", loc1)
        environment.add_agent("same_ns", loc1)
        environment.add_agent("diff_ns", loc2)
        environment.add_agent("diff_proc", loc3)
        
        # Set visibility levels
        environment.observability.set_visibility("observer", VisibilityLevel.NAMESPACE)
        
        # Get perception
        perception = environment.perceive("observer")
        entities = perception.get('entities', {})
        
        # Should see self and same namespace
        assert "observer" in entities
        assert "same_ns" in entities
        assert "diff_ns" not in entities  # Different namespace
        
    @pytest.mark.asyncio
    async def test_environmental_dynamics(self, environment):
        """Test dynamic environment changes"""
        initial_state = environment.dynamics.state_variables.copy()
        
        # Update environment
        await environment.update(1.0)
        
        # State should change
        new_state = environment.dynamics.state_variables
        assert new_state['system_load'] != initial_state.get('system_load', -1)
        
        # Events should be processed
        assert environment.dynamics.event_queue.empty()
        
    @pytest.mark.asyncio
    async def test_agent_integration(self, environment, agent_factory):
        """Test integration with MAS agents"""
        factory, llm_service = agent_factory
        
        # Create adapter
        adapter = EnvironmentAdapter(environment)
        
        # Create and register agent
        agent = factory.create_agent(
            agent_type="reflexive",
            name="TestAgent",
            role="tester",
            capabilities=["testing"],
            llm_service=llm_service
        )
        
        await adapter.register_agent(agent, namespace="test")
        
        # Check registration
        assert str(agent.agent_id) in environment.entities
        assert str(agent.agent_id) in adapter.agent_locations
        
        # Test action execution
        success, result = await adapter.execute_agent_action(agent, {
            'type': 'request_resources',
            'resources': {'cpu': 10, 'memory': 100*1024*1024}
        })
        
        assert success
        assert 'allocated' in result
        
    @pytest.mark.asyncio
    async def test_communication_with_visibility(self, environment):
        """Test agent communication respecting visibility"""
        # Add two agents
        loc1 = SoftwareLocation(host="localhost", process_id=1, namespace="ns1")
        loc2 = SoftwareLocation(host="localhost", process_id=2, namespace="ns2")
        
        environment.add_agent("sender", loc1)
        environment.add_agent("receiver", loc2)
        
        # Set visibility - sender can't see receiver
        environment.observability.set_visibility("sender", VisibilityLevel.NAMESPACE)
        
        # Try to communicate
        success, result = await environment.execute_action("sender", {
            'type': 'communicate',
            'target': 'receiver',
            'message': {'content': 'Hello'}
        })
        
        assert not success
        assert 'not visible' in result.get('error', '')
        
    def test_network_topology(self, environment):
        """Test network connections"""
        # Add agents
        for i in range(3):
            location = SoftwareLocation(
                host="localhost",
                process_id=i,
                namespace=f"agent{i}"
            )
            environment.add_agent(f"agent{i}", location)
            
        # Create connections
        environment.spatial_model.add_connection("agent0", "agent1", "network")
        environment.spatial_model.add_connection("agent1", "agent2", "network")
        
        # Check connections
        assert environment.spatial_model.graph.has_edge("agent0", "agent1")
        assert environment.spatial_model.graph.has_edge("agent1", "agent2")
        assert not environment.spatial_model.graph.has_edge("agent0", "agent2")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])