#!/usr/bin/env python3
"""
Test direct LLM service to verify LMStudio integration
"""

import asyncio
import os

# Force environment variables
os.environ['LLM_PROVIDER'] = 'lmstudio'
os.environ['LLM_BASE_URL'] = 'http://host.docker.internal:1234/v1'
os.environ['LLM_MODEL'] = 'phi-4-mini-reasoning'
os.environ['ENABLE_MOCK_LLM'] = 'false'

import sys
sys.path.append('/app')
from src.services.llm_service import LLMService

async def test_llm():
    """Test LLM service directly"""
    print("=== Testing LLM Service ===")
    print(f"Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"Base URL: {os.getenv('LLM_BASE_URL')}")
    print(f"Model: {os.getenv('LLM_MODEL')}")
    print(f"Mock enabled: {os.getenv('ENABLE_MOCK_LLM')}")
    print()
    
    # Create LLM service
    llm = LLMService()
    
    print(f"LLM Service Mock Mode: {llm.enable_mock}")
    print(f"LLM Service Model: {llm.model}")
    print()
    
    if llm.enable_mock:
        print("❌ ERROR: LLM Service is in MOCK mode!")
        return
    
    # Test a simple prompt
    prompt = "What is 2+2? Give a short answer."
    print(f"Prompt: {prompt}")
    print("Sending to LMStudio...")
    
    try:
        response = await llm.generate(
            prompt=prompt,
            system_prompt="You are a helpful assistant. Be concise.",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"\n✅ Response from LMStudio: {response}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())