#!/usr/bin/env python3
"""
Test pour vérifier que les agents cognitifs utilisent vraiment LMStudio
"""

import asyncio
from src.services.llm_service import LLMService
from src.core.agents.cognitive_agent import CognitiveAgent
from uuid import uuid4
import json


async def test_llm_direct():
    """Test direct du service LLM"""
    print("="*80)
    print("🧪 TEST DIRECT DU SERVICE LLM")
    print("="*80)
    
    # Créer le service LLM
    llm_service = LLMService()
    print(f"\n📊 Configuration LLM:")
    print(f"   Model: {llm_service.model}")
    print(f"   Mock mode: {llm_service.enable_mock}")
    print(f"   Client: {'Configuré' if llm_service.client else 'Non configuré'}")
    
    if llm_service.enable_mock:
        print("\n⚠️  ATTENTION: Le service est en mode MOCK!")
        print("   Aucune requête ne sera envoyée à LMStudio")
        return
    
    # Test de génération
    print("\n📨 Envoi d'une requête à LMStudio...")
    print("   Prompt: 'Qu'est-ce que l'intelligence artificielle?'")
    
    try:
        response = await llm_service.generate(
            prompt="Qu'est-ce que l'intelligence artificielle? Réponds en une phrase.",
            system_prompt="Tu es un assistant utile.",
            temperature=0.7,
            max_tokens=100
        )
        
        print("\n✅ Réponse reçue!")
        print(f"   Contenu: {response}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")


async def test_cognitive_agent():
    """Test d'un agent cognitif"""
    print("\n" + "="*80)
    print("🧪 TEST AGENT COGNITIF AVEC LLM")
    print("="*80)
    
    # Créer le service LLM et l'agent
    llm_service = LLMService()
    
    agent = CognitiveAgent(
        agent_id=uuid4(),
        name="TestCognitiveAgent",
        role="assistant",
        capabilities=["reasoning", "analysis"],
        llm_service=llm_service
    )
    
    print(f"\n🤖 Agent créé: {agent.name}")
    print(f"   Type: Cognitive")
    print(f"   LLM Service: {'Mock' if llm_service.enable_mock else 'LMStudio'}")
    
    # Créer un message qui nécessite du raisonnement
    class MockMessage:
        def __init__(self, sender, performative, content):
            self.sender = sender
            self.performative = performative
            self.content = content
    
    message = MockMessage(
        sender="TestUser",
        performative="request",
        content={
            "action": "analyze",
            "query": "Explique les avantages et inconvénients de l'IA",
            "require_reasoning": True
        }
    )
    
    print("\n📨 Envoi d'un message nécessitant du raisonnement...")
    print(f"   Performative: {message.performative}")
    print(f"   Query: {message.content['query']}")
    
    try:
        # Appeler directement handle_message
        await agent.handle_message(message)
        print("\n✅ Message traité!")
        
        # Vérifier si l'agent a généré une réponse
        if agent.context.conversation_history:
            print(f"\n📊 Historique de conversation: {len(agent.context.conversation_history)} entrées")
            
    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Tests principaux"""
    # Test 1: Service LLM direct
    await test_llm_direct()
    
    # Test 2: Agent cognitif
    await test_cognitive_agent()
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("   Vérifiez LMStudio pour voir les requêtes!")
    print("="*80)


if __name__ == "__main__":
    # Run from within the container:
    # docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_cognitive_llm.py
    asyncio.run(main())