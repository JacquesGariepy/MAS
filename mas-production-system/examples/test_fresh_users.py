#!/usr/bin/env python3
"""
Test avec de nouveaux utilisateurs
"""

import asyncio
import httpx
import os
from uuid import uuid4
from datetime import datetime

if os.path.exists('/.dockerenv'):
    API_BASE_URL = "http://core:8000/api/v1"
else:
    API_BASE_URL = "http://localhost:8088/api/v1"


async def test_with_fresh_users():
    """Test avec de nouveaux utilisateurs"""
    async with httpx.AsyncClient() as client:
        print("🚀 TEST AVEC NOUVEAUX UTILISATEURS")
        print("=" * 50)
        
        # Créer des utilisateurs avec des noms uniques
        timestamp = datetime.now().strftime("%H%M%S")
        users = [
            {"username": f"user1_{timestamp}", "email": f"user1_{timestamp}@test.com", "password": "password123"},
            {"username": f"user2_{timestamp}", "email": f"user2_{timestamp}@test.com", "password": "password123"}
        ]
        
        tokens = []
        
        # 1. Créer les utilisateurs
        print("\n📝 Création des utilisateurs...")
        for user_data in users:
            auth_url = API_BASE_URL.replace('/api/v1', '')
            response = await client.post(
                f"{auth_url}/auth/register",
                json=user_data
            )
            
            if response.status_code == 201:
                print(f"✅ {user_data['username']} créé")
                
                # Se connecter
                login_response = await client.post(
                    f"{auth_url}/auth/token",
                    data={
                        "username": user_data["username"],
                        "password": user_data["password"],
                        "grant_type": "password"
                    }
                )
                
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    tokens.append((user_data["username"], token))
                    print(f"✅ {user_data['username']} connecté")
            else:
                print(f"❌ Erreur création {user_data['username']}: {response.text}")
        
        # 2. Créer des agents de chaque type
        print("\n🤖 Création des agents...")
        agent_configs = [
            {
                "name": "CognitiveAgent",
                "role": "Analyste",
                "agent_type": "reactive",
                "capabilities": ["analysis", "reasoning"]
            },
            {
                "name": "ReflexiveAgent",
                "role": "Moniteur",
                "agent_type": "reflexive",
                "capabilities": ["monitoring"],
                "reactive_rules": {
                    "alert": {
                        "condition": {"level": "high"},
                        "action": {"type": "notify"}
                    }
                }
            },
            {
                "name": "HybridAgent",
                "role": "Coordinateur",
                "agent_type": "hybrid",
                "capabilities": ["coordination"],
                "reactive_rules": {
                    "simple": {
                        "condition": {"type": "simple"},
                        "action": {"type": "handle"}
                    }
                },
                "configuration": {
                    "complexity_threshold": 0.5
                }
            }
        ]
        
        created_agents = []
        
        for i, (username, token) in enumerate(tokens):
            if i < len(agent_configs):
                agent_data = agent_configs[i]
                headers = {"Authorization": f"Bearer {token}"}
                
                response = await client.post(
                    f"{API_BASE_URL}/agents",
                    json=agent_data,
                    headers=headers
                )
                
                if response.status_code == 201:
                    agent = response.json()
                    created_agents.append(agent)
                    print(f"✅ {agent_data['name']} créé (Type: {agent_data['agent_type']})")
                else:
                    print(f"❌ Erreur création {agent_data['name']}: {response.status_code}")
                    print(f"   Détails: {response.text}")
        
        # 3. Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ")
        print(f"✅ Utilisateurs créés: {len(tokens)}")
        print(f"✅ Agents créés: {len(created_agents)}")
        
        agent_types = {"reactive": 0, "reflexive": 0, "hybrid": 0}
        for agent in created_agents:
            agent_types[agent["agent_type"]] += 1
        
        print(f"   - Cognitifs: {agent_types['reactive']}")
        print(f"   - Réflexifs: {agent_types['reflexive']}")
        print(f"   - Hybrides: {agent_types['hybrid']}")
        
        if len(created_agents) == 3:
            print("\n🎉 SUCCÈS: Tous les types d'agents fonctionnent !")
        else:
            print("\n⚠️ Certains agents n'ont pas pu être créés")


if __name__ == "__main__":
    asyncio.run(test_with_fresh_users())