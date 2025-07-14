"""
Test agents module
"""
import pytest
import asyncio
from uuid import uuid4

from src.core.agents import AgentFactory, AgentRuntime, AGENT_TYPES

@pytest.mark.asyncio
async def test_agent_factory_create():
    """Test agent creation via factory"""
    agent_id = uuid4()
    
    # Create cognitive agent
    agent = AgentFactory.create_agent(
        agent_type="cognitive",
        agent_id=agent_id,
        name="Test Agent",
        role="tester",
        capabilities=["test", "analyze"]
    )
    
    assert agent.agent_id == agent_id
    assert agent.name == "Test Agent"
    assert agent.role == "tester"
    assert "test" in agent.capabilities
    assert "analyze" in agent.capabilities

def test_agent_factory_invalid_type():
    """Test creating agent with invalid type"""
    with pytest.raises(ValueError, match="Unknown agent type"):
        AgentFactory.create_agent(
            agent_type="invalid_type",
            agent_id=uuid4(),
            name="Test",
            role="test",
            capabilities=[]
        )

@pytest.mark.asyncio
async def test_agent_runtime():
    """Test agent runtime management"""
    runtime = AgentRuntime()
    
    # Create an agent
    agent = AgentFactory.create_agent(
        agent_type="cognitive",
        agent_id=uuid4(),
        name="Runtime Test Agent",
        role="tester",
        capabilities=["test"]
    )
    
    # Start agent
    await runtime.start_agent(agent)
    
    # Check agent is running
    assert agent.agent_id in runtime.list_running_agents()
    assert runtime.get_running_agent(agent.agent_id) == agent
    
    # Stop agent
    await runtime.stop_agent(agent.agent_id)
    
    # Check agent is stopped
    assert agent.agent_id not in runtime.list_running_agents()
    assert runtime.get_running_agent(agent.agent_id) is None

@pytest.mark.asyncio
async def test_agent_runtime_double_start():
    """Test starting same agent twice"""
    runtime = AgentRuntime()
    agent_id = uuid4()
    
    agent = AgentFactory.create_agent(
        agent_type="cognitive",
        agent_id=agent_id,
        name="Test",
        role="test",
        capabilities=[]
    )
    
    await runtime.start_agent(agent)
    
    # Try to start again
    with pytest.raises(ValueError, match="already running"):
        await runtime.start_agent(agent)
    
    # Cleanup
    await runtime.stop_agent(agent_id)

def test_register_agent_type():
    """Test registering new agent type"""
    from src.core.agents.base_agent import BaseAgent
    
    class CustomAgent(BaseAgent):
        pass
    
    # Register new type
    AgentFactory.register_agent_type("custom", CustomAgent)
    
    assert "custom" in AGENT_TYPES
    assert AGENT_TYPES["custom"] == CustomAgent