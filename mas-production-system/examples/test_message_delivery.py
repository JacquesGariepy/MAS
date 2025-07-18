#!/usr/bin/env python3
"""
Test direct message delivery to verify the flow
"""

import asyncio
import aiohttp
import json
import time
from uuid import uuid4

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"

async def test_message_flow():
    """Test message flow step by step"""
    
    session = aiohttp.ClientSession()
    
    try:
        # 1. Create user and login
        print("1. Creating user...")
        timestamp = int(time.time())
        user_data = {
            "username": f"test_{timestamp}",
            "email": f"test_{timestamp}@test.com",
            "password": "test123456"  # Password must be at least 8 chars
        }
        
        async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
            if resp.status not in [200, 201]:
                print(f"   ❌ Failed to register: {resp.status}")
                return
        
        # Login
        login_form = aiohttp.FormData()
        login_form.add_field('username', user_data["username"])
        login_form.add_field('password', user_data["password"])
        
        async with session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
            if resp.status != 200:
                print(f"   ❌ Failed to login: {resp.status}")
                return
            auth_resp = await resp.json()
            token = auth_resp["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ User created and logged in")
        
        # 2. Create two agents
        print("\n2. Creating agents...")
        
        # Agent 1 - Sender
        agent1_data = {
            "name": f"Sender_{int(time.time())}",
            "agent_type": "reactive",
            "role": "sender",
            "capabilities": ["send"],
            "description": "Sender agent"
        }
        
        async with session.post(f"{API_V1}/agents", json=agent1_data, headers=headers) as resp:
            if resp.status not in [200, 201]:
                print(f"   ❌ Failed to create agent 1: {resp.status}")
                return
            agent1_resp = await resp.json()
            agent1_id = agent1_resp["id"]
            print(f"   ✅ Sender agent created: {agent1_id}")
        
        # Agent 2 - Receiver  
        agent2_data = {
            "name": f"Receiver_{int(time.time())}",
            "agent_type": "reactive",
            "role": "receiver",
            "capabilities": ["receive"],
            "description": "Receiver agent"
        }
        
        async with session.post(f"{API_V1}/agents", json=agent2_data, headers=headers) as resp:
            if resp.status not in [200, 201]:
                print(f"   ❌ Failed to create agent 2: {resp.status}")
                return
            agent2_resp = await resp.json()
            agent2_id = agent2_resp["id"]
            print(f"   ✅ Receiver agent created: {agent2_id}")
        
        # 3. Start both agents
        print("\n3. Starting agents...")
        async with session.post(f"{API_V1}/agents/{agent1_id}/start", headers=headers) as resp:
            if resp.status != 200:
                print(f"   ❌ Failed to start agent 1: {resp.status}")
                return
            print("   ✅ Sender agent started")
            
        async with session.post(f"{API_V1}/agents/{agent2_id}/start", headers=headers) as resp:
            if resp.status != 200:
                print(f"   ❌ Failed to start agent 2: {resp.status}")
                return
            print("   ✅ Receiver agent started")
        
        # Wait for startup
        await asyncio.sleep(2)
        
        # 4. Send message from agent1 to agent2
        print("\n4. Sending message from Sender to Receiver...")
        message_data = {
            "sender_id": agent1_id,
            "receiver_id": agent2_id,
            "performative": "request",
            "content": {
                "text": "Hello receiver, please respond"
            }
        }
        
        async with session.post(
            f"{API_V1}/agents/{agent1_id}/messages",
            json=message_data,
            headers=headers
        ) as resp:
            if resp.status not in [200, 201]:
                print(f"   ❌ Failed to send message: {resp.status}")
                error = await resp.text()
                print(f"   Error: {error}")
                return
            msg_resp = await resp.json()
            print(f"   ✅ Message sent: {msg_resp['id']}")
        
        # 5. Check messages for both agents
        print("\n5. Waiting for agents to process message...")
        
        for i in range(10):
            await asyncio.sleep(2)
            
            # Check receiver's messages
            print(f"\n   Checking Receiver agent messages...")
            async with session.get(f"{API_V1}/agents/{agent2_id}/messages", headers=headers) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    msg_count = len(messages) if isinstance(messages, list) else len(messages.get('items', []))
                    print(f"   Messages found: {msg_count}")
                    
                    if msg_count > 0:
                        msg_list = messages if isinstance(messages, list) else messages.get('items', [])
                        for msg in msg_list:
                            print(f"   - Message ID: {msg.get('id', 'Unknown')}")
                            print(f"     Sender: {msg.get('sender_id', 'Unknown')}")
                            print(f"     Receiver: {msg.get('receiver_id', 'Unknown')}")
                            print(f"     Type: {msg.get('performative', 'Unknown')}")
                            print(f"     Content: {msg.get('content', {})}")
                        break
        
        # 6. Check agent status
        print("\n6. Checking agent status...")
        async with session.get(f"{API_V1}/agents/{agent2_id}", headers=headers) as resp:
            if resp.status == 200:
                agent_info = await resp.json()
                print(f"   Status: {agent_info.get('status', 'Unknown')}")
                
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_message_flow())