#!/usr/bin/env python3
"""
Test direct de l'utilisation de LMStudio par un agent cognitif
"""

import asyncio
import aiohttp
import json
import time
import os

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"


async def main():
    print("="*80)
    print("🧪 TEST DIRECT LMSTUDIO - AGENT COGNITIF")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        timestamp = int(time.time() * 1000) % 1000000
        
        # 1. Créer un utilisateur
        print("\n📋 Création utilisateur...")
        user_data = {
            "username": f"test_llm_{timestamp}",
            "email": f"test_llm_{timestamp}@example.com",
            "password": "password123"
        }
        
        async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
            if resp.status in [200, 201]:
                print("✅ Utilisateur créé")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                return
                
        # 2. Login
        print("\n📋 Connexion...")
        login_form = aiohttp.FormData()
        login_form.add_field('username', user_data["username"])
        login_form.add_field('password', user_data["password"])
        
        async with session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
            if resp.status == 200:
                auth_resp = await resp.json()
                token = auth_resp["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                print("✅ Token obtenu")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                return
                
        # 3. Créer un agent cognitif
        print("\n📋 Création agent cognitif...")
        agent_data = {
            "name": f"CognitiveTestLLM_{timestamp}",
            "agent_type": "reactive",  # Type cognitif
            "role": "assistant",
            "capabilities": ["reasoning", "analysis", "conversation"],
            "description": "Agent cognitif pour tester LMStudio"
        }
        
        async with session.post(f"{API_V1}/agents", json=agent_data, headers=headers) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                agent_id = agent_resp["id"]
                print(f"✅ Agent créé: {agent_id}")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                return
                
        # 4. Démarrer l'agent
        print("\n📋 Démarrage agent...")
        async with session.post(f"{API_V1}/agents/{agent_id}/start", headers=headers) as resp:
            if resp.status == 200:
                print("✅ Agent démarré")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                
        # 5. Envoyer un message qui nécessite le LLM
        print("\n📋 Test de communication avec LLM...")
        print("⚠️  SURVEILLEZ LMSTUDIO MAINTENANT!")
        
        # Créer un deuxième agent pour recevoir la réponse
        agent2_data = {
            "name": f"ReceiverAgent_{timestamp}",
            "agent_type": "reflexive",
            "role": "receiver",
            "capabilities": ["receive"],
            "description": "Agent pour recevoir les messages"
        }
        
        async with session.post(f"{API_V1}/agents", json=agent2_data, headers=headers) as resp:
            if resp.status in [200, 201]:
                agent2_resp = await resp.json()
                agent2_id = agent2_resp["id"]
                print(f"✅ Agent récepteur créé: {agent2_id}")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                return
                
        # Message qui force l'utilisation du LLM
        message_data = {
            "sender_id": agent_id,
            "receiver_id": agent2_id,
            "performative": "request",
            "content": {
                "action": "analyze",
                "query": "Explique-moi en détail ce qu'est l'intelligence artificielle et donne 3 exemples concrets d'applications.",
                "require_reasoning": True
            }
        }
        
        print(f"\n📨 Envoi message nécessitant raisonnement LLM...")
        print(f"   Question: {message_data['content']['query']}")
        
        async with session.post(
            f"{API_V1}/agents/{agent_id}/messages",
            json=message_data,
            headers=headers
        ) as resp:
            if resp.status in [200, 201]:
                msg_resp = await resp.json()
                print(f"✅ Message envoyé: {msg_resp['id']}")
            else:
                print(f"❌ Erreur: {await resp.text()}")
                
        # 6. Attendre et vérifier la réponse
        print("\n⏳ Attente du traitement (10 secondes)...")
        await asyncio.sleep(10)
        
        # Vérifier les messages de l'agent cognitif
        print("\n📋 Vérification de l'activité de l'agent...")
        async with session.get(f"{API_V1}/agents/{agent_id}/messages", headers=headers) as resp:
            if resp.status == 200:
                messages = await resp.json()
                print(f"📊 Messages de l'agent cognitif: {len(messages)}")
                
                for msg in messages:
                    if msg.get('performative') == 'inform' and 'response' in msg.get('content', {}):
                        print("\n🎯 RÉPONSE LLM TROUVÉE!")
                        print(f"   Contenu: {msg['content']['response'][:200]}...")
                        
        # Vérifier aussi l'état du modèle
        print("\n🧠 Configuration LLM utilisée:")
        print(f"   Provider: {os.getenv('LLM_PROVIDER', 'unknown')}")
        print(f"   Model: {os.getenv('LLM_MODEL', 'unknown')}")
        print(f"   Base URL: {os.getenv('LLM_BASE_URL', 'unknown')}")
        
    print("\n" + "="*80)
    print("✅ TEST TERMINÉ - Vérifiez LMStudio pour les requêtes!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())