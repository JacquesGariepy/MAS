"""
Test script for the Agent Factory
Demonstrates creating all three types of agents with proper parameters
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.core.src.agents.agent_factory import AgentFactory
from services.core.src.utils.logger import get_logger

logger = get_logger(__name__)


def test_reactive_agent():
    """Test creating a reactive (cognitive) agent"""
    print("\n=== Testing Reactive Agent Creation ===")
    
    agent = AgentFactory.create_agent(
        agent_type="reactive",
        agent_id=uuid4(),
        name="ReactiveBot",
        role="Problem Solver",
        capabilities=["reasoning", "planning", "learning"],
        llm_service=None,  # Would normally pass LLM service here
        beliefs={"environment": "test", "mode": "development"},
        desires=["solve_problems", "learn_patterns"],
    )
    
    print(f"Created agent: {agent.name} (Type: {agent.__class__.__name__})")
    print(f"  - Role: {agent.role}")
    print(f"  - Capabilities: {agent.capabilities}")
    print(f"  - Beliefs: {agent.beliefs}")
    print(f"  - Desires: {agent.desires}")
    
    return agent


def test_reflexive_agent():
    """Test creating a reflexive (rule-based) agent"""
    print("\n=== Testing Reflexive Agent Creation ===")
    
    # Define some reactive rules
    reactive_rules = {
        "greet_rule": {
            "condition": {"performative": "request", "content": {"type": "greeting"}},
            "action": {"type": "respond", "performative": "inform", "content": "Hello! How can I help you?"}
        },
        "emergency_rule": {
            "condition": {"priority": "critical"},
            "action": {"type": "respond", "performative": "inform", "content": "Emergency response activated!"}
        }
    }
    
    agent = AgentFactory.create_agent(
        agent_type="reflexive",
        agent_id=uuid4(),
        name="ReflexBot",
        role="Quick Responder",
        capabilities=["fast_response", "rule_execution"],
        llm_service=None,
        reactive_rules=reactive_rules,
        beliefs={"status": "ready"},
    )
    
    print(f"Created agent: {agent.name} (Type: {agent.__class__.__name__})")
    print(f"  - Role: {agent.role}")
    print(f"  - Capabilities: {agent.capabilities}")
    print(f"  - Number of rules: {len(agent.reactive_rules)}")
    print(f"  - Rules: {list(agent.reactive_rules.keys())}")
    
    return agent


def test_hybrid_agent():
    """Test creating a hybrid agent"""
    print("\n=== Testing Hybrid Agent Creation ===")
    
    # Rules for reflexive processing
    reactive_rules = {
        "simple_query": {
            "condition": {"performative": "query", "complexity": "low"},
            "action": {"type": "respond", "performative": "inform", "content": "Quick answer"}
        }
    }
    
    agent = AgentFactory.create_agent(
        agent_type="hybrid",
        agent_id=uuid4(),
        name="HybridBot",
        role="Adaptive Assistant",
        capabilities=["fast_response", "deep_reasoning", "mode_switching"],
        llm_service=None,  # Would normally pass LLM service
        reactive_rules=reactive_rules,
        cognitive_threshold=0.6,  # Switch to cognitive mode above this complexity
        beliefs={"mode": "adaptive"},
        desires=["optimize_responses", "balance_speed_quality"],
    )
    
    print(f"Created agent: {agent.name} (Type: {agent.__class__.__name__})")
    print(f"  - Role: {agent.role}")
    print(f"  - Capabilities: {agent.capabilities}")
    print(f"  - Number of rules: {len(agent.reactive_rules)}")
    print(f"  - Cognitive threshold: {agent.cognitive_threshold}")
    print(f"  - Current mode: {agent.current_mode}")
    
    return agent


def test_error_handling():
    """Test error handling for invalid agent types"""
    print("\n=== Testing Error Handling ===")
    
    try:
        AgentFactory.create_agent(
            agent_type="invalid_type",
            agent_id=uuid4(),
            name="InvalidBot",
            role="Test",
            capabilities=[],
        )
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")
    
    # Test getting available types
    available_types = AgentFactory.get_available_types()
    print(f"\nAvailable agent types: {available_types}")


async def test_agent_lifecycle():
    """Test basic agent lifecycle operations"""
    print("\n=== Testing Agent Lifecycle ===")
    
    # Create a reflexive agent
    agent = AgentFactory.create_agent(
        agent_type="reflexive",
        agent_id=uuid4(),
        name="LifecycleBot",
        role="Test Agent",
        capabilities=["testing"],
        reactive_rules={
            "test_rule": {
                "condition": {"test": True},
                "action": {"type": "respond", "content": "Test response"}
            }
        }
    )
    
    # Test perception
    perception = await agent.perceive({"messages": [{"test": True}]})
    print(f"Perception result: {perception}")
    
    # Test decision making
    decisions = await agent.decide(perception)
    print(f"Decisions made: {len(decisions)} actions")
    
    # Test mode statistics for hybrid agent
    if hasattr(agent, 'get_mode_statistics'):
        stats = agent.get_mode_statistics()
        print(f"Mode statistics: {stats}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent Factory Test Suite")
    print("=" * 60)
    
    # Test creating each type of agent
    reactive_agent = test_reactive_agent()
    reflexive_agent = test_reflexive_agent()
    hybrid_agent = test_hybrid_agent()
    
    # Test error handling
    test_error_handling()
    
    # Test async operations
    print("\n" + "=" * 60)
    asyncio.run(test_agent_lifecycle())
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()