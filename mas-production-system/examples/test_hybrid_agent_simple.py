#!/usr/bin/env python3
"""
Simple test to verify the hybrid agent 'NoneType' fix without LLM dependency
"""

import asyncio
import sys
sys.path.append('/app')

from src.core.agents.hybrid_agent import HybridAgent
from src.utils.logger import get_logger
from uuid import uuid4

logger = get_logger(__name__)

async def test_hybrid_agent_perceive_fix():
    """Test hybrid agent perceive method with None environment"""
    print("\n🧪 TESTING HYBRID AGENT PERCEIVE METHOD FIX")
    print("="*50)
    
    # Create hybrid agent without LLM service (for reflexive mode only)
    print("\n1️⃣ Creating hybrid agent without LLM...")
    agent = HybridAgent(
        agent_id=uuid4(),
        name="TestHybrid",
        role="tester",
        capabilities=["testing", "validation"],
        llm_service=None,  # No LLM to avoid timeout
        reactive_rules={
            "test_trigger": {"condition": {"type": "test"}, "action": {"type": "respond", "content": "test response"}},
            "error_trigger": {"condition": {"type": "error"}, "action": {"type": "fix", "target": "error"}}
        },
        cognitive_threshold=0.9  # High threshold to favor reflexive mode
    )
    print(f"✅ Created agent: {agent.name}")
    
    # Test 1: Perceive with None environment (this was causing the error)
    print("\n2️⃣ Testing perceive with None environment...")
    try:
        perception = await agent.perceive(None)
        print("✅ SUCCESS! Perceive handled None environment without error!")
        print(f"   - Perception type: {type(perception)}")
        print(f"   - Has environment key: {'environment' in perception}")
        print(f"   - Has messages key: {'messages' in perception}")
        print(f"   - Messages value: {perception.get('messages', [])}")
        print(f"   - Complexity: {perception.get('complexity', 0):.2f}")
        print(f"   - Suggested mode: {perception.get('suggested_mode', 'unknown')}")
    except Exception as e:
        print(f"❌ FAILED! Perceive error with None: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test decide with reflexive mode (no LLM needed)
    print("\n3️⃣ Testing decide in reflexive mode...")
    try:
        # Create perception with test message
        env = {
            "messages": [{"type": "test", "content": "test message", "id": "msg1"}]
        }
        perception = await agent.perceive(env)
        print(f"   - Perception complexity: {perception.get('complexity', 0):.2f}")
        
        # Decide should use reflexive mode due to low complexity
        actions = await agent.decide(perception)
        print(f"✅ Decide executed successfully!")
        print(f"   - Actions generated: {len(actions)}")
        print(f"   - Current mode: {agent.current_mode}")
        if actions:
            print(f"   - First action: {actions[0]}")
    except Exception as e:
        print(f"❌ Decide failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test _assess_complexity with None values
    print("\n4️⃣ Testing _assess_complexity with edge cases...")
    try:
        # Test with empty perception
        complexity1 = agent._assess_complexity({})
        print(f"   - Empty perception complexity: {complexity1:.2f}")
        
        # Test with None values in perception
        complexity2 = agent._assess_complexity({"messages": None, "tasks": None})
        print(f"   - None values complexity: {complexity2:.2f}")
        
        # Test with missing keys
        complexity3 = agent._assess_complexity({"unrelated": "data"})
        print(f"   - Missing keys complexity: {complexity3:.2f}")
        
        print("✅ _assess_complexity handles edge cases!")
    except Exception as e:
        print(f"❌ _assess_complexity failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ ALL TESTS PASSED! The 'NoneType' error in hybrid agent is fixed!")
    return True

async def test_bdi_cycle():
    """Test BDI cycle without starting full agent runtime"""
    print("\n\n🔄 TESTING BDI CYCLE DIRECTLY")
    print("="*50)
    
    # Create agent
    agent = HybridAgent(
        agent_id=uuid4(),
        name="BDI-Test-Agent",
        role="executor",
        capabilities=["testing"],
        llm_service=None,
        reactive_rules={
            "default": {"condition": {}, "action": {"type": "process"}}
        }
    )
    
    # Initialize BDI attributes
    agent.bdi.beliefs = {"test": True}
    agent.bdi.desires = ["complete_test"]
    agent.bdi.intentions = []
    
    # Set context environment
    agent.context.environment = None  # This was causing the error
    
    print("1️⃣ Testing perceive with None context.environment...")
    try:
        perception = await agent.perceive(agent.context.environment)
        print("✅ Perceive handled None context.environment!")
        print(f"   - Environment in perception: {perception.get('environment')}")
    except Exception as e:
        print(f"❌ Perceive failed: {e}")
        return False
    
    print("\n2️⃣ Testing deliberate...")
    try:
        intentions = await agent.deliberate()
        print(f"✅ Deliberate succeeded! Intentions: {intentions}")
    except Exception as e:
        print(f"❌ Deliberate failed: {e}")
        return False
    
    print("\n3️⃣ Testing act...")
    try:
        actions = await agent.act()
        print(f"✅ Act succeeded! Actions: {len(actions)}")
    except Exception as e:
        print(f"❌ Act failed: {e}")
        return False
    
    print("\n✅ BDI CYCLE TEST PASSED!")
    return True

async def main():
    """Run all tests"""
    print("\n🚀 HYBRID AGENT 'NoneType' FIX VERIFICATION (SIMPLE)")
    print("="*60)
    
    # Test 1: Basic perceive fix
    test1_result = await test_hybrid_agent_perceive_fix()
    
    # Test 2: BDI cycle
    test2_result = await test_bdi_cycle()
    
    if test1_result and test2_result:
        print("\n\n🎉 ALL TESTS PASSED!")
        print("✅ The 'NoneType' object has no attribute 'get' error has been fixed!")
        print("✅ Hybrid agents can now handle None environment correctly!")
    else:
        print("\n\n❌ Some tests failed. The fix may need more work.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())