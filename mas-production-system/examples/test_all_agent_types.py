#!/usr/bin/env python3
"""
Test complet du système MAS v2.0 avec tous les types d'agents activés
Teste la création de tous les types d'agents et l'envoi de messages entre eux
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Configuration
# Si on est dans Docker, utiliser le nom du service
import os
if os.path.exists('/.dockerenv'):
    # Nous sommes dans un conteneur Docker
    API_BASE_URL = "http://core:8000/api/v1"
else:
    # Exécution locale
    API_BASE_URL = "http://localhost:8088/api/v1"  # Port 8088 pour docker-compose.dev.yml


class MASTestAllAgents:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.users = {}
        self.tokens = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def register_user(self, username: str, email: str, password: str) -> Dict:
        """Enregistrer un nouvel utilisateur"""
        # Note: auth est à la racine, pas sous /api/v1
        auth_url = API_BASE_URL.replace('/api/v1', '')
        response = await self.client.post(
            f"{auth_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        
        if response.status_code != 201:
            print(f"❌ Erreur lors de l'enregistrement de {username}: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
            
        return response.json()
    
    async def login_user(self, username: str, password: str) -> str:
        """Se connecter et obtenir un token"""
        # Note: auth est à la racine, pas sous /api/v1
        auth_url = API_BASE_URL.replace('/api/v1', '')
        response = await self.client.post(
            f"{auth_url}/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur lors de la connexion de {username}: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
            
        data = response.json()
        return data["access_token"]
    
    async def create_agent(self, token: str, agent_data: Dict) -> Optional[Dict]:
        """Créer un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents",
            json=agent_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"❌ Erreur lors de la création de l'agent {agent_data['name']}: {response.status_code}")
            print(f"   Type: {agent_data['agent_type']}")
            print(f"   Détails: {response.text}")
            return None
            
        return response.json()
    
    async def send_message(self, token: str, sender_id: str, receiver_id: str, 
                          performative: str, content: Dict) -> Optional[Dict]:
        """Envoyer un message entre agents"""
        headers = {"Authorization": f"Bearer {token}"}
        
        conversation_id = str(uuid4())
        message_data = {
            "receiver_id": receiver_id,
            "performative": performative,
            "content": content,
            "conversation_id": conversation_id
        }
        
        print(f"\n📤 Envoi d'un message:")
        print(f"   De: {sender_id}")
        print(f"   À: {receiver_id}")
        print(f"   Type: {performative}")
        print(f"   Contenu: {json.dumps(content, indent=2)}")
        print(f"   Conversation ID: {conversation_id}")
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents/{sender_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"❌ Erreur lors de l'envoi du message: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
        
        result = response.json()
        print(f"✅ Message envoyé avec succès! ID: {result.get('id', 'N/A')}")
        return result
    
    async def get_messages(self, token: str, agent_id: str, message_type: str = "received") -> List[Dict]:
        """Récupérer les messages d'un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.client.get(
            f"{API_BASE_URL}/agents/{agent_id}/messages",
            params={"message_type": message_type},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur lors de la récupération des messages: {response.status_code}")
            return []
            
        data = response.json()
        return data.get("items", [])
    
    async def create_memory(self, token: str, agent_id: str, content: str, 
                           memory_type: str = "semantic") -> Optional[Dict]:
        """Créer une mémoire pour un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "importance": 0.8,
            "metadata": {
                "source": "test_script",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents/{agent_id}/memories",
            json=memory_data,
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Erreur lors de la création de la mémoire: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
            
        return response.json()
    
    async def run_complete_test(self):
        """Exécuter le test complet avec tous les types d'agents"""
        print("\n" + "="*80)
        print("🚀 TEST COMPLET DU SYSTÈME MAS v2.0 - TOUS LES TYPES D'AGENTS")
        print("="*80)
        
        # 1. Créer les utilisateurs
        print("\n📝 Étape 1: Création des utilisateurs")
        print("-" * 40)
        
        # Generate unique usernames to avoid conflicts
        import time
        unique_id = str(int(time.time()))[-6:]
        users_data = [
            {"username": f"alice_{unique_id}", "email": f"alice_{unique_id}@test.com", "password": "alice12345"},
            {"username": f"bob_{unique_id}", "email": f"bob_{unique_id}@test.com", "password": "bob12345"},
            {"username": f"charlie_{unique_id}", "email": f"charlie_{unique_id}@test.com", "password": "charlie12345"}
        ]
        
        # Variables pour stocker les propriétaires des agents
        cognitive_owner = None
        reflexive_owner = None
        hybrid_owner = None
        
        for user_data in users_data:
            user = await self.register_user(**user_data)
            if user:
                self.users[user_data["username"]] = user
                token = await self.login_user(user_data["username"], user_data["password"])
                if token:
                    self.tokens[user_data["username"]] = token
                    print(f"✅ {user_data['username']} créé et connecté")
                else:
                    print(f"❌ Échec de connexion pour {user_data['username']}")
            else:
                print(f"❌ Échec de création pour {user_data['username']}")
        
        # 2. Créer des agents de chaque type
        print("\n🤖 Étape 2: Création des agents (tous les types)")
        print("-" * 40)
        
        agents_by_user = {}
        agent_configs = [
            # Agents cognitifs (reactive)
            {
                "name": "CognitiveAnalyst",
                "role": "Analyste de données",
                "agent_type": "reactive",
                "capabilities": ["analysis", "reasoning", "planning"],
                "configuration": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            },
            {
                "name": "CognitiveStrategist",
                "role": "Stratège",
                "agent_type": "reactive",
                "capabilities": ["strategy", "planning", "decision_making"],
                "configuration": {
                    "model": "gpt-4",
                    "temperature": 0.8
                }
            },
            # Agents réflexifs
            {
                "name": "ReflexiveMonitor",
                "role": "Moniteur système",
                "agent_type": "reflexive",
                "capabilities": ["monitoring", "alerting", "fast_response"],
                "reactive_rules": {
                    "alert_rule": {
                        "condition": {"alert_level": "high"},
                        "action": {"type": "notify", "content": "Alert triggered!"}
                    }
                }
            },
            {
                "name": "ReflexiveResponder",
                "role": "Répondeur rapide",
                "agent_type": "reflexive",
                "capabilities": ["quick_response", "rule_execution"],
                "reactive_rules": {
                    "greeting_rule": {
                        "condition": {"type": "greeting"},
                        "action": {"type": "respond", "content": "Hello!"}
                    }
                }
            },
            # Agents hybrides
            {
                "name": "HybridCoordinator",
                "role": "Coordinateur adaptatif",
                "agent_type": "hybrid",
                "capabilities": ["coordination", "adaptation", "multi_mode"],
                "configuration": {
                    "complexity_threshold": 0.6,
                    "learning_rate": 0.1
                },
                "reactive_rules": {
                    "simple_task": {
                        "condition": {"complexity": "low"},
                        "action": {"type": "execute", "content": "Quick execution"}
                    }
                }
            },
            {
                "name": "HybridOptimizer",
                "role": "Optimiseur de performance",
                "agent_type": "hybrid",
                "capabilities": ["optimization", "learning", "dual_mode"],
                "configuration": {
                    "complexity_threshold": 0.7,
                    "adaptive": True
                }
            }
        ]
        
        # Distribuer les agents entre les utilisateurs
        for i, (username, token) in enumerate(self.tokens.items()):
            agents_by_user[username] = []
            
            # Chaque utilisateur crée 2 agents
            for j in range(2):
                agent_config = agent_configs[(i * 2 + j) % len(agent_configs)]
                agent = await self.create_agent(token, agent_config)
                
                if agent:
                    agents_by_user[username].append(agent)
                    print(f"✅ {username}: Agent '{agent['name']}' créé (Type: {agent['agent_type']})")
                else:
                    print(f"❌ {username}: Échec création agent '{agent_config['name']}'")
        
        # Compter les agents par type
        agent_count_by_type = {"reactive": 0, "cognitive": 0, "reflexive": 0, "hybrid": 0}
        total_agents = 0
        for agents in agents_by_user.values():
            for agent in agents:
                agent_type = agent["agent_type"]
                # Map cognitive back to reactive for display consistency
                if agent_type == "cognitive":
                    agent_count_by_type["reactive"] += 1
                    agent_count_by_type["cognitive"] += 1
                else:
                    agent_count_by_type[agent_type] += 1
                total_agents += 1
        
        print(f"\n📊 Résumé des agents créés:")
        print(f"   - Total: {total_agents}")
        print(f"   - Cognitifs (reactive): {agent_count_by_type['reactive']}")
        print(f"   - Réflexifs: {agent_count_by_type['reflexive']}")
        print(f"   - Hybrides: {agent_count_by_type['hybrid']}")
        
        # 3. Tester l'envoi de messages entre différents types d'agents
        print("\n💬 Étape 3: Test de communication inter-agents")
        print("-" * 40)
        
        messages_sent = 0
        
        # Test 1: Cognitive -> Reflexive
        print("\n🔄 Test 1: Communication Cognitive -> Reflexive")
        cognitive_sender = None
        cognitive_owner = None
        reflexive_receiver = None
        reflexive_owner = None
        
        # Trouver un agent cognitif et un agent réflexif
        for username, agents in agents_by_user.items():
            for agent in agents:
                if agent["agent_type"] == "reactive" and not cognitive_sender:
                    cognitive_sender = agent
                    cognitive_owner = username
                    print(f"   ✓ Agent cognitif trouvé: {agent['name']} (propriétaire: {username})")
                elif agent["agent_type"] == "reflexive" and not reflexive_receiver:
                    reflexive_receiver = agent
                    reflexive_owner = username
                    print(f"   ✓ Agent réflexif trouvé: {agent['name']} (propriétaire: {username})")
                    
        if cognitive_sender and reflexive_receiver and cognitive_owner:
            print(f"\n🎯 Envoi de {cognitive_sender['name']} vers {reflexive_receiver['name']}")
            msg = await self.send_message(
                self.tokens[cognitive_owner],
                cognitive_sender["id"],
                reflexive_receiver["id"],
                "request",
                {
                    "action": "monitor_status", 
                    "target": "system_health",
                    "parameters": {
                        "metrics": ["cpu", "memory", "disk"],
                        "interval": "5m"
                    }
                }
            )
            if msg:
                messages_sent += 1
                print("   ✅ Message envoyé avec succès")
            else:
                print("   ❌ Échec de l'envoi du message")
        else:
            print("   ⚠️ Agents non trouvés pour ce test")
            if not cognitive_sender:
                print("      - Aucun agent cognitif disponible")
            if not reflexive_receiver:
                print("      - Aucun agent réflexif disponible")
        
        # Test 2: Reflexive -> Hybrid
        print("\n🔄 Test 2: Communication Reflexive -> Hybrid")
        reflexive_sender = None
        reflexive_owner = None
        hybrid_receiver = None
        hybrid_owner = None
        
        for username, agents in agents_by_user.items():
            for agent in agents:
                if agent["agent_type"] == "reflexive" and not reflexive_sender:
                    reflexive_sender = agent
                    reflexive_owner = username
                    print(f"   ✓ Agent réflexif trouvé: {agent['name']} (propriétaire: {username})")
                elif agent["agent_type"] == "hybrid" and not hybrid_receiver:
                    hybrid_receiver = agent
                    hybrid_owner = username
                    print(f"   ✓ Agent hybride trouvé: {agent['name']} (propriétaire: {username})")
                    
        if reflexive_sender and hybrid_receiver and reflexive_owner:
            print(f"\n🎯 Envoi de {reflexive_sender['name']} vers {hybrid_receiver['name']}")
            msg = await self.send_message(
                self.tokens[reflexive_owner],
                reflexive_sender["id"],
                hybrid_receiver["id"],
                "inform",
                {
                    "status": "alert", 
                    "level": "medium", 
                    "details": "CPU usage 75%",
                    "timestamp": datetime.utcnow().isoformat(),
                    "recommendations": [
                        "Scale up instances",
                        "Optimize queries",
                        "Check memory leaks"
                    ]
                }
            )
            if msg:
                messages_sent += 1
                print("   ✅ Message envoyé avec succès")
            else:
                print("   ❌ Échec de l'envoi du message")
        else:
            print("   ⚠️ Agents non trouvés pour ce test")
            if not reflexive_sender:
                print("      - Aucun agent réflexif disponible")
            if not hybrid_receiver:
                print("      - Aucun agent hybride disponible")
        
        # Test 3: Hybrid -> Cognitive
        print("\n🔄 Test 3: Communication Hybrid -> Cognitive")
        hybrid_sender = None
        hybrid_owner = None
        cognitive_receiver = None
        cognitive_owner = None
        
        for username, agents in agents_by_user.items():
            for agent in agents:
                if agent["agent_type"] == "hybrid" and not hybrid_sender:
                    hybrid_sender = agent
                    hybrid_owner = username
                    print(f"   ✓ Agent hybride trouvé: {agent['name']} (propriétaire: {username})")
                elif agent["agent_type"] == "reactive" and not cognitive_receiver:
                    cognitive_receiver = agent
                    cognitive_owner = username
                    print(f"   ✓ Agent cognitif trouvé: {agent['name']} (propriétaire: {username})")
                    
        if hybrid_sender and cognitive_receiver and hybrid_owner:
            print(f"\n🎯 Envoi de {hybrid_sender['name']} vers {cognitive_receiver['name']}")
            msg = await self.send_message(
                self.tokens[hybrid_owner],
                hybrid_sender["id"],
                cognitive_receiver["id"],
                "propose",
                {
                    "optimization": "resource_allocation", 
                    "current_usage": {
                        "cpu": "75%",
                        "memory": "60%",
                        "disk": "45%"
                    },
                    "proposed_changes": {
                        "add_instances": 2,
                        "upgrade_tier": "premium",
                        "enable_autoscaling": True
                    },
                    "expected_gain": "25%",
                    "cost_impact": "+$150/month"
                }
            )
            if msg:
                messages_sent += 1
                print("   ✅ Message envoyé avec succès")
            else:
                print("   ❌ Échec de l'envoi du message")
        else:
            print("   ⚠️ Agents non trouvés pour ce test")
            if not hybrid_sender:
                print("      - Aucun agent hybride disponible")
            if not cognitive_receiver:
                print("      - Aucun agent cognitif disponible")
        
        # Test 4: Communication bidirectionnelle
        print("\n🔄 Test 4: Communication bidirectionnelle")
        
        # Utiliser les agents du Test 1 s'ils existent
        if cognitive_sender and reflexive_receiver and cognitive_owner and reflexive_owner:
            print(f"\n🎯 Test de réponse: {reflexive_receiver['name']} répond à {cognitive_sender['name']}")
            
            # Le réflexif répond au cognitif
            response_msg = await self.send_message(
                self.tokens[reflexive_owner],
                reflexive_receiver["id"],
                cognitive_sender["id"],
                "inform",
                {
                    "response_to": "monitor_status",
                    "status": "monitoring_active",
                    "metrics": {
                        "cpu": "45%",
                        "memory": "62%",
                        "disk": "78%",
                        "network": "normal"
                    },
                    "alerts": [],
                    "health_score": 85
                }
            )
            if response_msg:
                messages_sent += 1
                print("   ✅ Message de réponse envoyé avec succès")
            else:
                print("   ❌ Échec de l'envoi du message de réponse")
        else:
            print("   ⚠️ Test bidirectionnel impossible - agents manquants")
            if not cognitive_sender:
                print("      - Agent cognitif manquant")
            if not reflexive_receiver:
                print("      - Agent réflexif manquant")
            if not cognitive_owner:
                print("      - Propriétaire de l'agent cognitif manquant")
            if not reflexive_owner:
                print("      - Propriétaire de l'agent réflexif manquant")
        
        print(f"\n📨 Total messages envoyés: {messages_sent}")
        
        # Récapitulatif des tests de communication
        print("\n📋 Récapitulatif des tests de communication:")
        print("-" * 40)
        print(f"   - Tests exécutés: 4")
        print(f"   - Messages envoyés avec succès: {messages_sent}")
        print(f"   - Taux de réussite: {(messages_sent / 4 * 100):.1f}%" if messages_sent > 0 else "   - Taux de réussite: 0%")
        
        # Attendre un peu pour que les messages soient traités
        print("\n⏳ Attente de 5 secondes pour le traitement complet des messages...")
        for i in range(5, 0, -1):
            print(f"   {i}...", end='', flush=True)
            await asyncio.sleep(1)
        print(" Terminé!")
        
        # 4. Créer des mémoires pour chaque type d'agent
        print("\n🧠 Étape 4: Création de mémoires")
        print("-" * 40)
        
        memories_created = 0
        
        for username, agents in agents_by_user.items():
            token = self.tokens[username]
            for agent in agents:
                memory_content = f"Test memory for {agent['agent_type']} agent: {agent['name']}"
                memory = await self.create_memory(token, agent["id"], memory_content)
                if memory:
                    memories_created += 1
                    print(f"✅ Mémoire créée pour {agent['name']} ({agent['agent_type']})")
        
        print(f"\n💾 Total mémoires créées: {memories_created}")
        
        # 5. Vérifier la réception des messages
        print("\n📥 Étape 5: Vérification de la réception des messages")
        print("-" * 40)
        
        total_received = 0
        all_messages = []
        
        for username, agents in agents_by_user.items():
            token = self.tokens[username]
            for agent in agents:
                messages = await self.get_messages(token, agent["id"], "received")
                if messages:
                    total_received += len(messages)
                    print(f"\n✅ {agent['name']} ({agent['agent_type']}) a reçu {len(messages)} message(s):")
                    
                    for i, msg in enumerate(messages, 1):
                        print(f"\n   📨 Message {i}:")
                        print(f"      - De: {msg.get('sender_id', 'N/A')}")
                        print(f"      - Type: {msg.get('performative', 'N/A')}")
                        print(f"      - Conversation: {msg.get('conversation_id', 'N/A')}")
                        print(f"      - Timestamp: {msg.get('created_at', 'N/A')}")
                        print(f"      - Contenu:")
                        content = msg.get('content', {})
                        print(f"        {json.dumps(content, indent=8)}")
                        
                        all_messages.append({
                            'receiver': agent['name'],
                            'receiver_type': agent['agent_type'],
                            'message': msg
                        })
                else:
                    print(f"\n⚪ {agent['name']} ({agent['agent_type']}) n'a reçu aucun message")
        
        print(f"\n📬 Total messages reçus: {total_received}")
        
        # Afficher aussi les messages envoyés par chaque agent
        print("\n📤 Vérification des messages envoyés")
        print("-" * 40)
        
        total_sent = 0
        
        for username, agents in agents_by_user.items():
            token = self.tokens[username]
            for agent in agents:
                sent_messages = await self.get_messages(token, agent["id"], "sent")
                if sent_messages:
                    total_sent += len(sent_messages)
                    print(f"\n✅ {agent['name']} ({agent['agent_type']}) a envoyé {len(sent_messages)} message(s)")
                    
                    for i, msg in enumerate(sent_messages, 1):
                        print(f"\n   📤 Message envoyé {i}:")
                        print(f"      - Vers: {msg.get('receiver_id', 'N/A')}")
                        print(f"      - Type: {msg.get('performative', 'N/A')}")
                        print(f"      - Contenu: {json.dumps(msg.get('content', {}), indent=8)}")
        
        print(f"\n📨 Total messages envoyés (vérification): {total_sent}")
        
        # Créer un dictionnaire pour mapper les IDs des agents
        agents_by_id = {}
        for username, agents in agents_by_user.items():
            for agent in agents:
                agents_by_id[agent['id']] = {
                    'name': agent['name'],
                    'agent_type': agent['agent_type']
                }
        
        # Afficher un résumé des conversations
        print("\n🔄 Résumé des conversations")
        print("-" * 40)
        
        if all_messages:
            print("\nFlux de communication détecté:")
            conversations = {}
            
            for msg_info in all_messages:
                msg = msg_info['message']
                conv_id = msg.get('conversation_id', 'N/A')
                if conv_id not in conversations:
                    conversations[conv_id] = []
                conversations[conv_id].append(msg_info)
            
            for conv_id, msgs in conversations.items():
                print(f"\n📍 Conversation {conv_id[:8]}...")
                for msg_info in msgs:
                    msg = msg_info['message']
                    receiver = msg_info['receiver']
                    receiver_type = msg_info['receiver_type']
                    sender_id = msg.get('sender_id', 'N/A')
                    sender_name = 'Inconnu'
                    sender_type = 'N/A'
                    
                    if sender_id in agents_by_id:
                        sender_name = agents_by_id[sender_id]['name']
                        sender_type = agents_by_id[sender_id]['agent_type']
                    
                    print(f"   {sender_name} ({sender_type}) → {receiver} ({receiver_type}): {msg.get('performative', 'N/A')}")
        
        # Diagramme de flux de communication
        print("\n🗺️  Diagramme de flux de communication")
        print("-" * 40)
        
        # Créer une matrice de communication
        comm_matrix = {}
        for msg_info in all_messages:
            msg = msg_info['message']
            sender_id = msg.get('sender_id', 'N/A')
            receiver = msg_info['receiver']
            
            if sender_id in agents_by_id:
                sender = agents_by_id[sender_id]['name']
                sender_type = agents_by_id[sender_id]['agent_type']
                key = f"{sender} ({sender_type})"
                
                if key not in comm_matrix:
                    comm_matrix[key] = {}
                    
                receiver_key = f"{receiver} ({msg_info['receiver_type']})"
                if receiver_key not in comm_matrix[key]:
                    comm_matrix[key][receiver_key] = 0
                comm_matrix[key][receiver_key] += 1
        
        # Afficher la matrice
        if comm_matrix:
            print("\nMatrice de communication (nombre de messages):")
            print("")
            for sender, receivers in comm_matrix.items():
                print(f"\n📤 {sender}:")
                for receiver, count in receivers.items():
                    print(f"   → {receiver}: {count} message(s)")
        
        # Résumé final
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DU TEST")
        print("="*80)
        print(f"✅ Utilisateurs créés: {len(self.users)}")
        print(f"✅ Agents créés: {total_agents}")
        print(f"   - Cognitifs: {agent_count_by_type['reactive']}")
        print(f"   - Réflexifs: {agent_count_by_type['reflexive']}")
        print(f"   - Hybrides: {agent_count_by_type['hybrid']}")
        print(f"✅ Messages envoyés: {messages_sent}")
        print(f"✅ Messages reçus: {total_received}")
        print(f"✅ Mémoires créées: {memories_created}")
        
        if agent_count_by_type['reflexive'] > 0 and agent_count_by_type['hybrid'] > 0:
            print("\n🎉 SUCCÈS: Tous les types d'agents sont maintenant fonctionnels!")
        else:
            print("\n⚠️  Certains types d'agents n'ont pas pu être créés")
        
        print("="*80)


async def main():
    """Fonction principale"""
    async with MASTestAllAgents() as tester:
        await tester.run_complete_test()


if __name__ == "__main__":
    asyncio.run(main())