#!/usr/bin/env python3
"""
Task Response Tracker
Suit et enregistre les réponses des tâches exécutées par les agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from services.core.src.database.models import Task, Agent, Message


class TaskResponseTracker:
    """Gestionnaire pour suivre et enregistrer les réponses des tâches"""
    
    def __init__(self, database_url: str):
        """
        Initialise le tracker
        
        Args:
            database_url: URL de connexion à la base de données
        """
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_task_response(
        self, 
        task_id: UUID, 
        response_data: Dict[str, Any],
        status: str = "completed"
    ) -> Optional[Task]:
        """
        Enregistre la réponse d'une tâche
        
        Args:
            task_id: ID de la tâche
            response_data: Données de réponse à stocker
            status: Nouveau statut de la tâche
            
        Returns:
            Task mise à jour ou None si erreur
        """
        async with self.SessionLocal() as session:
            # Récupérer la tâche
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                print(f"❌ Tâche {task_id} non trouvée!")
                return None
            
            # Mettre à jour la tâche avec la réponse
            task.result = response_data
            task.status = status
            task.updated_at = datetime.utcnow()
            
            if status == "completed":
                task.completed_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(task)
            
            print(f"✅ Réponse enregistrée pour la tâche {task.title}")
            return task
    
    async def track_task_execution(self, task_id: UUID, agent_id: UUID):
        """
        Simule l'exécution d'une tâche et enregistre les résultats
        
        Args:
            task_id: ID de la tâche à exécuter
            agent_id: ID de l'agent exécutant
        """
        async with self.SessionLocal() as session:
            # Récupérer la tâche et l'agent
            task_stmt = select(Task).where(Task.id == task_id)
            task_result = await session.execute(task_stmt)
            task = task_result.scalar_one_or_none()
            
            agent_stmt = select(Agent).where(Agent.id == agent_id)
            agent_result = await session.execute(agent_stmt)
            agent = agent_result.scalar_one_or_none()
            
            if not task or not agent:
                print("❌ Tâche ou agent non trouvé!")
                return
            
            print(f"\n🚀 Exécution de la tâche '{task.title}' par l'agent '{agent.name}'")
            
            # Marquer la tâche comme en cours
            task.status = "in_progress"
            task.updated_at = datetime.utcnow()
            await session.commit()
            
            # Simuler l'exécution de la tâche
            print("⏳ Traitement en cours...")
            await asyncio.sleep(2)  # Simulation
            
            # Générer une réponse basée sur le type de tâche
            response = await self._generate_task_response(task, agent)
            
            # Créer un message de l'agent pour documenter l'exécution
            message = Message(
                id=uuid4(),
                sender_id=agent.id,
                receiver_id=agent.id,  # Message à soi-même pour documentation
                performative="inform",
                content={
                    "task_id": str(task.id),
                    "action": "task_completed",
                    "result": response,
                    "execution_time": "2 seconds",
                    "timestamp": datetime.utcnow().isoformat()
                },
                protocol="fipa-acl",
                conversation_id=uuid4(),
                created_at=datetime.utcnow()
            )
            
            session.add(message)
            
            # Mettre à jour les métriques de l'agent
            agent.total_actions += 1
            agent.successful_actions += 1
            agent.total_messages += 1
            agent.last_active_at = datetime.utcnow()
            
            # Enregistrer la réponse dans la tâche
            task.result = response
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            await session.commit()
            
            print(f"✅ Tâche terminée avec succès!")
            print(f"📊 Résultat: {json.dumps(response, indent=2)}")
    
    async def _generate_task_response(self, task: Task, agent: Agent) -> Dict[str, Any]:
        """
        Génère une réponse simulée basée sur le type de tâche
        
        Args:
            task: La tâche à exécuter
            agent: L'agent exécutant
            
        Returns:
            Dictionnaire contenant la réponse
        """
        response = {
            "success": True,
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "task_type": task.task_type,
            "execution_time": "2 seconds",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Adapter la réponse selon le type de tâche
        if task.task_type == "analysis":
            response.update({
                "analysis_results": {
                    "data_points_analyzed": 150,
                    "patterns_found": 3,
                    "anomalies_detected": 0,
                    "confidence_score": 0.92,
                    "recommendations": [
                        "Continue monitoring current trends",
                        "No immediate action required",
                        "Review again in 24 hours"
                    ]
                }
            })
        elif task.task_type == "data_processing":
            response.update({
                "processing_results": {
                    "records_processed": 1000,
                    "records_created": 50,
                    "records_updated": 200,
                    "records_deleted": 0,
                    "errors_encountered": 0,
                    "processing_speed": "500 records/second"
                }
            })
        elif task.task_type == "negotiation":
            response.update({
                "negotiation_results": {
                    "participants": 3,
                    "rounds": 5,
                    "agreement_reached": True,
                    "final_terms": {
                        "price": 150.00,
                        "quantity": 10,
                        "delivery_date": "2024-02-01"
                    },
                    "satisfaction_score": 0.85
                }
            })
        elif task.task_type == "coordination":
            response.update({
                "coordination_results": {
                    "agents_coordinated": 4,
                    "tasks_distributed": 12,
                    "conflicts_resolved": 2,
                    "efficiency_gain": "35%",
                    "timeline": {
                        "start": datetime.utcnow().isoformat(),
                        "estimated_completion": "2024-01-15T18:00:00"
                    }
                }
            })
        else:
            # Type générique
            response.update({
                "generic_results": {
                    "status": "completed",
                    "output": f"Task '{task.title}' executed successfully",
                    "metrics": {
                        "cpu_usage": "15%",
                        "memory_usage": "250MB",
                        "network_calls": 5
                    }
                }
            })
        
        # Ajouter les métadonnées de la tâche si disponibles
        if task.task_metadata:
            response["task_metadata"] = task.task_metadata
        
        return response
    
    async def get_task_history(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Récupère l'historique complet des tâches d'un agent
        
        Args:
            agent_id: ID de l'agent
            
        Returns:
            Dictionnaire contenant l'historique des tâches
        """
        async with self.SessionLocal() as session:
            # Récupérer toutes les tâches de l'agent
            stmt = select(Task).where(Task.assigned_to == agent_id).order_by(Task.created_at.desc())
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            history = {
                "agent_id": str(agent_id),
                "total_tasks": len(tasks),
                "tasks_by_status": {},
                "tasks_by_type": {},
                "recent_tasks": []
            }
            
            # Analyser les tâches
            for task in tasks:
                # Par statut
                status = task.status
                if status not in history["tasks_by_status"]:
                    history["tasks_by_status"][status] = 0
                history["tasks_by_status"][status] += 1
                
                # Par type
                task_type = task.task_type
                if task_type not in history["tasks_by_type"]:
                    history["tasks_by_type"][task_type] = 0
                history["tasks_by_type"][task_type] += 1
                
                # Ajouter aux tâches récentes (max 5)
                if len(history["recent_tasks"]) < 5:
                    history["recent_tasks"].append({
                        "id": str(task.id),
                        "title": task.title,
                        "type": task.task_type,
                        "status": task.status,
                        "priority": task.priority,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "has_result": task.result is not None
                    })
            
            return history


