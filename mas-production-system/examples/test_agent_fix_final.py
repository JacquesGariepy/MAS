#!/usr/bin/env python3
"""
Final test to verify agent creation is working
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Configuration  
API_BASE_URL = "http://core:8000/api/v1"

class TestAgentCreation:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.unique_id = str(uuid4())[:8]
        
    async def create_user_and_login(self, username: str) -> Optional[str]:
        """Create a user and get token"""
        try:
            # Create unique username
            unique_username = f"{username}_{self.unique_id}"
            
            # Register
            response = await self.client.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    "username": unique_username,
                    "email": f"{unique_username}@test.com",
                    "password": "test123456",
                    "full_name": f"Test User {username}"
                }
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to register {unique_username}: {response.status_code}")
                return None
            
            # Login
            response = await self.client.post(
                f"{API_BASE_URL}/auth/token",
                data={
                    "username": unique_username,
                    "password": "test123456"
                }
            )
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                print(f"✅ User {unique_username} created and logged in")
                return token
            else:
                print(f"❌ Failed to login {unique_username}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    async def test_agent_creation(self, token: str, agent_type: str) -> bool:
        """Test creating an agent of specific type"""
        try:
            agent_data = {
                "name": f"Test_{agent_type}_{self.unique_id}",
                "role": f"Test {agent_type} agent",
                "agent_type": agent_type,
                "capabilities": ["test", "demo"],
                "initial_beliefs": {"test": True},
                "initial_desires": ["complete_test"],
                "reactive_rules": {
                    "test_rule": {
                        "condition": {"type": "test"},
                        "action": {"type": "respond", "content": "Test response"}
                    }
                }
            }
            
            response = await self.client.post(
                f"{API_BASE_URL}/agents",
                json=agent_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                agent = response.json()
                print(f"✅ Successfully created {agent_type} agent: {agent['name']} (ID: {agent['id']})")
                return True
            else:
                print(f"❌ Failed to create {agent_type} agent: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating {agent_type} agent: {e}")
            return False
    
    async def run_test(self):
        """Run the complete test"""
        print("=" * 80)
        print("🧪 AGENT CREATION FIX VERIFICATION TEST")
        print("=" * 80)
        
        # Create test user
        print("\n📝 Creating test user...")
        token = await self.create_user_and_login("testuser")
        
        if not token:
            print("❌ Failed to create user and login")
            return
        
        # Test all agent types
        agent_types = ["reactive", "reflexive", "hybrid"]
        success_count = 0
        
        print("\n🤖 Testing agent creation for all types:")
        print("-" * 40)
        
        for agent_type in agent_types:
            if await self.test_agent_creation(token, agent_type):
                success_count += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Agents created: {success_count}/{len(agent_types)}")
        
        if success_count == len(agent_types):
            print("\n🎉 SUCCESS! All agent types can be created!")
            print("✅ The import path fix has resolved the issue!")
        else:
            print(f"\n⚠️  WARNING: Only {success_count}/{len(agent_types)} agent types were created")
            
        await self.client.aclose()

async def main():
    test = TestAgentCreation()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())