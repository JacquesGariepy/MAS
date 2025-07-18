#!/usr/bin/env python3
"""
Système MAS Complet : Gestionnaire de Projet Intelligent

Ce système démontre toutes les fonctionnalités du MAS à travers un cas d'usage concret :
Une équipe d'agents collabore pour gérer un projet de développement logiciel depuis
la réception de la demande client jusqu'à la livraison finale.

Agents impliqués :
1. ProjectManager (Hybrid) - Coordination générale et décisions stratégiques
2. TechLead (Cognitive) - Architecture technique et supervision du développement
3. Developer1 & Developer2 (Cognitive) - Implémentation du code
4. QAEngineer (Hybrid) - Tests et assurance qualité
5. DevOpsEngineer (Reflexive) - Déploiement et infrastructure
6. DocumentationWriter (Cognitive) - Documentation technique et utilisateur
7. ClientLiaison (Hybrid) - Communication avec le client

Workflow complet :
1. Réception de la demande client
2. Analyse et planification du projet
3. Distribution des tâches
4. Développement itératif avec coordination
5. Tests et validation
6. Documentation
7. Déploiement
8. Livraison au client
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4
import aiohttp
from enum import Enum

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectPhase(Enum):
    """Phases du projet"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    DELIVERY = "delivery"
    COMPLETED = "completed"

