#!/usr/bin/env python3
"""
Final verification that agent creation is fixed
"""

import requests
import time
from uuid import uuid4

# Configuration
BASE_URL = "http://localhost:8088"

def test_agent_creation():
    unique_id = str(uuid4())[:8]
    username = f"verify_{unique_id}"
    email = f"verify_{unique_id}@test.com"
    password = "test123456"
    
    print("=" * 80)
    print("🧪 AGENT CREATION FIX VERIFICATION")
    print("=" * 80)
    
    # 1. Register user
    print(f"\n1. Registering user {username}...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": f"Test User {username}"
        }
    )
    
    if response.status_code == 201:
        print(f"✅ User created successfully")
    else:
        print(f"❌ Failed to create user: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # 2. Login
    print("\n2. Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
    else:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    # 3. Test creating each agent type
    headers = {"Authorization": f"Bearer {token}"}
    agent_tests = [
        ("reactive", "ReactiveTestAgent"),
        ("reflexive", "ReflexiveTestAgent"),
        ("hybrid", "HybridTestAgent")
    ]
    
    success_count = 0
    
    print("\n3. Creating agents...")
    print("-" * 40)
    
    for agent_type, agent_name in agent_tests:
        print(f"\n   Testing {agent_type} agent...")
        
        agent_data = {
            "name": f"{agent_name}_{unique_id}",
            "role": f"Test {agent_type} agent",
            "agent_type": agent_type,
            "capabilities": ["test"],
            "initial_beliefs": {"test": True},
            "initial_desires": ["complete_test"],
            "reactive_rules": {} if agent_type in ["reflexive", "hybrid"] else None
        }
        
        # Remove None values
        agent_data = {k: v for k, v in agent_data.items() if v is not None}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/agents",
            json=agent_data,
            headers=headers
        )
        
        if response.status_code == 201:
            agent = response.json()
            print(f"   ✅ {agent_type.capitalize()} agent created successfully!")
            print(f"      ID: {agent['id']}")
            print(f"      Name: {agent['name']}")
            success_count += 1
        else:
            print(f"   ❌ Failed to create {agent_type} agent: {response.status_code}")
            print(f"      Error: {response.text}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    
    if success_count == len(agent_tests):
        print(f"🎉 SUCCESS! All {success_count} agent types created successfully!")
        print("✅ The agent creation issue has been FIXED!")
        print("\nFix summary:")
        print("1. Corrected import paths in agent_factory.py")
        print("2. Added missing abstract method implementations")
        print("3. All agent types (reactive, reflexive, hybrid) now work!")
    else:
        print(f"⚠️  PARTIAL SUCCESS: {success_count}/{len(agent_tests)} agents created")
    
    return success_count == len(agent_tests)

if __name__ == "__main__":
    test_agent_creation()