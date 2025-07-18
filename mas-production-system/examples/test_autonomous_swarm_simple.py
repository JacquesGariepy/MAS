#!/usr/bin/env python3
"""
Test simple pour vérifier que autonomous_swarm.py fonctionne
"""

import asyncio
import sys
sys.path.append('/app')

from autonomous_swarm import AutonomousSwarmWithLogging

async def test_simple():
    """Test simple du swarm"""
    print("\n🧪 TEST SIMPLE DU SWARM AUTONOME")
    print("="*50)
    
    # Créer un petit swarm
    print("\n1️⃣ Création du swarm avec 3 agents...")
    swarm = AutonomousSwarmWithLogging(num_agents=3)
    await swarm.initialize(3)
    
    print("\n✅ Agents créés:")
    for agent in swarm.agents:
        print(f"   - {agent.name} ({type(agent).__name__})")
    
    # Tester la décomposition de tâche
    print("\n2️⃣ Test de décomposition de tâche...")
    task = "Créer un système de recommandation"
    task_graph = swarm.decompose_task(task)
    print(f"✅ Tâche décomposée en {len(task_graph.nodes())} sous-tâches")
    
    # Tester l'exécution d'une sous-tâche
    print("\n3️⃣ Test d'exécution d'une sous-tâche...")
    if swarm.agents:
        agent = swarm.agents[0]
        result = await swarm.execute_workflow(
            agent,
            "test_subtask", 
            {"phase": "test", "node_id": 0}
        )
        print(f"✅ Résultat: {result['status']} en {result['duration']:.2f}s")
    
    # Nettoyer
    print("\n4️⃣ Nettoyage...")
    await swarm.cleanup()
    
    print("\n✅ TEST TERMINÉ AVEC SUCCÈS!")

if __name__ == "__main__":
    asyncio.run(test_simple())