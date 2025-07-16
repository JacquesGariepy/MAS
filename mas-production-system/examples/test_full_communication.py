#!/usr/bin/env python3
"""
Script complet pour tester la communication entre agents avec démarrage automatique.
Ce script :
1. Démarre tous les agents (passage de idle à working)
2. Corrige les problèmes de variables dans les tests
3. Teste tous les scénarios de communication
4. Vérifie l'utilisation du LLM pour les agents cognitifs
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@mas.ai"
ADMIN_PASSWORD = "securepassword123"


class MASCommunicationTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.agents = []
        self.users = {}
        self.test_results = {
            "agents_started": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "llm_responses": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }
    
    async def setup(self):
        """Initialiser la session et l'authentification"""
        self.session = aiohttp.ClientSession()
        
        # Login admin
        login_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        async with self.session.post(f"{API_BASE_URL}/auth/login", data=login_data) as resp:
            if resp.status != 200:
                raise Exception(f"Admin login failed: {await resp.text()}")
            self.admin_token = (await resp.json())["access_token"]
    
    async def cleanup(self):
        """Fermer la session"""
        if self.session:
            await self.session.close()
    
    async def create_test_users(self) -> Dict[str, str]:
        """Créer des utilisateurs de test"""
        print("\n📋 Création des utilisateurs de test...")
        
        users_data = [
            ("alice", "alice@mas.ai", "password123"),
            ("bob", "bob@mas.ai", "password123"),
            ("charlie", "charlie@mas.ai", "password123")
        ]
        
        for username, email, password in users_data:
            # Register
            register_data = {
                "username": username,
                "email": email,
                "password": password
            }
            
            async with self.session.post(f"{API_BASE_URL.replace('/api/v1', '')}/auth/register", json=register_data) as resp:
                if resp.status not in [201, 400]:  # 400 = déjà existe
                    print(f"   ❌ Erreur création {username}: {await resp.text()}")
                    continue
            
            # Login
            login_data = {"username": username, "password": password}
            async with self.session.post(f"{API_BASE_URL.replace('/api/v1', '')}/auth/token", data=login_data) as resp:
                if resp.status == 200:
                    token = (await resp.json())["access_token"]
                    self.users[username] = token
                    print(f"   ✅ {username} créé/connecté")
        
        return self.users
    
    async def create_test_agents(self) -> List[Dict[str, Any]]:
        """Créer les agents de test"""
        print("\n🤖 Création des agents de test...")
        
        agents_config = [
            {
                "owner": "alice",
                "name": "Agent Cognitif Alice",
                "agent_type": "cognitive",
                "role": "Analyste",
                "capabilities": ["analyse", "synthèse"],
                "initial_beliefs": {"domain": "finance"},
                "initial_desires": ["analyser", "communiquer"]
            },
            {
                "owner": "bob",
                "name": "Agent Reflexif Bob",
                "agent_type": "reflexive",
                "role": "Exécuteur",
                "capabilities": ["exécution", "réaction"],
                "initial_beliefs": {"speed": "fast"},
                "initial_desires": ["réagir", "exécuter"],
                "reactive_rules": {
                    "on_message": "respond_immediately",
                    "on_task": "execute_now"
                }
            },
            {
                "owner": "charlie",
                "name": "Agent Hybride Charlie",
                "agent_type": "hybrid",
                "role": "Coordinateur",
                "capabilities": ["coordination", "planification"],
                "initial_beliefs": {"approach": "balanced"},
                "initial_desires": ["coordonner", "optimiser"],
                "reactive_rules": {}
            }
        ]
        
        created_agents = []
        
        for config in agents_config:
            owner = config.pop("owner")
            if owner not in self.users:
                print(f"   ❌ Propriétaire {owner} non trouvé")
                continue
            
            headers = {"Authorization": f"Bearer {self.users[owner]}"}
            
            async with self.session.post(f"{API_BASE_URL}/agents", json=config, headers=headers) as resp:
                if resp.status == 201:
                    agent = await resp.json()
                    agent["owner"] = owner  # Ajouter le propriétaire pour référence
                    created_agents.append(agent)
                    print(f"   ✅ {config['name']} créé (ID: {agent['id'][:8]}...)")
                else:
                    print(f"   ❌ Échec création {config['name']}: {await resp.text()}")
        
        self.agents = created_agents
        return created_agents
    
    async def start_all_agents(self):
        """Démarrer tous les agents (passage de idle à working)"""
        print("\n🚀 Démarrage de tous les agents...")
        
        for agent in self.agents:
            agent_id = agent["id"]
            owner = agent["owner"]
            headers = {"Authorization": f"Bearer {self.users[owner]}"}
            
            # Vérifier le statut actuel
            async with self.session.get(f"{API_BASE_URL}/agents/{agent_id}", headers=headers) as resp:
                if resp.status == 200:
                    current_agent = await resp.json()
                    current_status = current_agent.get("status", "unknown")
                    
                    if current_status == "working":
                        print(f"   ✅ {agent['name']} - Déjà actif")
                        self.test_results["agents_started"] += 1
                        continue
            
            # Démarrer l'agent
            async with self.session.post(f"{API_BASE_URL}/agents/{agent_id}/start", headers=headers) as resp:
                if resp.status == 200:
                    print(f"   ▶️  {agent['name']} - Démarré avec succès!")
                    self.test_results["agents_started"] += 1
                elif resp.status == 400:
                    error = await resp.json()
                    if "already" in error.get("detail", "").lower():
                        print(f"   ✅ {agent['name']} - Déjà actif")
                        self.test_results["agents_started"] += 1
                    else:
                        print(f"   ❌ {agent['name']} - {error.get('detail', 'Erreur')}")
                else:
                    print(f"   ❌ {agent['name']} - Erreur HTTP {resp.status}")
        
        print(f"\n   📊 {self.test_results['agents_started']}/{len(self.agents)} agents démarrés")
    
    async def test_cognitive_llm_usage(self):
        """Tester l'utilisation du LLM par les agents cognitifs"""
        print("\n🧠 Test d'utilisation du LLM par les agents cognitifs...")
        
        cognitive_agent = next((a for a in self.agents if a["agent_type"] == "cognitive"), None)
        if not cognitive_agent:
            print("   ❌ Aucun agent cognitif trouvé")
            return
        
        reflexive_agent = next((a for a in self.agents if a["agent_type"] == "reflexive"), None)
        if not reflexive_agent:
            print("   ❌ Aucun agent réflexif trouvé")
            return
        
        # Envoyer un message complexe nécessitant le LLM
        sender_token = self.users[reflexive_agent["owner"]]
        headers = {"Authorization": f"Bearer {sender_token}"}
        
        message_data = {
            "receiver_id": cognitive_agent["id"],
            "performative": "query-ref",
            "content": {
                "query": "Peux-tu analyser les avantages et inconvénients de l'architecture microservices versus monolithique?",
                "context": "Nous devons choisir une architecture pour notre nouveau projet"
            }
        }
        
        print(f"\n   📤 Envoi d'une requête complexe à {cognitive_agent['name']}...")
        
        async with self.session.post(
            f"{API_BASE_URL}/agents/{reflexive_agent['id']}/messages",
            json=message_data,
            headers=headers
        ) as resp:
            if resp.status == 201:
                print("   ✅ Requête envoyée avec succès")
                
                # Attendre la réponse
                await asyncio.sleep(3)
                
                # Vérifier les messages reçus
                cognitive_token = self.users[cognitive_agent["owner"]]
                headers = {"Authorization": f"Bearer {cognitive_token}"}
                
                async with self.session.get(
                    f"{API_BASE_URL}/agents/{cognitive_agent['id']}/messages",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        messages = (await resp.json()).get("items", [])
                        
                        # Chercher une réponse générée par le LLM
                        for msg in messages:
                            if msg.get("sender_id") == cognitive_agent["id"]:
                                content = msg.get("content", {})
                                if isinstance(content, dict) and len(str(content)) > 100:
                                    print("   ✅ Réponse LLM détectée!")
                                    print(f"      Longueur: {len(str(content))} caractères")
                                    print(f"      Aperçu: {str(content)[:150]}...")
                                    self.test_results["llm_responses"] += 1
                                    return
                        
                        print("   ⚠️  Aucune réponse LLM trouvée")
            else:
                print(f"   ❌ Échec envoi: {await resp.text()}")
    
    async def test_all_communications(self):
        """Tester tous les scénarios de communication"""
        print("\n💬 Tests de communication entre agents...")
        
        # Mapping des agents par type
        agents_by_type = {
            "cognitive": next((a for a in self.agents if a["agent_type"] == "cognitive"), None),
            "reflexive": next((a for a in self.agents if a["agent_type"] == "reflexive"), None),
            "hybrid": next((a for a in self.agents if a["agent_type"] == "hybrid"), None)
        }
        
        # Vérifier que tous les types sont présents
        missing_types = [t for t, a in agents_by_type.items() if a is None]
        if missing_types:
            print(f"   ❌ Types manquants: {missing_types}")
            return
        
        # Définir les tests
        test_scenarios = [
            ("Test 1: Cognitive → Reflexive", "cognitive", "reflexive", "inform", {"info": "Analyse terminée"}),
            ("Test 2: Reflexive → Hybrid", "reflexive", "hybrid", "request", {"action": "coordination"}),
            ("Test 3: Hybrid → Cognitive", "hybrid", "cognitive", "propose", {"proposal": "nouvelle stratégie"}),
            ("Test 4: Bidirectionnel", "cognitive", "hybrid", "query-ref", {"question": "Status?"})
        ]
        
        for test_name, sender_type, receiver_type, performative, content in test_scenarios:
            print(f"\n   🧪 {test_name}")
            
            sender = agents_by_type[sender_type]
            receiver = agents_by_type[receiver_type]
            
            # Token du propriétaire de l'expéditeur
            sender_token = self.users[sender["owner"]]
            headers = {"Authorization": f"Bearer {sender_token}"}
            
            message_data = {
                "receiver_id": receiver["id"],
                "performative": performative,
                "content": content
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/agents/{sender['id']}/messages",
                json=message_data,
                headers=headers
            ) as resp:
                if resp.status == 201:
                    print(f"      ✅ Message envoyé: {sender['name']} → {receiver['name']}")
                    self.test_results["messages_sent"] += 1
                    self.test_results["tests_passed"] += 1
                    
                    # Pour le test bidirectionnel, envoyer une réponse
                    if "Bidirectionnel" in test_name:
                        await asyncio.sleep(1)
                        
                        # Réponse du receiver
                        receiver_token = self.users[receiver["owner"]]
                        headers = {"Authorization": f"Bearer {receiver_token}"}
                        
                        reply_data = {
                            "receiver_id": sender["id"],
                            "performative": "inform",
                            "content": {"response": "Status: opérationnel"}
                        }
                        
                        async with self.session.post(
                            f"{API_BASE_URL}/agents/{receiver['id']}/messages",
                            json=reply_data,
                            headers=headers
                        ) as resp2:
                            if resp2.status == 201:
                                print(f"      ✅ Réponse envoyée: {receiver['name']} → {sender['name']}")
                                self.test_results["messages_sent"] += 1
                else:
                    print(f"      ❌ Échec: {await resp.text()}")
                    self.test_results["tests_failed"] += 1
        
        # Attendre un peu pour le traitement
        print("\n   ⏳ Attente du traitement des messages (5 secondes)...")
        await asyncio.sleep(5)
    
    async def verify_message_processing(self):
        """Vérifier que les messages ont été traités"""
        print("\n📊 Vérification du traitement des messages...")
        
        total_received = 0
        
        for agent in self.agents:
            token = self.users[agent["owner"]]
            headers = {"Authorization": f"Bearer {token}"}
            
            async with self.session.get(
                f"{API_BASE_URL}/agents/{agent['id']}/messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    messages = (await resp.json()).get("items", [])
                    received = len([m for m in messages if m.get("receiver_id") == agent["id"]])
                    total_received += received
                    
                    print(f"   📨 {agent['name']}: {received} messages reçus")
                    
                    # Afficher un échantillon
                    for msg in messages[:2]:
                        sender_name = next((a["name"] for a in self.agents if a["id"] == msg.get("sender_id")), "Unknown")
                        print(f"      • De: {sender_name}, Type: {msg.get('performative')}")
        
        self.test_results["messages_received"] = total_received
    
    async def run_complete_test(self):
        """Exécuter la suite complète de tests"""
        print("\n" + "="*60)
        print("🚀 TEST COMPLET DE COMMUNICATION MAS")
        print("="*60)
        
        try:
            await self.setup()
            
            # 1. Créer les utilisateurs et agents
            await self.create_test_users()
            await self.create_test_agents()
            
            if not self.agents:
                print("\n❌ Aucun agent créé, impossible de continuer")
                return
            
            # 2. Démarrer tous les agents
            await self.start_all_agents()
            
            # 3. Tester l'utilisation du LLM
            await self.test_cognitive_llm_usage()
            
            # 4. Tester toutes les communications
            await self.test_all_communications()
            
            # 5. Vérifier le traitement
            await self.verify_message_processing()
            
            # 6. Afficher le résumé
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60)
        
        print(f"""
   🤖 Agents démarrés: {self.test_results['agents_started']}/{len(self.agents)}
   📤 Messages envoyés: {self.test_results['messages_sent']}
   📥 Messages reçus: {self.test_results['messages_received']}
   🧠 Réponses LLM: {self.test_results['llm_responses']}
   ✅ Tests réussis: {self.test_results['tests_passed']}
   ❌ Tests échoués: {self.test_results['tests_failed']}
   
   🎯 Taux de réussite: {self.test_results['tests_passed']/(self.test_results['tests_passed']+self.test_results['tests_failed'])*100:.1f}%
        """)
        
        # Diagnostic
        if self.test_results['llm_responses'] == 0:
            print("\n⚠️  ATTENTION: Aucune réponse LLM détectée!")
            print("   Vérifiez que LMStudio est démarré et que le modèle qwen3-8b est chargé")
            print("   URL attendue: http://host.docker.internal:1234/v1")
        
        if self.test_results['messages_received'] < self.test_results['messages_sent']:
            print("\n⚠️  Certains messages n'ont pas été reçus")
            print("   Les agents doivent être en statut 'working' pour traiter les messages")


async def main():
    """Point d'entrée principal"""
    tester = MASCommunicationTester()
    await tester.run_complete_test()


if __name__ == "__main__":
    print("🔧 Configuration:")
    print(f"   API URL: {API_BASE_URL}")
    print(f"   LLM: LMStudio avec qwen3-8b")
    print("")
    
    asyncio.run(main())