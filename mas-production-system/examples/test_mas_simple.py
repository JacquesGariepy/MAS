#!/usr/bin/env python3
"""
Simple test for MAS agent types - direct test without health check
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2


async def main():
    """Test principal"""
    print("="*80)
    print("🧪 TEST SIMPLE DES AGENTS MAS")
    print("="*80)
    
    # Configuration du timeout pour la session
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Phase 1: Créer un utilisateur de test
        print("\n📋 Phase 1: Création d'un utilisateur de test")
        print("-" * 60)
        
        timestamp = int(time.time() * 1000) % 1000000
        username = f"test_user_{timestamp}"
        
        try:
            # Créer/connecter l'utilisateur
            login_data = {
                "username": username,
                "password": "test123"
            }
            
            print(f"\n🔑 Connexion utilisateur: {username}")
            async with session.post(f"{API_BASE_URL}/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    token = auth_resp["access_token"]
                    print(f"   ✅ Token obtenu")
                    
                    # Headers pour les requêtes suivantes
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print(f"   ❌ Échec connexion: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Erreur: {error_text}")
                    return
                    
        except Exception as e:
            print(f"   ❌ Erreur lors de la connexion: {str(e)}")
            return
            
        # Phase 2: Créer un agent cognitive simple
        print("\n📋 Phase 2: Création d'un agent cognitive")
        print("-" * 60)
        
        agent_data = {
            "name": f"TestAgent_{timestamp}",
            "type": "reactive",  # Type cognitive
            "role": "assistant",
            "capabilities": ["conversation", "analysis"],
            "description": "Agent de test",
            "llm_config": {
                "provider": "mock",
                "model": "mock-model",
                "temperature": 0.7
            }
        }
        
        try:
            print(f"\n🤖 Création agent: {agent_data['name']}")
            async with session.post(
                f"{API_BASE_URL}/agents", 
                json=agent_data,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    agent_resp = await resp.json()
                    agent_id = agent_resp.get("id", agent_resp.get("agent_id"))
                    print(f"   ✅ Agent créé avec ID: {agent_id}")
                    print(f"   Type: {agent_data['type']}")
                    print(f"   État: {agent_resp.get('status', 'idle')}")
                else:
                    print(f"   ❌ Échec création: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Détails: {error_text}")
                    
        except Exception as e:
            print(f"   ❌ Erreur lors de la création: {str(e)}")
            
        # Phase 3: Lister les agents
        print("\n📋 Phase 3: Liste des agents")
        print("-" * 60)
        
        try:
            async with session.get(
                f"{API_BASE_URL}/agents",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    agents = await resp.json()
                    print(f"\n📊 Nombre total d'agents: {len(agents)}")
                    for agent in agents[-3:]:  # Afficher les 3 derniers
                        print(f"   - {agent.get('name')} ({agent.get('type')}) - État: {agent.get('status')}")
                else:
                    print(f"   ❌ Échec récupération: {resp.status}")
                    
        except Exception as e:
            print(f"   ❌ Erreur lors de la récupération: {str(e)}")
            
    print("\n" + "="*80)
    print("✅ TEST TERMINÉ")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())