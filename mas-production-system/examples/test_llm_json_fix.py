#!/usr/bin/env python3
"""Test script to verify LLM JSON response handling fix"""

import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.core.src.services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_json_response():
    """Test JSON response generation with phi-4-mini-reasoning model"""
    llm_service = LLMService()
    
    # Test different types of prompts
    test_prompts = [
        {
            "name": "Agent Analysis",
            "prompt": """
            Analyze the following perceptions:
            - Current beliefs: {"status": "active", "role": "coordinator"}
            - Current desires: ["complete_task", "collaborate"]
            - Current perceptions: {"message_count": 0, "current_task": null}
            
            Provide analysis with:
            1. environment_changes
            2. desire_opportunities
            3. threats
            4. trends
            """,
            "system": "You are an analytical agent. Analyze the given data and provide structured insights."
        },
        {
            "name": "Simple Decision",
            "prompt": "Based on current state, decide the next action: wait or proceed?",
            "system": "You are a decision-making agent."
        },
        {
            "name": "Complex Analysis",
            "prompt": """
            Given the current system state:
            - 5 active agents
            - 3 pending tasks
            - Resource utilization at 60%
            
            Analyze and provide recommendations.
            """,
            "system": "You are a system coordinator agent."
        }
    ]
    
    for test in test_prompts:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"{'='*60}")
        
        try:
            response = await llm_service.generate(
                prompt=test['prompt'],
                system_prompt=test['system'],
                json_response=True,
                temperature=0.7,
                task_type='reasoning'
            )
            
            if response.get('success'):
                print(f"✅ Success! Response structure:")
                print(f"   - Type: {type(response['response'])}")
                print(f"   - Keys: {list(response['response'].keys()) if isinstance(response['response'], dict) else 'N/A'}")
                print(f"   - Extracted from reasoning: {response.get('extracted_from_reasoning', False)}")
                print(f"\nJSON Response:")
                import json
                print(json.dumps(response['response'], indent=2))
            else:
                print(f"❌ Failed: {response.get('error')}")
                if response.get('raw_text'):
                    print(f"\nRaw text (first 500 chars):")
                    print(response['raw_text'][:500])
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_json_response())