#!/usr/bin/env python3
"""
Final fixed test for MAS agent types
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


async def main():
    """Test principal"""
    print("="*80)
    print("🧪 MAS AGENT TEST - FIXED VERSION")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        # Create test user with all required fields
        timestamp = int(time.time() * 1000) % 1000000
        
        # Phase 1: Register user
        print("\n📋 Phase 1: User Registration")
        print("-" * 60)
        
        user_data = {
            "username": f"test_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "password123"  # At least 8 characters
        }
        
        print(f"🔑 Registering user: {user_data['username']}")
        try:
            async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                if resp.status in [200, 201]:
                    user_resp = await resp.json()
                    print(f"   ✅ User registered successfully")
                else:
                    print(f"   ❌ Registration failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
        # Phase 2: Login
        print("\n📋 Phase 2: Login")
        print("-" * 60)
        
        # Use form data for login (OAuth2 standard)
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        print(f"🔑 Logging in as: {login_data['username']}")
        try:
            async with session.post(
                f"{API_BASE_URL}/auth/login", 
                data=login_data,  # Form data, not JSON
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    token = auth_resp["access_token"]
                    print(f"   ✅ Login successful")
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print(f"   ❌ Login failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
                    # Try with JSON format as fallback
                    async with session.post(f"{API_BASE_URL}/auth/login", json=login_data) as resp2:
                        if resp2.status == 200:
                            auth_resp = await resp2.json()
                            token = auth_resp["access_token"]
                            print(f"   ✅ Login successful (JSON format)")
                            headers = {"Authorization": f"Bearer {token}"}
                        else:
                            return
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return
            
        # Phase 3: Create agents
        print("\n📋 Phase 3: Creating Agents")
        print("-" * 60)
        
        agents_data = [
            {
                "name": f"Cognitive_{timestamp}",
                "type": "reactive",  # Cognitive agent
                "role": "analyst",
                "capabilities": ["reasoning", "analysis"],
                "description": "Cognitive agent with LLM reasoning"
            },
            {
                "name": f"Reflexive_{timestamp}",
                "type": "reflexive",
                "role": "responder",
                "capabilities": ["quick-response", "rule-based"],
                "description": "Reflexive agent with rule-based responses",
                "reactive_rules": {
                    "greeting": "Hello! How can I help?",
                    "help": "I can assist with various tasks."
                }
            },
            {
                "name": f"Hybrid_{timestamp}",
                "type": "hybrid",
                "role": "coordinator",
                "capabilities": ["coordination", "adaptive"],
                "description": "Hybrid agent combining cognitive and reflexive",
                "reactive_rules": {
                    "urgent": "Handling urgent request immediately",
                    "status": "All systems operational"
                },
                "cognitive_threshold": 0.7
            }
        ]
        
        created_agents = []
        for agent_data in agents_data:
            print(f"\n🤖 Creating {agent_data['type']} agent: {agent_data['name']}")
            try:
                async with session.post(
                    f"{API_BASE_URL}/agents", 
                    json=agent_data,
                    headers=headers
                ) as resp:
                    if resp.status in [200, 201]:
                        agent_resp = await resp.json()
                        agent_id = agent_resp.get("id", agent_resp.get("agent_id"))
                        created_agents.append(agent_resp)
                        print(f"   ✅ Created with ID: {agent_id}")
                        print(f"   Status: {agent_resp.get('status', 'unknown')}")
                    else:
                        print(f"   ❌ Failed: {resp.status}")
                        error_text = await resp.text()
                        print(f"   Error: {error_text}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                
        # Phase 4: Start agents
        print("\n📋 Phase 4: Starting Agents")
        print("-" * 60)
        
        for agent in created_agents:
            agent_id = agent.get("id", agent.get("agent_id"))
            if agent_id:
                print(f"\n🚀 Starting agent: {agent['name']}")
                try:
                    async with session.post(
                        f"{API_BASE_URL}/agents/{agent_id}/start",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            print(f"   ✅ Agent started successfully")
                        else:
                            print(f"   ❌ Failed to start: {resp.status}")
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    
        # Phase 5: List all agents
        print("\n📋 Phase 5: Final Agent Status")
        print("-" * 60)
        
        try:
            async with session.get(
                f"{API_BASE_URL}/agents",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    all_agents = await resp.json()
                    print(f"\n📊 Total agents: {len(all_agents)}")
                    print("\nCreated agents:")
                    for agent in all_agents:
                        if timestamp in str(agent.get('name', '')):
                            print(f"   - {agent['name']} ({agent['type']}) - Status: {agent.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Failed to list agents: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    print("\n" + "="*80)
    print("✅ TEST COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())