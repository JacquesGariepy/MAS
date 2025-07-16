#!/usr/bin/env python3
"""
Test agent creation with unique users - using the working pattern from test_all_agent_types.py
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Configuration - same as test_all_agent_types.py
import os
if os.path.exists('/.dockerenv'):
    # We're in a Docker container
    API_BASE_URL = "http://core:8000/api/v1"
else:
    # Local execution
    API_BASE_URL = "http://localhost:8088/api/v1"


class MASTestUniqueAgents:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.unique_id = str(uuid4())[:8]
        self.users = {}
        self.tokens = {}
        self.agents = {}
        
    async def register_user(self, username: str, email: str, password: str = "test123456") -> bool:
        """Register a new user"""
        try:
            response = await self.client.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": f"Test User {username}"
                }
            )
            
            if response.status_code == 201:
                self.users[username] = response.json()
                print(f"✅ {username} created")
                return True
            else:
                print(f"❌ Error registering {username}: {response.status_code}")
                print(f"   Details: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception registering {username}: {str(e)}")
            return False
    
    async def login_user(self, username: str, password: str = "test123456") -> Optional[str]:
        """Login and get access token"""
        try:
            response = await self.client.post(
                f"{API_BASE_URL}/auth/token",
                data={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.tokens[username] = token
                print(f"✅ {username} logged in")
                return token
            else:
                print(f"❌ Error logging in {username}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception logging in {username}: {str(e)}")
            return None
    
    async def create_agent(self, username: str, agent_name: str, agent_type: str) -> Optional[Dict]:
        """Create an agent for a user"""
        token = self.tokens.get(username)
        if not token:
            print(f"❌ No token for {username}")
            return None
        
        try:
            # Agent data with all required fields
            agent_data = {
                "name": agent_name,
                "role": f"Test {agent_type} agent",
                "agent_type": agent_type,
                "capabilities": ["communication", "analysis", "learning"],
                "initial_beliefs": {
                    "environment": "test",
                    "purpose": f"testing {agent_type} functionality"
                },
                "initial_desires": ["complete_tests", "demonstrate_capability"],
                "reactive_rules": {
                    "greeting": {
                        "condition": {"performative": "request", "content": {"type": "greeting"}},
                        "action": {"type": "respond", "performative": "inform", "content": "Hello!"}
                    }
                } if agent_type in ["reflexive", "hybrid"] else {}
            }
            
            response = await self.client.post(
                f"{API_BASE_URL}/agents",
                json=agent_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                agent = response.json()
                if username not in self.agents:
                    self.agents[username] = []
                self.agents[username].append(agent)
                print(f"✅ Created {agent_type} agent '{agent_name}' for {username}")
                return agent
            else:
                print(f"❌ Error creating agent {agent_name}: {response.status_code}")
                print(f"   Type: {agent_type}")
                print(f"   Details: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception creating agent: {str(e)}")
            return None
    
    async def run_test(self):
        """Run the complete test"""
        print("=" * 80)
        print("🧪 TESTING AGENT CREATION WITH UNIQUE USERS")
        print("=" * 80)
        
        # Step 1: Create unique users
        print("\n📝 Step 1: Creating unique test users")
        print("-" * 40)
        
        test_users = [
            (f"alice_{self.unique_id}", f"alice_{self.unique_id}@test.com"),
            (f"bob_{self.unique_id}", f"bob_{self.unique_id}@test.com"),
            (f"charlie_{self.unique_id}", f"charlie_{self.unique_id}@test.com")
        ]
        
        created_users = []
        for username, email in test_users:
            if await self.register_user(username, email):
                if await self.login_user(username):
                    created_users.append(username)
        
        if not created_users:
            print("\n❌ No users created successfully. Cannot continue.")
            return
        
        print(f"\n✅ Created and logged in {len(created_users)} users")
        
        # Step 2: Create agents of each type
        print("\n🤖 Step 2: Creating agents (all types)")
        print("-" * 40)
        
        agent_types_per_user = [
            ("reactive", "CognitiveAnalyst"),
            ("reactive", "CognitiveStrategist"),
            ("reflexive", "ReflexiveMonitor"),
            ("reflexive", "ReflexiveResponder"),
            ("hybrid", "HybridCoordinator"),
            ("hybrid", "HybridOptimizer")
        ]
        
        created_count = {"reactive": 0, "reflexive": 0, "hybrid": 0}
        
        # Distribute agents among users
        for i, (agent_type, agent_name) in enumerate(agent_types_per_user):
            user_idx = i % len(created_users)
            username = created_users[user_idx]
            
            if await self.create_agent(username, f"{agent_name}_{self.unique_id}", agent_type):
                created_count[agent_type] += 1
        
        # Summary
        total_created = sum(created_count.values())
        print(f"\n📊 Summary of agents created:")
        print(f"   - Total: {total_created}")
        print(f"   - Cognitive (reactive): {created_count['reactive']}")
        print(f"   - Reflexive: {created_count['reflexive']}")
        print(f"   - Hybrid: {created_count['hybrid']}")
        
        print("\n" + "=" * 80)
        print("📊 FINAL RESULTS")
        print("=" * 80)
        print(f"✅ Users created: {len(created_users)}")
        print(f"✅ Agents created: {total_created}/{len(agent_types_per_user)}")
        
        if total_created == len(agent_types_per_user):
            print("\n🎉 SUCCESS! All agent types were created successfully!")
            print("✅ The import path fix has resolved the agent creation issue!")
        elif total_created > 0:
            print(f"\n⚠️  PARTIAL SUCCESS: {total_created}/{len(agent_types_per_user)} agents created")
            print("Some agent types may still have issues.")
        else:
            print("\n❌ FAILURE: No agents could be created")
            print("The issue persists - further investigation needed.")
        
        await self.client.aclose()


async def main():
    test = MASTestUniqueAgents()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())