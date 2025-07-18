#!/usr/bin/env python3
"""Test LLM configuration to verify it's using the real API"""

import sys
import os
sys.path.append('/app')

import asyncio
from src.services.llm_service import LLMService
from src.config import settings

async def test_llm_config():
    """Test the LLM configuration"""
    print("=== LLM Configuration Test ===")
    print(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"LLM_MODEL: {settings.LLM_MODEL}")
    print(f"ENABLE_MOCK_LLM: {settings.ENABLE_MOCK_LLM}")
    print(f"LLM_API_KEY: {'***' + settings.LLM_API_KEY[-4:] if settings.LLM_API_KEY else 'None'}")
    print(f"OPENAI_API_KEY: {'***' + settings.OPENAI_API_KEY[-4:] if settings.OPENAI_API_KEY else 'None'}")
    
    llm_service = LLMService()
    print(f"\nLLM Service Mock Mode: {llm_service.enable_mock}")
    print(f"LLM Service Model: {llm_service.model}")
    print(f"LLM Service API Key: {'***' + llm_service.api_key[-4:] if llm_service.api_key else 'None'}")
    
    # Test a simple generation
    print("\n=== Testing LLM Generation ===")
    try:
        result = await llm_service.generate(
            prompt="Say 'Hello from OpenAI' if you're the real OpenAI API, or 'Hello from Mock' if you're in mock mode.",
            json_response=False
        )
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response')}")
        if 'mock_mode' in str(result):
            print("⚠️  WARNING: Still in mock mode!")
        else:
            print("✅ Using real OpenAI API!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_config())