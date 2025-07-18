#!/usr/bin/env python3
"""
Test de debug pour vérifier la communication agent-LLM
"""

import asyncio
import aiohttp
import json
import time
import sys
sys.path.append('/app')

from src.services.llm_service import LLMService
from src.core.agents import AgentFactory, get_agent_runtime
from uuid import uuid4

async def test_direct_llm():
    """Test 1: Vérifier que le LLM répond directement"""
    print("\n=== TEST 1: LLM Direct ===")
    
    llm = LLMService()
    print(f"LLM Mock Mode: {llm.enable_mock}")
    print(f"LLM Model: {llm.model}")
    
    if not llm.enable_mock:
        try:
            response = await llm.generate(
                prompt="Dis simplement 'Bonjour'",
                system_prompt="Tu es un assistant. Réponds très brièvement.",
                temperature=0.1,
                max_tokens=20
            )
            print(f"✅ Réponse LLM: {response}")
        except Exception as e:
            print(f"❌ Erreur LLM: {e}")
    else:
        print("❌ LLM en mode MOCK!")
        
async def test_agent_creation():
    """Test 2: Créer un agent et vérifier son état"""
    print("\n=== TEST 2: Création d'Agent ===")
    
    factory = AgentFactory()
    runtime = get_agent_runtime()
    llm = LLMService()
    
    # Créer un agent cognitif simple
    agent_id = uuid4()
    agent = factory.create_agent(
        agent_type="cognitive",
        agent_id=agent_id,
        name="TestAgent",
        role="assistant",
        capabilities=["test"],
        llm_service=llm,
        initial_beliefs={"test": True},
        initial_desires=["test_desire"]
    )
    
    print(f"✅ Agent créé: {agent.name} (ID: {agent.id})")
    print(f"   Type: {agent.__class__.__name__}")
    print(f"   LLM Service: {agent.llm_service is not None}")
    print(f"   LLM Mock: {agent.llm_service.enable_mock if agent.llm_service else 'N/A'}")
    
    # Enregistrer et démarrer l'agent
    await runtime.register_agent(agent)
    await runtime.start_agent(agent)
    
    print(f"✅ Agent démarré")
    
    # Attendre un peu
    await asyncio.sleep(2)
    
    # Vérifier si l'agent est en cours d'exécution
    is_running = await runtime.is_agent_running(agent_id)
    print(f"   Running: {is_running}")
    
    # Envoyer un message à l'agent
    print("\n=== TEST 3: Envoi de Message ===")
    
    class TestMessage:
        def __init__(self):
            self.sender = "test_sender"
            self.receiver = str(agent_id)
            self.performative = "inform"
            self.content = {"message": "Test message"}
            
    message = TestMessage()
    await agent.receive_message(message)
    print("✅ Message envoyé à l'agent")
    
    # Attendre le traitement
    await asyncio.sleep(5)
    
    # Vérifier les métriques
    metrics = await agent.get_metrics()
    print(f"\n📊 Métriques de l'agent:")
    print(f"   Messages traités: {metrics.get('messages_processed', 0)}")
    print(f"   Actions exécutées: {metrics.get('actions_executed', 0)}")
    print(f"   Erreurs: {metrics.get('errors', 0)}")
    
    # Arrêter l'agent
    await runtime.stop_agent(agent_id)
    print("\n✅ Agent arrêté")

async def test_agent_perceive():
    """Test 4: Tester directement la méthode perceive d'un agent cognitif"""
    print("\n=== TEST 4: Test Perceive ===")
    
    from src.core.agents.cognitive_agent import CognitiveAgent
    
    llm = LLMService()
    agent = CognitiveAgent(
        agent_id=uuid4(),
        name="PerceiveTest",
        role="test",
        capabilities=["test"],
        llm_service=llm,
        initial_beliefs={"test": True}
    )
    
    print(f"Agent créé avec LLM Mock: {agent.llm_service.enable_mock}")
    
    try:
        # Tester perceive directement
        environment = {"test_env": True, "timestamp": time.time()}
        perceptions = await agent.perceive(environment)
        print(f"✅ Perceptions: {perceptions}")
    except Exception as e:
        print(f"❌ Erreur perceive: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("="*60)
    print("🔍 DEBUG AGENT-LLM COMMUNICATION")
    print("="*60)
    
    # Test 1: LLM direct
    await test_direct_llm()
    
    # Test 2 & 3: Agent creation et messaging
    await test_agent_creation()
    
    # Test 4: Perceive direct
    await test_agent_perceive()
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    asyncio.run(main())