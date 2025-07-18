#!/usr/bin/env python3
"""
Démonstration avancée du système MAS : Construction collaborative d'une application web complète
par une équipe d'agents spécialisés travaillant en synergie.

Scénario : Développer un système de gestion de tâches (Todo App) avec :
- API REST complète (CRUD)
- Base de données PostgreSQL
- Interface web React
- Tests automatisés
- Documentation
- Déploiement Docker

Les agents collaborent selon leurs spécialités pour réaliser ce projet complexe.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class WebAppBuilderDemo:
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.organization_id = None
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
        
    async def create_user_and_login(self, session: aiohttp.ClientSession, username: str, email: str, password: str) -> str:
        """Créer un utilisateur et obtenir le token"""
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
            print(f"❌ Erreur création utilisateur {username}: {await register_resp.text()}")
            return None
            
        # Login
        login_data = {"username": username, "password": password}
        login_resp = await session.post(
            f"{API_BASE_URL.replace('/api/v1', '')}/auth/token",
            data=login_data
        )
        
        if login_resp.status == 200:
            token_data = await login_resp.json()
            return token_data["access_token"]
        else:
            print(f"❌ Échec connexion {username}: {login_resp.status}")
            return None
            
    async def create_specialized_agent(self, session: aiohttp.ClientSession, owner: str, agent_config: Dict) -> Dict:
        """Créer un agent spécialisé"""
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
            print(f"❌ Erreur création agent: {create_resp.status}")
            return None
            
    async def send_message(self, session: aiohttp.ClientSession, sender_id: str, receiver_id: str, 
                          performative: str, content: Dict, sender_token: str) -> bool:
        """Envoyer un message entre agents"""
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
        
        return resp.status == 201
        
    async def create_organization(self, session: aiohttp.ClientSession) -> str:
        """Créer une organisation pour coordonner les agents"""
        token = self.users.get("project_manager")
        headers = {"Authorization": f"Bearer {token}"}
        
        org_data = {
            "name": "WebDev Team",
            "structure": "team",
            "roles": {
                "project_manager": ["coordination", "planning"],
                "architect": ["design", "technical_decisions"],
                "backend_dev": ["api_development", "database"],
                "frontend_dev": ["ui_development", "user_experience"],
                "qa_engineer": ["testing", "quality_assurance"],
                "devops": ["deployment", "infrastructure"]
            }
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/organizations",
            json=org_data,
            headers=headers
        )
        
        if resp.status == 201:
            org = await resp.json()
            return org['id']
        return None
        
    async def run_demo(self):
        """Exécuter la démonstration complète"""
        print("="*80)
        print("🚀 DÉMONSTRATION MAS : Construction Collaborative d'une Application Web")
        print("="*80)
        print(f"\n📋 Projet: {self.project_data['name']}")
        print(f"📝 Description: {self.project_data['description']}")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Créer l'équipe
            print("\n\n🏗️ PHASE 1: Constitution de l'équipe de développement")
            print("-"*60)
            
            # Générer un ID unique
            unique_id = str(int(time.time()))[-6:]
            
            # Créer les utilisateurs
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
                    
            # Phase 2: Créer les agents spécialisés
            print("\n\n🤖 PHASE 2: Création des agents spécialisés")
            print("-"*60)
            
            agent_configs = [
                {
                    "owner": "project_manager",
                    "config": {
                        "name": f"ProjectCoordinator_{unique_id}",
                        "agent_type": "hybrid",
                        "role": "Chef de projet - Coordination et planification",
                        "capabilities": ["coordination", "planning", "task_allocation", "progress_tracking"],
                        "initial_beliefs": {
                            "project": self.project_data,
                            "timeline": "2 semaines",
                            "methodology": "Agile"
                        },
                        "initial_desires": ["livrer_projet", "coordonner_equipe", "respecter_delais"],
                        "reactive_rules": [
                            {
                                "condition": {"message_type": "status_update"},
                                "action": "aggregate_progress"
                            }
                        ],
                        "configuration": {
                            "complexity_threshold": 0.7,
                            "mode_stats": {"reflexive": 0, "cognitive": 0}
                        }
                    }
                },
                {
                    "owner": "architect",
                    "config": {
                        "name": f"SystemArchitect_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Architecte système - Conception technique",
                        "capabilities": ["system_design", "technology_selection", "architecture_patterns"],
                        "initial_beliefs": {
                            "best_practices": ["SOLID", "DRY", "KISS"],
                            "architecture": "microservices",
                            "stack": self.project_data["requirements"]
                        },
                        "initial_desires": ["concevoir_architecture", "assurer_scalabilite", "maintenir_qualite"],
                        "initial_intentions": ["analyser_requirements", "designer_système"],
                        "configuration": {
                            "llm_enabled": True,
                            "reasoning_depth": 5,
                            "planning_enabled": True
                        }
                    }
                },
                {
                    "owner": "backend_dev",
                    "config": {
                        "name": f"BackendDeveloper_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Développeur Backend - API et base de données",
                        "capabilities": ["api_development", "database_design", "backend_optimization"],
                        "initial_beliefs": {
                            "framework": "FastAPI",
                            "database": "PostgreSQL",
                            "patterns": ["Repository", "Service Layer", "DTO"]
                        },
                        "initial_desires": ["developper_api", "optimiser_performance", "securiser_endpoints"],
                        "configuration": {
                            "llm_enabled": True,
                            "reasoning_depth": 4
                        }
                    }
                },
                {
                    "owner": "frontend_dev",
                    "config": {
                        "name": f"FrontendDeveloper_{unique_id}",
                        "agent_type": "cognitive",
                        "role": "Développeur Frontend - Interface utilisateur",
                        "capabilities": ["ui_development", "responsive_design", "state_management"],
                        "initial_beliefs": {
                            "framework": "React",
                            "styling": "TailwindCSS",
                            "state": "Redux Toolkit"
                        },
                        "initial_desires": ["creer_ui_intuitive", "optimiser_ux", "assurer_responsive"],
                        "configuration": {
                            "llm_enabled": True,
                            "reasoning_depth": 4
                        }
                    }
                },
                {
                    "owner": "qa_engineer",
                    "config": {
                        "name": f"QAEngineer_{unique_id}",
                        "agent_type": "hybrid",
                        "role": "Ingénieur QA - Tests et qualité",
                        "capabilities": ["test_automation", "quality_assurance", "bug_tracking"],
                        "initial_beliefs": {
                            "testing_frameworks": ["Jest", "Pytest", "Cypress"],
                            "coverage_target": 80,
                            "test_types": ["unit", "integration", "e2e"]
                        },
                        "initial_desires": ["assurer_qualite", "automatiser_tests", "prevenir_bugs"],
                        "reactive_rules": [
                            {
                                "condition": {"code_change": True},
                                "action": "run_tests"
                            }
                        ],
                        "configuration": {
                            "complexity_threshold": 0.5
                        }
                    }
                },
                {
                    "owner": "devops_engineer",
                    "config": {
                        "name": f"DevOpsEngineer_{unique_id}",
                        "agent_type": "reflexive",
                        "role": "Ingénieur DevOps - Infrastructure et déploiement",
                        "capabilities": ["containerization", "ci_cd", "infrastructure_automation"],
                        "initial_beliefs": {
                            "tools": ["Docker", "Kubernetes", "GitHub Actions"],
                            "environment": ["dev", "staging", "production"]
                        },
                        "reactive_rules": [
                            {
                                "condition": {"event": "code_push"},
                                "action": "trigger_pipeline"
                            },
                            {
                                "condition": {"event": "deploy_request"},
                                "action": "deploy_environment"
                            }
                        ]
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
                    
            # Phase 3: Créer l'organisation
            print("\n\n🏢 PHASE 3: Création de l'organisation")
            print("-"*60)
            
            self.organization_id = await self.create_organization(session)
            if self.organization_id:
                print("✅ Organisation 'WebDev Team' créée")
                
            # Phase 4: Workflow de développement collaboratif
            print("\n\n⚡ PHASE 4: Développement collaboratif")
            print("-"*60)
            
            # Le chef de projet lance le projet
            if "project_manager" in self.agents and "architect" in self.agents:
                pm_agent = self.agents["project_manager"]
                arch_agent = self.agents["architect"]
                
                print(f"\n📨 {pm_agent['name']} → {arch_agent['name']}")
                print("   📋 Demande de conception de l'architecture")
                
                await self.send_message(
                    session,
                    pm_agent['id'],
                    arch_agent['id'],
                    "request",
                    {
                        "action": "design_architecture",
                        "project": self.project_data,
                        "deadline": "48h"
                    },
                    self.users["project_manager"]
                )
                
            # L'architecte propose une architecture
            await asyncio.sleep(2)
            
            if "architect" in self.agents and "project_manager" in self.agents:
                arch_agent = self.agents["architect"]
                pm_agent = self.agents["project_manager"]
                
                print(f"\n📨 {arch_agent['name']} → {pm_agent['name']}")
                print("   📐 Proposition d'architecture")
                
                architecture_proposal = {
                    "backend": {
                        "framework": "FastAPI",
                        "structure": "Clean Architecture",
                        "layers": ["API", "Service", "Repository", "Domain"],
                        "database": {
                            "type": "PostgreSQL",
                            "orm": "SQLAlchemy"
                        }
                    },
                    "frontend": {
                        "framework": "React 18",
                        "language": "TypeScript",
                        "state": "Redux Toolkit",
                        "routing": "React Router v6",
                        "ui": "TailwindCSS + HeadlessUI"
                    },
                    "deployment": {
                        "containerization": "Docker",
                        "orchestration": "Docker Compose",
                        "ci_cd": "GitHub Actions"
                    }
                }
                
                await self.send_message(
                    session,
                    arch_agent['id'],
                    pm_agent['id'],
                    "propose",
                    {
                        "proposal": "architecture_design",
                        "details": architecture_proposal,
                        "benefits": ["scalable", "maintainable", "testable"]
                    },
                    self.users["architect"]
                )
                
            # Le PM accepte et distribue les tâches
            await asyncio.sleep(2)
            
            if all(k in self.agents for k in ["project_manager", "backend_dev", "frontend_dev"]):
                pm_agent = self.agents["project_manager"]
                backend_agent = self.agents["backend_dev"]
                frontend_agent = self.agents["frontend_dev"]
                
                # Tâche pour le backend
                print(f"\n📨 {pm_agent['name']} → {backend_agent['name']}")
                print("   🔧 Assignment: Développer l'API REST")
                
                await self.send_message(
                    session,
                    pm_agent['id'],
                    backend_agent['id'],
                    "request",
                    {
                        "action": "develop_api",
                        "endpoints": [
                            "POST /api/tasks",
                            "GET /api/tasks",
                            "PUT /api/tasks/{id}",
                            "DELETE /api/tasks/{id}",
                            "GET /api/categories",
                            "POST /api/categories"
                        ],
                        "models": ["Task", "Category", "Priority"],
                        "architecture": architecture_proposal["backend"]
                    },
                    self.users["project_manager"]
                )
                
                # Tâche pour le frontend
                print(f"\n📨 {pm_agent['name']} → {frontend_agent['name']}")
                print("   🎨 Assignment: Développer l'interface utilisateur")
                
                await self.send_message(
                    session,
                    pm_agent['id'],
                    frontend_agent['id'],
                    "request",
                    {
                        "action": "develop_ui",
                        "pages": ["TaskList", "TaskDetail", "CreateTask", "Categories"],
                        "components": ["TaskCard", "TaskForm", "CategorySelector", "PriorityBadge"],
                        "architecture": architecture_proposal["frontend"]
                    },
                    self.users["project_manager"]
                )
                
            # Les développeurs informent de leur progression
            await asyncio.sleep(3)
            
            if "backend_dev" in self.agents and "qa_engineer" in self.agents:
                backend_agent = self.agents["backend_dev"]
                qa_agent = self.agents["qa_engineer"]
                
                print(f"\n📨 {backend_agent['name']} → {qa_agent['name']}")
                print("   🧪 Demande de tests pour l'API")
                
                await self.send_message(
                    session,
                    backend_agent['id'],
                    qa_agent['id'],
                    "request",
                    {
                        "action": "create_tests",
                        "type": "api_tests",
                        "endpoints": ["tasks", "categories"],
                        "test_scenarios": [
                            "CRUD operations",
                            "Validation errors",
                            "Authentication",
                            "Performance"
                        ]
                    },
                    self.users["backend_dev"]
                )
                
            # Le QA crée et exécute les tests
            await asyncio.sleep(2)
            
            if "qa_engineer" in self.agents and "devops_engineer" in self.agents:
                qa_agent = self.agents["qa_engineer"]
                devops_agent = self.agents["devops_engineer"]
                
                print(f"\n📨 {qa_agent['name']} → {devops_agent['name']}")
                print("   🚀 Tests passés, demande de déploiement")
                
                await self.send_message(
                    session,
                    qa_agent['id'],
                    devops_agent['id'],
                    "inform",
                    {
                        "status": "tests_passed",
                        "coverage": 85,
                        "ready_for_deployment": True,
                        "environment": "staging"
                    },
                    self.users["qa_engineer"]
                )
                
            # Phase 5: Vérification des messages et collaboration
            print("\n\n📊 PHASE 5: Résultats de la collaboration")
            print("-"*60)
            
            # Vérifier les messages de chaque agent
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
                
                sent_resp = await session.get(
                    f"{API_BASE_URL}/agents/{agent['id']}/messages/sent",
                    headers=headers
                )
                
                if inbox_resp.status == 200 and sent_resp.status == 200:
                    inbox = await inbox_resp.json()
                    sent = await sent_resp.json()
                    
                    print(f"\n📧 {agent['name']}:")
                    print(f"   📥 Messages reçus: {len(inbox['items'])}")
                    print(f"   📤 Messages envoyés: {len(sent['items'])}")
                    
                    # Afficher quelques messages
                    if inbox['items']:
                        print("   📨 Derniers messages reçus:")
                        for msg in inbox['items'][:2]:
                            sender_id = msg.get('sender_id', 'Unknown')
                            # Trouver le nom de l'expéditeur
                            sender_name = "Unknown"
                            for r, a in self.agents.items():
                                if a['id'] == sender_id:
                                    sender_name = a['name']
                                    break
                            print(f"      • De: {sender_name}")
                            print(f"        Type: {msg['performative']}")
                            
            # Résumé final
            print("\n\n🎯 RÉSUMÉ DE LA DÉMONSTRATION")
            print("="*80)
            print(f"✅ Équipe créée: {len(self.agents)} agents spécialisés")
            print(f"✅ Organisation: Structure d'équipe établie")
            print(f"✅ Collaboration: Échanges multi-agents réussis")
            print("\n📋 Workflow démontré:")
            print("   1. Chef de projet → Architecte (conception)")
            print("   2. Architecte → Chef de projet (proposition)")
            print("   3. Chef de projet → Développeurs (assignments)")
            print("   4. Développeurs → QA (tests)")
            print("   5. QA → DevOps (déploiement)")
            print("\n🚀 Le système MAS a démontré sa capacité à:")
            print("   • Coordonner une équipe complexe")
            print("   • Gérer des workflows multi-étapes")
            print("   • Permettre la communication inter-agents")
            print("   • Réaliser des projets complexes de manière autonome")

async def main():
    demo = WebAppBuilderDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🔧 MAS - Démonstration de développement collaboratif d'application web")
    print("   Cette démo montre comment des agents spécialisés peuvent collaborer")
    print("   pour construire une application complète de manière autonome.")
    print()
    
    asyncio.run(main())