async def demo_task_tracking():
    """Démonstration du suivi des tâches"""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_production"
    
    tracker = TaskResponseTracker(DATABASE_URL)
    
    # IDs de test (à remplacer par des IDs réels)
    AGENT_ID = UUID("cebac9bf-55f1-4f03-93b5-ecd89127b834")
    
    print("🔍 Démonstration du suivi des réponses de tâches")
    print("=" * 60)
    
    # Créer une tâche de test
    async with tracker.SessionLocal() as session:
        # Vérifier si l'agent existe
        agent_stmt = select(Agent).where(Agent.id == AGENT_ID)
        agent_result = await session.execute(agent_stmt)
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            print(f"❌ Agent {AGENT_ID} non trouvé!")
            return
        
        print(f"✅ Agent trouvé: {agent.name} ({agent.role})")
        
        # Créer une nouvelle tâche
        new_task = Task(
            id=uuid4(),
            owner_id=agent.owner_id,
            title="Analyse des données de performance",
            description="Analyser les métriques de performance du système",
            task_type="analysis",
            status="pending",
            priority="high",
            assigned_to=AGENT_ID,
            task_metadata={
                "target_metrics": ["response_time", "throughput", "error_rate"],
                "time_window": "last_24_hours"
            },
            created_at=datetime.utcnow()
        )
        
        session.add(new_task)
        await session.commit()
        
        print(f"\n📝 Nouvelle tâche créée: {new_task.title}")
        print(f"   ID: {new_task.id}")
        print(f"   Type: {new_task.task_type}")
        print(f"   Priorité: {new_task.priority}")
        
        # Exécuter la tâche
        await tracker.track_task_execution(new_task.id, AGENT_ID)
        
        # Afficher l'historique
        print("\n📊 Historique des tâches de l'agent:")
        history = await tracker.get_task_history(AGENT_ID)
        print(json.dumps(history, indent=2))


async def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await demo_task_tracking()
    else:
        print("Usage:")
        print("  python task_response_tracker.py demo    # Exécuter la démonstration")
        print("\nCe script montre comment:")
        print("  - Créer et assigner des tâches aux agents")
        print("  - Suivre l'exécution des tâches")
        print("  - Enregistrer les réponses dans la colonne 'result'")
        print("  - Générer des messages de documentation")
        print("  - Mettre à jour les métriques des agents")


if __name__ == "__main__":
    asyncio.run(main())