#!/usr/bin/env python3
"""Test minimal de création d'agent"""
import requests
import json

API_URL = "http://localhost:8088"

# Login first
print("Login...")
response = requests.post(f"{API_URL}/auth/token", data={
    "username": "test123",
    "password": "password123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test minimal agent creation
print("\nCreating minimal agent...")
agent_data = {
    "name": "Test Agent",
    "role": "Test Role",
    "agent_type": "COGNITIVE",
    "organization_id": None
}

response = requests.post(
    f"{API_URL}/api/v1/agents",  # Essayons sans le double /agents
    json=agent_data,
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Si ça ne marche pas, essayons l'autre URL
if response.status_code == 404:
    print("\nTrying alternative URL...")
    response = requests.post(
        f"{API_URL}/api/v1/agents/agents",
        json=agent_data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Debug: print response headers
    if response.status_code == 500:
        print("\nDebug - Response headers:")
        print(json.dumps(dict(response.headers), indent=2))