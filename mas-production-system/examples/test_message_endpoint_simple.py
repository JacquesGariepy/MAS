#!/usr/bin/env python3
"""
Test simple et direct du endpoint de messages
"""

import asyncio
import httpx
from uuid import uuid4

# Configuration adaptative Docker/Local
import os
if os.path.exists('/.dockerenv'):
    # Dans Docker, utiliser le nom du service
    API_BASE_URL = "http://core:8000/api/v1"
else:
    # En local, utiliser localhost avec le port du docker-compose.dev.yml
    API_BASE_URL = "http://localhost:8088/api/v1"


async def test_message_endpoint():
    """Test direct du endpoint de messages"""
    async with httpx.AsyncClient() as client:
        print("🔍 Test du endpoint de messages\n")
        
        # 1. Créer un utilisateur
        print("1️⃣ Création d'un utilisateur de test...")
        username = f"msg_test_{uuid4().hex[:8]}"
        # Auth est à la racine, pas sous /api/v1
        auth_url = API_BASE_URL.replace('/api/v1', '')
        register_resp = await client.post(
            f"{auth_url}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "testpass123"
            }
        )
        
        if register_resp.status_code != 201:
            print(f"❌ Erreur création utilisateur: {register_resp.text}")
            return
            
        print(f"✅ Utilisateur '{username}' créé")
        
        # 2. Se connecter
        print("\n2️⃣ Connexion...")
        login_resp = await client.post(
            f"{auth_url}/auth/token",
            data={
                "username": username,
                "password": "testpass123",
                "grant_type": "password"
            }
        )
        
        if login_resp.status_code != 200:
            print(f"❌ Erreur connexion: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Connecté avec succès")
        
        # 3. Créer deux agents cognitifs
        print("\n3️⃣ Création de deux agents cognitifs...")
        
        agent1_resp = await client.post(
            f"{API_BASE_URL}/agents",
            json={
                "name": "Agent_Sender",
                "role": "Sender",
                "agent_type": "reactive",  # cognitive
                "capabilities": ["messaging", "analysis"]
            },
            headers=headers
        )
        
        if agent1_resp.status_code != 201:
            print(f"❌ Erreur création agent 1: {agent1_resp.text}")
            return
            
        agent1 = agent1_resp.json()
        print(f"✅ Agent 1 créé: {agent1['name']} (ID: {agent1['id']})")
        
        agent2_resp = await client.post(
            f"{API_BASE_URL}/agents",
            json={
                "name": "Agent_Receiver",
                "role": "Receiver",
                "agent_type": "reactive",  # cognitive
                "capabilities": ["messaging", "processing"]
            },
            headers=headers
        )
        
        if agent2_resp.status_code != 201:
            print(f"❌ Erreur création agent 2: {agent2_resp.text}")
            return
            
        agent2 = agent2_resp.json()
        print(f"✅ Agent 2 créé: {agent2['name']} (ID: {agent2['id']})")
        
        # 4. Tester l'envoi d'un message
        print("\n4️⃣ Test d'envoi de message...")
        
        conversation_id = str(uuid4())
        message_resp = await client.post(
            f"{API_BASE_URL}/agents/{agent1['id']}/messages",
            json={
                "receiver_id": agent2['id'],
                "performative": "request",
                "content": {
                    "action": "test_communication",
                    "message": "Hello from Agent 1!",
                    "timestamp": "2024-01-15T10:00:00"
                },
                "conversation_id": conversation_id
            },
            headers=headers
        )
        
        print(f"   URL: POST /api/v1/agents/{agent1['id']}/messages")
        print(f"   Status: {message_resp.status_code}")
        
        if message_resp.status_code == 201:
            message = message_resp.json()
            print(f"✅ Message envoyé avec succès!")
            print(f"   - ID: {message['id']}")
            print(f"   - De: {message['sender_id']}")
            print(f"   - À: {message['receiver_id']}")
            print(f"   - Performative: {message['performative']}")
            print(f"   - Conversation: {message['conversation_id']}")
        else:
            print(f"❌ Erreur envoi message: {message_resp.text}")
            return
        
        # 5. Vérifier la réception
        print("\n5️⃣ Vérification de la réception...")
        
        received_resp = await client.get(
            f"{API_BASE_URL}/agents/{agent2['id']}/messages",
            params={"message_type": "received"},
            headers=headers
        )
        
        if received_resp.status_code == 200:
            messages = received_resp.json()
            print(f"✅ Messages reçus par l'agent 2: {messages['total']}")
            
            if messages['total'] > 0:
                for msg in messages['items']:
                    print(f"   - Message de {msg['sender_id'][:8]}...")
                    print(f"     Performative: {msg['performative']}")
                    print(f"     Content: {msg['content']}")
                    print(f"     Lu: {'Oui' if msg['is_read'] else 'Non'}")
        else:
            print(f"❌ Erreur récupération messages: {received_resp.text}")
        
        # 6. Test avec d'autres types d'agents
        print("\n6️⃣ Test avec agents réflexifs...")
        
        reflex_resp = await client.post(
            f"{API_BASE_URL}/agents",
            json={
                "name": "ReflexAgent",
                "role": "Quick Responder",
                "agent_type": "reflexive",
                "capabilities": ["fast_response"],
                "reactive_rules": {
                    "greet": {
                        "condition": {"type": "greeting"},
                        "action": {"type": "respond", "content": "Hello!"}
                    }
                }
            },
            headers=headers
        )
        
        print(f"   Création agent réflexif: Status {reflex_resp.status_code}")
        
        if reflex_resp.status_code == 201:
            reflex_agent = reflex_resp.json()
            print(f"✅ Agent réflexif créé: {reflex_agent['name']}")
            
            # Envoyer un message à l'agent réflexif
            msg_to_reflex = await client.post(
                f"{API_BASE_URL}/agents/{agent1['id']}/messages",
                json={
                    "receiver_id": reflex_agent['id'],
                    "performative": "inform",
                    "content": {"type": "greeting", "message": "Hi reflexive agent!"}
                },
                headers=headers
            )
            
            if msg_to_reflex.status_code == 201:
                print(f"✅ Message envoyé à l'agent réflexif")
            else:
                print(f"❌ Erreur: {msg_to_reflex.text}")
        else:
            print(f"❌ Erreur création agent réflexif: {reflex_resp.text}")
        
        print("\n✨ Test terminé!")


if __name__ == "__main__":
    asyncio.run(test_message_endpoint())