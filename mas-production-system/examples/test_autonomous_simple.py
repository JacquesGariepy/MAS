#!/usr/bin/env python3
"""Test simple de l'agent autonome avec une requête prédéfinie"""

import sys
import os
sys.path.append('/app')

import asyncio
from autonomous import AutonomousAgent

async def test_autonomous():
    """Test l'agent autonome avec une requête simple"""
    agent = AutonomousAgent()
    
    # Requête de test
    request = "créer un test unitaire simple en Python pour une fonction qui additionne deux nombres"
    
    print(f"🚀 Test de l'agent autonome avec la requête: {request}")
    
    try:
        result = await agent.process_request(request)
        
        print("\n✅ Requête traitée avec succès!")
        print(f"📊 Résumé: {result.get('summary', 'N/A')}")
        print(f"📝 Étapes complétées: {result.get('completed_steps', 0)}")
        
        if 'solution' in result:
            print("\n💡 Solution proposée:")
            print(result['solution'])
            
        if 'code' in result:
            print("\n📄 Code généré:")
            print(result['code'])
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_autonomous())