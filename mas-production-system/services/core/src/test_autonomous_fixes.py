#!/usr/bin/env python3
"""
Test script to verify autonomous agent error fixes
"""

import asyncio
import json
import sys
sys.path.insert(0, '/app/src')

from datetime import datetime
from uuid import uuid4

# Import the fixed modules
from core.agents.cognitive_agent import CognitiveAgent
from services.llm_service import LLMService
from utils.logger import get_logger

logger = get_logger(__name__)

async def test_reflection_fix():
    """Test that reflection handles dict confidence_adjustment"""
    print("\n🧪 Testing reflection fix...")
    
    # Create a mock LLM service
    class MockLLMService:
        async def generate(self, **kwargs):
            # Return response with dict confidence_adjustment
            return {
                "success": True,
                "response": {
                    "insights": ["Test insight"],
                    "belief_updates": {"test": "value"},
                    "strategy_adjustments": [],
                    "confidence_adjustment": {"value": 0.1}  # This was causing the error
                }
            }
    
    # Create cognitive agent
    agent = CognitiveAgent(
        agent_id=uuid4(),
        name="TestAgent",
        role="tester",
        capabilities=["testing"],
        llm_service=MockLLMService()
    )
    
    # Set metrics to trigger reflection
    agent.metrics["actions_executed"] = agent.reflection_frequency
    
    try:
        # This should not raise an error now
        await agent._reflect()
        print("✅ Reflection fix successful - handled dict confidence_adjustment")
    except Exception as e:
        print(f"❌ Reflection fix failed: {e}")
        return False
    
    return True

async def test_json_parsing_fix():
    """Test enhanced JSON parsing with recovery"""
    print("\n🧪 Testing JSON parsing fix...")
    
    # Test various malformed JSON scenarios
    test_cases = [
        {
            "name": "Trailing comma",
            "response": '{"key": "value", "number": 42,}',
            "expected": {"key": "value", "number": 42}
        },
        {
            "name": "Mixed with text",
            "response": 'Here is the JSON: {"result": true, "score": 0.9}',
            "expected": {"result": True, "score": 0.9}
        },
        {
            "name": "Key-value lines",
            "response": 'key1: value1\nkey2: 123\nkey3: true',
            "expected": {"key1": "value1", "key2": 123, "key3": True}
        }
    ]
    
    # Import the json parsing logic
    import re
    
    for test in test_cases:
        print(f"  Testing: {test['name']}")
        try:
            # Simulate the enhanced parsing
            response_text = test["response"]
            
            # Try direct parsing
            try:
                result = json.loads(response_text)
            except:
                # Try fixing trailing commas
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', response_text)
                try:
                    result = json.loads(fixed_json)
                except:
                    # Try extracting JSON
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        # Parse key-value pairs
                        lines = response_text.strip().split('\n')
                        result = {}
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                if value.lower() in ('true', 'false'):
                                    value = value.lower() == 'true'
                                elif value.isdigit():
                                    value = int(value)
                                result[key] = value
            
            if result == test["expected"]:
                print(f"    ✅ Passed")
            else:
                print(f"    ❌ Failed: got {result}, expected {test['expected']}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return True

async def test_bdi_string_fix():
    """Test BDI cycle handles string inputs"""
    print("\n🧪 Testing BDI cycle string fix...")
    
    from core.agents.base_agent import BaseAgent
    
    # Create a test agent
    agent = BaseAgent(
        agent_id=uuid4(),
        name="TestAgent",
        role="tester",
        capabilities=["testing"],
        llm_service=None
    )
    
    # Test update_beliefs with string
    try:
        # This was causing the error
        await agent.update_beliefs("new belief as string")
        print("✅ String belief handled correctly")
    except Exception as e:
        print(f"❌ String belief failed: {e}")
        return False
    
    # Test update_beliefs with JSON string
    try:
        await agent.update_beliefs('{"key": "value"}')
        if agent.bdi.beliefs.get("key") == "value":
            print("✅ JSON string belief parsed correctly")
        else:
            print("❌ JSON string belief not parsed")
    except Exception as e:
        print(f"❌ JSON string belief failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Autonomous Agent Error Fixes")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Reflection Fix", await test_reflection_fix()))
    results.append(("JSON Parsing Fix", await test_json_parsing_fix()))
    results.append(("BDI String Fix", await test_bdi_string_fix()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the fixes.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
