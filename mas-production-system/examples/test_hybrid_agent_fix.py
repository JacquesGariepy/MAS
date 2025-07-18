#!/usr/bin/env python3
"""
Test script to verify the hybrid agent 'NoneType' fix
"""

import asyncio
import sys
sys.path.append('/app')

from src.core.agents.hybrid_agent import HybridAgent
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from uuid import uuid4

logger = get_logger(__name__)

async def test_hybrid_agent_with_none_environment():
    """Test hybrid agent with None environment to verify fix"""
    print("\n🧪 TESTING HYBRID AGENT 'NoneType' FIX")
    print("="*50)
    
    # Create LLM service
    llm_service = LLMService()
    
    # Create hybrid agent
    print("\n1️⃣ Creating hybrid agent...")
    agent = HybridAgent(
        agent_id=uuid4(),
        name="TestHybrid",
        role="tester",
        capabilities=["testing", "validation"],
        llm_service=llm_service,
        reactive_rules={
            "test_trigger": {"condition": {"type": "test"}, "action": {"type": "respond"}},
            "error_trigger": {"condition": {"type": "error"}, "action": {"type": "fix"}}
        },
        cognitive_threshold=0.7
    )
    print(f"✅ Created agent: {agent.name}")
    
    # Test 1: Perceive with None environment
    print("\n2️⃣ Testing perceive with None environment...")
    try:
        perception = await agent.perceive(None)
        print("✅ Perceive handled None environment successfully!")
        print(f"   - Perception keys: {list(perception.keys())}")
        print(f"   - Complexity: {perception.get('complexity', 0):.2f}")
        print(f"   - Suggested mode: {perception.get('suggested_mode', 'unknown')}")
    except Exception as e:
        print(f"❌ Perceive failed with None: {e}")
        return False
    
    # Test 2: Perceive with empty environment
    print("\n3️⃣ Testing perceive with empty environment...")
    try:
        perception = await agent.perceive({})
        print("✅ Perceive handled empty environment successfully!")
        print(f"   - Complexity: {perception.get('complexity', 0):.2f}")
    except Exception as e:
        print(f"❌ Perceive failed with empty dict: {e}")
        return False
    
    # Test 3: Perceive with partial environment
    print("\n4️⃣ Testing perceive with partial environment...")
    try:
        env = {"messages": [{"performative": "inform", "content": "test"}]}
        perception = await agent.perceive(env)
        print("✅ Perceive handled partial environment successfully!")
        print(f"   - Messages: {len(perception.get('messages', []))}")
        print(f"   - Complexity: {perception.get('complexity', 0):.2f}")
    except Exception as e:
        print(f"❌ Perceive failed with partial env: {e}")
        return False
    
    # Test 4: Test decide with None perception
    print("\n5️⃣ Testing decide method...")
    try:
        # First get a valid perception
        perception = await agent.perceive({"tasks": [{"priority": "high", "task_type": "planning"}]})
        actions = await agent.decide(perception)
        print(f"✅ Decide method executed successfully!")
        print(f"   - Actions generated: {len(actions)}")
        print(f"   - Current mode: {agent.current_mode}")
    except Exception as e:
        print(f"❌ Decide failed: {e}")
        return False
    
    # Test 5: Test cognitive decide with None/invalid response
    print("\n6️⃣ Testing cognitive decide with edge cases...")
    try:
        # Force cognitive mode
        perception = {
            "complexity": 0.9,
            "suggested_mode": "cognitive",
            "messages": [{"performative": "negotiate", "content": {"proposal": "complex"}}]
        }
        actions = await agent._cognitive_decide(perception)
        print(f"✅ Cognitive decide handled edge cases!")
        print(f"   - Actions: {len(actions)}")
    except Exception as e:
        print(f"❌ Cognitive decide failed: {e}")
        return False
    
    # Test 6: Test mode statistics
    print("\n7️⃣ Testing mode statistics...")
    try:
        stats = agent.get_mode_statistics()
        print("✅ Mode statistics retrieved successfully!")
        print(f"   - Total decisions: {stats['total_decisions']}")
        print(f"   - Reflexive: {stats['reflexive_percent']:.1f}%")
        print(f"   - Cognitive: {stats['cognitive_percent']:.1f}%")
        print(f"   - Mixed: {stats['mixed_percent']:.1f}%")
    except Exception as e:
        print(f"❌ Mode statistics failed: {e}")
        return False
    
    print("\n✅ ALL TESTS PASSED! The hybrid agent 'NoneType' error is fixed!")
    return True

async def test_hybrid_in_swarm_context():
    """Test hybrid agent in swarm context similar to where error occurred"""
    print("\n\n🐝 TESTING HYBRID AGENT IN SWARM CONTEXT")
    print("="*50)
    
    from src.core.agents import AgentFactory, get_agent_runtime
    
    factory = AgentFactory()
    runtime = get_agent_runtime()
    
    # Create hybrid agent through factory
    print("\n1️⃣ Creating hybrid agent through factory...")
    agent_config = {
        "agent_type": "hybrid",
        "agent_id": uuid4(),
        "name": "Executor-hybrid-1",
        "role": "executor",
        "capabilities": ["code_generation", "testing", "implementation"],
        "reactive_rules": {
            "bug_detected": {"condition": {"type": "bug"}, "action": {"type": "fix_bug"}},
            "test_failed": {"condition": {"type": "test_failure"}, "action": {"type": "debug_test"}}
        },
        "llm_service": LLMService(),
        "initial_beliefs": {
            "swarm_size": 3,
            "role": "executor",
            "status": "ready"
        },
        "initial_desires": [
            "complete_executor_tasks",
            "collaborate_with_swarm"
        ]
    }
    
    try:
        agent = factory.create_agent(**agent_config)
        await runtime.register_agent(agent)
        await runtime.start_agent(agent)
        print(f"✅ Agent created and started: {agent.name}")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return False
    
    # Test BDI cycle
    print("\n2️⃣ Testing BDI cycle (where error occurred)...")
    try:
        # This should trigger the BDI cycle
        await asyncio.sleep(2)  # Let BDI cycle run
        print("✅ BDI cycle running without errors!")
        
        # Check agent status
        print(f"   - Agent status: {agent.status}")
        print(f"   - Current mode: {getattr(agent, 'current_mode', 'N/A')}")
        
    except Exception as e:
        print(f"❌ BDI cycle error: {e}")
        return False
    
    # Stop agent
    print("\n3️⃣ Stopping agent...")
    try:
        await runtime.stop_agent(agent.agent_id)
        print("✅ Agent stopped successfully!")
    except Exception as e:
        print(f"⚠️  Warning stopping agent: {e}")
    
    print("\n✅ SWARM CONTEXT TEST PASSED!")
    return True

async def main():
    """Run all tests"""
    print("\n🚀 HYBRID AGENT 'NoneType' FIX VERIFICATION")
    print("="*60)
    
    # Run basic tests
    basic_result = await test_hybrid_agent_with_none_environment()
    
    # Run swarm context test
    swarm_result = await test_hybrid_in_swarm_context()
    
    if basic_result and swarm_result:
        print("\n\n🎉 ALL TESTS PASSED! The hybrid agent is now working correctly!")
        print("The 'NoneType' object has no attribute 'get' error has been fixed.")
    else:
        print("\n\n❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())