class ProjectManagementSystem:
    """Système de gestion de projet avec agents MAS"""
    
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.project_data = {}
        self.current_phase = ProjectPhase.ANALYSIS
        self.communication_log = []
        self.deliverables = {}
        
    async def initialize_system(self):
        """Initialise le système complet avec tous les agents"""
        print("\n" + "="*80)
        print("🚀 INITIALISATION DU SYSTÈME DE GESTION DE PROJET MAS")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Créer les utilisateurs et agents
            await self._create_project_team(session)
            
            # Configurer les capacités de chaque agent
            await self._configure_agent_capabilities(session)
            
            # Établir les canaux de communication
            await self._setup_communication_channels(session)
            
        print("\n✅ Système initialisé avec succès!")
        print(f"   • {len(self.agents)} agents créés")
        print(f"   • Tous les canaux de communication établis")
        print(f"   • Prêt à recevoir les demandes clients\n")
    
    async def _create_project_team(self, session: aiohttp.ClientSession):
        """Crée l'équipe complète du projet"""
        team_config = [
            {
                "username": "project_manager",
                "email": "pm@mas-project.com",
                "agent_name": "ProjectManager",
                "agent_type": "hybrid",
                "role": "Chef de projet - Coordination et stratégie",
                "capabilities": {
                    "skills": ["project_management", "planning", "coordination", "risk_assessment"],
                    "role": "Project Manager",
                    "decision_threshold": 0.7
                }
            },
            {
                "username": "tech_lead",
                "email": "tech@mas-project.com",
                "agent_name": "TechLead",
                "agent_type": "cognitive",
                "role": "Architecte technique principal",
                "capabilities": {
                    "skills": ["architecture", "system_design", "code_review", "technical_decisions"],
                    "role": "Technical Lead",
                    "expertise": ["python", "fastapi", "postgresql", "docker", "kubernetes"]
                }
            },
            {
                "username": "developer_1",
                "email": "dev1@mas-project.com",
                "agent_name": "BackendDeveloper",
                "agent_type": "cognitive",
                "role": "Développeur Backend Senior",
                "capabilities": {
                    "skills": ["backend_development", "api_design", "database_design", "testing"],
                    "role": "Backend Developer",
                    "expertise": ["python", "fastapi", "sqlalchemy", "postgresql"]
                }
            },
            {
                "username": "developer_2",
                "email": "dev2@mas-project.com",
                "agent_name": "FrontendDeveloper",
                "agent_type": "cognitive",
                "role": "Développeur Frontend Senior",
                "capabilities": {
                    "skills": ["frontend_development", "ui_design", "responsive_design", "testing"],
                    "role": "Frontend Developer",
                    "expertise": ["react", "typescript", "tailwindcss", "nextjs"]
                }
            },
            {
                "username": "qa_engineer",
                "email": "qa@mas-project.com",
                "agent_name": "QAEngineer",
                "agent_type": "hybrid",
                "role": "Ingénieur Assurance Qualité",
                "capabilities": {
                    "skills": ["testing", "test_automation", "quality_assurance", "bug_tracking"],
                    "role": "QA Engineer",
                    "tools": ["pytest", "selenium", "postman", "jira"]
                }
            },
            {
                "username": "devops_engineer",
                "email": "devops@mas-project.com",
                "agent_name": "DevOpsEngineer",
                "agent_type": "reflexive",
                "role": "Ingénieur DevOps - Infrastructure et déploiement",
                "capabilities": {
                    "skills": ["deployment", "ci_cd", "infrastructure", "monitoring"],
                    "role": "DevOps Engineer",
                    "tools": ["docker", "kubernetes", "github_actions", "terraform"]
                }
            },
            {
                "username": "doc_writer",
                "email": "docs@mas-project.com",
                "agent_name": "DocumentationWriter",
                "agent_type": "cognitive",
                "role": "Rédacteur technique",
                "capabilities": {
                    "skills": ["technical_writing", "documentation", "api_docs", "user_guides"],
                    "role": "Documentation Writer",
                    "formats": ["markdown", "openapi", "docusaurus", "readme"]
                }
            },
            {
                "username": "client_liaison",
                "email": "client@mas-project.com",
                "agent_name": "ClientLiaison",
                "agent_type": "hybrid",
                "role": "Responsable relation client",
                "capabilities": {
                    "skills": ["communication", "requirement_gathering", "client_management", "reporting"],
                    "role": "Client Liaison",
                    "communication_style": "professional_friendly"
                }
            }
        ]
        
        print("\n📋 Création de l'équipe du projet...")
        print("-" * 60)
        
        for member in team_config:
            # Créer l'utilisateur
            user_data = await self._create_user(
                session,
                member["username"],
                member["email"],
                "secure_password_123"
            )
            
            if user_data:
                # Créer l'agent
                agent_data = await self._create_agent(
                    session,
                    user_data["token"],
                    member["agent_name"],
                    member["agent_type"],
                    member["capabilities"]
                )
                
                if agent_data:
                    self.agents[member["agent_name"]] = {
                        "id": agent_data["id"],
                        "type": member["agent_type"],
                        "role": member["role"],
                        "capabilities": member["capabilities"],
                        "token": user_data["token"],
                        "status": "ready"
                    }
                    
                    print(f"✅ {member['agent_name']} ({member['agent_type']}) - {member['role']}")
    
    async def process_client_request(self, client_request: Dict[str, Any]):
        """Traite une demande client de bout en bout"""
        print("\n" + "="*80)
        print("📨 NOUVELLE DEMANDE CLIENT REÇUE")
        print("="*80)
        
        self.project_data = {
            "id": f"project_{uuid4().hex[:8]}",
            "client_request": client_request,
            "created_at": datetime.utcnow().isoformat(),
            "phases": {},
            "status": "active"
        }
        
        # Afficher la demande
        print(f"\n🏢 Client: {client_request['client_name']}")
        print(f"📋 Projet: {client_request['project_name']}")
        print(f"📝 Description: {client_request['description']}")
        print(f"📅 Deadline: {client_request['deadline']}")
        print(f"💰 Budget: ${client_request['budget']:,}")
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Analyse de la demande
            await self._phase_analysis(session, client_request)
            
            # Phase 2: Planification du projet
            await self._phase_planning(session)
            
            # Phase 3: Développement
            await self._phase_development(session)
            
            # Phase 4: Tests et QA
            await self._phase_testing(session)
            
            # Phase 5: Documentation
            await self._phase_documentation(session)
            
            # Phase 6: Déploiement
            await self._phase_deployment(session)
            
            # Phase 7: Livraison au client
            await self._phase_delivery(session)
        
        print("\n" + "="*80)
        print("🎉 PROJET TERMINÉ AVEC SUCCÈS!")
        print("="*80)
        self._display_final_summary()
    
    async def _phase_analysis(self, session: aiohttp.ClientSession, client_request: Dict[str, Any]):
        """Phase 1: Analyse de la demande client"""
        print("\n\n🔍 PHASE 1: ANALYSE DE LA DEMANDE")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.ANALYSIS
        
        # Le ClientLiaison analyse la demande et clarifie les besoins
        analysis_task = {
            "title": "Analyser et clarifier la demande client",
            "description": f"Analyser la demande du client {client_request['client_name']} pour le projet {client_request['project_name']}",
            "context": client_request,
            "expected_output": "requirements_analysis"
        }
        
        # Envoyer la tâche au ClientLiaison
        print("📤 ClientLiaison: Analyse des besoins client...")
        requirements = await self._assign_task_to_agent(
            session,
            "ClientLiaison",
            analysis_task
        )
        
        # Le TechLead fait une analyse technique
        tech_analysis_task = {
            "title": "Analyse technique de faisabilité",
            "description": "Évaluer la faisabilité technique et identifier les technologies nécessaires",
            "context": {
                "client_request": client_request,
                "requirements": requirements
            },
            "expected_output": "technical_feasibility"
        }
        
        print("📤 TechLead: Analyse de faisabilité technique...")
        feasibility = await self._assign_task_to_agent(
            session,
            "TechLead",
            tech_analysis_task
        )
        
        # Communication entre agents pour affiner l'analyse
        await self._inter_agent_communication(
            session,
            "ClientLiaison",
            "TechLead",
            {
                "type": "clarification",
                "content": "Besoin de précisions sur les contraintes techniques",
                "questions": ["Quelle charge attendue?", "Besoins de scalabilité?", "Intégrations tierces?"]
            }
        )
        
        self.project_data["phases"]["analysis"] = {
            "requirements": requirements,
            "feasibility": feasibility,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase d'analyse complétée")
    
    async def _phase_planning(self, session: aiohttp.ClientSession):
        """Phase 2: Planification du projet"""
        print("\n\n📅 PHASE 2: PLANIFICATION DU PROJET")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.PLANNING
        
        # Le ProjectManager crée le plan de projet
        planning_task = {
            "title": "Créer le plan de projet détaillé",
            "description": "Planifier les sprints, jalons et allocation des ressources",
            "context": {
                "analysis": self.project_data["phases"]["analysis"],
                "deadline": self.project_data["client_request"]["deadline"],
                "team_size": len(self.agents)
            },
            "expected_output": "project_plan"
        }
        
        print("📤 ProjectManager: Création du plan de projet...")
        project_plan = await self._assign_task_to_agent(
            session,
            "ProjectManager",
            planning_task
        )
        
        # Distribution des responsabilités
        print("\n📊 Distribution des tâches par le ProjectManager:")
        
        # Simuler la distribution des tâches
        task_distribution = {
            "sprint_1": {
                "duration": "2 semaines",
                "tasks": [
                    {"agent": "TechLead", "task": "Concevoir l'architecture système"},
                    {"agent": "BackendDeveloper", "task": "Implémenter l'API REST"},
                    {"agent": "FrontendDeveloper", "task": "Créer l'interface utilisateur"},
                    {"agent": "DevOpsEngineer", "task": "Configurer l'environnement de développement"}
                ]
            },
            "sprint_2": {
                "duration": "2 semaines",
                "tasks": [
                    {"agent": "BackendDeveloper", "task": "Implémenter la logique métier"},
                    {"agent": "FrontendDeveloper", "task": "Intégrer avec l'API"},
                    {"agent": "QAEngineer", "task": "Créer les tests automatisés"},
                    {"agent": "DocumentationWriter", "task": "Commencer la documentation"}
                ]
            }
        }
        
        for sprint, details in task_distribution.items():
            print(f"\n   {sprint.upper()} ({details['duration']}):")
            for task in details['tasks']:
                print(f"   • {task['agent']}: {task['task']}")
        
        self.project_data["phases"]["planning"] = {
            "project_plan": project_plan,
            "task_distribution": task_distribution,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase de planification complétée")
    
    async def _phase_development(self, session: aiohttp.ClientSession):
        """Phase 3: Développement du projet"""
        print("\n\n💻 PHASE 3: DÉVELOPPEMENT")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.DEVELOPMENT
        
        # Sprint 1: Architecture et fondations
        print("\n🏃 SPRINT 1: Architecture et Fondations")
        print("-" * 40)
        
        # TechLead conçoit l'architecture
        architecture_task = {
            "title": "Concevoir l'architecture système",
            "description": "Créer les diagrammes et définir la structure du projet",
            "expected_output": "architecture_design"
        }
        
        print("📤 TechLead: Conception de l'architecture...")
        architecture = await self._assign_task_to_agent(
            session,
            "TechLead",
            architecture_task
        )
        
        # Coordination entre TechLead et développeurs
        await self._broadcast_to_team(
            session,
            "TechLead",
            ["BackendDeveloper", "FrontendDeveloper"],
            {
                "type": "architecture_briefing",
                "content": "Présentation de l'architecture système",
                "architecture": architecture
            }
        )
        
        # Développement en parallèle
        print("\n🔧 Développement en parallèle:")
        
        # Backend development
        backend_task = {
            "title": "Implémenter l'API REST",
            "description": "Créer les endpoints et la logique de base",
            "architecture": architecture,
            "expected_output": "api_implementation"
        }
        
        # Frontend development
        frontend_task = {
            "title": "Créer l'interface utilisateur",
            "description": "Développer les composants UI principaux",
            "architecture": architecture,
            "expected_output": "ui_implementation"
        }
        
        # DevOps setup
        devops_task = {
            "title": "Configurer l'infrastructure",
            "description": "Mettre en place Docker, CI/CD et environnements",
            "expected_output": "infrastructure_config"
        }
        
        # Exécution parallèle des tâches
        results = await asyncio.gather(
            self._assign_task_to_agent(session, "BackendDeveloper", backend_task),
            self._assign_task_to_agent(session, "FrontendDeveloper", frontend_task),
            self._assign_task_to_agent(session, "DevOpsEngineer", devops_task)
        )
        
        print("   ✅ API Backend implémentée")
        print("   ✅ Interface Frontend créée")
        print("   ✅ Infrastructure configurée")
        
        # Intégration et synchronisation
        print("\n🔄 Synchronisation de l'équipe...")
        await self._team_sync_meeting(session, "Sprint 1 Review")
        
        # Sprint 2: Fonctionnalités avancées
        print("\n\n🏃 SPRINT 2: Fonctionnalités Avancées")
        print("-" * 40)
        
        # Tâches du sprint 2
        advanced_features = await self._develop_advanced_features(session)
        
        self.project_data["phases"]["development"] = {
            "architecture": architecture,
            "sprint_1_results": results,
            "sprint_2_results": advanced_features,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase de développement complétée")
    
    async def _phase_testing(self, session: aiohttp.ClientSession):
        """Phase 4: Tests et Assurance Qualité"""
        print("\n\n🧪 PHASE 4: TESTS ET ASSURANCE QUALITÉ")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.TESTING
        
        # QAEngineer coordonne les tests
        test_plan_task = {
            "title": "Créer et exécuter le plan de test",
            "description": "Tests unitaires, intégration, et end-to-end",
            "context": {
                "development_results": self.project_data["phases"]["development"]
            },
            "expected_output": "test_results"
        }
        
        print("📤 QAEngineer: Exécution des tests...")
        test_results = await self._assign_task_to_agent(
            session,
            "QAEngineer",
            test_plan_task
        )
        
        # Simulation de résultats de tests
        print("\n📊 Résultats des tests:")
        print("   • Tests unitaires: 156/156 ✅ (100%)")
        print("   • Tests d'intégration: 45/48 ⚠️ (93.75%)")
        print("   • Tests E2E: 22/25 ⚠️ (88%)")
        print("   • Coverage: 87%")
        
        # Communication des bugs aux développeurs
        bugs_found = [
            {"severity": "high", "component": "backend", "description": "API timeout sur charge élevée"},
            {"severity": "medium", "component": "frontend", "description": "Problème de responsive sur mobile"},
            {"severity": "low", "component": "backend", "description": "Log verbeux en production"}
        ]
        
        print("\n🐛 Bugs identifiés:")
        for bug in bugs_found:
            print(f"   • [{bug['severity'].upper()}] {bug['component']}: {bug['description']}")
        
        # Correction des bugs
        print("\n🔧 Correction des bugs en cours...")
        
        # Assignation des bugs aux développeurs
        for bug in bugs_found:
            if bug["component"] == "backend":
                await self._inter_agent_communication(
                    session,
                    "QAEngineer",
                    "BackendDeveloper",
                    {
                        "type": "bug_report",
                        "bug": bug,
                        "priority": bug["severity"]
                    }
                )
            else:
                await self._inter_agent_communication(
                    session,
                    "QAEngineer",
                    "FrontendDeveloper",
                    {
                        "type": "bug_report",
                        "bug": bug,
                        "priority": bug["severity"]
                    }
                )
        
        # Attendre les corrections
        await asyncio.sleep(2)  # Simulation
        
        print("\n✅ Tous les bugs critiques corrigés")
        print("📊 Tests de régression: 100% passés")
        
        self.project_data["phases"]["testing"] = {
            "test_results": test_results,
            "bugs_found": bugs_found,
            "final_status": "all_tests_passing",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase de tests complétée")
    
    async def _phase_documentation(self, session: aiohttp.ClientSession):
        """Phase 5: Documentation du projet"""
        print("\n\n📚 PHASE 5: DOCUMENTATION")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.DOCUMENTATION
        
        # DocumentationWriter crée la documentation complète
        doc_task = {
            "title": "Créer la documentation complète du projet",
            "description": "Documentation technique, API, et guide utilisateur",
            "context": {
                "architecture": self.project_data["phases"]["development"]["architecture"],
                "api_specs": "OpenAPI 3.0 specifications",
                "user_flows": "Main user journeys"
            },
            "expected_output": "complete_documentation"
        }
        
        print("📤 DocumentationWriter: Création de la documentation...")
        documentation = await self._assign_task_to_agent(
            session,
            "DocumentationWriter",
            doc_task
        )
        
        # Types de documentation créés
        doc_types = [
            "README.md - Guide de démarrage rapide",
            "API_REFERENCE.md - Documentation complète de l'API",
            "ARCHITECTURE.md - Décisions d'architecture",
            "USER_GUIDE.md - Guide utilisateur détaillé",
            "DEPLOYMENT.md - Guide de déploiement",
            "CONTRIBUTING.md - Guide de contribution"
        ]
        
        print("\n📄 Documents créés:")
        for doc in doc_types:
            print(f"   • {doc}")
        
        # Revue collaborative de la documentation
        print("\n👀 Revue collaborative de la documentation...")
        
        # TechLead révise la documentation technique
        await self._inter_agent_communication(
            session,
            "DocumentationWriter",
            "TechLead",
            {
                "type": "review_request",
                "content": "Revue de la documentation technique",
                "documents": ["ARCHITECTURE.md", "API_REFERENCE.md"]
            }
        )
        
        print("   ✅ Documentation technique validée par TechLead")
        print("   ✅ Guide utilisateur validé par ClientLiaison")
        
        self.project_data["phases"]["documentation"] = {
            "documents": doc_types,
            "status": "completed_and_reviewed",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase de documentation complétée")
    
    async def _phase_deployment(self, session: aiohttp.ClientSession):
        """Phase 6: Déploiement en production"""
        print("\n\n🚀 PHASE 6: DÉPLOIEMENT")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.DEPLOYMENT
        
        # DevOpsEngineer gère le déploiement
        deployment_task = {
            "title": "Déployer l'application en production",
            "description": "Déploiement complet avec monitoring et backups",
            "context": {
                "infrastructure": "Kubernetes cluster",
                "environment": "Production AWS",
                "strategy": "Blue-Green deployment"
            },
            "expected_output": "deployment_status"
        }
        
        print("📤 DevOpsEngineer: Déploiement en production...")
        
        # Étapes de déploiement
        deployment_steps = [
            "🔍 Vérification des prérequis",
            "📦 Build des images Docker",
            "🔐 Configuration des secrets",
            "☸️ Déploiement sur Kubernetes",
            "🔄 Migration de base de données",
            "🌐 Configuration du load balancer",
            "📊 Activation du monitoring",
            "✅ Tests de santé"
        ]
        
        for step in deployment_steps:
            print(f"   {step}")
            await asyncio.sleep(0.5)  # Simulation
        
        deployment_result = await self._assign_task_to_agent(
            session,
            "DevOpsEngineer",
            deployment_task
        )
        
        # Vérification post-déploiement
        print("\n🔍 Vérification post-déploiement:")
        print("   • Application: ✅ Running")
        print("   • Database: ✅ Connected")
        print("   • API Health: ✅ Healthy")
        print("   • SSL Certificate: ✅ Valid")
        print("   • Monitoring: ✅ Active")
        
        # URLs de production
        print("\n🌐 URLs de production:")
        print("   • Application: https://app.project-mas.com")
        print("   • API: https://api.project-mas.com")
        print("   • Documentation: https://docs.project-mas.com")
        print("   • Monitoring: https://monitoring.project-mas.com")
        
        self.project_data["phases"]["deployment"] = {
            "status": "successfully_deployed",
            "urls": {
                "app": "https://app.project-mas.com",
                "api": "https://api.project-mas.com",
                "docs": "https://docs.project-mas.com"
            },
            "completed_at": datetime.utcnow().isoformat()
        }
        
        print("\n✅ Phase de déploiement complétée")
    
    async def _phase_delivery(self, session: aiohttp.ClientSession):
        """Phase 7: Livraison au client"""
        print("\n\n🎁 PHASE 7: LIVRAISON AU CLIENT")
        print("-" * 60)
        
        self.current_phase = ProjectPhase.DELIVERY
        
        # ClientLiaison prépare la livraison
        delivery_task = {
            "title": "Préparer la livraison finale au client",
            "description": "Package complet avec documentation et accès",
            "context": {
                "project_data": self.project_data,
                "client": self.project_data["client_request"]["client_name"]
            },
            "expected_output": "delivery_package"
        }
        
        print("📤 ClientLiaison: Préparation du package de livraison...")
        delivery_package = await self._assign_task_to_agent(
            session,
            "ClientLiaison",
            delivery_task
        )
        
        # Contenu de la livraison
        print("\n📦 Package de livraison:")
        print("   • Code source complet (GitHub)")
        print("   • Documentation complète")
        print("   • Accès aux environnements")
        print("   • Guide de démarrage rapide")
        print("   • Contrat de maintenance")
        print("   • Rapport de projet détaillé")
        
        # Communication finale avec le client
        print("\n💬 Communication avec le client:")
        print(f"   De: ClientLiaison")
        print(f"   À: {self.project_data['client_request']['client_name']}")
        print(f"   Objet: Livraison du projet {self.project_data['client_request']['project_name']}")
        print("\n   Message:")
        print("   Nous sommes heureux de vous annoncer que votre projet")
        print("   a été complété avec succès. Tous les objectifs ont été")
        print("   atteints et l'application est maintenant en production.")
        
        # Métriques finales
        print("\n📊 Métriques du projet:")
        print(f"   • Durée totale: 6 semaines")
        print(f"   • Budget utilisé: 92% du budget alloué")
        print(f"   • Qualité: 98% (basé sur les tests et revues)")
        print(f"   • Satisfaction équipe: 95%")
        
        self.project_data["phases"]["delivery"] = {
            "package": delivery_package,
            "delivered_to": self.project_data["client_request"]["client_name"],
            "status": "delivered",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        self.current_phase = ProjectPhase.COMPLETED
        print("\n✅ Projet livré avec succès!")
    
    # Méthodes utilitaires
    async def _create_user(self, session: aiohttp.ClientSession, 
                          username: str, email: str, password: str) -> Optional[Dict]:
        """Crée un utilisateur et retourne le token"""
        try:
            # Enregistrement
            register_data = {
                "username": username,
                "email": email,
                "password": password
            }
            
            async with session.post(
                f"{API_BASE_URL.replace('/api/v1', '')}/auth/register",
                json=register_data
            ) as resp:
                if resp.status not in [200, 201]:
                    logger.error(f"Failed to register {username}: {resp.status}")
                    return None
            
            # Connexion
            login_data = {
                "username": username,
                "password": password
            }
            
            async with session.post(
                f"{API_BASE_URL.replace('/api/v1', '')}/auth/login",
                data=login_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "token": data["access_token"],
                        "username": username
                    }
                    
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
        
        return None
    
    async def _create_agent(self, session: aiohttp.ClientSession,
                           token: str, name: str, agent_type: str,
                           capabilities: Dict) -> Optional[Dict]:
        """Crée un agent avec les capacités spécifiées"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            agent_data = {
                "name": name,
                "type": agent_type,
                "description": capabilities.get("role", "Agent MAS"),
                "capabilities": capabilities,
                "model": "gpt-4"
            }
            
            async with session.post(
                f"{API_BASE_URL}/agents",
                json=agent_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    agent = await resp.json()
                    
                    # Démarrer l'agent
                    async with session.post(
                        f"{API_BASE_URL}/agents/{agent['id']}/start",
                        headers=headers
                    ) as start_resp:
                        if start_resp.status == 200:
                            return agent
                            
        except Exception as e:
            logger.error(f"Error creating agent {name}: {str(e)}")
        
        return None
    
    async def _assign_task_to_agent(self, session: aiohttp.ClientSession,
                                   agent_name: str, task: Dict) -> Dict:
        """Assigne une tâche à un agent et attend le résultat"""
        agent_info = self.agents.get(agent_name)
        if not agent_info:
            return {"error": f"Agent {agent_name} not found"}
        
        headers = {"Authorization": f"Bearer {agent_info['token']}"}
        
        task_data = {
            "title": task["title"],
            "description": task["description"],
            "priority": "high",
            "metadata": task
        }
        
        try:
            # Créer la tâche
            async with session.post(
                f"{API_BASE_URL}/agents/{agent_info['id']}/tasks",
                json=task_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    # Simuler le traitement
                    await asyncio.sleep(2)
                    
                    # Retourner un résultat simulé
                    return {
                        "status": "completed",
                        "agent": agent_name,
                        "task": task["title"],
                        "result": f"{task.get('expected_output', 'task_result')}_completed",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error assigning task to {agent_name}: {str(e)}")
        
        return {"error": "Task assignment failed"}
    
    async def _inter_agent_communication(self, session: aiohttp.ClientSession,
                                       sender: str, recipient: str,
                                       message: Dict):
        """Gère la communication entre agents"""
        sender_info = self.agents.get(sender)
        recipient_info = self.agents.get(recipient)
        
        if not sender_info or not recipient_info:
            return
        
        headers = {"Authorization": f"Bearer {sender_info['token']}"}
        
        message_data = {
            "recipient": recipient_info["id"],
            "performative": message.get("type", "inform"),
            "content": message
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/agents/{sender_info['id']}/messages",
                json=message_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.communication_log.append({
                        "from": sender,
                        "to": recipient,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error in agent communication: {str(e)}")
    
    async def _broadcast_to_team(self, session: aiohttp.ClientSession,
                               sender: str, recipients: List[str],
                               message: Dict):
        """Diffuse un message à plusieurs agents"""
        tasks = []
        for recipient in recipients:
            task = self._inter_agent_communication(session, sender, recipient, message)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _team_sync_meeting(self, session: aiohttp.ClientSession, meeting_topic: str):
        """Simule une réunion de synchronisation d'équipe"""
        print(f"\n🤝 Réunion d'équipe: {meeting_topic}")
        
        # Le ProjectManager anime la réunion
        all_agents = list(self.agents.keys())
        if "ProjectManager" in all_agents:
            all_agents.remove("ProjectManager")
        
        await self._broadcast_to_team(
            session,
            "ProjectManager",
            all_agents,
            {
                "type": "meeting",
                "topic": meeting_topic,
                "agenda": ["Progress update", "Blockers", "Next steps"]
            }
        )
        
        print("   • Tous les agents synchronisés")
        print("   • Blockers identifiés et résolus")
        print("   • Prochaines étapes clarifiées")
    
    async def _develop_advanced_features(self, session: aiohttp.ClientSession) -> Dict:
        """Développe les fonctionnalités avancées du sprint 2"""
        features = {
            "authentication": "Système d'authentification JWT",
            "real_time": "WebSocket pour les mises à jour temps réel",
            "analytics": "Dashboard analytique",
            "notifications": "Système de notifications push"
        }
        
        print("\n🚀 Développement des fonctionnalités avancées:")
        for feature, description in features.items():
            print(f"   • {description}")
            await asyncio.sleep(0.5)  # Simulation
        
        return {
            "features": features,
            "status": "completed",
            "quality": "production_ready"
        }
    
    async def _configure_agent_capabilities(self, session: aiohttp.ClientSession):
        """Configure les capacités détaillées de chaque agent"""
        # Configuration avancée des agents (règles, seuils, etc.)
        pass
    
    async def _setup_communication_channels(self, session: aiohttp.ClientSession):
        """Établit les canaux de communication entre agents"""
        # Configuration des canaux de communication privilégiés
        pass
    
    def _display_final_summary(self):
        """Affiche le résumé final du projet"""
        print("\n📊 RÉSUMÉ FINAL DU PROJET")
        print("="*60)
        print(f"🆔 ID Projet: {self.project_data['id']}")
        print(f"📋 Nom: {self.project_data['client_request']['project_name']}")
        print(f"🏢 Client: {self.project_data['client_request']['client_name']}")
        print(f"⏱️ Durée: 6 semaines")
        print(f"👥 Équipe: {len(self.agents)} agents")
        print(f"📨 Communications: {len(self.communication_log)} messages échangés")
        
        print("\n✅ Livrables:")
        print("   • Application web complète")
        print("   • API REST documentée")
        print("   • Tests automatisés (87% coverage)")
        print("   • Documentation complète")
        print("   • Infrastructure DevOps")
        print("   • Monitoring et alerting")
        
        print("\n🎯 Objectifs atteints:")
        print("   • ✅ Respect du délai")
        print("   • ✅ Dans le budget")
        print("   • ✅ Qualité production")
        print("   • ✅ Client satisfait")


async def main():
    """Fonction principale pour démontrer le système complet"""
    
    # Créer le système
    pms = ProjectManagementSystem()
    
    # Initialiser avec tous les agents
    await pms.initialize_system()
    
    # Simuler une demande client
    client_request = {
        "client_name": "TechCorp Industries",
        "project_name": "Plateforme de Gestion des Ressources Humaines",
        "description": """
        Nous avons besoin d'une plateforme moderne de gestion RH incluant:
        - Gestion des employés et des départements
        - Système de congés et absences
        - Évaluations de performance
        - Tableau de bord analytique
        - Intégration avec notre système de paie existant
        - Application mobile pour les employés
        """,
        "requirements": [
            "Interface web responsive",
            "API REST pour intégrations",
            "Authentification SSO",
            "Support multi-tenant",
            "Conformité RGPD",
            "Haute disponibilité (99.9%)"
        ],
        "deadline": (datetime.utcnow() + timedelta(days=42)).isoformat(),
        "budget": 150000,
        "contact": "john.doe@techcorp.com"
    }
    
    # Traiter la demande de bout en bout
    await pms.process_client_request(client_request)
    
    print("\n🎉 Démonstration complète du système MAS terminée!")
    print("Ce système a démontré:")
    print("• Collaboration entre 8 agents spécialisés")
    print("• Gestion complète d'un projet de développement")
    print("• Communication inter-agents sophistiquée")
    print("• Adaptation aux différentes phases du projet")
    print("• Livraison réussie au client")


if __name__ == "__main__":
    asyncio.run(main())