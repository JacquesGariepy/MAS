#!/usr/bin/env python3
"""
Test the code generation capability of the unified swarm
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedLLMService

async def test_code_generation():
    """Test that the LLM service can generate actual code"""
    print("Testing Code Generation Capability")
    print("="*50)
    
    # Create LLM service
    llm_service = UnifiedLLMService(config={'mock_mode': False})
    
    # Test 1: Generate code for calculator
    print("\n1. Testing calculator code generation:")
    prompt = "Generate code to implement a calculator function that can add, subtract, multiply and divide"
    result = await llm_service.generate(prompt)
    print(f"Response type: {type(result)}")
    print(f"Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    
    # Test 2: Analyze a request
    print("\n2. Testing request analysis:")
    analysis = await llm_service.analyze_request("create test for calculator")
    print(f"Analysis: {analysis}")
    
    # Test 3: Decompose task
    print("\n3. Testing task decomposition:")
    decomposition = await llm_service.decompose_task("create test for calculator", analysis)
    print(f"Decomposition: {decomposition}")
    print(f"Number of subtasks: {len(decomposition)}")
    for i, task in enumerate(decomposition, 1):
        print(f"  {i}. {task.get('description', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_code_generation())