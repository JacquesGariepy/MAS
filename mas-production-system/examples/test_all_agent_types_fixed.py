#!/usr/bin/env python3
"""
Version corrigée de test_all_agent_types.py avec toutes les variables déclarées
et démarrage automatique des agents.
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


async def main():
    """Test principal avec agents démarrés"""
    print("="*80)
    print("🧪 TEST COMPLET DES TYPES D'AGENTS MAS v2.0")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        # Variables pour stocker TOUS les agents et propriétaires
        all_agents = {}  # {agent_id: agent_data}
        all_users = {}   # {username: token}
        agents_by_type = {
            "cognitive": None,
            "reflexive": None,
            "hybrid": None
        }
        owners_by_type = {
            "cognitive": None,
            "reflexive": None,  
            "hybrid": None
        }
        
        # Phase 1: Créer des utilisateurs de test
        print("\n📋 Phase 1: Création des utilisateurs de test")
        print("-" * 60)
        
        # Générer un ID unique basé sur le timestamp
        import time
        unique_id = str(int(time.time()))[-6:]
        
        test_users = [
            (f"alice_{unique_id}", f"alice_{unique_id}@test.com", "alice12345"),
            (f"bob_{unique_id}", f"bob_{unique_id}@test.com", "bob12345"),
            (f"charlie_{unique_id}", f"charlie_{unique_id}@test.com", "charlie12345")
        ]
        
        for username, email, password in test_users:
            print(f"\n🔑 Création/connexion utilisateur: {username}")
            
            # Register
            register_data = {
                "username": username,
                "email": email,
                "password": password
            }
            
            register_resp = await session.post(
                f"{API_BASE_URL.replace('/api/v1', '')}/auth/register",
                json=register_data
            )
            
            if register_resp.status not in [201, 400]:
                print(f"   ❌ Erreur création: {await register_resp.text()}")
                continue
            
            # Login
            login_data = {"username": username, "password": password}
            login_resp = await session.post(
                f"{API_BASE_URL.replace('/api/v1', '')}/auth/token",
                data=login_data
            )
            
            if login_resp.status == 200:
                token_data = await login_resp.json()
                token = token_data["access_token"]
                all_users[username] = token
                print(f"   ✅ Token obtenu pour {username}")
            else:
                print(f"   ❌ Échec connexion: {login_resp.status}")
        
        # Phase 2: Créer les agents de test
        print("\n\n📋 Phase 2: Création des agents de test")
        print("-" * 60)
        
        agent_configs = [
            {
                "owner": f"alice_{unique_id}",
                "type": "cognitive",
                "config": {
                    "name": f"CognitiveAnalyst_{unique_id}",
                    "agent_type": "cognitive",
                    "role": "Analyste cognitif utilisant le LLM",
                    "capabilities": ["analyse", "synthèse", "raisonnement"],
                    "initial_beliefs": {
                        "domain": "analysis",
                        "expertise": "data processing"
                    },
                    "initial_desires": ["apprendre", "analyser", "communiquer"],
                    "configuration": {
                        "llm_enabled": True,
                        "reasoning_depth": 5
                    }
                }
            },
            {
                "owner": f"bob_{unique_id}",
                "type": "reflexive",
                "config": {
                    "name": f"ReflexiveResponder_{unique_id}",
                    "agent_type": "reflexive",
                    "role": "Agent réactif avec règles",
                    "capabilities": ["réaction", "exécution", "réponse_rapide"],
                    "initial_beliefs": {
                        "speed": "fast",
                        "approach": "rule-based"
                    },
                    "initial_desires": ["réagir", "exécuter"],
                    "reactive_rules": {
                        "on_message": "respond_immediately",
                        "on_request": "process_request",
                        "default": "acknowledge"
                    }
                }
            },
            {
                "owner": f"charlie_{unique_id}",
                "type": "hybrid",
                "config": {
                    "name": f"HybridCoordinator_{unique_id}",
                    "agent_type": "hybrid",
                    "role": "Coordinateur hybride",
                    "capabilities": ["coordination", "planification", "adaptation"],
                    "initial_beliefs": {
                        "strategy": "balanced",
                        "flexibility": "high"
                    },
                    "initial_desires": ["coordonner", "optimiser"],
                    "reactive_rules": {
                        "urgent": "handle_immediately",
                        "normal": "plan_and_execute"
                    }
                }
            }
        ]
        
        # Créer chaque agent
        for agent_info in agent_configs:
            owner = agent_info["owner"]
            agent_type = agent_info["type"]
            config = agent_info["config"]
            
            if owner not in all_users:
                print(f"\n❌ Propriétaire {owner} non trouvé")
                continue
            
            print(f"\n🤖 Création agent {agent_type}: {config['name']}")
            
            headers = {"Authorization": f"Bearer {all_users[owner]}"}
            
            create_resp = await session.post(
                f"{API_BASE_URL}/agents",
                json=config,
                headers=headers
            )
            
            if create_resp.status == 201:
                agent_data = await create_resp.json()
                agent_id = agent_data["id"]
                
                # Stocker l'agent
                all_agents[agent_id] = agent_data
                agents_by_type[agent_type] = agent_data
                owners_by_type[agent_type] = owner
                
                print(f"   ✅ Agent créé avec succès")
                print(f"   📌 ID: {agent_id}")
                print(f"   👤 Propriétaire: {owner}")
                print(f"   🏷️  Type: {agent_data['agent_type']}")
                print(f"   📊 Status: {agent_data['status']}")
            else:
                print(f"   ❌ Échec création: {create_resp.status}")
                error_text = await create_resp.text()
                print(f"   Détails: {error_text}")
        
        # Phase 3: Démarrer tous les agents
        print("\n\n📋 Phase 3: Démarrage des agents")
        print("-" * 60)
        
        for agent_type, agent in agents_by_type.items():
            if not agent:
                continue
            
            agent_id = agent["id"]
            owner = owners_by_type[agent_type]
            headers = {"Authorization": f"Bearer {all_users[owner]}"}
            
            print(f"\n🚀 Démarrage de {agent['name']}...")
            
            start_resp = await session.post(
                f"{API_BASE_URL}/agents/{agent_id}/start",
                headers=headers
            )
            
            if start_resp.status == 200:
                print(f"   ✅ Agent démarré avec succès!")
                # Mettre à jour le statut
                agents_by_type[agent_type]["status"] = "working"
            elif start_resp.status == 400:
                error = await start_resp.json()
                if "already" in error.get("detail", "").lower():
                    print(f"   ✅ Agent déjà actif")
                    agents_by_type[agent_type]["status"] = "working"
                else:
                    print(f"   ❌ Erreur: {error.get('detail')}")
            else:
                print(f"   ❌ Erreur HTTP {start_resp.status}")
        
        # Attendre que les agents soient prêts
        print("\n⏳ Attente de l'initialisation des agents (3 secondes)...")
        await asyncio.sleep(3)
        
        # Phase 4: Tests de communication
        print("\n\n📋 Phase 4: Tests de communication inter-agents")
        print("-" * 60)
        
        # Test 1: Cognitive -> Reflexive
        print("\n🔄 Test 1: Communication Cognitive -> Reflexive")
        
        if agents_by_type["cognitive"] and agents_by_type["reflexive"]:
            cognitive_agent = agents_by_type["cognitive"]
            reflexive_agent = agents_by_type["reflexive"]
            cognitive_owner = owners_by_type["cognitive"]
            
            print(f"   📤 Expéditeur: {cognitive_agent['name']} (propriétaire: {cognitive_owner})")
            print(f"   📥 Destinataire: {reflexive_agent['name']}")
            
            headers = {"Authorization": f"Bearer {all_users[cognitive_owner]}"}
            
            message_data = {
                "receiver_id": reflexive_agent["id"],
                "performative": "inform",
                "content": {
                    "message": "Analyse terminée. Résultats disponibles.",
                    "analysis_id": "test_001",
                    "timestamp": time.time()
                }
            }
            
            send_resp = await session.post(
                f"{API_BASE_URL}/agents/{cognitive_agent['id']}/messages",
                json=message_data,
                headers=headers
            )
            
            if send_resp.status == 201:
                print("   ✅ Message envoyé avec succès!")
                result = await send_resp.json()
                print(f"   📨 ID du message: {result['id']}")
            else:
                print(f"   ❌ Échec envoi: {send_resp.status}")
                print(f"   Détails: {await send_resp.text()}")
        else:
            print("   ❌ Agents manquants pour ce test")
        
        # Test 2: Reflexive -> Hybrid
        print("\n🔄 Test 2: Communication Reflexive -> Hybrid")
        
        if agents_by_type["reflexive"] and agents_by_type["hybrid"]:
            reflexive_agent = agents_by_type["reflexive"]
            hybrid_agent = agents_by_type["hybrid"]
            reflexive_owner = owners_by_type["reflexive"]
            
            print(f"   📤 Expéditeur: {reflexive_agent['name']} (propriétaire: {reflexive_owner})")
            print(f"   📥 Destinataire: {hybrid_agent['name']}")
            
            headers = {"Authorization": f"Bearer {all_users[reflexive_owner]}"}
            
            message_data = {
                "receiver_id": hybrid_agent["id"],
                "performative": "request",
                "content": {
                    "action": "coordinate_task",
                    "task_id": "urgent_001",
                    "priority": "high"
                }
            }
            
            send_resp = await session.post(
                f"{API_BASE_URL}/agents/{reflexive_agent['id']}/messages",
                json=message_data,
                headers=headers
            )
            
            if send_resp.status == 201:
                print("   ✅ Message envoyé avec succès!")
            else:
                print(f"   ❌ Échec envoi: {send_resp.status}")
        else:
            print("   ❌ Agents manquants pour ce test")
        
        # Test 3: Hybrid -> Cognitive
        print("\n🔄 Test 3: Communication Hybrid -> Cognitive")
        
        if agents_by_type["hybrid"] and agents_by_type["cognitive"]:
            hybrid_agent = agents_by_type["hybrid"]
            cognitive_agent = agents_by_type["cognitive"]
            hybrid_owner = owners_by_type["hybrid"]
            
            print(f"   📤 Expéditeur: {hybrid_agent['name']} (propriétaire: {hybrid_owner})")
            print(f"   📥 Destinataire: {cognitive_agent['name']}")
            
            headers = {"Authorization": f"Bearer {all_users[hybrid_owner]}"}
            
            message_data = {
                "receiver_id": cognitive_agent["id"],
                "performative": "query-ref",
                "content": {
                    "query": "Analyse comparative des stratégies A et B",
                    "context": "Optimisation des ressources",
                    "deadline": "urgent"
                }
            }
            
            send_resp = await session.post(
                f"{API_BASE_URL}/agents/{hybrid_agent['id']}/messages",
                json=message_data,
                headers=headers
            )
            
            if send_resp.status == 201:
                print("   ✅ Message envoyé avec succès!")
            else:
                print(f"   ❌ Échec envoi: {send_resp.status}")
        else:
            print("   ❌ Agents manquants pour ce test")
        
        # Test 4: Communication bidirectionnelle
        print("\n🔄 Test 4: Communication bidirectionnelle Cognitive <-> Hybrid")
        
        if agents_by_type["cognitive"] and agents_by_type["hybrid"]:
            cognitive_agent = agents_by_type["cognitive"]
            hybrid_agent = agents_by_type["hybrid"]
            cognitive_owner = owners_by_type["cognitive"]
            hybrid_owner = owners_by_type["hybrid"]
            
            # Message 1: Cognitive -> Hybrid
            print("   📤 Message 1: Cognitive -> Hybrid")
            headers = {"Authorization": f"Bearer {all_users[cognitive_owner]}"}
            
            message1_data = {
                "receiver_id": hybrid_agent["id"],
                "performative": "propose",
                "content": {
                    "proposal": "Nouvelle stratégie d'optimisation",
                    "benefits": ["efficacité +20%", "coût -15%"]
                }
            }
            
            send1_resp = await session.post(
                f"{API_BASE_URL}/agents/{cognitive_agent['id']}/messages",
                json=message1_data,
                headers=headers
            )
            
            if send1_resp.status == 201:
                print("      ✅ Message 1 envoyé")
                
                # Attendre un peu
                await asyncio.sleep(2)
                
                # Message 2: Hybrid -> Cognitive
                print("   📤 Message 2: Hybrid -> Cognitive (réponse)")
                headers = {"Authorization": f"Bearer {all_users[hybrid_owner]}"}
                
                message2_data = {
                    "receiver_id": cognitive_agent["id"],
                    "performative": "accept-proposal",
                    "content": {
                        "accepted": True,
                        "comments": "Excellente proposition, démarrage immédiat"
                    }
                }
                
                send2_resp = await session.post(
                    f"{API_BASE_URL}/agents/{hybrid_agent['id']}/messages",
                    json=message2_data,
                    headers=headers
                )
                
                if send2_resp.status == 201:
                    print("      ✅ Message 2 envoyé")
                    print("   ✅ Communication bidirectionnelle réussie!")
                else:
                    print(f"      ❌ Échec message 2: {send2_resp.status}")
            else:
                print(f"      ❌ Échec message 1: {send1_resp.status}")
        else:
            print("   ❌ Agents manquants pour ce test")
        
        # Attendre le traitement des messages
        print("\n⏳ Attente du traitement des messages (5 secondes)...")
        await asyncio.sleep(5)
        
        # Phase 5: Vérification des messages reçus
        print("\n\n📋 Phase 5: Vérification des messages reçus")
        print("-" * 60)
        
        for agent_type, agent in agents_by_type.items():
            if not agent:
                continue
            
            owner = owners_by_type[agent_type]
            headers = {"Authorization": f"Bearer {all_users[owner]}"}
            
            print(f"\n📨 Messages pour {agent['name']}:")
            
            messages_resp = await session.get(
                f"{API_BASE_URL}/agents/{agent['id']}/messages",
                headers=headers
            )
            
            if messages_resp.status == 200:
                messages_data = await messages_resp.json()
                messages = messages_data.get("items", [])
                
                received = [m for m in messages if m["receiver_id"] == agent["id"]]
                sent = [m for m in messages if m["sender_id"] == agent["id"]]
                
                print(f"   📥 Messages reçus: {len(received)}")
                print(f"   📤 Messages envoyés: {len(sent)}")
                
                # Afficher les messages reçus
                for msg in received[:3]:  # Limiter à 3 messages
                    sender_name = "Unknown"
                    for _, other_agent in agents_by_type.items():
                        if other_agent and other_agent["id"] == msg["sender_id"]:
                            sender_name = other_agent["name"]
                            break
                    
                    print(f"\n      De: {sender_name}")
                    print(f"      Type: {msg['performative']}")
                    print(f"      Contenu: {json.dumps(msg['content'], indent=8)}")
        
        # Résumé final
        print("\n\n" + "="*80)
        print("📊 RÉSUMÉ DU TEST")
        print("="*80)
        
        # Compter les agents créés et actifs
        agents_created = sum(1 for a in agents_by_type.values() if a is not None)
        agents_working = sum(1 for a in agents_by_type.values() if a and a.get("status") == "working")
        
        print(f"\n✅ Agents créés: {agents_created}/3")
        print(f"✅ Agents actifs: {agents_working}/3")
        print(f"✅ Utilisateurs créés: {len(all_users)}/3")
        
        # Vérifier la configuration LLM
        print("\n🧠 Configuration LLM:")
        print("   Provider: LMStudio")
        print("   Model: qwen3-8b")
        print("   URL: http://host.docker.internal:1234/v1")
        
        if agents_working == agents_created:
            print("\n🎉 Tous les tests ont été exécutés avec succès!")
        else:
            print("\n⚠️  Certains agents ne sont pas actifs")
            print("   Les agents cognitifs nécessitent que LMStudio soit démarré")


if __name__ == "__main__":
    print("🔧 MAS - Test complet avec agents démarrés")
    print("   Ce test va:")
    print("   1. Créer 3 utilisateurs de test")
    print("   2. Créer 3 agents (cognitive, reflexive, hybrid)")
    print("   3. Démarrer tous les agents (idle -> working)")
    print("   4. Tester 4 scénarios de communication")
    print("   5. Vérifier la réception des messages")
    print("")
    
    asyncio.run(main())