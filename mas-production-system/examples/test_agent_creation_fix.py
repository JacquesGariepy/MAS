#!/usr/bin/env python
"""
Test script to verify agent creation is working after the fix
"""

import os
import sys
import time
import requests
from uuid import uuid4

BASE_URL = "http://core:8000/api/v1"

def create_user_and_get_token(username: str, email: str):
    """Create a user and get access token"""
    register_data = {
        "username": username,
        "email": email,
        "password": "test123456",
        "full_name": f"Test User {username}"
    }
    
    # Try to register
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if response.status_code in [200, 201, 400]:
        # Now login to get token
        login_data = {
            "username": username,
            "password": "test123456"
        }
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
        
        if response.status_code == 200:
            return response.json().get("access_token")
    
    print(f"❌ Failed to get token for {username}: {response.status_code}")
    print(f"   Response: {response.text}")
    return None

def test_agent_creation():
    """Test creating agents of all types"""
    
    print("=" * 80)
    print("🧪 TEST: Agent Creation Fix Verification")
    print("=" * 80)
    
    # Create test user with unique username
    test_id = str(uuid4())[:8]
    username = f"test_user_{test_id}"
    email = f"test_{test_id}@example.com"
    
    print(f"\n📝 Creating test user: {username}")
    token = create_user_and_get_token(username, email)
    
    if not token:
        print("❌ Failed to create user and get token")
        return
    
    print(f"✅ User created and authenticated")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test agent types
    agent_types = [
        ("reactive", "CognitiveAgent"),
        ("reflexive", "ReflexiveAgent"),
        ("hybrid", "HybridAgent")
    ]
    
    created_agents = []
    
    print("\n🤖 Testing agent creation:")
    print("-" * 40)
    
    for agent_type, agent_name in agent_types:
        agent_data = {
            "name": f"{agent_name}_{test_id}",
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
        
        print(f"\n📌 Creating {agent_type} agent: {agent_name}")
        
        response = requests.post(
            f"{BASE_URL}/agents", 
            json=agent_data,
            headers=headers
        )
        
        if response.status_code == 201:
            agent = response.json()
            created_agents.append(agent)
            print(f"   ✅ Successfully created {agent_type} agent")
            print(f"      ID: {agent['id']}")
            print(f"      Name: {agent['name']}")
            print(f"      Status: {agent['status']}")
        else:
            print(f"   ❌ Failed to create {agent_type} agent: {response.status_code}")
            print(f"      Error: {response.text}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Total agents created: {len(created_agents)}/{len(agent_types)}")
    
    for agent_type, _ in agent_types:
        count = sum(1 for a in created_agents if a.get('agent_type') == agent_type)
        status = "✅" if count > 0 else "❌"
        print(f"{status} {agent_type.capitalize()} agents: {count}")
    
    if len(created_agents) == len(agent_types):
        print("\n🎉 SUCCESS: All agent types can be created!")
    else:
        print("\n⚠️  WARNING: Some agent types failed to create")
    
    return len(created_agents) == len(agent_types)

if __name__ == "__main__":
    success = test_agent_creation()
    sys.exit(0 if success else 1)