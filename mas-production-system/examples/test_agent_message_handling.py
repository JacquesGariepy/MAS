#!/usr/bin/env python3
"""
Test agent message handling to debug why responses aren't generated
"""

import asyncio
import sys
sys.path.append('/app')

from src.services.llm_service import LLMService
from src.core.agents import AgentFactory, get_agent_runtime
from uuid import uuid4
import json
from datetime import datetime

class SimpleMessage:
    """Simple message class that matches what agents expect"""
    def __init__(self, sender_id, receiver_id, performative, content):
        self.sender = sender_id
        self.sender_id = sender_id
        self.receiver = receiver_id
        self.receiver_id = receiver_id
        self.performative = performative
        self.content = content
        self.timestamp = datetime.utcnow().isoformat()

async def test_agent_message_handling():
    """Test how agents handle messages"""
    print("="*60)
    print("TEST: Agent Message Handling")
    print("="*60)
    
    # 1. Create LLM service
    llm = LLMService()
    print(f"\n1. LLM Service created (Mock: {llm.enable_mock})")
    
    # 2. Create agent factory and runtime
    factory = AgentFactory()
    runtime = get_agent_runtime()
    
    # 3. Create a cognitive agent
    agent_id = uuid4()
    agent = factory.create_agent(
        agent_type="reactive",  # This creates a CognitiveAgent
        agent_id=agent_id,
        name="MessageTestAgent",
        role="assistant",
        capabilities=["communication", "analysis"],
        llm_service=llm,
        initial_beliefs={"ready": True},
        initial_desires=["respond_to_messages", "help_users"]
    )
    
    print(f"\n2. Agent created: {agent.name} (Type: {type(agent).__name__})")
    
    # 4. Register and start agent
    await runtime.register_agent(agent)
    await runtime.start_agent(agent)
    print("   ✅ Agent registered and started")
    
    # Wait for agent to initialize
    await asyncio.sleep(2)
    
    # 5. Send a test message
    print("\n3. Sending test message...")
    
    message = SimpleMessage(
        sender_id=str(uuid4()),
        receiver_id=str(agent_id),
        performative="request",
        content={
            "action": "analyze",
            "question": "What is 2+2? Please respond with the answer."
        }
    )
    
    # Send message directly to agent
    await agent.receive_message(message)
    print("   ✅ Message sent to agent's queue")
    
    # 6. Wait and check for processing
    print("\n4. Waiting for agent to process message...")
    
    # Give the agent more time to process
    for i in range(15):
        await asyncio.sleep(1)
        
        # Check if agent is still running
        is_running = await runtime.is_agent_running(agent_id)
        
        metrics = await agent.get_metrics()
        messages_processed = metrics.get('messages_processed', 0)
        errors = metrics.get('errors', 0)
        
        print(f"   Check {i+1}: Running={is_running}, Messages={messages_processed}, Errors={errors}, Queue={agent._message_queue.qsize()}")
        
        if messages_processed > 0:
            print("   ✅ Message was processed!")
            break
        
        if errors > 0:
            print("   ❌ Errors detected in agent!")
            break
    
    # 7. Check agent's beliefs and context
    print("\n5. Agent state after processing:")
    print(f"   Beliefs: {json.dumps(agent.bdi.beliefs, indent=2)}")
    print(f"   Desires: {agent.bdi.desires}")
    print(f"   Intentions: {agent.bdi.intentions}")
    print(f"   Conversation history: {len(agent.context.conversation_history)} entries")
    
    if agent.context.conversation_history:
        print("\n   Last conversation entry:")
        last_entry = agent.context.conversation_history[-1]
        print(f"   Type: {last_entry.get('type')}")
        print(f"   Timestamp: {last_entry.get('timestamp')}")
    
    # 8. Stop agent
    print("\n6. Stopping agent...")
    await runtime.stop_agent(agent_id)
    print("   ✅ Agent stopped")
    print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_agent_message_handling())