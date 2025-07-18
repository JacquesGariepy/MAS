#!/usr/bin/env python3
"""
Test agent directly without runtime
"""

import asyncio
import sys
sys.path.append('/app')

from src.services.llm_service import LLMService
from src.core.agents import AgentFactory
from uuid import uuid4

class SimpleMessage:
    def __init__(self, content):
        self.sender = "test_sender"
        self.performative = "inform"
        self.content = content

async def test_direct_agent():
    print("Testing agent directly...")
    
    # Create LLM service
    llm = LLMService()
    
    # Create agent
    factory = AgentFactory()
    agent = factory.create_agent(
        agent_type="reactive",
        agent_id=uuid4(),
        name="DirectTestAgent",
        role="assistant",
        capabilities=["test"],
        llm_service=llm,
        initial_beliefs={"ready": True},
        initial_desires=["respond"]
    )
    
    print(f"\nAgent created: {agent.name}")
    
    # Start agent directly
    agent_task = asyncio.create_task(agent.run())
    print("Agent task started")
    
    # Wait for startup
    await asyncio.sleep(1)
    
    # Send message
    print("\nSending message...")
    message = SimpleMessage({"text": "Hello agent"})
    await agent.receive_message(message)
    print(f"Message sent, queue size: {agent._message_queue.qsize()}")
    
    # Wait and check
    print("\nWaiting for processing...")
    for i in range(10):
        await asyncio.sleep(1)
        metrics = await agent.get_metrics()
        print(f"Check {i+1}: Messages={metrics['messages_processed']}, Errors={metrics['errors']}, Queue={agent._message_queue.qsize()}")
        if metrics['messages_processed'] > 0:
            print("✅ Message processed!")
            break
    
    # Stop agent
    print("\nStopping agent...")
    await agent.stop()
    
    # Cancel task
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass
    
    print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_direct_agent())