#!/usr/bin/env python3
"""
Force Task Completion
Script pour forcer la complétion d'une tâche bloquée en "pending"
et récupérer/générer une réponse
"""

import asyncio
import json
from datetime import datetime
from uuid import UUID, uuid4
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from services.core.src.database.models import Task, Agent, Message
from services.core.src.core.agents import AgentFactory, get_agent_runtime
from services.core.src.services.llm_service import LLMService
from services.core.src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskForcer:
    """Gestionnaire pour forcer la complétion de tâches bloquées"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.runtime = get_agent_runtime()
    
    async def check_pending_tasks(self, agent_id: UUID = None):
        """Vérifie toutes les tâches en pending"""
        async with self.SessionLocal() as session:
            stmt = select(Task).where(Task.status == "pending")
            if agent_id:
                stmt = stmt.where(Task.assigned_to == agent_id)
            
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            print(f"\n🔍 Tâches en attente trouvées: {len(tasks)}")
            for task in tasks:
                print(f"\n📌 Tâche: {task.title}")
                print(f"   ID: {task.id}")
                print(f"   Type: {task.task_type}")
                print(f"   Priorité: {task.priority}")
                print(f"   Assignée à: {task.assigned_to}")
                print(f"   Créée le: {task.created_at}")
                
                # Vérifier si l'agent est actif
                if task.assigned_to:
                    agent_stmt = select(Agent).where(Agent.id == task.assigned_to)
                    agent_result = await session.execute(agent_stmt)
                    agent = agent_result.scalar_one_or_none()
                    
                    if agent:
                        print(f"   Agent: {agent.name} - Status: {agent.status}")
                        print(f"   Agent actif: {'✅' if agent.is_active else '❌'}")
                        
                        # Vérifier si l'agent est dans le runtime
                        is_running = await self.runtime.is_agent_running(agent.id)
                        print(f"   Agent en cours d'exécution: {'✅' if is_running else '❌'}")
            
            return tasks
    
    async def force_complete_task(self, task_id: UUID):
        """Force la complétion d'une tâche avec une réponse simulée"""
        async with self.SessionLocal() as session:
            # Récupérer la tâche
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                print(f"❌ Tâche {task_id} non trouvée!")
                return None
            
            print(f"\n🔧 Forçage de la complétion de: {task.title}")
            
            # Récupérer l'agent assigné
            agent = None
            if task.assigned_to:
                agent_stmt = select(Agent).where(Agent.id == task.assigned_to)
                agent_result = await session.execute(agent_stmt)
                agent = agent_result.scalar_one_or_none()
            
            # Générer une réponse appropriée
            response = await self._generate_forced_response(task, agent)
            
            # Mettre à jour la tâche
            task.status = "completed"
            task.result = response
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            
            # Créer un message pour documenter l'action
            if agent:
                message = Message(
                    id=uuid4(),
                    sender_id=agent.id,
                    receiver_id=agent.id,
                    performative="inform",
                    content={
                        "action": "task_forced_completion",
                        "task_id": str(task.id),
                        "reason": "Task was stuck in pending state",
                        "forced_by": "system",
                        "result": response
                    },
                    protocol="fipa-acl",
                    conversation_id=uuid4(),
                    created_at=datetime.utcnow()
                )
                session.add(message)
                
                # Mettre à jour les métriques de l'agent
                agent.total_actions += 1
                agent.successful_actions += 1
                agent.last_active_at = datetime.utcnow()
            
            await session.commit()
            
            print(f"✅ Tâche forcée à 'completed'")
            print(f"📊 Réponse générée: {json.dumps(response, indent=2)}")
            
            return task
    
    async def restart_agent_for_task(self, agent_id: UUID):
        """Redémarre un agent pour traiter ses tâches"""
        async with self.SessionLocal() as session:
            # Récupérer l'agent
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await session.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                print(f"❌ Agent {agent_id} non trouvé!")
                return
            
            print(f"\n🔄 Redémarrage de l'agent: {agent.name}")
            
            # Vérifier si l'agent est déjà en cours d'exécution
            if await self.runtime.is_agent_running(agent_id):
                print("⚠️  L'agent est déjà en cours d'exécution")
                
                # Récupérer l'agent du runtime
                runtime_agent = self.runtime.get_running_agent(agent_id)
                if runtime_agent:
                    # Vérifier sa file de tâches
                    print(f"📌 Tâches en attente dans la file: {runtime_agent._tasks.qsize()}")
                    
                    # Forcer le traitement des tâches
                    await self._force_agent_task_processing(runtime_agent)
            else:
                print("🚀 Démarrage de l'agent...")
                
                # Créer et démarrer l'agent
                try:
                    # Simuler un LLM service basique
                    class MockLLMService:
                        async def generate(self, prompt, **kwargs):
                            return json.dumps({
                                "reasoning": "Processing task",
                                "new_intentions": ["complete_current_task"],
                                "confidence": 0.8,
                                "plan_sketch": "Execute task steps"
                            })
                    
                    llm_service = MockLLMService()
                    
                    # Créer l'instance de l'agent
                    runtime_agent = AgentFactory.create_agent(
                        agent_type=agent.agent_type,
                        agent_id=agent.id,
                        name=agent.name,
                        role=agent.role,
                        capabilities=agent.capabilities or [],
                        llm_service=llm_service,
                        initial_beliefs=agent.beliefs or {},
                        initial_desires=agent.desires or []
                    )
                    
                    # Enregistrer et démarrer l'agent
                    await self.runtime.register_agent(runtime_agent)
                    
                    # Ajouter les tâches en attente
                    tasks_stmt = select(Task).where(
                        Task.assigned_to == agent_id,
                        Task.status.in_(["pending", "assigned"])
                    )
                    tasks_result = await session.execute(tasks_stmt)
                    pending_tasks = tasks_result.scalars().all()
                    
                    print(f"📥 Ajout de {len(pending_tasks)} tâches à la file de l'agent")
                    for task in pending_tasks:
                        await runtime_agent.add_task(task)
                    
                    # Démarrer l'agent en arrière-plan
                    asyncio.create_task(runtime_agent.run())
                    
                    # Attendre un peu pour laisser l'agent traiter
                    print("⏳ Attente du traitement des tâches...")
                    await asyncio.sleep(5)
                    
                    # Vérifier le statut
                    metrics = await runtime_agent.get_metrics()
                    print(f"📊 Métriques de l'agent:")
                    print(f"   Actions exécutées: {metrics['actions_executed']}")
                    print(f"   Tâches complétées: {metrics['tasks_completed']}")
                    print(f"   Erreurs: {metrics['errors']}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors du démarrage de l'agent: {str(e)}")
                    print(f"❌ Erreur: {str(e)}")
    
    async def _force_agent_task_processing(self, agent):
        """Force un agent à traiter ses tâches en attente"""
        print("🔨 Forçage du traitement des tâches...")
        
        # Déclencher manuellement le cycle de traitement
        try:
            await agent._process_tasks()
            print("✅ Cycle de traitement forcé")
        except Exception as e:
            print(f"❌ Erreur lors du forçage: {str(e)}")
    
    async def _generate_forced_response(self, task: Task, agent: Agent = None) -> dict:
        """Génère une réponse forcée pour une tâche"""
        base_response = {
            "success": True,
            "forced": True,
            "reason": "Task was stuck in pending state",
            "timestamp": datetime.utcnow().isoformat(),
            "execution_method": "forced_completion"
        }
        
        if agent:
            base_response.update({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "agent_status": agent.status
            })
        
        # Adapter selon le type de tâche
        if task.task_type == "analysis":
            base_response["result"] = {
                "analysis_summary": "Forced completion - Analysis data unavailable",
                "status": "completed_with_warning",
                "data_analyzed": False,
                "recommendations": [
                    "Re-run analysis when agent is available",
                    "Check agent status and configuration"
                ]
            }
        elif task.task_type == "data_processing":
            base_response["result"] = {
                "processing_status": "forced_completion",
                "records_processed": 0,
                "warning": "No actual processing performed"
            }
        elif task.task_type == "negotiation":
            base_response["result"] = {
                "negotiation_status": "aborted",
                "reason": "Agent unavailable",
                "fallback_action": "Use default terms"
            }
        else:
            base_response["result"] = {
                "status": "forced_completion",
                "output": f"Task '{task.title}' marked as complete without execution",
                "warning": "No actual execution performed"
            }
        
        # Inclure les métadonnées de la tâche
        if task.task_metadata:
            base_response["original_metadata"] = task.task_metadata
        
        return base_response
    
    async def analyze_task_blockage(self, task_id: UUID):
        """Analyse pourquoi une tâche est bloquée"""
        async with self.SessionLocal() as session:
            # Récupérer la tâche
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                print(f"❌ Tâche {task_id} non trouvée!")
                return
            
            print(f"\n🔍 Analyse du blocage de: {task.title}")
            print("=" * 60)
            
            analysis = {
                "task_id": str(task.id),
                "status": task.status,
                "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "time_in_pending": None,
                "issues_found": []
            }
            
            # Calculer le temps en pending
            if task.created_at:
                time_diff = datetime.utcnow() - task.created_at
                analysis["time_in_pending"] = f"{time_diff.total_seconds() / 3600:.1f} heures"
                print(f"⏱️  Temps en attente: {analysis['time_in_pending']}")
            
            # Vérifier l'agent
            if task.assigned_to:
                agent_stmt = select(Agent).where(Agent.id == task.assigned_to)
                agent_result = await session.execute(agent_stmt)
                agent = agent_result.scalar_one_or_none()
                
                if not agent:
                    analysis["issues_found"].append("Agent assigné introuvable")
                    print("❌ Agent assigné introuvable!")
                else:
                    print(f"👤 Agent: {agent.name} ({agent.agent_type})")
                    print(f"   Status: {agent.status}")
                    print(f"   Actif: {'Oui' if agent.is_active else 'Non'}")
                    
                    if not agent.is_active:
                        analysis["issues_found"].append("Agent inactif")
                    
                    if agent.status != "working":
                        analysis["issues_found"].append(f"Agent en status '{agent.status}' au lieu de 'working'")
                    
                    # Vérifier si l'agent est dans le runtime
                    is_running = await self.runtime.is_agent_running(agent.id)
                    print(f"   En cours d'exécution: {'Oui' if is_running else 'Non'}")
                    
                    if not is_running:
                        analysis["issues_found"].append("Agent non démarré dans le runtime")
                    else:
                        # Vérifier les métriques de l'agent
                        runtime_agent = self.runtime.get_running_agent(agent.id)
                        if runtime_agent:
                            metrics = await runtime_agent.get_metrics()
                            print(f"   Métriques:")
                            print(f"     - Actions: {metrics['actions_executed']}")
                            print(f"     - Messages: {metrics['messages_processed']}")
                            print(f"     - Tâches: {metrics['tasks_completed']}")
                            print(f"     - Erreurs: {metrics['errors']}")
                            
                            if metrics['errors'] > 0:
                                analysis["issues_found"].append(f"{metrics['errors']} erreurs détectées")
            else:
                analysis["issues_found"].append("Aucun agent assigné")
                print("❌ Aucun agent assigné à la tâche!")
            
            # Vérifier les dépendances
            if task.depends_on:
                print(f"\n📌 Dépendances: {len(task.depends_on)} tâches")
                for dep_id in task.depends_on:
                    dep_stmt = select(Task).where(Task.id == UUID(dep_id))
                    dep_result = await session.execute(dep_stmt)
                    dep_task = dep_result.scalar_one_or_none()
                    
                    if dep_task:
                        print(f"   - {dep_task.title}: {dep_task.status}")
                        if dep_task.status != "completed":
                            analysis["issues_found"].append(f"Dépendance non complétée: {dep_task.title}")
                    else:
                        analysis["issues_found"].append(f"Dépendance introuvable: {dep_id}")
            
            # Résumé
            print(f"\n📊 Résumé de l'analyse:")
            if analysis["issues_found"]:
                print("❌ Problèmes trouvés:")
                for issue in analysis["issues_found"]:
                    print(f"   - {issue}")
            else:
                print("✅ Aucun problème évident détecté")
                print("   La tâche pourrait être en attente de traitement normal")
            
            return analysis


