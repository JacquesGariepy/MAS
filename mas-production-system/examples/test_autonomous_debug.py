#!/usr/bin/env python3
"""
Test de débogage pour autonomous.py
"""

import sys
import os
sys.path.append('/app')

import asyncio
from autonomous import AutonomousAgent
import logging

# Configuration du logging pour plus de détails
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_autonomous_debug():
    """Test l'agent autonome avec débogage"""
    print("🧪 Test de débogage de l'agent autonome")
    print("="*60)
    
    agent = AutonomousAgent()
    
    # Vérifier l'état initial
    print(f"📍 Agent ID: {agent.agent_id}")
    print(f"📍 Nom: {agent.name}")
    print(f"📍 Nombre d'agents: {len(agent.sub_agents)}")
    
    # Initialiser
    print("\n🔧 Initialisation...")
    try:
        await agent.initialize()
        print(f"✅ Initialisé! Nombre d'agents: {len(agent.sub_agents)}")
        
        # Lister les agents créés
        if agent.sub_agents:
            print("\n👥 Agents créés:")
            for i, agent_info in enumerate(agent.sub_agents):
                print(f"  {i+1}. {agent_info['agent'].name} - Role: {agent_info['role']}")
        else:
            print("❌ Aucun agent créé!")
            
        # Vérifier FileSystemTool
        if agent.filesystem_tool:
            print(f"\n✅ FileSystemTool disponible: {agent.filesystem_tool.name}")
        else:
            print("❌ FileSystemTool non disponible")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Nettoyage...")
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_autonomous_debug())