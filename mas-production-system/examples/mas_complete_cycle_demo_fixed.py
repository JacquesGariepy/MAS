#!/usr/bin/env python3
"""
Script de démonstration complet du système MAS v2.0
Avec support pour TOUS les types d'agents (cognitive, reflexive, hybrid)
"""

import asyncio
import httpx
import json
import random
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Configuration
import os
if os.path.exists('/.dockerenv'):
    # Dans Docker
    API_BASE_URL = "http://core:8000/api/v1"
else:
    # En local avec docker-compose.dev.yml
    API_BASE_URL = "http://localhost:8088/api/v1"


class MASCompleteDemo:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.users = {}
        self.tokens = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_api_health(self) -> bool:
        """Vérifier que l'API est accessible"""
        try:
            response = await self.client.get(f"{API_BASE_URL.replace('/api/v1', '')}/docs")
            return response.status_code == 200
        except:
            return False
    
    async def register_user(self, username: str, email: str, password: str) -> Dict:
        """Enregistrer un nouvel utilisateur"""
        # Auth est à la racine, pas sous /api/v1
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
            return None
            
        data = response.json()
        return data["access_token"]
    
    async def create_agent(self, token: str, agent_data: Dict) -> Optional[Dict]:
        """Créer un agent avec gestion d'erreur améliorée"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents",
            json=agent_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"⚠️  Impossible de créer l'agent {agent_data['name']} (type: {agent_data['agent_type']})")
            return None
            
        return response.json()
    
    async def send_message(self, token: str, sender_id: str, receiver_id: str, 
                          performative: str, content: Dict) -> Optional[Dict]:
        """Envoyer un message entre agents"""
        headers = {"Authorization": f"Bearer {token}"}
        
        message_data = {
            "receiver_id": receiver_id,
            "performative": performative,
            "content": content,
            "conversation_id": str(uuid4())
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents/{sender_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"⚠️  Erreur lors de l'envoi du message: {response.status_code}")
            return None
            
        return response.json()
    
    async def create_task(self, token: str, task_data: Dict) -> Optional[Dict]:
        """Créer une tâche"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.client.post(
            f"{API_BASE_URL}/tasks",
            json=task_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"⚠️  Erreur lors de la création de la tâche: {response.status_code}")
            return None
            
        return response.json()
    
    async def create_memory(self, token: str, agent_id: str, content: str, 
                           memory_type: str = "semantic") -> Optional[Dict]:
        """Créer une mémoire pour un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "importance": random.uniform(0.5, 1.0),
            "metadata": {
                "source": "demo_script",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents/{agent_id}/memories",
            json=memory_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"⚠️  Erreur lors de la création de la mémoire: {response.status_code}")
            return None
            
        return response.json()
    
    async def run_complete_cycle(self):
        """Exécuter le cycle complet de démonstration"""
        print("\n" + "="*80)
        print("🚀 DÉMONSTRATION COMPLÈTE DU SYSTÈME MAS v2.0")
        print("   Avec support pour TOUS les types d'agents")
        print("="*80)
        
        # Vérifier l'API
        if not await self.check_api_health():
            print("❌ L'API MAS n'est pas accessible sur http://localhost:8000")
            print("   Assurez-vous que les services sont démarrés avec: docker-compose up -d")
            return
        
        print("✅ API MAS accessible")
        
        # 1. Créer les utilisateurs
        print("\n📝 Étape 1: Création des utilisateurs")
        print("-" * 40)
        
        # Alice
        alice = await self.register_user("alice", "alice@mas.ai", "alice12345")
        if alice:
            self.users["alice"] = {"info": alice, "agents": []}
            alice_token = await self.login_user("alice", "alice12345")
            if alice_token:
                self.tokens["alice"] = alice_token
                print("✅ Alice créée et connectée")
        
        # Bob
        bob = await self.register_user("bob", "bob@mas.ai", "bob12345")
        if bob:
            self.users["bob"] = {"info": bob, "agents": []}
            bob_token = await self.login_user("bob", "bob12345")
            if bob_token:
                self.tokens["bob"] = bob_token
                print("✅ Bob créé et connecté")
        
        # Charlie
        charlie = await self.register_user("charlie", "charlie@mas.ai", "charlie12345")
        if charlie:
            self.users["charlie"] = {"info": charlie, "agents": []}
            charlie_token = await self.login_user("charlie", "charlie12345")
            if charlie_token:
                self.tokens["charlie"] = charlie_token
                print("✅ Charlie créé et connecté")
        
        # 2. Créer des agents de différents types
        print("\n🤖 Étape 2: Création des agents (tous types)")
        print("-" * 40)
        
        # Agents d'Alice - Types cognitifs et hybrides
        alice_agents_config = [
            {
                "name": "Alice_Strategist",
                "role": "Strategic Planner",
                "agent_type": "reactive",  # Cognitive
                "capabilities": ["strategic_planning", "decision_making", "analysis"],
                "configuration": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "planning_horizon": "long_term"
                }
            },
            {
                "name": "Alice_Coordinator",
                "role": "Team Coordinator",
                "agent_type": "hybrid",
                "capabilities": ["coordination", "task_distribution", "monitoring"],
                "configuration": {
                    "complexity_threshold": 0.6,
                    "learning_rate": 0.1
                },
                "reactive_rules": {
                    "urgent_task": {
                        "condition": {"priority": "critical"},
                        "action": {"type": "immediate_response", "content": "Handling urgent task"}
                    }
                }
            }
        ]
        
        # Agents de Bob - Types réflexifs et cognitifs
        bob_agents_config = [
            {
                "name": "Bob_Monitor",
                "role": "System Monitor",
                "agent_type": "reflexive",
                "capabilities": ["monitoring", "alerting", "quick_response"],
                "reactive_rules": {
                    "high_alert": {
                        "condition": {"alert_level": "high", "priority": 1},
                        "action": {"type": "notify", "content": "High priority alert!", "response_time": "immediate"}
                    },
                    "status_check": {
                        "condition": {"request_type": "status", "priority": 2},
                        "action": {"type": "report", "content": "System operational"}
                    }
                }
            },
            {
                "name": "Bob_Analyst",
                "role": "Data Analyst",
                "agent_type": "reactive",  # Cognitive
                "capabilities": ["data_analysis", "pattern_recognition", "reporting"],
                "configuration": {
                    "model": "gpt-3.5-turbo",
                    "analysis_depth": "comprehensive"
                }
            }
        ]
        
        # Agents de Charlie - Types hybrides et réflexifs
        charlie_agents_config = [
            {
                "name": "Charlie_Optimizer",
                "role": "Performance Optimizer",
                "agent_type": "hybrid",
                "capabilities": ["optimization", "learning", "adaptation"],
                "configuration": {
                    "complexity_threshold": 0.5,
                    "adaptive_mode": True,
                    "optimization_target": "efficiency"
                },
                "reactive_rules": {
                    "quick_opt": {
                        "condition": {"optimization_type": "simple"},
                        "action": {"type": "apply", "content": "Quick optimization applied"}
                    }
                }
            },
            {
                "name": "Charlie_Responder",
                "role": "Quick Responder",
                "agent_type": "reflexive",
                "capabilities": ["fast_response", "rule_execution", "notification"],
                "reactive_rules": {
                    "greeting": {
                        "condition": {"message_type": "greeting", "priority": 3},
                        "action": {"type": "respond", "content": "Hello! Ready to assist."}
                    },
                    "emergency": {
                        "condition": {"emergency": True, "priority": 1},
                        "action": {"type": "escalate", "content": "Emergency protocol activated!"}
                    }
                }
            }
        ]
        
        # Créer les agents pour chaque utilisateur
        agent_creation_stats = {"reactive": 0, "reflexive": 0, "hybrid": 0}
        
        # Agents d'Alice
        if "alice" in self.tokens:
            for agent_config in alice_agents_config:
                agent = await self.create_agent(self.tokens["alice"], agent_config)
                if agent:
                    self.users["alice"]["agents"].append(agent)
                    agent_creation_stats[agent["agent_type"]] += 1
                    print(f"✅ Alice: {agent['name']} créé (Type: {agent['agent_type']})")
        
        # Agents de Bob
        if "bob" in self.tokens:
            for agent_config in bob_agents_config:
                agent = await self.create_agent(self.tokens["bob"], agent_config)
                if agent:
                    self.users["bob"]["agents"].append(agent)
                    agent_creation_stats[agent["agent_type"]] += 1
                    print(f"✅ Bob: {agent['name']} créé (Type: {agent['agent_type']})")
        
        # Agents de Charlie
        if "charlie" in self.tokens:
            for agent_config in charlie_agents_config:
                agent = await self.create_agent(self.tokens["charlie"], agent_config)
                if agent:
                    self.users["charlie"]["agents"].append(agent)
                    agent_creation_stats[agent["agent_type"]] += 1
                    print(f"✅ Charlie: {agent['name']} créé (Type: {agent['agent_type']})")
        
        total_agents = sum(agent_creation_stats.values())
        print(f"\n📊 Agents créés par type:")
        print(f"   - Cognitifs (reactive): {agent_creation_stats['reactive']}")
        print(f"   - Réflexifs: {agent_creation_stats['reflexive']}")
        print(f"   - Hybrides: {agent_creation_stats['hybrid']}")
        print(f"   - Total: {total_agents}")
        
        # 3. Communication entre agents
        print("\n💬 Étape 3: Communication inter-agents")
        print("-" * 40)
        
        messages_sent = 0
        alice_agents = self.users.get("alice", {}).get("agents", [])
        bob_agents = self.users.get("bob", {}).get("agents", [])
        charlie_agents = self.users.get("charlie", {}).get("agents", [])
        
        # Test de communication entre différents types
        # 1. Cognitive -> Reflexive
        if alice_agents and bob_agents:
            cognitive_agent = next((a for a in alice_agents if a["agent_type"] == "reactive"), None)
            reflexive_agent = next((a for a in bob_agents if a["agent_type"] == "reflexive"), None)
            
            if cognitive_agent and reflexive_agent:
                msg = await self.send_message(
                    self.tokens["alice"],
                    cognitive_agent["id"],
                    reflexive_agent["id"],
                    "request",
                    {"request_type": "status", "message": "What's the current system status?"}
                )
                if msg:
                    messages_sent += 1
                    print("✅ Message envoyé: Cognitive -> Reflexive (status check)")
        
        # 2. Reflexive -> Hybrid
        if bob_agents and charlie_agents:
            reflexive_agent = next((a for a in bob_agents if a["agent_type"] == "reflexive"), None)
            hybrid_agent = next((a for a in charlie_agents if a["agent_type"] == "hybrid"), None)
            
            if reflexive_agent and hybrid_agent:
                msg = await self.send_message(
                    self.tokens["bob"],
                    reflexive_agent["id"],
                    hybrid_agent["id"],
                    "inform",
                    {"alert_level": "medium", "optimization_type": "simple", "data": {"cpu": 75, "memory": 60}}
                )
                if msg:
                    messages_sent += 1
                    print("✅ Message envoyé: Reflexive -> Hybrid (optimization request)")
        
        # 3. Hybrid -> Cognitive
        if charlie_agents and alice_agents:
            hybrid_agent = next((a for a in charlie_agents if a["agent_type"] == "hybrid"), None)
            cognitive_agent = next((a for a in alice_agents if a["agent_type"] == "reactive"), None)
            
            if hybrid_agent and cognitive_agent:
                msg = await self.send_message(
                    self.tokens["charlie"],
                    hybrid_agent["id"],
                    cognitive_agent["id"],
                    "propose",
                    {"optimization_plan": "resource_reallocation", "expected_gain": "25%", "complexity": "high"}
                )
                if msg:
                    messages_sent += 1
                    print("✅ Message envoyé: Hybrid -> Cognitive (optimization proposal)")
        
        print(f"\n📨 Total messages envoyés: {messages_sent}")
        
        # 4. Créer des tâches
        print("\n📋 Étape 4: Création de tâches")
        print("-" * 40)
        
        tasks_created = 0
        
        task_configs = [
            {
                "title": "Analyser les performances du système",
                "description": "Analyse complète des métriques de performance",
                "task_type": "analysis",
                "priority": "high"
            },
            {
                "title": "Optimiser l'allocation des ressources",
                "description": "Optimisation basée sur les patterns détectés",
                "task_type": "optimization",
                "priority": "medium"
            },
            {
                "title": "Coordonner la réponse aux alertes",
                "description": "Mise en place d'un protocole de réponse rapide",
                "task_type": "coordination",
                "priority": "critical"
            }
        ]
        
        for i, (username, token) in enumerate(self.tokens.items()):
            if i < len(task_configs):
                task = await self.create_task(token, task_configs[i])
                if task:
                    tasks_created += 1
                    print(f"✅ {username}: Tâche '{task_configs[i]['title']}' créée")
        
        print(f"\n📊 Total tâches créées: {tasks_created}")
        
        # 5. Créer des mémoires
        print("\n🧠 Étape 5: Stockage de mémoires")
        print("-" * 40)
        
        memories_created = 0
        
        memory_contents = [
            "Learned optimization pattern: CPU usage peaks at 14:00 daily",
            "Strategic insight: Resource allocation improved by 20% with new algorithm",
            "Alert pattern: False positives reduced by implementing threshold adjustment",
            "Coordination success: Multi-agent task completion time reduced by 35%",
            "System knowledge: Database queries optimized with new indexing strategy",
            "Behavioral pattern: User activity highest on weekdays 9-17h"
        ]
        
        for username, user_data in self.users.items():
            if username in self.tokens:
                for agent in user_data.get("agents", []):
                    content = random.choice(memory_contents)
                    memory = await self.create_memory(
                        self.tokens[username],
                        agent["id"],
                        f"{agent['name']}: {content}"
                    )
                    if memory:
                        memories_created += 1
        
        print(f"✅ {memories_created} mémoires créées pour les agents")
        
        # 6. Résumé final
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
        print("="*80)
        print(f"✅ Utilisateurs créés: {len(self.users)}")
        print(f"✅ Agents créés: {total_agents}")
        print(f"   - Cognitifs: {agent_creation_stats['reactive']}")
        print(f"   - Réflexifs: {agent_creation_stats['reflexive']}")
        print(f"   - Hybrides: {agent_creation_stats['hybrid']}")
        print(f"✅ Messages envoyés: {messages_sent}")
        print(f"✅ Tâches créées: {tasks_created}")
        print(f"✅ Mémoires stockées: {memories_created}")
        
        if agent_creation_stats['reflexive'] > 0 and agent_creation_stats['hybrid'] > 0:
            print("\n🎉 SUCCÈS: Tous les types d'agents sont maintenant opérationnels!")
            print("   Le système MAS v2.0 est pleinement fonctionnel avec:")
            print("   - Agents cognitifs pour le raisonnement complexe")
            print("   - Agents réflexifs pour les réponses rapides")
            print("   - Agents hybrides pour l'adaptation dynamique")
        else:
            print("\n⚠️  Attention: Certains types d'agents n'ont pas pu être créés")
            print("   Vérifiez que le serveur a été redémarré après l'ajout des nouveaux types")
        
        print("\n💡 Prochaines étapes:")
        print("   1. Redémarrer le serveur: docker-compose restart core")
        print("   2. Exécuter: python3 test_all_agent_types.py")
        print("   3. Observer les interactions multi-agents en temps réel")
        print("="*80)


async def main():
    """Fonction principale"""
    async with MASCompleteDemo() as demo:
        await demo.run_complete_cycle()


if __name__ == "__main__":
    asyncio.run(main())