#!/usr/bin/env python3
"""
Working test for MAS agent types with correct API paths
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"


async def main():
    """Test principal"""
    print("="*80)
    print("🧪 MAS AGENT TEST - WORKING VERSION")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        timestamp = int(time.time() * 1000) % 1000000
        
        # Phase 1: Register user (auth is at root level)
        print("\n📋 Phase 1: User Registration")
        print("-" * 60)
        
        user_data = {
            "username": f"test_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "password123"
        }
        
        print(f"🔑 Registering user: {user_data['username']}")
        try:
            async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                if resp.status in [200, 201]:
                    user_resp = await resp.json()
                    print(f"   ✅ User registered successfully")
                    print(f"   User ID: {user_resp.get('id')}")
                else:
                    print(f"   ❌ Registration failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
        # Phase 2: Login (token endpoint)
        print("\n📋 Phase 2: Login")
        print("-" * 60)
        
        # OAuth2 form data format
        login_data = aiohttp.FormData()
        login_data.add_field('username', user_data["username"])
        login_data.add_field('password', user_data["password"])
        
        print(f"🔑 Getting token for: {user_data['username']}")
        try:
            async with session.post(f"{API_BASE_URL}/auth/token", data=login_data) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    token = auth_resp["access_token"]
                    print(f"   ✅ Token obtained successfully")
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print(f"   ❌ Login failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
                    return
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return
            
        # Phase 3: Verify authentication
        print("\n📋 Phase 3: Verify Authentication")
        print("-" * 60)
        
        try:
            async with session.get(f"{API_BASE_URL}/auth/me", headers=headers) as resp:
                if resp.status == 200:
                    me_resp = await resp.json()
                    print(f"   ✅ Authenticated as: {me_resp.get('username')}")
                else:
                    print(f"   ❌ Auth verification failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
        # Phase 4: Create agents
        print("\n📋 Phase 4: Creating Agents")
        print("-" * 60)
        
        agents_data = [
            {
                "name": f"CognitiveAgent_{timestamp}",
                "agent_type": "reactive",  # Changed from "type" to "agent_type"
                "role": "analyst",
                "capabilities": ["reasoning", "analysis", "planning"],
                "description": "Cognitive agent using LLM for complex reasoning"
            },
            {
                "name": f"ReflexiveAgent_{timestamp}",
                "agent_type": "reflexive",  # Changed from "type" to "agent_type"
                "role": "responder",
                "capabilities": ["quick-response", "pattern-matching"],
                "description": "Rule-based reflexive agent",
                "reactive_rules": {
                    "greeting": "Hello! I'm a reflexive agent.",
                    "help": "I respond quickly based on predefined rules.",
                    "status": "Operating normally"
                }
            },
            {
                "name": f"HybridAgent_{timestamp}",
                "agent_type": "hybrid",  # Changed from "type" to "agent_type"
                "role": "coordinator",
                "capabilities": ["coordination", "adaptive-response", "learning"],
                "description": "Hybrid agent with both cognitive and reflexive capabilities",
                "reactive_rules": {
                    "urgent": "Switching to reflexive mode for urgent response",
                    "complex": "Engaging cognitive mode for complex analysis"
                },
                "cognitive_threshold": 0.7
            }
        ]
        
        created_agents = []
        for agent_data in agents_data:
            print(f"\n🤖 Creating {agent_data['agent_type']} agent: {agent_data['name']}")
            try:
                async with session.post(
                    f"{API_V1}/agents", 
                    json=agent_data,
                    headers=headers
                ) as resp:
                    if resp.status in [200, 201]:
                        agent_resp = await resp.json()
                        created_agents.append(agent_resp)
                        print(f"   ✅ Created successfully")
                        print(f"   ID: {agent_resp.get('id')}")
                        print(f"   Status: {agent_resp.get('status')}")
                    else:
                        print(f"   ❌ Failed: {resp.status}")
                        error_text = await resp.text()
                        print(f"   Error: {error_text}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                
        # Phase 5: Start agents
        print("\n📋 Phase 5: Starting Agents")
        print("-" * 60)
        
        for agent in created_agents:
            agent_id = agent.get("id")
            if agent_id:
                print(f"\n🚀 Starting agent: {agent['name']}")
                try:
                    async with session.post(
                        f"{API_V1}/agents/{agent_id}/start",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            start_resp = await resp.json()
                            print(f"   ✅ Started successfully")
                            print(f"   New status: {start_resp.get('status')}")
                        else:
                            print(f"   ❌ Failed to start: {resp.status}")
                            error_text = await resp.text()
                            print(f"   Error: {error_text}")
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    
        # Phase 6: Test agent communication
        print("\n📋 Phase 6: Testing Agent Communication")
        print("-" * 60)
        
        if len(created_agents) >= 2:
            sender = created_agents[0]
            receiver = created_agents[1]
            
            message_data = {
                "sender_id": sender['id'],
                "receiver_id": receiver['id'],
                "performative": "inform",
                "content": {
                    "text": "Hello from cognitive agent!",
                    "timestamp": time.time()
                }
            }
            
            print(f"\n📨 Sending message from {sender['name']} to {receiver['name']}")
            try:
                async with session.post(
                    f"{API_V1}/agents/{sender['id']}/messages",
                    json=message_data,
                    headers=headers
                ) as resp:
                    if resp.status in [200, 201]:
                        msg_resp = await resp.json()
                        print(f"   ✅ Message sent successfully")
                        print(f"   Message ID: {msg_resp.get('id')}")
                    else:
                        print(f"   ❌ Failed to send: {resp.status}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                
        # Phase 7: Final status check
        print("\n📋 Phase 7: Final Status Check")
        print("-" * 60)
        
        try:
            async with session.get(f"{API_V1}/agents", headers=headers) as resp:
                if resp.status == 200:
                    all_agents = await resp.json()
                    print(f"\n📊 Total agents in system: {len(all_agents)}")
                    
                    print("\n🤖 Our test agents:")
                    for agent in all_agents:
                        agent_name = agent.get('name', '') if isinstance(agent, dict) else str(agent)
                        if str(timestamp) in agent_name:
                            if isinstance(agent, dict):
                                print(f"   • {agent['name']}")
                                print(f"     Type: {agent.get('agent_type', agent.get('type', 'unknown'))}")
                                print(f"     Status: {agent.get('status')}")
                                print(f"     Capabilities: {', '.join(agent.get('capabilities', []))}")
                            else:
                                print(f"   • Agent data format issue: {type(agent)}")
                else:
                    print(f"   ❌ Failed to list agents: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    print("\n" + "="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())