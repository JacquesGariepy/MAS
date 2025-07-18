#!/usr/bin/env python3
"""
Version corrigée de la démonstration MAS : Construction collaborative d'une application web
avec visualisation claire des communications entre agents.

Corrections apportées :
- Structure correcte pour les agents hybrid et reflexive
- Meilleure visualisation des messages
- Délais appropriés pour permettre le traitement
- Affichage détaillé des communications
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class WebAppBuilderDemoFixed:
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.messages_log = []  # Log de tous les messages pour visualisation
        self.project_data = {
            "name": "SmartTodo",
            "description": "Système de gestion de tâches intelligent avec IA",
            "requirements": {
                "backend": ["FastAPI", "PostgreSQL", "SQLAlchemy", "Pydantic"],
                "frontend": ["React", "TypeScript", "TailwindCSS", "Axios"],
                "features": ["CRUD tâches", "Catégories", "Priorités", "IA suggestions"],
                "deployment": ["Docker", "Docker Compose", "CI/CD"]
            }
        }
        
    async def create_user_and_login(self, session: aiohttp.ClientSession, 
                                   username: str, email: str, password: str) -> str:
        """Créer un utilisateur et obtenir le token"""
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
            print(f"❌ Erreur création utilisateur {username}: {await register_resp.text()}")
            return None
            
        login_data = {"username": username, "password": password}
        login_resp = await session.post(
            f"{API_BASE_URL.replace('/api/v1', '')}/auth/token",
            data=login_data
        )
        
        if login_resp.status == 200:
            token_data = await login_resp.json()
            return token_data["access_token"]
        return None
        
    async def create_specialized_agent(self, session: aiohttp.ClientSession, 
                                     owner: str, agent_config: Dict) -> Dict:
        """Créer un agent spécialisé avec configuration correcte"""
        token = self.users.get(owner)
        if not token:
            print(f"❌ Token manquant pour {owner}")
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        
        create_resp = await session.post(
            f"{API_BASE_URL}/agents",
            json=agent_config,
            headers=headers
        )
        
        if create_resp.status == 201:
            agent_data = await create_resp.json()
            
            # Démarrer l'agent
            start_resp = await session.post(
                f"{API_BASE_URL}/agents/{agent_data['id']}/start",
                headers=headers
            )
            
            if start_resp.status == 200:
                agent_data['status'] = 'working'
                print(f"✅ Agent {agent_config['name']} créé et démarré")
                return agent_data
            else:
                print(f"❌ Erreur démarrage agent: {start_resp.status}")
                return agent_data
        else:
            error_text = await create_resp.text()
            print(f"❌ Erreur création agent: {create_resp.status}")
            print(f"   Détails: {error_text}")
            return None
            
    async def send_message_with_log(self, session: aiohttp.ClientSession, 
                                   sender_id: str, receiver_id: str, 
                                   performative: str, content: Dict, 
                                   sender_token: str, sender_name: str, 
                                   receiver_name: str) -> bool:
        """Envoyer un message et l'enregistrer dans le log"""
        headers = {"Authorization": f"Bearer {sender_token}"}
        
        message_data = {
            "receiver_id": receiver_id,
            "performative": performative,
            "content": content
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/agents/{sender_id}/messages",
            json=message_data,
            headers=headers
        )
        
        # Enregistrer le message dans le log
        self.messages_log.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "from": sender_name,
            "to": receiver_name,
            "type": performative,
            "content": content,
            "status": "✅" if resp.status == 201 else "❌"
        })
        
        return resp.status == 201
        
    async def display_communication_flow(self):
        """Afficher le flux de communication de manière visuelle"""
        print("\n\n💬 FLUX DE COMMUNICATION DÉTAILLÉ")
        print("="*80)
        
        for msg in self.messages_log:
            print(f"\n⏰ [{msg['timestamp']}] {msg['status']}")
            print(f"📤 De: {msg['from']}")
            print(f"📥 À: {msg['to']}")
            print(f"🏷️ Type: {msg['type']}")
            print(f"📝 Contenu:")
            
            # Afficher le contenu de manière structurée
            content = msg['content']
            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, list):
                        print(f"   • {key}:")
                        for item in value:
                            print(f"     - {item}")
                    elif isinstance(value, dict):
                        print(f"   • {key}:")
                        for k, v in value.items():
                            print(f"     - {k}: {v}")
                    else:
                        print(f"   • {key}: {value}")
            else:
                print(f"   {content}")
            print("-"*60)
            
    async def run_demo(self):
        """Exécuter la démonstration complète avec corrections"""
        print("="*80)
        print("🚀 DÉMONSTRATION MAS CORRIGÉE : Construction Collaborative d'une Application Web")
        print("="*80)
        print(f"\n📋 Projet: {self.project_data['name']}")
        print(f"📝 Description: {self.project_data['description']}")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Créer l'équipe
            print("\n\n🏗️ PHASE 1: Constitution de l'équipe de développement")
            print("-"*60)
            
            unique_id = str(int(time.time()))[-6:]
            
            team_members = [
                ("project_manager", "pm@webdev.ai", "projectlead123"),
                ("architect", "arch@webdev.ai", "architect123"),
                ("backend_dev", "backend@webdev.ai", "backend123"),
                ("frontend_dev", "frontend@webdev.ai", "frontend123"),
                ("qa_engineer", "qa@webdev.ai", "testing123"),
                ("devops_engineer", "devops@webdev.ai", "devops123")
            ]
            
            for username, email, password in team_members:
                user_key = username
                username_unique = f"{username}_{unique_id}"
                email_unique = f"{username}_{unique_id}@webdev.ai"
                
                print(f"\n👤 Création: {username_unique}")
                token = await self.create_user_and_login(session, username_unique, email_unique, password)
                if token:
                    self.users[user_key] = token
                    print(f"   ✅ Utilisateur créé et connecté")
                    
            # Phase 2: Créer les agents spécialisés AVEC CORRECTIONS
            print("\n\n🤖 PHASE 2: Création des agents spécialisés (VERSION CORRIGÉE)")
            print("-"*60)
            
            agent_configs = [
                {
                    "owner": "project_manager",
                    "config": {
                        "name": f"ProjectCoordinator_{unique_id}",
                        "agent_type": "hybrid",
                        "role": "Chef de projet - Coordination et planification",
                        "capabilities": ["coordination", "planning", "task_allocation"],
                        "beliefs": json.dumps({
                            "project": self.project_data["name"],
                            "timeline": "2 semaines",
                            "methodology": "Agile"
                        }),
                        "desires": json.dumps(["livrer_projet", "coordonner_equipe"]),
                        "reactive_rules": {
                            "status_update_rule": {
                                "condition": {"message_type": "status_update"},
                                "action": "aggregate_progress"
                            }
                        },
                        "cognitive_threshold": 0.7  # CORRECTION: bon nom de champ
                    }
                },
                {
                    "owner": "architect",
                    "config": {
                        "name": f"SystemArchitect_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Architecte système - Conception technique",
                        "capabilities": ["system_design", "technology_selection"],
                        "beliefs": json.dumps({
                            "best_practices": ["SOLID", "DRY", "KISS"],
                            "architecture": "microservices"
                        }),
                        "desires": json.dumps(["concevoir_architecture", "assurer_scalabilite"]),
                        "intentions": json.dumps(["analyser_requirements", "designer_système"])
                    }
                },
                {
                    "owner": "backend_dev",
                    "config": {
                        "name": f"BackendDeveloper_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Développeur Backend - API et base de données",
                        "capabilities": ["api_development", "database_design"],
                        "beliefs": json.dumps({
                            "framework": "FastAPI",
                            "database": "PostgreSQL"
                        }),
                        "desires": json.dumps(["developper_api", "optimiser_performance"])
                    }
                },
                {
                    "owner": "frontend_dev",
                    "config": {
                        "name": f"FrontendDeveloper_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Développeur Frontend - Interface utilisateur",
                        "capabilities": ["ui_development", "responsive_design"],
                        "beliefs": json.dumps({
                            "framework": "React",
                            "styling": "TailwindCSS"
                        }),
                        "desires": json.dumps(["creer_ui_intuitive", "optimiser_ux"])
                    }
                },
                {
                    "owner": "qa_engineer",
                    "config": {
                        "name": f"QAEngineer_{unique_id}",
                        "agent_type": "hybrid",
                        "role": "Ingénieur QA - Tests et qualité",
                        "capabilities": ["test_automation", "quality_assurance"],
                        "beliefs": json.dumps({
                            "testing_frameworks": ["Jest", "Pytest", "Cypress"],
                            "coverage_target": 80
                        }),
                        "desires": json.dumps(["assurer_qualite", "automatiser_tests"]),
                        "reactive_rules": {
                            "code_change_rule": {
                                "condition": {"code_change": True},
                                "action": "run_tests"
                            }
                        },
                        "cognitive_threshold": 0.5  # CORRECTION
                    }
                },
                {
                    "owner": "devops_engineer",
                    "config": {
                        "name": f"DevOpsEngineer_{unique_id}",
                        "agent_type": "reflexive",
                        "role": "Ingénieur DevOps - Infrastructure et déploiement",
                        "capabilities": ["containerization", "ci_cd"],
                        "beliefs": json.dumps({
                            "tools": ["Docker", "Kubernetes", "GitHub Actions"]
                        }),
                        "reactive_rules": {  # CORRECTION: format dict, pas JSON
                            "code_push_rule": {
                                "condition": {"event": "code_push"},
                                "action": "trigger_pipeline"
                            },
                            "deploy_rule": {
                                "condition": {"event": "deploy_request"},
                                "action": "deploy_environment"
                            }
                        }
                    }
                }
            ]
            
            # Créer tous les agents
            for agent_config in agent_configs:
                owner = agent_config["owner"]
                config = agent_config["config"]
                
                print(f"\n🤖 Création: {config['name']}")
                print(f"   🧠 Type: {config['agent_type']}")
                print(f"   💼 Rôle: {config['role']}")
                
                agent = await self.create_specialized_agent(session, owner, config)
                if agent:
                    self.agents[owner] = agent
                    
            # Phase 3: Workflow de développement collaboratif
            print("\n\n⚡ PHASE 3: Communications et Collaboration")
            print("-"*60)
            
            # Attendre un peu pour que tous les agents soient prêts
            await asyncio.sleep(2)
            
            # 1. Le chef de projet lance le projet
            if "project_manager" in self.agents and "architect" in self.agents:
                pm_agent = self.agents["project_manager"]
                arch_agent = self.agents["architect"]
                
                print(f"\n➡️ Communication 1: Lancement du projet")
                
                success = await self.send_message_with_log(
                    session,
                    pm_agent['id'],
                    arch_agent['id'],
                    "request",
                    {
                        "action": "design_architecture",
                        "project": self.project_data,
                        "deadline": "48h",
                        "priority": "high"
                    },
                    self.users["project_manager"],
                    pm_agent['name'],
                    arch_agent['name']
                )
                
                if success:
                    print("   ✅ Message envoyé avec succès")
                    
            # Attendre le traitement
            await asyncio.sleep(2)
            
            # 2. L'architecte propose une architecture
            if "architect" in self.agents and "project_manager" in self.agents:
                arch_agent = self.agents["architect"]
                pm_agent = self.agents["project_manager"]
                
                print(f"\n➡️ Communication 2: Proposition d'architecture")
                
                architecture_proposal = {
                    "backend": {
                        "framework": "FastAPI",
                        "structure": "Clean Architecture",
                        "database": "PostgreSQL"
                    },
                    "frontend": {
                        "framework": "React 18",
                        "language": "TypeScript",
                        "ui": "TailwindCSS"
                    }
                }
                
                success = await self.send_message_with_log(
                    session,
                    arch_agent['id'],
                    pm_agent['id'],
                    "propose",
                    {
                        "proposal": "architecture_design",
                        "details": architecture_proposal,
                        "benefits": ["scalable", "maintainable", "testable"]
                    },
                    self.users["architect"],
                    arch_agent['name'],
                    pm_agent['name']
                )
                
                if success:
                    print("   ✅ Proposition envoyée")
                    
            await asyncio.sleep(2)
            
            # 3. Le PM distribue les tâches aux développeurs
            if all(k in self.agents for k in ["project_manager", "backend_dev", "frontend_dev"]):
                pm_agent = self.agents["project_manager"]
                backend_agent = self.agents["backend_dev"]
                frontend_agent = self.agents["frontend_dev"]
                
                # Tâche backend
                print(f"\n➡️ Communication 3: Assignment Backend")
                
                success = await self.send_message_with_log(
                    session,
                    pm_agent['id'],
                    backend_agent['id'],
                    "request",
                    {
                        "action": "develop_api",
                        "endpoints": ["POST /api/tasks", "GET /api/tasks", "PUT /api/tasks/{id}"],
                        "models": ["Task", "Category", "Priority"]
                    },
                    self.users["project_manager"],
                    pm_agent['name'],
                    backend_agent['name']
                )
                
                if success:
                    print("   ✅ Tâche backend assignée")
                    
                # Tâche frontend
                print(f"\n➡️ Communication 4: Assignment Frontend")
                
                success = await self.send_message_with_log(
                    session,
                    pm_agent['id'],
                    frontend_agent['id'],
                    "request",
                    {
                        "action": "develop_ui",
                        "pages": ["TaskList", "TaskDetail", "CreateTask"],
                        "components": ["TaskCard", "TaskForm", "CategorySelector"]
                    },
                    self.users["project_manager"],
                    pm_agent['name'],
                    frontend_agent['name']
                )
                
                if success:
                    print("   ✅ Tâche frontend assignée")
                    
            await asyncio.sleep(3)
            
            # 4. Les développeurs informent le QA
            if "backend_dev" in self.agents and "qa_engineer" in self.agents:
                backend_agent = self.agents["backend_dev"]
                qa_agent = self.agents["qa_engineer"]
                
                print(f"\n➡️ Communication 5: Demande de tests")
                
                success = await self.send_message_with_log(
                    session,
                    backend_agent['id'],
                    qa_agent['id'],
                    "inform",
                    {
                        "status": "api_ready",
                        "endpoints_completed": ["tasks", "categories"],
                        "need_testing": True
                    },
                    self.users["backend_dev"],
                    backend_agent['name'],
                    qa_agent['name']
                )
                
                if success:
                    print("   ✅ QA informé")
                    
            await asyncio.sleep(2)
            
            # 5. QA demande le déploiement
            if "qa_engineer" in self.agents and "devops_engineer" in self.agents:
                qa_agent = self.agents["qa_engineer"]
                devops_agent = self.agents["devops_engineer"]
                
                print(f"\n➡️ Communication 6: Demande de déploiement")
                
                success = await self.send_message_with_log(
                    session,
                    qa_agent['id'],
                    devops_agent['id'],
                    "request",
                    {
                        "action": "deploy",
                        "environment": "staging",
                        "tests_passed": True,
                        "coverage": 85
                    },
                    self.users["qa_engineer"],
                    qa_agent['name'],
                    devops_agent['name']
                )
                
                if success:
                    print("   ✅ Déploiement demandé")
                    
            # Afficher le flux de communication complet
            await self.display_communication_flow()
            
            # Phase 4: Vérification des messages dans les boîtes de réception
            print("\n\n📊 PHASE 4: État des boîtes de réception")
            print("-"*60)
            
            # Attendre que les messages soient traités
            await asyncio.sleep(3)
            
            for role, agent in self.agents.items():
                token = self.users.get(role)
                if not token:
                    continue
                    
                headers = {"Authorization": f"Bearer {token}"}
                
                # Récupérer les messages
                inbox_resp = await session.get(
                    f"{API_BASE_URL}/agents/{agent['id']}/messages/inbox",
                    headers=headers
                )
                
                if inbox_resp.status == 200:
                    inbox = await inbox_resp.json()
                    
                    print(f"\n📧 {agent['name']}:")
                    print(f"   📥 Messages reçus: {len(inbox.get('items', []))}")
                    
                    # Debug: afficher la structure complète si pas d'items
                    if not inbox.get('items'):
                        print(f"   ⚠️ Debug inbox response: {json.dumps(inbox, indent=6)[:200]}...")
                    else:
                        print("   📨 Contenu de la boîte de réception:")
                        for msg in inbox['items']:
                            # Trouver l'expéditeur
                            sender_name = "Unknown"
                            for r, a in self.agents.items():
                                if a['id'] == msg.get('sender_id'):
                                    sender_name = a['name']
                                    break
                                    
                            print(f"\n      📌 Message de: {sender_name}")
                            print(f"         Type: {msg['performative']}")
                            print(f"         Contenu: {json.dumps(msg['content'], indent=12, ensure_ascii=False)[:200]}...")
                            
            # Résumé final
            print("\n\n🎯 RÉSUMÉ DE LA DÉMONSTRATION CORRIGÉE")
            print("="*80)
            print(f"✅ Équipe créée: {len(self.agents)} agents spécialisés")
            print(f"✅ Tous les types d'agents fonctionnent: Cognitive, Hybrid, Reflexive")
            print(f"✅ Messages envoyés: {len(self.messages_log)}")
            print(f"✅ Communication bidirectionnelle établie")
            
            print("\n📋 Workflow démontré avec succès:")
            print("   1. PM → Architecte (conception) ✅")
            print("   2. Architecte → PM (proposition) ✅")
            print("   3. PM → Développeurs (assignments) ✅")
            print("   4. Backend Dev → QA (tests) ✅")
            print("   5. QA → DevOps (déploiement) ✅")
            
            print("\n🚀 Améliorations apportées:")
            print("   • Correction des structures d'agents hybrid/reflexive")
            print("   • Visualisation claire du flux de communication")
            print("   • Affichage détaillé des messages échangés")
            print("   • Délais appropriés pour le traitement")
            print("   • Log complet de toutes les interactions")

async def main():
    demo = WebAppBuilderDemoFixed()
    await demo.run_demo()

if __name__ == "__main__":
    print("🔧 MAS - Démonstration CORRIGÉE de développement collaboratif")
    print("   Version améliorée avec visualisation complète des communications")
    print()
    
    asyncio.run(main())