async def main():
    """Fonction principale"""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_production"
    
    forcer = TaskForcer(DATABASE_URL)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python force_task_completion.py check [agent_id]      # Vérifier les tâches en attente")
        print("  python force_task_completion.py analyze <task_id>     # Analyser pourquoi une tâche est bloquée")
        print("  python force_task_completion.py force <task_id>       # Forcer la complétion d'une tâche")
        print("  python force_task_completion.py restart <agent_id>    # Redémarrer un agent")
        print("\nExemple avec l'agent mentionné:")
        print("  python force_task_completion.py check cebac9bf-55f1-4f03-93b5-ecd89127b834")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        agent_id = UUID(sys.argv[2]) if len(sys.argv) > 2 else None
        await forcer.check_pending_tasks(agent_id)
    
    elif command == "analyze" and len(sys.argv) > 2:
        task_id = UUID(sys.argv[2])
        await forcer.analyze_task_blockage(task_id)
    
    elif command == "force" and len(sys.argv) > 2:
        task_id = UUID(sys.argv[2])
        await forcer.force_complete_task(task_id)
    
    elif command == "restart" and len(sys.argv) > 2:
        agent_id = UUID(sys.argv[2])
        await forcer.restart_agent_for_task(agent_id)
    
    else:
        print("❌ Commande invalide. Voir l'usage ci-dessus.")


if __name__ == "__main__":
    asyncio.run(main())