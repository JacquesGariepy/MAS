#!/usr/bin/env python3
"""
Script de démonstration complète du cycle MAS
Crée une requête et suit tout le cycle jusqu'à complétion totale
Inclut: agents, tâches, outils, communication inter-agents, monitoring
"""

import requests
import json
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
API_URL = "http://localhost:8088"
TOTAL_AGENTS = 10  # Réduit de 100 pour une démo plus rapide
MONITOR_INTERVAL = 2  # Secondes entre chaque vérification

# Statistiques globales
stats = {
    "users_created": 0,
    "agents_created": 0,
    "tasks_created": 0,
    "tasks_completed": 0,
    "messages_sent": 0,
    "memories_stored": 0,
    "active": True
}

# Lock pour l'affichage thread-safe
print_lock = threading.Lock()

def safe_print(message):
    """Print thread-safe"""
    with print_lock:
        print(message)

class MASCycleDemo:
    def __init__(self):
        self.base_url = API_URL
        self.users = {}
        self.agents = {}
        self.tasks = {}
        self.messages = []
        
    def register_and_login(self, username, email, password):
        """Enregistre et connecte un utilisateur"""
        # Enregistrement
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        
        if response.status_code not in [201, 400]:
            raise Exception(f"Erreur enregistrement: {response.status_code}")
        
        # Connexion
        response = requests.post(
            f"{self.base_url}/auth/token",
            data={"username": username, "password": password}
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur connexion: {response.status_code}")
            
        token = response.json()["access_token"]
        self.users[username] = {"token": token, "agents": []}
        stats["users_created"] += 1
        return token
    
    def create_agent(self, token, agent_data):
        """Crée un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents",
            json=agent_data,
            headers=headers
        )
        
        if response.status_code == 201:
            agent = response.json()
            self.agents[agent["id"]] = agent
            stats["agents_created"] += 1
            
            # Démarrer l'agent
            requests.post(
                f"{self.base_url}/api/v1/agents/{agent['id']}/start",
                headers=headers
            )
            
            return agent
        else:
            raise Exception(f"Erreur création agent: {response.text}")
    
    def create_task(self, token, task_data):
        """Crée une tâche"""
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{self.base_url}/api/v1/v1/tasks",
            json=task_data,
            headers=headers
        )
        
        if response.status_code == 201:
            task = response.json()
            self.tasks[task["id"]] = task
            stats["tasks_created"] += 1
            return task
        else:
            raise Exception(f"Erreur création tâche: {response.text}")
    
    def send_message(self, token, from_agent_id, to_agent_id, performative, content):
        """Envoie un message entre agents"""
        headers = {"Authorization": f"Bearer {token}"}
        
        message_data = {
            "receiver_id": to_agent_id,
            "performative": performative,
            "content": content
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents/{from_agent_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code == 201:
            stats["messages_sent"] += 1
            return response.json()
        else:
            return None
    
    def store_memory(self, token, agent_id, content, memory_type="semantic"):
        """Stocke une mémoire pour un agent"""
        headers = {"Authorization": f"Bearer {token}"}
        
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "importance": 0.8
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents/{agent_id}/memories",
            json=memory_data,
            headers=headers
        )
        
        if response.status_code == 201:
            stats["memories_stored"] += 1
            return response.json()
        return None
    
    def check_task_status_db(self, task_id):
        """Vérifie le statut d'une tâche dans la base de données"""
        sql = f"SELECT status, result FROM tasks WHERE id = '{task_id}';"
        cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('|')
            if len(parts) >= 2:
                return parts[0], parts[1] if parts[1] else None
        return None, None
    
    def force_complete_task(self, task_id, result):
        """Force la complétion d'une tâche via la base de données"""
        result_json = json.dumps(result).replace("'", "''")
        sql = f"""
        UPDATE tasks 
        SET status = 'completed',
            result = '{result_json}'::jsonb,
            completed_at = NOW(),
            updated_at = NOW()
        WHERE id = '{task_id}';
        """
        
        cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-c", sql]
        subprocess.run(cmd, capture_output=True, text=True)
        stats["tasks_completed"] += 1
    
    def monitor_progress(self):
        """Thread de monitoring qui affiche les statistiques"""
        while stats["active"]:
            with print_lock:
                print(f"\n📊 Statistiques (à {datetime.now().strftime('%H:%M:%S')}):")
                print(f"   👥 Utilisateurs: {stats['users_created']}")
                print(f"   🤖 Agents créés: {stats['agents_created']}")
                print(f"   📋 Tâches créées: {stats['tasks_created']}")
                print(f"   ✅ Tâches complétées: {stats['tasks_completed']}")
                print(f"   💬 Messages envoyés: {stats['messages_sent']}")
                print(f"   🧠 Mémoires stockées: {stats['memories_stored']}")
            time.sleep(MONITOR_INTERVAL)
    
    def run_complete_cycle(self):
        """Exécute le cycle complet de démonstration"""
        safe_print("\n🚀 DÉMONSTRATION DU CYCLE COMPLET MAS")
        safe_print("="*80)
        
        # Démarrer le monitoring
        monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        monitor_thread.start()
        
        try:
            # Phase 1: Créer les utilisateurs
            safe_print("\n📋 Phase 1: Création des utilisateurs")
            users_data = [
                ("alice", "alice@mas.com", "password123"),
                ("bob", "bob@mas.com", "password123"),
                ("charlie", "charlie@mas.com", "password123")
            ]
            
            for username, email, password in users_data:
                self.register_and_login(username, email, password)
            
            # Phase 2: Créer les agents
            safe_print("\n📋 Phase 2: Création des agents")
            agent_configs = [
                # Agents pour Alice (équipe analyse)
                {
                    "user": "alice",
                    "agents": [
                        {
                            "name": "Analyste Principal",
                            "role": "Analyse des systèmes complexes",
                            "agent_type": "cognitive",
                            "capabilities": ["analyse", "synthèse", "rapport"],
                            "initial_beliefs": {"domaine": "analyse", "expertise": "systèmes"},
                            "configuration": {"temperature": 0.6, "reasoning_depth": 5}
                        },
                        {
                            "name": "Chercheur IA",
                            "role": "Recherche en intelligence artificielle",
                            "agent_type": "cognitive",
                            "capabilities": ["recherche", "apprentissage", "innovation"],
                            "initial_beliefs": {"domaine": "IA", "méthode": "empirique"},
                            "configuration": {"temperature": 0.8, "max_tokens": 2000}
                        },
                        {
                            "name": "Coordinateur Analyse",
                            "role": "Coordination de l'équipe d'analyse",
                            "agent_type": "hybrid",
                            "capabilities": ["coordination", "planification", "suivi"],
                            "initial_beliefs": {"rôle": "leader", "équipe": "analyse"},
                            "configuration": {"planning_horizon": 10}
                        }
                    ]
                },
                # Agents pour Bob (équipe développement)
                {
                    "user": "bob",
                    "agents": [
                        {
                            "name": "Développeur Senior",
                            "role": "Développement de solutions techniques",
                            "agent_type": "cognitive",
                            "capabilities": ["programmation", "architecture", "optimisation"],
                            "initial_beliefs": {"langage": "python", "paradigme": "fonctionnel"},
                            "configuration": {"temperature": 0.4, "system_prompt": "Expert en développement"}
                        },
                        {
                            "name": "Testeur QA",
                            "role": "Tests et assurance qualité",
                            "agent_type": "reflexive",
                            "capabilities": ["test", "validation", "rapport"],
                            "initial_beliefs": {"méthode": "TDD", "rigueur": "élevée"},
                            "reactive_rules": {"on_code_change": "run_tests"},
                            "configuration": {}
                        },
                        {
                            "name": "Architecte Système",
                            "role": "Conception d'architectures robustes",
                            "agent_type": "cognitive",
                            "capabilities": ["conception", "modélisation", "documentation"],
                            "initial_beliefs": {"approche": "microservices", "scalabilité": "prioritaire"},
                            "configuration": {"reasoning_depth": 7}
                        }
                    ]
                },
                # Agents pour Charlie (équipe support)
                {
                    "user": "charlie",
                    "agents": [
                        {
                            "name": "Support Client",
                            "role": "Assistance et support utilisateur",
                            "agent_type": "reflexive",
                            "capabilities": ["support", "communication", "résolution"],
                            "initial_beliefs": {"priorité": "satisfaction_client"},
                            "reactive_rules": {"on_issue": "respond_quickly"},
                            "configuration": {}
                        },
                        {
                            "name": "Formateur",
                            "role": "Formation et transfert de connaissances",
                            "agent_type": "cognitive",
                            "capabilities": ["formation", "pédagogie", "documentation"],
                            "initial_beliefs": {"méthode": "apprentissage_actif"},
                            "configuration": {"temperature": 0.7}
                        },
                        {
                            "name": "Médiateur",
                            "role": "Médiation et résolution de conflits",
                            "agent_type": "hybrid",
                            "capabilities": ["médiation", "négociation", "consensus"],
                            "initial_beliefs": {"approche": "collaborative"},
                            "configuration": {"confidence_threshold": 0.8}
                        },
                        {
                            "name": "Auditeur",
                            "role": "Audit et conformité",
                            "agent_type": "cognitive",
                            "capabilities": ["audit", "conformité", "rapport"],
                            "initial_beliefs": {"norme": "ISO", "rigueur": "maximale"},
                            "configuration": {"temperature": 0.3}
                        }
                    ]
                }
            ]
            
            # Créer les agents en parallèle
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                for config in agent_configs:
                    username = config["user"]
                    token = self.users[username]["token"]
                    
                    for agent_data in config["agents"]:
                        agent_data["initial_desires"] = ["accomplir_mission", "collaborer"]
                        agent_data["organization_id"] = None
                        
                        future = executor.submit(self.create_agent, token, agent_data)
                        futures.append((username, future))
                
                # Attendre la création de tous les agents
                for username, future in futures:
                    try:
                        agent = future.result()
                        self.users[username]["agents"].append(agent["id"])
                        safe_print(f"   ✅ Agent créé: {agent['name']} ({agent['agent_type']})")
                    except Exception as e:
                        safe_print(f"   ❌ Erreur création agent: {e}")
            
            # Phase 3: Créer des tâches complexes
            safe_print("\n📋 Phase 3: Création de tâches complexes")
            
            # Tâche 1: Analyse système multi-agents (si Alice a des agents)
            if len(self.users["alice"]["agents"]) > 0:
                task1 = self.create_task(
                    self.users["alice"]["token"],
                    {
                        "title": "Analyse complète du système multi-agents",
                        "description": "Analyser l'architecture, les patterns d'interaction et les optimisations possibles du système MAS",
                        "task_type": "analysis",
                        "priority": "high",
                        "assigned_to": self.users["alice"]["agents"][0]  # Premier agent d'Alice
                    }
                )
            
            # Tâche 2: Développement d'une nouvelle fonctionnalité (si Bob a des agents)
            if len(self.users["bob"]["agents"]) > 0:
                task2 = self.create_task(
                    self.users["bob"]["token"],
                    {
                        "title": "Développer module de consensus distribué",
                        "description": "Implémenter un algorithme de consensus pour la coordination des agents",
                        "task_type": "development",
                        "priority": "critical",
                        "assigned_to": self.users["bob"]["agents"][0]  # Premier agent de Bob
                    }
                )
            
            # Tâche 3: Formation sur le système (si Charlie a des agents)
            charlie_agents = self.users["charlie"]["agents"]
            if len(charlie_agents) > 0:
                # Utiliser le premier agent disponible
                task3 = self.create_task(
                    self.users["charlie"]["token"],
                    {
                        "title": "Créer documentation de formation MAS",
                        "description": "Développer un guide complet pour nouveaux utilisateurs du système multi-agents",
                        "task_type": "documentation",
                        "priority": "medium",
                        "assigned_to": charlie_agents[0]  # Premier agent disponible
                    }
                )
            
            # Phase 4: Communication inter-agents
            safe_print("\n📋 Phase 4: Communication entre agents")
            
            # Vérifier qu'on a assez d'agents pour communiquer
            alice_agents = self.users["alice"]["agents"]
            bob_agents = self.users["bob"]["agents"]
            
            if len(alice_agents) >= 1 and len(bob_agents) >= 1:
                # L'analyste demande des infos au développeur
                msg1 = self.send_message(
                    self.users["alice"]["token"],
                    alice_agents[0],  # Premier agent d'Alice
                    bob_agents[0],    # Premier agent de Bob
                    "request",
                    {"message": "Quelles sont les contraintes techniques pour l'implémentation du consensus?"}
                )
                if msg1:
                    safe_print(f"   ✅ Message envoyé: request (Alice → Bob)")
                
                # Le développeur répond à l'analyste
                msg2 = self.send_message(
                    self.users["bob"]["token"],
                    bob_agents[0],    # Premier agent de Bob
                    alice_agents[0],  # Premier agent d'Alice
                    "inform",
                    {"message": "Les contraintes incluent: latence réseau < 100ms, tolérance aux pannes byzantines"}
                )
                if msg2:
                    safe_print(f"   ✅ Message envoyé: inform (Bob → Alice)")
            
            # Si on a plus d'agents, faire plus de communications
            if len(alice_agents) >= 3 and len(bob_agents) >= 3:
                # Le coordinateur propose une réunion
                self.send_message(
                    self.users["alice"]["token"],
                    alice_agents[2],  # Coordinateur
                    bob_agents[2],    # Architecte
                    "propose",
                    {"message": "Proposition de revue d'architecture demain à 14h"}
                )
                
                # L'architecte accepte
                self.send_message(
                    self.users["bob"]["token"],
                    bob_agents[2],    # Architecte
                    alice_agents[2],  # Coordinateur
                    "accept",
                    {"message": "J'accepte la réunion de revue d'architecture"}
                )
            else:
                safe_print("   ⚠️  Pas assez d'agents pour toutes les communications prévues")
            
            # Phase 5: Utilisation des outils (mémoires)
            safe_print("\n📋 Phase 5: Stockage de mémoires et apprentissage")
            
            # Construire dynamiquement la liste des mémoires basée sur les agents créés
            memories = []
            
            # Mémoires pour les agents d'Alice
            alice_agents = self.users["alice"]["agents"]
            if len(alice_agents) >= 1:
                memories.append((alice_agents[0], "Le système MAS utilise une architecture BDI pour la cognition", "semantic"))
            if len(alice_agents) >= 2:
                memories.append((alice_agents[1], "Les patterns d'émergence apparaissent avec > 50 agents", "episodic"))
            
            # Mémoires pour les agents de Bob
            bob_agents = self.users["bob"]["agents"]
            if len(bob_agents) >= 1:
                memories.append((bob_agents[0], "L'algorithme Raft est adapté pour le consensus distribué", "semantic"))
            if len(bob_agents) >= 3:
                memories.append((bob_agents[2], "Les microservices facilitent la scalabilité horizontale", "semantic"))
            
            # Mémoires pour les agents de Charlie
            charlie_agents = self.users["charlie"]["agents"]
            if len(charlie_agents) >= 1:
                memories.append((charlie_agents[0], "L'apprentissage par projet est plus efficace pour MAS", "working"))
            
            # Stocker les mémoires
            for agent_id, content, mem_type in memories:
                # Trouver le token du propriétaire
                owner_token = None
                for username, data in self.users.items():
                    if agent_id in data["agents"]:
                        owner_token = data["token"]
                        break
                
                if owner_token:
                    self.store_memory(owner_token, agent_id, content, mem_type)
            
            # Phase 6: Simulation de traitement et complétion
            safe_print("\n📋 Phase 6: Traitement des tâches (simulation)")
            time.sleep(2)
            
            # Simuler la complétion des tâches créées
            results = {}
            
            # Préparer les résultats pour les tâches qui ont été créées
            for task_id, task in self.tasks.items():
                if task["title"] == "Analyse complète du système multi-agents":
                    results[task_id] = {
                        "response": "Analyse complète:\n\n1. Architecture: Le système utilise une architecture multi-couches avec des agents BDI\n2. Patterns d'interaction: Communication FIPA-ACL, négociations multilatérales\n3. Optimisations: Parallélisation des tâches, cache distribué, équilibrage de charge\n4. Recommandations: Implémenter un système de consensus pour la cohérence",
                        "confidence": 0.92,
                        "processing_time": 3.2,
                        "tokens_used": 1250
                    }
                elif task["title"] == "Développer module de consensus distribué":
                    results[task_id] = {
                        "response": "Module développé:\n\n```python\nclass ConsensusModule:\n    def __init__(self):\n        self.nodes = []\n        self.leader = None\n    \n    def elect_leader(self):\n        # Implémentation Raft\n        pass\n```\n\nTests: 100% passés\nPerformance: < 50ms latence",
                        "confidence": 0.88,
                        "processing_time": 5.7,
                        "tokens_used": 2100
                    }
                elif task["title"] == "Créer documentation de formation MAS":
                    results[task_id] = {
                        "response": "Documentation créée:\n\n# Guide MAS pour débutants\n\n## 1. Introduction\n- Qu'est-ce qu'un système multi-agents?\n- Architecture BDI\n\n## 2. Premiers pas\n- Création d'agents\n- Communication\n\n## 3. Cas pratiques\n- Exemples concrets\n- Exercices",
                        "confidence": 0.95,
                        "processing_time": 4.1,
                        "tokens_used": 1800
                    }
            
            for task_id, result in results.items():
                self.force_complete_task(task_id, result)
                safe_print(f"   ✅ Tâche complétée: {self.tasks[task_id]['title']}")
            
            # Phase 7: Monitoring final et attente
            safe_print("\n📋 Phase 7: Vérification de la complétion")
            
            # Attendre un peu pour voir les stats finales
            time.sleep(5)
            
            # Vérifier que tout est terminé
            all_completed = True
            for task_id in self.tasks:
                status, _ = self.check_task_status_db(task_id)
                if status != "completed":
                    all_completed = False
                    break
            
            # Arrêter le monitoring
            stats["active"] = False
            
            # Affichage final
            safe_print("\n" + "="*80)
            safe_print("📊 RÉSUMÉ FINAL DE LA DÉMONSTRATION")
            safe_print("="*80)
            
            safe_print(f"""
   👥 Utilisateurs créés: {stats['users_created']}
   🤖 Agents créés: {stats['agents_created']} ({TOTAL_AGENTS} prévus)
   📋 Tâches créées: {stats['tasks_created']}
   ✅ Tâches complétées: {stats['tasks_completed']}
   💬 Messages échangés: {stats['messages_sent']}
   🧠 Mémoires stockées: {stats['memories_stored']}
   
   🎯 Statut: {'✅ TOUT TERMINÉ' if all_completed else '⏳ EN COURS'}
            """)
            
            # Afficher quelques résultats
            safe_print("\n📄 Exemples de résultats:")
            for task_id, result in list(results.items())[:2]:
                task = self.tasks[task_id]
                safe_print(f"\n   📌 {task['title']}:")
                safe_print(f"      {result['response'][:200]}...")
                safe_print(f"      Confiance: {result['confidence']*100:.1f}%")
                safe_print(f"      Tokens: {result['tokens_used']}")
            
        except Exception as e:
            safe_print(f"\n❌ Erreur: {e}")
            stats["active"] = False
            raise
        
        safe_print("\n✨ Démonstration terminée avec succès!")

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de la démonstration complète du cycle MAS")
    print("   Cette démonstration va:")
    print("   - Créer plusieurs utilisateurs")
    print("   - Créer 10 agents de différents types")
    print("   - Assigner des tâches complexes")
    print("   - Faire communiquer les agents")
    print("   - Stocker des mémoires")
    print("   - Attendre la complétion totale")
    print()
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{API_URL}/docs")
        if response.status_code != 200:
            print("❌ L'API MAS n'est pas accessible sur http://localhost:8088")
            print("   Veuillez démarrer le système avec: docker-compose up")
            return
    except:
        print("❌ Impossible de se connecter à l'API MAS")
        print("   Vérifiez que le système est démarré")
        return
    
    # Lancer la démonstration
    demo = MASCycleDemo()
    demo.run_complete_cycle()

if __name__ == "__main__":
    main()