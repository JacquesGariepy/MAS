#!/usr/bin/env python3
"""
Diagnose Agent Processing
Diagnostic pour comprendre pourquoi les agents ne traitent pas les tâches
"""

import asyncio
import json
from datetime import datetime
from uuid import UUID
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from services.core.src.database.models import Task, Agent, Message
from services.core.src.core.agents import get_agent_runtime


async def diagnose_agent_processing():
    """Diagnostic complet du traitement des tâches par les agents"""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_production"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    runtime = get_agent_runtime()
    
    print("🔍 Diagnostic du traitement des tâches par les agents")
    print("=" * 60)
    
    async with SessionLocal() as session:
        # 1. Vérifier tous les agents actifs
        print("\n1️⃣ Agents actifs dans la base de données:")
        stmt = select(Agent).where(Agent.is_active == True)
        result = await session.execute(stmt)
        agents = result.scalars().all()
        
        for agent in agents:
            print(f"\n👤 {agent.name} ({agent.role})")
            print(f"   ID: {agent.id}")
            print(f"   Type: {agent.agent_type}")
            print(f"   Status: {agent.status}")
            print(f"   Dernière activité: {agent.last_active_at}")
            
            # Vérifier dans le runtime
            is_running = await runtime.is_agent_running(agent.id)
            print(f"   En cours d'exécution: {'✅' if is_running else '❌'}")
            
            # Compter les tâches
            task_stmt = select(Task).where(Task.assigned_to == agent.id)
            task_result = await session.execute(task_stmt)
            all_tasks = task_result.scalars().all()
            
            pending_tasks = [t for t in all_tasks if t.status == "pending"]
            completed_tasks = [t for t in all_tasks if t.status == "completed"]
            
            print(f"   Tâches: {len(all_tasks)} total")
            print(f"     - En attente: {len(pending_tasks)}")
            print(f"     - Complétées: {len(completed_tasks)}")
            print(f"     - Avec résultat: {len([t for t in completed_tasks if t.result is not None])}")
        
        # 2. Vérifier les agents dans le runtime
        print(f"\n2️⃣ Agents dans le runtime:")
        running_agents = runtime.list_running_agents()
        print(f"   Nombre d'agents en cours: {len(running_agents)}")
        
        for agent_id in running_agents:
            runtime_agent = runtime.get_running_agent(agent_id)
            if runtime_agent:
                print(f"\n   🏃 Agent en cours: {runtime_agent.name}")
                metrics = await runtime_agent.get_metrics()
                print(f"      Actions: {metrics['actions_executed']}")
                print(f"      Messages: {metrics['messages_processed']}")
                print(f"      Tâches: {metrics['tasks_completed']}")
                print(f"      Erreurs: {metrics['errors']}")
                print(f"      File de tâches: {runtime_agent._tasks.qsize()} en attente")
                print(f"      File de messages: {runtime_agent._message_queue.qsize()} en attente")
                print(f"      En cours d'exécution: {'✅' if runtime_agent._running else '❌'}")
        
        # 3. Analyser les problèmes potentiels
        print("\n3️⃣ Analyse des problèmes potentiels:")
        
        # Agents avec status working mais pas dans le runtime
        working_not_running = []
        for agent in agents:
            if agent.status == "working" and not await runtime.is_agent_running(agent.id):
                working_not_running.append(agent)
        
        if working_not_running:
            print("\n❌ Agents marqués 'working' mais non actifs:")
            for agent in working_not_running:
                print(f"   - {agent.name} (ID: {agent.id})")
        
        # Tâches anciennes en pending
        print("\n⏰ Tâches en attente depuis longtemps:")
        old_pending_stmt = select(Task).where(
            Task.status == "pending",
            Task.created_at < datetime.utcnow().replace(hour=datetime.utcnow().hour - 1)
        )
        old_pending_result = await session.execute(old_pending_stmt)
        old_tasks = old_pending_result.scalars().all()
        
        for task in old_tasks[:5]:  # Limiter à 5
            age = datetime.utcnow() - task.created_at
            print(f"   - {task.title} (âge: {age.total_seconds() / 3600:.1f}h)")
            if task.assigned_to:
                agent_stmt = select(Agent).where(Agent.id == task.assigned_to)
                agent_result = await session.execute(agent_stmt)
                agent = agent_result.scalar_one_or_none()
                if agent:
                    print(f"     Assignée à: {agent.name} (status: {agent.status})")
        
        # 4. Vérifier la configuration
        print("\n4️⃣ Points de vérification:")
        
        # Le runtime a-t-il été initialisé correctement ?
        print(f"   ✓ Runtime initialisé: {'✅' if runtime else '❌'}")
        
        # Y a-t-il des erreurs dans les logs récents ?
        recent_messages_stmt = select(Message).where(
            Message.performative == "failure"
        ).order_by(Message.created_at.desc()).limit(5)
        recent_messages_result = await session.execute(recent_messages_stmt)
        error_messages = recent_messages_result.scalars().all()
        
        if error_messages:
            print(f"\n   ⚠️  Messages d'erreur récents:")
            for msg in error_messages:
                print(f"      - {msg.created_at}: {msg.content.get('error', 'Unknown error')}")
        
        # 5. Recommandations
        print("\n5️⃣ Recommandations:")
        
        if not running_agents:
            print("   🔸 Aucun agent n'est actuellement en cours d'exécution")
            print("      → Utilisez le script 'start_agent.py' pour démarrer les agents")
        
        if working_not_running:
            print("   🔸 Des agents ont un status incorrect")
            print("      → Réinitialisez leur status ou redémarrez-les")
        
        if old_tasks:
            print("   🔸 Des tâches sont bloquées depuis longtemps")
            print("      → Utilisez 'force_task_completion.py' pour les débloquer")
        
        print("\n📌 Problème principal identifié:")
        if not running_agents:
            print("   Les agents ne sont pas démarrés dans le runtime.")
            print("   Le système a des agents créés mais ils ne sont pas actifs.")
            print("\n   Solution: Démarrer les agents avec le runtime approprié")
            print("   ou utiliser 'force_task_completion.py' pour traiter manuellement.")
        else:
            print("   Les agents sont actifs mais peuvent avoir des problèmes de traitement.")
            print("   Vérifiez les logs et les configurations des agents.")


if __name__ == "__main__":
    asyncio.run(diagnose_agent_processing())