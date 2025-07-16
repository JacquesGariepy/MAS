#!/usr/bin/env python3
"""
Test direct de la factory d'agents
"""

import sys
sys.path.append('/app')

from uuid import uuid4
from src.agents.agent_factory import AgentFactory

def test_factory():
    """Test direct de création d'agents"""
    print("🔧 Test Direct de l'Agent Factory")
    print("=" * 50)
    
    # Test 1: Agent Cognitif
    print("\n1️⃣ Création d'un agent cognitif...")
    try:
        cognitive = AgentFactory.create_agent(
            agent_type="reactive",
            agent_id=uuid4(),
            name="TestCognitive",
            role="Analyste",
            capabilities=["reasoning", "planning"],
            llm_service=None
        )
        print(f"✅ Agent cognitif créé: {cognitive.__class__.__name__}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Agent Réflexif
    print("\n2️⃣ Création d'un agent réflexif...")
    try:
        reflexive = AgentFactory.create_agent(
            agent_type="reflexive",
            agent_id=uuid4(),
            name="TestReflexive",
            role="Moniteur",
            capabilities=["monitoring", "alerting"],
            llm_service=None,
            reactive_rules={
                "alert_rule": {
                    "condition": {"level": "high"},
                    "action": {"type": "notify"}
                }
            }
        )
        print(f"✅ Agent réflexif créé: {reflexive.__class__.__name__}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Agent Hybride
    print("\n3️⃣ Création d'un agent hybride...")
    try:
        hybrid = AgentFactory.create_agent(
            agent_type="hybrid",
            agent_id=uuid4(),
            name="TestHybrid",
            role="Coordinateur",
            capabilities=["coordination", "adaptation"],
            llm_service=None,
            reactive_rules={"simple": {"condition": {}, "action": {}}},
            complexity_threshold=0.5
        )
        print(f"✅ Agent hybride créé: {hybrid.__class__.__name__}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test terminé !")


if __name__ == "__main__":
    test_factory()