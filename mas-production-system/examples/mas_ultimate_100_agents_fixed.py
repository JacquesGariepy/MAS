#!/usr/bin/env python3
"""
Version corrigée du script mas_ultimate_100_agents.py
Avec gestion d'erreurs améliorée et logs détaillés
"""

import requests
import json
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random
import sys

# Configuration
API_URL = "http://localhost:8088"
TARGET_AGENTS = 100
AGENTS_PER_USER = 10  # Quota par utilisateur

# Statistiques globales
stats = {
    "users_created": 0,
    "users_failed": 0,
    "agents_created": 0,
    "agents_failed": 0,
    "tasks_created": 0,
    "tasks_completed": 0,
    "messages_sent": 0,
    "memories_stored": 0,
    "negotiations_created": 0,
    "auctions_created": 0,
    "organizations_created": 0,
    "active": True
}

# Lock pour l'affichage thread-safe
print_lock = threading.Lock()

def safe_print(message):
    """Print thread-safe"""
    with print_lock:
        print(message)

class MAS100AgentsDemo:
    def __init__(self):
        self.base_url = API_URL
        self.users = {}
        self.all_agents = []
        self.tasks = {}
        self.organizations = {}
        self.debug = True  # Mode debug activé
        
    def verify_api_endpoints(self):
        """Vérifie la disponibilité des endpoints nécessaires"""
        safe_print("\n🔍 Vérification des endpoints API...")
        
        required_endpoints = {
            "/docs": "GET",
            "/auth/register": "POST",
            "/auth/token": "POST",
            "/api/v1/agents": "GET"
        }
        
        all_ok = True
        for endpoint, method in required_endpoints.items():
            try:
                url = f"{self.base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.options(url, timeout=5)
                
                if response.status_code < 500:
                    safe_print(f"   ✅ {method} {endpoint}: OK")
                else:
                    safe_print(f"   ❌ {method} {endpoint}: Erreur serveur ({response.status_code})")
                    all_ok = False
            except Exception as e:
                safe_print(f"   ❌ {method} {endpoint}: Non accessible ({type(e).__name__})")
                all_ok = False
        
        return all_ok
        
    def create_user_batch(self, start_index, count):
        """Crée un batch d'utilisateurs avec meilleure gestion d'erreurs"""
        created_users = []
        
        if self.debug:
            safe_print(f"\n🔍 Création de batch {start_index} à {start_index + count - 1}")
        
        for i in range(start_index, start_index + count):
            username = f"user_{int(time.time())}_{i}"
            email = f"{username}@mas100.com"
            password = "demo12345"  # Au moins 8 caractères
            
            try:
                # Enregistrement
                register_data = {
                    "username": username,
                    "email": email,
                    "password": password
                }
                
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json=register_data,
                    timeout=10
                )
                
                # Si l'utilisateur existe déjà (400) ou créé avec succès (201)
                if response.status_code in [201, 400]:
                    # Tentative de connexion
                    login_response = requests.post(
                        f"{self.base_url}/auth/token",
                        data={"username": username, "password": password},
                        timeout=10
                    )
                    
                    if login_response.status_code == 200:
                        try:
                            token_data = login_response.json()
                            if "access_token" in token_data:
                                token = token_data["access_token"]
                                self.users[username] = {
                                    "token": token,
                                    "agents": [],
                                    "agent_count": 0
                                }
                                created_users.append(username)
                                stats["users_created"] += 1
                                
                                if self.debug:
                                    safe_print(f"   ✅ Utilisateur {username} créé/connecté")
                            else:
                                stats["users_failed"] += 1
                                if self.debug:
                                    safe_print(f"   ❌ Pas de token pour {username}")
                        except json.JSONDecodeError:
                            stats["users_failed"] += 1
                            if self.debug:
                                safe_print(f"   ❌ Réponse invalide pour {username}")
                    else:
                        stats["users_failed"] += 1
                        if self.debug:
                            safe_print(f"   ❌ Échec connexion {username}: {login_response.status_code}")
                else:
                    stats["users_failed"] += 1
                    if self.debug:
                        safe_print(f"   ❌ Échec enregistrement {username}: {response.status_code}")
                        if response.status_code == 422:
                            try:
                                error_detail = response.json()
                                safe_print(f"      Détail: {error_detail}")
                            except:
                                pass
                        
            except requests.exceptions.RequestException as e:
                stats["users_failed"] += 1
                if self.debug:
                    safe_print(f"   ❌ Erreur réseau pour {username}: {type(e).__name__}")
            except Exception as e:
                stats["users_failed"] += 1
                if self.debug:
                    safe_print(f"   ❌ Erreur inattendue pour {username}: {e}")
        
        return created_users
    
    def create_agent_for_user(self, username, agent_config):
        """Crée un agent pour un utilisateur spécifique"""
        try:
            token = self.users[username]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Ajouter les champs obligatoires
            agent_config["initial_desires"] = agent_config.get("initial_desires", ["accomplir_mission", "collaborer"])
            agent_config["organization_id"] = None
            
            # S'assurer que reactive_rules est un dict pour les agents reflexifs
            if agent_config["agent_type"] == "reflexive" and "reactive_rules" not in agent_config:
                agent_config["reactive_rules"] = {}
            
            response = requests.post(
                f"{self.base_url}/api/v1/agents",
                json=agent_config,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                agent = response.json()
                self.users[username]["agents"].append(agent["id"])
                self.users[username]["agent_count"] += 1
                self.all_agents.append(agent)
                stats["agents_created"] += 1
                
                # Démarrer l'agent
                try:
                    requests.post(
                        f"{self.base_url}/api/v1/agents/{agent['id']}/start",
                        headers=headers,
                        timeout=5
                    )
                except:
                    pass  # Ne pas échouer si le démarrage échoue
                
                return agent
            else:
                stats["agents_failed"] += 1
                if self.debug:
                    safe_print(f"   ❌ Échec création agent: {response.status_code}")
                return None
                
        except Exception as e:
            stats["agents_failed"] += 1
            if self.debug:
                safe_print(f"   ❌ Erreur création agent: {e}")
            return None
    
    def generate_agent_configs(self, count):
        """Génère des configurations d'agents variées"""
        agent_types = ["cognitive", "reflexive", "hybrid"]
        roles = [
            "Analyste", "Développeur", "Architecte", "Chercheur", "Coordinateur",
            "Testeur", "Designer", "Formateur", "Support", "Auditeur",
            "Stratège", "Négociateur", "Médiateur", "Planificateur", "Optimiseur"
        ]
        
        capabilities_map = {
            "Analyste": ["analyse", "synthèse", "rapport"],
            "Développeur": ["programmation", "debugging", "optimisation"],
            "Architecte": ["conception", "modélisation", "documentation"],
            "Chercheur": ["recherche", "innovation", "expérimentation"],
            "Coordinateur": ["coordination", "planification", "suivi"],
            "Testeur": ["test", "validation", "rapport"],
            "Designer": ["conception", "créativité", "esthétique"],
            "Formateur": ["formation", "pédagogie", "communication"],
            "Support": ["support", "résolution", "communication"],
            "Auditeur": ["audit", "conformité", "analyse"],
            "Stratège": ["stratégie", "vision", "décision"],
            "Négociateur": ["négociation", "persuasion", "diplomatie"],
            "Médiateur": ["médiation", "consensus", "résolution"],
            "Planificateur": ["planification", "organisation", "priorisation"],
            "Optimiseur": ["optimisation", "performance", "efficacité"]
        }
        
        configs = []
        
        for i in range(count):
            role = roles[i % len(roles)]
            agent_type = agent_types[i % len(agent_types)]
            
            config = {
                "name": f"{role} {i+1}",
                "role": f"Spécialiste en {role.lower()}",
                "agent_type": agent_type,
                "capabilities": capabilities_map.get(role, ["général"]),
                "initial_beliefs": {
                    "rôle": role.lower(),
                    "expérience": random.choice(["junior", "intermédiaire", "senior"]),
                    "domaine": random.choice(["tech", "business", "recherche", "support"])
                },
                "configuration": {
                    "temperature": round(random.uniform(0.3, 0.9), 2),
                    "reasoning_depth": random.randint(3, 7),
                    "max_tokens": random.choice([1000, 2000, 4000])
                }
            }
            
            # Ajouter des reactive_rules pour les agents reflexifs
            if agent_type == "reflexive":
                config["reactive_rules"] = {
                    "on_task": "execute_immediately",
                    "on_error": "report_and_retry"
                }
            
            configs.append(config)
        
        return configs
    
    def run_mega_demo(self):
        """Lance la démonstration avec 100 agents"""
        safe_print("\n🚀 DÉMONSTRATION ULTIME MAS - 100 AGENTS")
        safe_print("="*80)
        
        # Vérifier les endpoints d'abord
        if not self.verify_api_endpoints():
            safe_print("\n❌ Certains endpoints nécessaires ne sont pas disponibles!")
            safe_print("   Vérifiez que l'API MAS est correctement démarrée.")
            return
        
        # Thread de monitoring
        monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        monitor_thread.start()
        
        try:
            # Phase 1: Créer suffisamment d'utilisateurs
            safe_print("\n📋 Phase 1: Création des utilisateurs")
            users_needed = (TARGET_AGENTS + AGENTS_PER_USER - 1) // AGENTS_PER_USER
            safe_print(f"   Création de {users_needed} utilisateurs pour {TARGET_AGENTS} agents...")
            
            # Création séquentielle pour éviter les problèmes de concurrence
            all_created_users = []
            batch_size = 5
            
            for i in range(0, users_needed, batch_size):
                current_batch_size = min(batch_size, users_needed - i)
                batch_users = self.create_user_batch(i, current_batch_size)
                all_created_users.extend(batch_users)
                
                if self.debug:
                    safe_print(f"   Batch {i//batch_size + 1}: {len(batch_users)} utilisateurs créés")
            
            safe_print(f"\n   📊 Résultat création utilisateurs:")
            safe_print(f"      ✅ Créés: {stats['users_created']}")
            safe_print(f"      ❌ Échoués: {stats['users_failed']}")
            
            if not all_created_users:
                safe_print("\n❌ Aucun utilisateur créé! Vérifiez l'API d'authentification.")
                return
            
            # Phase 2: Créer les agents
            safe_print(f"\n📋 Phase 2: Création de {TARGET_AGENTS} agents")
            
            # Générer les configurations
            agent_configs = self.generate_agent_configs(TARGET_AGENTS)
            
            # Distribuer les agents entre les utilisateurs disponibles
            agents_to_create = min(TARGET_AGENTS, len(all_created_users) * AGENTS_PER_USER)
            
            for i, config in enumerate(agent_configs[:agents_to_create]):
                # Sélectionner l'utilisateur
                user_index = i // AGENTS_PER_USER
                if user_index < len(all_created_users):
                    username = all_created_users[user_index]
                    agent = self.create_agent_for_user(username, config)
                    if agent and i % 10 == 0:  # Afficher tous les 10 agents
                        safe_print(f"   📊 {stats['agents_created']} agents créés...")
            
            safe_print(f"\n   📊 Résultat création agents:")
            safe_print(f"      ✅ Créés: {stats['agents_created']}")
            safe_print(f"      ❌ Échoués: {stats['agents_failed']}")
            
            # Suite de la démo seulement si on a des agents
            if stats['agents_created'] > 0:
                # Phase 3: Créer des tâches
                safe_print("\n📋 Phase 3: Création de tâches")
                self.create_demo_tasks()
                
                # Phase 4: Communications
                safe_print("\n📋 Phase 4: Communications inter-agents")
                self.create_demo_messages()
                
                # Phase 5: Mémoires
                safe_print("\n📋 Phase 5: Stockage de mémoires")
                self.create_demo_memories()
            
            # Attente finale
            time.sleep(5)
            
        except Exception as e:
            safe_print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Arrêter le monitoring
            stats["active"] = False
            
            # Résumé final
            self.print_final_summary()
    
    def create_demo_tasks(self):
        """Crée des tâches de démonstration"""
        task_types = ["analysis", "development", "research", "optimization", "documentation"]
        priorities = ["low", "medium", "high", "critical"]
        
        tasks_created = 0
        max_tasks = min(50, len(self.all_agents))
        
        for i in range(max_tasks):
            if i < len(self.all_agents):
                agent = self.all_agents[i]
                
                # Trouver le propriétaire
                owner_token = None
                for username, data in self.users.items():
                    if agent["id"] in data["agents"]:
                        owner_token = data["token"]
                        break
                
                if owner_token:
                    try:
                        headers = {"Authorization": f"Bearer {owner_token}"}
                        task_data = {
                            "title": f"Tâche {i+1}: {random.choice(['Analyser', 'Développer', 'Rechercher'])}",
                            "description": f"Description de la tâche {i+1}",
                            "task_type": task_types[i % len(task_types)],
                            "priority": priorities[i % len(priorities)],
                            "assigned_to": agent["id"]
                        }
                        
                        response = requests.post(
                            f"{self.base_url}/api/v1/v1/tasks",
                            json=task_data,
                            headers=headers,
                            timeout=5
                        )
                        
                        if response.status_code == 201:
                            stats["tasks_created"] += 1
                            tasks_created += 1
                    except:
                        pass
        
        safe_print(f"   ✅ {tasks_created} tâches créées")
    
    def create_demo_messages(self):
        """Crée des messages de démonstration"""
        if len(self.all_agents) < 2:
            return
        
        messages_sent = 0
        performatives = ["inform", "request", "propose", "accept", "reject", "query"]
        
        for i in range(min(100, len(self.all_agents) * 2)):
            try:
                sender = random.choice(self.all_agents)
                receiver = random.choice([a for a in self.all_agents if a["id"] != sender["id"]])
                
                # Trouver le token du propriétaire
                sender_token = None
                for username, data in self.users.items():
                    if sender["id"] in data["agents"]:
                        sender_token = data["token"]
                        break
                
                if sender_token:
                    headers = {"Authorization": f"Bearer {sender_token}"}
                    message_data = {
                        "receiver_id": receiver["id"],
                        "performative": random.choice(performatives),
                        "content": {"message": f"Message {i+1}"}
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/agents/{sender['id']}/messages",
                        json=message_data,
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 201:
                        stats["messages_sent"] += 1
                        messages_sent += 1
            except:
                pass
        
        safe_print(f"   ✅ {messages_sent} messages envoyés")
    
    def create_demo_memories(self):
        """Crée des mémoires de démonstration"""
        memories_stored = 0
        memory_types = ["semantic", "episodic", "working"]
        
        for i in range(min(150, len(self.all_agents) * 3)):
            try:
                agent = random.choice(self.all_agents)
                
                # Trouver le token
                agent_token = None
                for username, data in self.users.items():
                    if agent["id"] in data["agents"]:
                        agent_token = data["token"]
                        break
                
                if agent_token:
                    headers = {"Authorization": f"Bearer {agent_token}"}
                    memory_data = {
                        "content": f"Connaissance {i+1}: Pattern observé",
                        "memory_type": random.choice(memory_types),
                        "importance": round(random.uniform(0.5, 1.0), 2)
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/agents/{agent['id']}/memories",
                        json=memory_data,
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 201:
                        stats["memories_stored"] += 1
                        memories_stored += 1
            except:
                pass
        
        safe_print(f"   ✅ {memories_stored} mémoires stockées")
    
    def monitor_progress(self):
        """Thread de monitoring"""
        while stats["active"]:
            with print_lock:
                print(f"\n📊 Progression (à {datetime.now().strftime('%H:%M:%S')}):")
                print(f"   👥 Utilisateurs: {stats['users_created']} créés, {stats['users_failed']} échoués")
                print(f"   🤖 Agents: {stats['agents_created']}/{TARGET_AGENTS} ({stats['agents_failed']} échoués)")
                print(f"   📋 Tâches: {stats['tasks_created']} créées")
                print(f"   💬 Messages: {stats['messages_sent']}")
                print(f"   🧠 Mémoires: {stats['memories_stored']}")
            time.sleep(10)
    
    def print_final_summary(self):
        """Affiche le résumé final"""
        safe_print("\n" + "="*80)
        safe_print("📊 RÉSUMÉ FINAL - DÉMONSTRATION 100 AGENTS")
        safe_print("="*80)
        
        safe_print(f"""
   👥 Utilisateurs: {stats['users_created']} créés ({stats['users_failed']} échoués)
   🤖 Agents: {stats['agents_created']}/{TARGET_AGENTS} ({stats['agents_created']*100//TARGET_AGENTS if TARGET_AGENTS > 0 else 0}%)
   📋 Tâches créées: {stats['tasks_created']}
   💬 Messages échangés: {stats['messages_sent']}
   🧠 Mémoires stockées: {stats['memories_stored']}
   
   🎯 Statut: {'✅ SUCCÈS' if stats['agents_created'] > 0 else '❌ ÉCHEC'}
        """)
        
        if self.all_agents:
            safe_print("\n🤖 Échantillon d'agents créés:")
            for agent in self.all_agents[:5]:
                safe_print(f"   - {agent['name']} ({agent['agent_type']}) - {agent['role']}")
            
            if len(self.all_agents) > 5:
                safe_print(f"   ... et {len(self.all_agents) - 5} autres agents")

def main():
    """Point d'entrée principal"""
    print("🚀 DÉMONSTRATION ULTIME MAS - 100 AGENTS (VERSION CORRIGÉE)")
    print("   Cette démonstration va créer:")
    print(f"   - {TARGET_AGENTS} agents")
    print(f"   - ~{(TARGET_AGENTS + AGENTS_PER_USER - 1) // AGENTS_PER_USER} utilisateurs")
    print("   - Tâches, messages et mémoires")
    print()
    
    # Vérifier l'API
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        if response.status_code != 200:
            print("❌ L'API MAS n'est pas accessible sur", API_URL)
            print("   Vérifiez que le serveur est démarré avec: docker-compose up")
            return
    except Exception as e:
        print(f"❌ Impossible de se connecter à l'API: {e}")
        print("   Vérifiez que le serveur est démarré avec: docker-compose up")
        return
    
    # Lancer la démo
    demo = MAS100AgentsDemo()
    demo.run_mega_demo()

if __name__ == "__main__":
    main()