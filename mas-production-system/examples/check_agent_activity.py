#!/usr/bin/env python3
"""
Script simple pour vérifier rapidement l'activité d'un agent
"""

import asyncio
import sys
import os
from uuid import UUID

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from services.core.src.database.models import Agent, Task, Message, Memory


async def check_agent_activity(agent_id: str):
    """Vérifie rapidement l'activité d'un agent"""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_production"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    agent_uuid = UUID(agent_id)
    
    async with SessionLocal() as session:
        # Agent info
        stmt = select(Agent).where(Agent.id == agent_uuid)
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            print(f"❌ Agent {agent_id} non trouvé!")
            return
        
        print(f"\n🤖 Agent: {agent.name} ({agent.role})")
        print(f"   Type: {agent.agent_type}")
        print(f"   Statut: {agent.status}")
        print(f"   Actif: {'✓' if agent.is_active else '✗'}")
        
        # Compter les tâches
        task_count = await session.execute(
            select(func.count()).select_from(Task).where(Task.assigned_to == agent_uuid)
        )
        tasks_total = task_count.scalar()
        
        # Compter les tâches par statut
        task_status = await session.execute(
            select(Task.status, func.count()).select_from(Task)
            .where(Task.assigned_to == agent_uuid)
            .group_by(Task.status)
        )
        status_counts = {status: count for status, count in task_status.all()}
        
        print(f"\n📝 Tâches: {tasks_total} total")
        for status, count in status_counts.items():
            print(f"   - {status}: {count}")
        
        # Compter les messages
        sent_count = await session.execute(
            select(func.count()).select_from(Message).where(Message.sender_id == agent_uuid)
        )
        sent_total = sent_count.scalar()
        
        received_count = await session.execute(
            select(func.count()).select_from(Message).where(Message.receiver_id == agent_uuid)
        )
        received_total = received_count.scalar()
        
        print(f"\n💬 Messages:")
        print(f"   - Envoyés: {sent_total}")
        print(f"   - Reçus: {received_total}")
        
        # Compter les mémoires
        memory_count = await session.execute(
            select(func.count()).select_from(Memory).where(Memory.agent_id == agent_uuid)
        )
        memories_total = memory_count.scalar()
        
        print(f"\n🧠 Mémoires: {memories_total} stockées")
        
        # Récupérer la dernière tâche
        last_task = await session.execute(
            select(Task).where(Task.assigned_to == agent_uuid)
            .order_by(Task.created_at.desc())
            .limit(1)
        )
        task = last_task.scalar_one_or_none()
        
        if task:
            print(f"\n📌 Dernière tâche:")
            print(f"   Titre: {task.title}")
            print(f"   Statut: {task.status}")
            print(f"   Priorité: {task.priority}")
            if task.result:
                print(f"   Résultat: {task.result}")


def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("Usage: python check_agent_activity.py <agent_id>")
        print("Exemple: python check_agent_activity.py cebac9bf-55f1-4f03-93b5-ecd89127b834")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    asyncio.run(check_agent_activity(agent_id))


if __name__ == "__main__":
    main()