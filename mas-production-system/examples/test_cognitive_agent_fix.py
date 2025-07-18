#!/usr/bin/env python3
"""
Test simple pour vérifier que les agents cognitifs fonctionnent avec phi-4-mini-reasoning
"""

import asyncio
import json
import sys
sys.path.append('/app')

from src.services.llm_service import LLMService
from src.core.agents.cognitive_agent import CognitiveAgent
from uuid import uuid4
from datetime import datetime

async def test_cognitive_agent_perception():
    """Test the cognitive agent perception with phi-4-mini-reasoning"""
    print("="*60)
    print("TEST: Cognitive Agent with phi-4-mini-reasoning")
    print("="*60)
    
    # 1. Create LLM service
    llm = LLMService()
    print(f"\n1. LLM Service:")
    print(f"   Mock Mode: {llm.enable_mock}")
    print(f"   Model: {llm.model}")
    print(f"   Base URL: {llm.client.base_url if llm.client else 'No client'}")
    
    # 2. Create cognitive agent
    agent = CognitiveAgent(
        agent_id=uuid4(),
        name="TestCognitiveAgent",
        role="analyst",
        capabilities=["analyze", "plan", "reason"],
        llm_service=llm,
        initial_beliefs={"test_mode": True, "environment": "testing"},
        initial_desires=["understand_environment", "process_messages"]
    )
    
    print(f"\n2. Cognitive Agent created:")
    print(f"   Name: {agent.name}")
    print(f"   Role: {agent.role}")
    print(f"   Beliefs: {agent.bdi.beliefs}")
    print(f"   Desires: {agent.bdi.desires}")
    
    # 3. Test perception
    print(f"\n3. Testing perception...")
    
    environment = {
        "timestamp": datetime.utcnow().isoformat(),
        "messages_pending": True,
        "system_status": "operational"
    }
    
    try:
        perceptions = await agent.perceive(environment)
        print(f"   ✅ Perception succeeded!")
        print(f"   Result type: {type(perceptions)}")
        print(f"   Content: {json.dumps(perceptions, indent=2)}")
    except Exception as e:
        print(f"   ❌ Perception failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Test deliberation
    print(f"\n4. Testing deliberation...")
    
    try:
        intentions = await agent.deliberate()
        print(f"   ✅ Deliberation succeeded!")
        print(f"   New intentions: {intentions}")
        print(f"   Current intentions: {agent.bdi.intentions}")
    except Exception as e:
        print(f"   ❌ Deliberation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Test simple LLM call
    print(f"\n5. Testing direct LLM call...")
    
    try:
        response = await llm.generate(
            prompt="Respond with a simple JSON object containing status='ok'",
            system_prompt="You are a helpful assistant. Always respond with valid JSON.",
            temperature=0.1,
            json_response=True,
            max_tokens=50
        )
        print(f"   ✅ LLM call succeeded!")
        print(f"   Response: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"   ❌ LLM call failed: {type(e).__name__}: {e}")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_cognitive_agent_perception())