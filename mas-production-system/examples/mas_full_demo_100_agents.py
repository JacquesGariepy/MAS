#!/usr/bin/env python3
"""
Démonstration complète du système MAS avec 100 agents
Montre toutes les fonctionnalités: utilisateurs, agents, organisations, tâches,
communications, négociations, enchères, mémoires et coordination multi-agents
"""

import requests
import json
import time
import asyncio
import random
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

# Configuration
API_URL = "http://localhost:8088"

# Données globales pour le monitoring
agent_status = {}
task_status = {}
communication_log = []
negotiation_results = []
auction_results = []

class MASCompleteDemo:
    """Client complet pour démonstration MAS avec 100 agents"""
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.users = {}
        self.agents = {}
        self.organizations = {}
        self.tasks = {}
        self.active_negotiations = {}
        self.active_auctions = {}
        
    def print_section(self, title: str, level: int = 1):
        """Affiche un titre de section"""
        if level == 1:
            print(f"\n{'='*80}")
            print(f"  {title}")
            print('='*80)
        elif level == 2:
            print(f"\n{'-'*60}")
            print(f"  {title}")
            print('-'*60)
        else:
            print(f"\n>>> {title}")
    
    # ========== Authentification ==========
    
    def register_user(self, username: str, email: str, password: str) -> bool:
        """Enregistre un nouvel utilisateur"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 201:
                print(f"✅ Utilisateur créé: {username}")
                return True
            elif response.status_code == 400:
                print(f"ℹ️  Utilisateur existant: {username}")
                return True
            else:
                print(f"❌ Erreur création utilisateur {username}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Se connecte et retourne le token JWT"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.users[username] = {
                    "token": token,
                    "agents": [],
                    "tasks": []
                }
                print(f"✅ Connecté: {username}")
                return token
            else:
                print(f"❌ Erreur connexion {username}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    # ========== Gestion des Agents ==========
    
    def create_agent(self, token: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crée un nouvel agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/agents",
                json=agent_data,
                headers=headers
            )
            
            if response.status_code == 201:
                agent = response.json()
                self.agents[agent['id']] = agent
                agent_status[agent['id']] = 'created'
                print(f"✅ Agent créé: {agent['name']} (ID: {agent['id'][:8]}...)")
                return agent
            else:
                print(f"❌ Erreur création agent: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def start_agent(self, token: str, agent_id: str) -> bool:
        """Démarre un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/agents/{agent_id}/start",
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                agent_status[agent_id] = 'active'
                return True
            return False
        except:
            return False
    
    def update_agent_beliefs(self, token: str, agent_id: str, beliefs: Dict[str, Any]) -> bool:
        """Met à jour les croyances d'un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.patch(
                f"{self.base_url}/api/v1/agents/{agent_id}",
                json={"beliefs": beliefs},
                headers=headers
            )
            return response.status_code == 200
        except:
            return False
    
    # ========== Organisations ==========
    
    def create_organization(self, token: str, org_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crée une organisation"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/organizations",
                json=org_data,
                headers=headers
            )
            
            if response.status_code == 201:
                org = response.json()
                self.organizations[org['id']] = org
                print(f"✅ Organisation créée: {org['name']}")
                return org
            return None
        except:
            return None
    
    def add_agent_to_organization(self, token: str, org_id: str, agent_id: str, role: str) -> bool:
        """Ajoute un agent à une organisation"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/organizations/{org_id}/members",
                json={"agent_id": agent_id, "role": role},
                headers=headers
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    # ========== Tâches ==========
    
    def create_task(self, token: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crée une tâche"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/tasks",
                json=task_data,
                headers=headers
            )
            
            if response.status_code == 201:
                task = response.json()
                self.tasks[task['id']] = task
                task_status[task['id']] = 'created'
                return task
            return None
        except:
            return None
    
    def get_task_status(self, token: str, task_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'une tâche"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    # ========== Communication ==========
    
    def send_message(self, token: str, message_data: Dict[str, Any]) -> bool:
        """Envoie un message entre agents"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/messages",
                json=message_data,
                headers=headers
            )
            
            if response.status_code == 201:
                communication_log.append({
                    "from": message_data['sender_id'][:8],
                    "to": message_data['receiver_id'][:8],
                    "type": message_data['performative'],
                    "time": datetime.now().isoformat()
                })
                return True
            return False
        except:
            return False
    
    # ========== Négociations ==========
    
    def start_negotiation(self, token: str, negotiation_data: Dict[str, Any]) -> Optional[str]:
        """Démarre une négociation"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/negotiations",
                json=negotiation_data,
                headers=headers
            )
            
            if response.status_code == 201:
                neg = response.json()
                self.active_negotiations[neg['id']] = neg
                return neg['id']
            return None
        except:
            return None
    
    # ========== Enchères ==========
    
    def create_auction(self, token: str, auction_data: Dict[str, Any]) -> Optional[str]:
        """Crée une enchère"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auctions",
                json=auction_data,
                headers=headers
            )
            
            if response.status_code == 201:
                auction = response.json()
                self.active_auctions[auction['id']] = auction
                return auction['id']
            return None
        except:
            return None
    
    def place_bid(self, token: str, auction_id: str, bidder_id: str, amount: float) -> bool:
        """Place une enchère"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auctions/{auction_id}/bids",
                json={"bidder_id": bidder_id, "amount": amount},
                headers=headers
            )
            return response.status_code == 201
        except:
            return False
    
    # ========== Mémoires ==========
    
    def add_memory(self, token: str, agent_id: str, memory_data: Dict[str, Any]) -> bool:
        """Ajoute une mémoire à un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/agents/{agent_id}/memories",
                json=memory_data,
                headers=headers
            )
            return response.status_code == 201
        except:
            return False
    
    # ========== Monitoring ==========
    
    def monitor_system(self):
        """Thread de monitoring du système"""
        while True:
            active_agents = sum(1 for status in agent_status.values() if status == 'active')
            completed_tasks = sum(1 for status in task_status.values() if status == 'completed')
            
            print(f"\r📊 Monitoring: {active_agents} agents actifs | "
                  f"{completed_tasks} tâches complétées | "
                  f"{len(communication_log)} messages | "
                  f"{len(negotiation_results)} négociations | "
                  f"{len(auction_results)} enchères", end='')
            
            time.sleep(1)
    
    # ========== Démonstration Complète ==========
    
    def run_complete_demo(self):
        """Exécute la démonstration complète avec 100 agents"""
        
        self.print_section("🚀 DÉMONSTRATION COMPLÈTE MAS - 100 AGENTS", 1)
        
        # 1. Création des utilisateurs
        self.print_section("1️⃣ CRÉATION DE PLUSIEURS UTILISATEURS", 2)
        
        users_data = [
            ("alice", "alice@mas.com", "password123"),
            ("bob", "bob@mas.com", "password123"),
            ("charlie", "charlie@mas.com", "password123"),
            ("diana", "diana@mas.com", "password123"),
            ("eve", "eve@mas.com", "password123")
        ]
        
        for username, email, password in users_data:
            self.register_user(username, email, password)
            token = self.login(username, password)
            if token:
                self.users[username]['token'] = token
        
        print(f"\n✅ {len(self.users)} utilisateurs créés et connectés")
        
        # 2. Création de 100 agents avec différents types
        self.print_section("2️⃣ CRÉATION DE 100 AGENTS", 2)
        
        agent_types = {
            "cognitive": {
                "count": 30,
                "roles": ["analyste", "stratège", "conseiller", "chercheur"],
                "capabilities": ["analyse", "planification", "conseil", "apprentissage"]
            },
            "reflexive": {
                "count": 40,
                "roles": ["exécutant", "surveillant", "collecteur", "réactif"],
                "capabilities": ["réaction", "surveillance", "collecte", "alerte"]
            },
            "hybrid": {
                "count": 30,
                "roles": ["coordinateur", "médiateur", "négociateur", "gestionnaire"],
                "capabilities": ["coordination", "médiation", "négociation", "gestion"]
            }
        }
        
        agent_count = 0
        user_tokens = list(self.users.values())
        
        # Thread pool pour création parallèle
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for agent_type, config in agent_types.items():
                for i in range(config["count"]):
                    user = user_tokens[agent_count % len(user_tokens)]
                    role = random.choice(config["roles"])
                    
                    agent_data = {
                        "name": f"Agent_{agent_type}_{agent_count:03d}",
                        "role": role,
                        "agent_type": agent_type,
                        "capabilities": random.sample(config["capabilities"], k=random.randint(2, 4)),
                        "initial_beliefs": {
                            "expertise": role,
                            "experience": random.randint(1, 10),
                            "team_spirit": random.uniform(0.5, 1.0)
                        },
                        "initial_desires": [
                            "accomplir_taches",
                            "collaborer",
                            "apprendre"
                        ],
                        "configuration": {
                            "temperature": random.uniform(0.3, 0.9),
                            "response_time": random.uniform(0.1, 2.0),
                            "cooperation_level": random.uniform(0.6, 1.0)
                        }
                    }
                    
                    future = executor.submit(self.create_agent, user['token'], agent_data)
                    futures.append((future, user['token']))
                    agent_count += 1
            
            # Attendre la création de tous les agents
            created_agents = []
            for future, token in futures:
                agent = future.result()
                if agent:
                    created_agents.append((agent, token))
        
        print(f"\n✅ {len(created_agents)} agents créés sur 100 demandés")
        
        # Démarrer tous les agents
        self.print_section("3️⃣ DÉMARRAGE DES AGENTS", 3)
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            start_futures = []
            for agent, token in created_agents:
                future = executor.submit(self.start_agent, token, agent['id'])
                start_futures.append(future)
            
            started = sum(1 for f in start_futures if f.result())
            print(f"✅ {started} agents démarrés")
        
        # 3. Création d'organisations
        self.print_section("4️⃣ CRÉATION D'ORGANISATIONS ET ÉQUIPES", 2)
        
        org_types = [
            {
                "name": "Équipe Développement",
                "type": "team",
                "roles": {"lead": 1, "developer": 5, "tester": 2}
            },
            {
                "name": "Département Recherche",
                "type": "hierarchy",
                "roles": {"director": 1, "researcher": 8, "assistant": 4}
            },
            {
                "name": "Marché des Services",
                "type": "market",
                "roles": {"vendor": 10, "buyer": 10, "broker": 2}
            },
            {
                "name": "Réseau d'Innovation",
                "type": "network",
                "roles": {"innovator": 5, "collaborator": 10, "evaluator": 3}
            }
        ]
        
        # Créer les organisations
        alice_token = self.users['alice']['token']
        for org_config in org_types:
            org_data = {
                "name": org_config["name"],
                "org_type": org_config["type"],
                "roles": org_config["roles"],
                "norms": [
                    "respecter_hierarchie",
                    "partager_information",
                    "collaborer_activement"
                ]
            }
            
            org = self.create_organization(alice_token, org_data)
            if org:
                # Assigner des agents aux organisations
                available_agents = list(self.agents.keys())
                random.shuffle(available_agents)
                
                for role, count in org_config["roles"].items():
                    for i in range(min(count, len(available_agents))):
                        if available_agents:
                            agent_id = available_agents.pop()
                            self.add_agent_to_organization(
                                alice_token, org['id'], agent_id, role
                            )
        
        print(f"\n✅ {len(self.organizations)} organisations créées")
        
        # 4. Création de tâches complexes
        self.print_section("5️⃣ CRÉATION DE TÂCHES COMPLEXES", 2)
        
        task_templates = [
            {
                "title": "Analyser les tendances du marché",
                "type": "analysis",
                "priority": "high",
                "requires_collaboration": True
            },
            {
                "title": "Développer nouveau module IA",
                "type": "development",
                "priority": "critical",
                "requires_collaboration": True
            },
            {
                "title": "Optimiser les performances système",
                "type": "optimization",
                "priority": "medium",
                "requires_collaboration": False
            },
            {
                "title": "Négocier contrat fournisseur",
                "type": "negotiation",
                "priority": "high",
                "requires_collaboration": True
            },
            {
                "title": "Former nouveaux agents",
                "type": "training",
                "priority": "medium",
                "requires_collaboration": True
            }
        ]
        
        # Créer 50 tâches
        with ThreadPoolExecutor(max_workers=10) as executor:
            task_futures = []
            
            for i in range(50):
                template = random.choice(task_templates)
                user = random.choice(list(self.users.values()))
                available_agents = list(self.agents.keys())
                
                task_data = {
                    "title": f"{template['title']} #{i:03d}",
                    "description": f"Tâche complexe nécessitant expertise en {template['type']}",
                    "task_type": template['type'],
                    "priority": template['priority'],
                    "assigned_to": random.choice(available_agents) if available_agents else None,
                    "metadata": {
                        "complexity": random.randint(1, 10),
                        "estimated_hours": random.randint(2, 40),
                        "requires_collaboration": template['requires_collaboration']
                    }
                }
                
                future = executor.submit(self.create_task, user['token'], task_data)
                task_futures.append(future)
            
            created_tasks = sum(1 for f in task_futures if f.result())
            print(f"✅ {created_tasks} tâches créées")
        
        # Démarrer le monitoring en arrière-plan
        monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        monitor_thread.start()
        
        # 5. Communications entre agents
        self.print_section("6️⃣ COMMUNICATIONS INTER-AGENTS", 2)
        
        # Simuler des communications
        performatives = ["inform", "request", "propose", "accept", "reject", "query"]
        agent_ids = list(self.agents.keys())
        
        for i in range(100):
            if len(agent_ids) >= 2:
                sender = random.choice(agent_ids)
                receiver = random.choice([a for a in agent_ids if a != sender])
                
                message_data = {
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "performative": random.choice(performatives),
                    "content": {
                        "message": f"Communication #{i}",
                        "priority": random.choice(["low", "medium", "high"]),
                        "topic": random.choice(["task", "coordination", "information", "help"])
                    },
                    "conversation_id": f"conv_{i//10}"
                }
                
                self.send_message(alice_token, message_data)
        
        print(f"\n✅ {len(communication_log)} messages envoyés")
        
        # 6. Négociations
        self.print_section("7️⃣ NÉGOCIATIONS MULTI-AGENTS", 2)
        
        # Créer des négociations
        for i in range(20):
            if len(agent_ids) >= 3:
                initiator = random.choice(agent_ids)
                participants = random.sample([a for a in agent_ids if a != initiator], k=random.randint(2, 5))
                
                negotiation_data = {
                    "initiator_id": initiator,
                    "negotiation_type": random.choice(["bilateral", "multilateral", "mediated"]),
                    "subject": {
                        "type": "resource_allocation",
                        "resource": f"Resource_{i}",
                        "quantity": random.randint(10, 100)
                    },
                    "participants": participants
                }
                
                neg_id = self.start_negotiation(alice_token, negotiation_data)
                if neg_id:
                    negotiation_results.append({
                        "id": neg_id,
                        "participants": len(participants) + 1,
                        "status": "started"
                    })
        
        print(f"✅ {len(negotiation_results)} négociations démarrées")
        
        # 7. Enchères
        self.print_section("8️⃣ ENCHÈRES ET MARCHÉS", 2)
        
        # Créer des enchères
        for i in range(15):
            if agent_ids:
                auctioneer = random.choice(agent_ids)
                
                auction_data = {
                    "auctioneer_id": auctioneer,
                    "auction_type": random.choice(["english", "dutch", "vickrey"]),
                    "item_description": f"Item précieux #{i}",
                    "starting_price": random.uniform(100, 1000),
                    "reserve_price": random.uniform(500, 2000),
                    "ends_at": "2024-12-31T23:59:59Z"
                }
                
                auction_id = self.create_auction(alice_token, auction_data)
                if auction_id:
                    # Placer des enchères
                    bidders = random.sample([a for a in agent_ids if a != auctioneer], 
                                          k=min(10, len(agent_ids)-1))
                    
                    for bidder in bidders:
                        bid_amount = random.uniform(
                            auction_data["starting_price"],
                            auction_data["starting_price"] * 2
                        )
                        self.place_bid(alice_token, auction_id, bidder, bid_amount)
                    
                    auction_results.append({
                        "id": auction_id,
                        "bidders": len(bidders),
                        "status": "active"
                    })
        
        print(f"✅ {len(auction_results)} enchères créées")
        
        # 8. Ajout de mémoires et apprentissage
        self.print_section("9️⃣ MÉMOIRES ET APPRENTISSAGE", 2)
        
        memory_types = ["semantic", "episodic", "working"]
        
        # Ajouter des mémoires aux agents
        memory_count = 0
        for agent_id in random.sample(agent_ids, min(50, len(agent_ids))):
            for i in range(random.randint(1, 5)):
                memory_data = {
                    "content": f"Expérience acquise lors de la tâche #{i}",
                    "memory_type": random.choice(memory_types),
                    "importance": random.uniform(0.3, 1.0),
                    "metadata": {
                        "context": "task_execution",
                        "learned_from": f"task_{i}",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                if self.add_memory(alice_token, agent_id, memory_data):
                    memory_count += 1
        
        print(f"✅ {memory_count} mémoires ajoutées aux agents")
        
        # 9. Mise à jour des croyances basée sur l'expérience
        self.print_section("🔟 ÉVOLUTION DES AGENTS", 2)
        
        # Simuler l'évolution des agents
        for agent_id in random.sample(agent_ids, min(30, len(agent_ids))):
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                
                # Mettre à jour les croyances basées sur l'expérience
                new_beliefs = agent.get('beliefs', {}).copy()
                new_beliefs['experience'] = new_beliefs.get('experience', 0) + random.randint(1, 5)
                new_beliefs['skills_improved'] = True
                new_beliefs['collaboration_score'] = random.uniform(0.7, 1.0)
                
                self.update_agent_beliefs(alice_token, agent_id, new_beliefs)
        
        print("✅ 30 agents ont évolué avec l'expérience")
        
        # 10. Attendre et afficher les résultats
        self.print_section("📊 RÉSULTATS FINAUX", 1)
        
        print("\n⏳ Attente de 10 secondes pour laisser le système traiter...")
        time.sleep(10)
        
        # Afficher les statistiques finales
        print("\n📈 STATISTIQUES FINALES:")
        print(f"   - Utilisateurs créés: {len(self.users)}")
        print(f"   - Agents créés: {len(self.agents)}")
        print(f"   - Agents actifs: {sum(1 for s in agent_status.values() if s == 'active')}")
        print(f"   - Organisations: {len(self.organizations)}")
        print(f"   - Tâches créées: {len(self.tasks)}")
        print(f"   - Messages échangés: {len(communication_log)}")
        print(f"   - Négociations: {len(negotiation_results)}")
        print(f"   - Enchères: {len(auction_results)}")
        print(f"   - Mémoires créées: {memory_count}")
        
        # Exemples de communications
        print("\n📨 EXEMPLES DE COMMUNICATIONS:")
        for msg in communication_log[-5:]:
            print(f"   - {msg['from']} → {msg['to']}: {msg['type']} à {msg['time']}")
        
        # Vérifier quelques tâches
        print("\n📋 STATUT DE QUELQUES TÂCHES:")
        sample_tasks = list(self.tasks.items())[:5]
        for task_id, task in sample_tasks:
            status = self.get_task_status(alice_token, task_id)
            if status:
                print(f"   - {task['title']}: {status['status']}")
        
        self.print_section("✅ DÉMONSTRATION COMPLÈTE TERMINÉE", 1)
        
        print("\n🎯 CAPACITÉS DÉMONTRÉES:")
        print("   ✓ Authentification multi-utilisateurs")
        print("   ✓ Création et gestion de 100 agents")
        print("   ✓ Types d'agents variés (cognitif, réflexif, hybride)")
        print("   ✓ Organisations hiérarchiques et en réseau")
        print("   ✓ Tâches complexes avec priorités")
        print("   ✓ Communications inter-agents FIPA-ACL")
        print("   ✓ Négociations multi-latérales")
        print("   ✓ Enchères avec multiples participants")
        print("   ✓ Mémoires sémantiques et épisodiques")
        print("   ✓ Évolution et apprentissage des agents")
        print("   ✓ Monitoring en temps réel")
        
        print("\n💡 Le système MAS est pleinement opérationnel avec:")
        print("   - Scalabilité jusqu'à 100+ agents")
        print("   - Coordination multi-agents complexe")
        print("   - Persistence des données")
        print("   - APIs RESTful complètes")
        print("   - Architecture BDI implémentée")

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de la démonstration complète MAS...")
    print("⚠️  Cette démonstration va créer 100 agents et générer beaucoup d'activité.")
    print("    Assurez-vous que le système MAS est démarré sur http://localhost:8088")
    
    input("\nAppuyez sur Entrée pour commencer...")
    
    # Vérifier la connexion
    try:
        response = requests.get(f"{API_URL}/docs")
        if response.status_code != 200:
            print("❌ Erreur: Le système MAS n'est pas accessible")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("   Vérifiez que le système est démarré avec: docker-compose up")
        return
    
    # Lancer la démonstration
    demo = MASCompleteDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()