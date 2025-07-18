#!/usr/bin/env python3
"""
Test BDI cycle timing to see if it's blocking message processing
"""

import asyncio
import time
import sys
sys.path.append('/app')

from src.services.llm_service import LLMService
from src.core.agents import AgentFactory, get_agent_runtime
from uuid import uuid4

async def test_bdi_timing():
    print("Testing BDI cycle timing...")
    
    # Create LLM service
    llm = LLMService()
    
    # Create agent
    factory = AgentFactory()
    agent_id = uuid4()
    agent = factory.create_agent(
        agent_type="reactive",
        agent_id=agent_id,
        name="TimingTestAgent",
        role="assistant",
        capabilities=["test"],
        llm_service=llm,
        initial_beliefs={"test": True},
        initial_desires=["test"]
    )
    
    print(f"\nAgent created: {agent.name}")
    
    # Test perceive timing
    print("\n1. Testing perceive() timing...")
    start = time.time()
    try:
        result = await agent.perceive({"test": "environment"})
        elapsed = time.time() - start
        print(f"   Perceive completed in {elapsed:.2f}s")
        print(f"   Result: {result}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"   Perceive failed after {elapsed:.2f}s: {e}")
    
    # Test deliberate timing
    print("\n2. Testing deliberate() timing...")
    start = time.time()
    try:
        result = await agent.deliberate()
        elapsed = time.time() - start
        print(f"   Deliberate completed in {elapsed:.2f}s")
        print(f"   Result: {result}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"   Deliberate failed after {elapsed:.2f}s: {e}")
    
    # Test full BDI cycle timing
    print("\n3. Testing full BDI cycle timing...")
    start = time.time()
    try:
        # Manually run BDI cycle
        perceptions = await agent.perceive({"test": "environment"})
        await agent.update_beliefs(perceptions)
        new_intentions = await agent.deliberate()
        for intention in new_intentions:
            await agent.commit_to_intention(intention)
        if agent.bdi.intentions:
            actions = await agent.act()
        
        elapsed = time.time() - start
        print(f"   Full BDI cycle completed in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"   BDI cycle failed after {elapsed:.2f}s: {e}")
    
    print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test_bdi_timing())