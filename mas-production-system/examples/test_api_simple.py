#!/usr/bin/env python3
"""
Test simple de l'API pour vérifier les endpoints
"""

import asyncio
import httpx
import os
from uuid import uuid4

# Configuration
if os.path.exists('/.dockerenv'):
    BASE_URL = "http://core:8000"
else:
    BASE_URL = "http://localhost:8088"


async def test_api():
    """Test simple de l'API"""
    async with httpx.AsyncClient() as client:
        print("🔍 Test Simple de l'API MAS")
        print("=" * 50)
        print(f"URL de base: {BASE_URL}")
        
        # 1. Test de l'endpoint de registre
        print("\n1️⃣ Test d'enregistrement d'utilisateur")
        username = f"test_{uuid4().hex[:8]}"
        
        register_data = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "password123"
        }
        
        print(f"   Envoi à: POST {BASE_URL}/auth/register")
        print(f"   Données: {register_data}")
        
        try:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json=register_data
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                print("   ✅ Utilisateur créé avec succès!")
                user = response.json()
                print(f"   ID: {user['id']}")
                
                # 2. Test de connexion
                print("\n2️⃣ Test de connexion")
                print(f"   Envoi à: POST {BASE_URL}/auth/token")
                
                login_response = await client.post(
                    f"{BASE_URL}/auth/token",
                    data={
                        "username": username,
                        "password": "password123",
                        "grant_type": "password"
                    }
                )
                
                print(f"   Status: {login_response.status_code}")
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    token = token_data["access_token"]
                    print("   ✅ Connexion réussie!")
                    print(f"   Token: {token[:20]}...")
                    
                    # 3. Test de création d'agent
                    print("\n3️⃣ Test de création d'agent")
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    agent_data = {
                        "name": "TestAgent",
                        "role": "Tester",
                        "agent_type": "reactive",
                        "capabilities": ["testing"]
                    }
                    
                    print(f"   Envoi à: POST {BASE_URL}/api/v1/agents")
                    
                    agent_response = await client.post(
                        f"{BASE_URL}/api/v1/agents",
                        json=agent_data,
                        headers=headers
                    )
                    
                    print(f"   Status: {agent_response.status_code}")
                    
                    if agent_response.status_code == 201:
                        agent = agent_response.json()
                        print("   ✅ Agent créé avec succès!")
                        print(f"   ID: {agent['id']}")
                        print(f"   Type: {agent['agent_type']}")
                    else:
                        print(f"   ❌ Erreur: {agent_response.text}")
                else:
                    print(f"   ❌ Erreur de connexion: {login_response.text}")
            else:
                print(f"   ❌ Erreur d'enregistrement: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Test terminé")


if __name__ == "__main__":
    asyncio.run(test_api())