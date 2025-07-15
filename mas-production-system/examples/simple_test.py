#!/usr/bin/env python3
"""
Test rapide de création d'agent et tâche
"""

import requests
import json

API_URL = "http://localhost:8088"

# 1. Login
print("1. Login...")
response = requests.post(
    f"{API_URL}/auth/token",
    data={"username": "test_user", "password": "password123"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Token: {token[:20]}...")

# 2. Créer agent
print("\n2. Créer agent...")
agent_data = {
    "name": "Assistant Test",
    "role": "Assistant général",
    "agent_type": "cognitive",
    "capabilities": ["conversation"]
}

response = requests.post(
    f"{API_URL}/api/v1/agents",
    json=agent_data,
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    agent = response.json()
    print(f"✅ Agent créé: {agent['name']} (ID: {agent['id']})")
else:
    print(f"❌ Erreur: {response.text}")
    exit(1)

# 3. Démarrer agent
agent_id = agent["id"]
print(f"\n3. Démarrer agent {agent_id}...")
response = requests.post(
    f"{API_URL}/api/v1/agents/{agent_id}/start",
    headers=headers
)
print(f"Status: {response.status_code}")

# 4. Créer tâche
print("\n4. Créer tâche...")
task_data = {
    "title": "Question test",
    "description": "Qu'est-ce que Python?",
    "task_type": "query",
    "priority": "high",
    "assigned_to": agent_id
}

response = requests.post(
    f"{API_URL}/api/v1/v1/tasks",
    json=task_data,
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    task = response.json()
    print(f"✅ Tâche créée: {task['id']}")
else:
    print(f"❌ Erreur: {response.text}")

print("\n✅ Test terminé!")