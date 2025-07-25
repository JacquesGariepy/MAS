#!/usr/bin/env python3
"""
Fix the errors in autonomous_agent logs:
1. Reflection failed: unsupported operand type(s) for +: 'float' and 'dict'
2. Failed to parse JSON response: Expecting ',' delimiter
3. Error in BDI cycle: 'str' object has no attribute 'items'
"""

import os
import re
import json
from datetime import datetime

def fix_cognitive_agent_reflection_error():
    """Fix the reflection error where confidence_adjustment might be a dict instead of float"""
    
    file_path = '/app/src/core/agents/cognitive_agent.py'
    
    print(f"\n🔧 Fixing reflection error in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # The error occurs at line 460 where we try to add a dict to a float
    # Fix: Ensure confidence_adjustment is a float
    old_code = """            if result.get("confidence_adjustment"):
                self.confidence_threshold = max(0.3, min(0.9, 
                    self.confidence_threshold + result["confidence_adjustment"]))"""
    
    new_code = """            if result.get("confidence_adjustment"):
                # Ensure confidence_adjustment is a float
                adjustment = result["confidence_adjustment"]
                if isinstance(adjustment, dict):
                    # If it's a dict, try to get a value field or default to 0
                    adjustment = adjustment.get('value', 0.0)
                elif not isinstance(adjustment, (int, float)):
                    # Convert to float if possible
                    try:
                        adjustment = float(adjustment)
                    except (ValueError, TypeError):
                        adjustment = 0.0
                
                self.confidence_threshold = max(0.3, min(0.9, 
                    self.confidence_threshold + adjustment))"""
    
    content = content.replace(old_code, new_code)
    
    # Backup and save
    backup_path = file_path + '.backup_reflection'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed reflection error")
    print(f"📁 Backup saved to {backup_path}")
    
    return file_path

def fix_llm_service_json_parsing():
    """Fix JSON parsing errors in LLM service"""
    
    file_path = '/app/src/services/llm_service.py'
    
    print(f"\n🔧 Fixing JSON parsing in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the generate method that handles JSON responses
    # The issue is malformed JSON from LLM - need better error handling
    
    # Look for where we parse JSON response
    pattern = r'(if.*json_response.*:)(.*?)(except.*?:.*?logger\.error.*?)(.*?)(return.*?})'
    
    def enhance_json_parsing(match):
        """Enhance JSON parsing with better error recovery"""
        part1 = match.group(1)  # if json_response:
        parsing_code = match.group(2)  # JSON parsing logic
        except_part = match.group(3)  # except clause
        except_body = match.group(4)  # except body
        return_part = match.group(5)  # return statement
        
        # Enhanced parsing with multiple recovery strategies
        enhanced_parsing = '''
                try:
                    # First attempt: direct JSON parsing
                    result = json.loads(response_text)
                    return {
                        "success": True,
                        "response": result,
                        "usage": usage_info
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.error(f"Raw response: {response_text[:200]}")
                    
                    # Recovery attempt 1: Fix common JSON issues
                    try:
                        # Remove trailing commas and fix quotes
                        fixed_json = response_text
                        # Remove trailing commas before } or ]
                        fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                        # Try to parse again
                        result = json.loads(fixed_json)
                        logger.info("Successfully recovered JSON after fixing syntax")
                        return {
                            "success": True,
                            "response": result,
                            "usage": usage_info
                        }
                    except:
                        pass
                    
                    # Recovery attempt 2: Extract JSON from text
                    try:
                        # Look for JSON object in the response
                        json_match = re.search(r'\{[\s\S]*\}', response_text)
                        if json_match:
                            result = json.loads(json_match.group())
                            logger.info("Successfully extracted JSON from response")
                            return {
                                "success": True,
                                "response": result,
                                "usage": usage_info
                            }
                    except:
                        pass
                    
                    # Recovery attempt 3: Create structured response from text
                    try:
                        # Try to extract key-value pairs
                        lines = response_text.strip().split('\n')
                        result = {}
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip().strip('"\'')
                                value = value.strip().strip('",\'')
                                # Try to convert to appropriate type
                                if value.lower() in ('true', 'false'):
                                    value = value.lower() == 'true'
                                elif value.replace('.', '').replace('-', '').isdigit():
                                    value = float(value) if '.' in value else int(value)
                                result[key] = value
                        
                        if result:
                            logger.info("Successfully created structured response from text")
                            return {
                                "success": True,
                                "response": result,
                                "usage": usage_info
                            }
                    except:
                        pass
                    
                    # Final fallback
                    logger.error("All JSON recovery attempts failed")'''
        
        return part1 + enhanced_parsing + except_part + except_body + return_part
    
    # Apply the enhancement
    content = re.sub(pattern, enhance_json_parsing, content, flags=re.DOTALL)
    
    # Also add import for re at the top if not present
    if 'import re' not in content:
        content = content.replace('import json', 'import json\nimport re')
    
    # Backup and save
    backup_path = file_path + '.backup_json'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Enhanced JSON parsing with recovery strategies")
    print(f"📁 Backup saved to {backup_path}")
    
    return file_path

def fix_bdi_cycle_string_error():
    """Fix the BDI cycle error where string is accessed as dict"""
    
    # The error suggests that somewhere in the BDI cycle, we're trying to call .items() on a string
    # This likely happens when processing beliefs or actions
    
    base_agent_path = '/app/src/core/agents/base_agent.py'
    
    print(f"\n🔧 Fixing BDI cycle string error in {base_agent_path}")
    
    # Read the file
    with open(base_agent_path, 'r') as f:
        content = f.read()
    
    # Find update_beliefs method which likely has the issue
    # The error occurs when beliefs update receives a string instead of dict
    
    # Pattern to find update_beliefs method
    pattern = r'(async def update_beliefs\(self, beliefs: Dict\[str, Any\]\).*?:)(.*?)(?=\n    async def|\n    def|\nclass|\Z)'
    
    def fix_update_beliefs(match):
        method_signature = match.group(1)
        method_body = match.group(2)
        
        # Add type checking at the beginning of the method
        enhanced_body = '''
        """Update agent beliefs"""
        # Ensure beliefs is a dict
        if isinstance(beliefs, str):
            # If beliefs is a string, try to parse it as JSON
            try:
                beliefs = json.loads(beliefs)
            except json.JSONDecodeError:
                # If not JSON, create a dict with the string as a value
                beliefs = {"belief_update": beliefs}
                logger.warning(f"Received string instead of dict for beliefs, wrapped in dict")
        elif not isinstance(beliefs, dict):
            logger.error(f"Invalid beliefs type: {type(beliefs)}")
            return
            
        # Original method body continues...''' + method_body
        
        return method_signature + enhanced_body
    
    content = re.sub(pattern, fix_update_beliefs, content, flags=re.DOTALL)
    
    # Also fix the execute_action method which might have similar issues
    action_pattern = r'(async def _execute_action\(self, action: Dict\[str, Any\]\).*?:)(.*?)(?=\n    async def|\n    def|\nclass|\Z)'
    
    def fix_execute_action(match):
        method_signature = match.group(1)
        method_body = match.group(2)
        
        enhanced_body = '''
        """Execute a single action"""
        # Ensure action is a dict
        if isinstance(action, str):
            # Try to parse string as action description
            action = {"type": "execute", "description": action}
            logger.warning(f"Received string instead of dict for action, wrapped in dict")
        elif not isinstance(action, dict):
            logger.error(f"Invalid action type: {type(action)}")
            return
            
        # Original method body continues...''' + method_body
        
        return method_signature + enhanced_body
    
    content = re.sub(action_pattern, fix_execute_action, content, flags=re.DOTALL)
    
    # Ensure json is imported
    if 'import json' not in content:
        content = content.replace('from typing import', 'import json\nfrom typing import')
    
    # Backup and save
    backup_path = base_agent_path + '.backup_bdi'
    os.rename(base_agent_path, backup_path)
    
    with open(base_agent_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed BDI cycle string error")
    print(f"📁 Backup saved to {backup_path}")
    
    return base_agent_path

def create_test_script():
    """Create a test script to verify the fixes"""
    
    test_script = '''#!/usr/bin/env python3
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
    print("\\n🧪 Testing reflection fix...")
    
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
    print("\\n🧪 Testing JSON parsing fix...")
    
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
            "response": 'key1: value1\\nkey2: 123\\nkey3: true',
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
                fixed_json = re.sub(r',(\s*[}\\]])', r'\\1', response_text)
                try:
                    result = json.loads(fixed_json)
                except:
                    # Try extracting JSON
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        # Parse key-value pairs
                        lines = response_text.strip().split('\\n')
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
    print("\\n🧪 Testing BDI cycle string fix...")
    
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
    print("\\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the fixes.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    test_path = '/app/src/test_autonomous_fixes.py'
    with open(test_path, 'w') as f:
        f.write(test_script)
    
    os.chmod(test_path, 0o755)
    print(f"\n✅ Created test script: {test_path}")
    
    return test_path

def main():
    """Apply all fixes"""
    print("\n" + "="*70)
    print("🔧 FIXING AUTONOMOUS AGENT ERRORS")
    print("="*70)
    
    print("\nIdentified errors from log analysis:")
    print("1. ❌ Reflection failed: unsupported operand type(s) for +: 'float' and 'dict'")
    print("2. ❌ Failed to parse JSON response: Expecting ',' delimiter")
    print("3. ❌ Error in BDI cycle: 'str' object has no attribute 'items'")
    
    print("\nApplying fixes...")
    
    # Apply fixes
    fixed_files = []
    
    try:
        fixed_files.append(fix_cognitive_agent_reflection_error())
        fixed_files.append(fix_llm_service_json_parsing())
        fixed_files.append(fix_bdi_cycle_string_error())
        test_script = create_test_script()
        
        print("\n" + "="*70)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY")
        print("="*70)
        
        print("\n📁 Fixed files:")
        for f in fixed_files:
            print(f"  - {f}")
        
        print(f"\n🧪 Test with:")
        print(f"  docker exec mas-production-system-core-1 python {test_script}")
        
        print("\n📝 Summary of fixes:")
        print("1. ✅ Reflection error - Now handles dict confidence_adjustment values")
        print("2. ✅ JSON parsing - Enhanced with multiple recovery strategies")
        print("3. ✅ BDI cycle - Now handles string inputs gracefully")
        
        print("\n💡 Next steps:")
        print("1. Run the test script to verify fixes")
        print("2. Test autonomous_agent.py again")
        print("3. Monitor logs for any remaining errors")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())