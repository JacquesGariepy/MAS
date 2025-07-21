#!/usr/bin/env python3
"""
Test de l'agent autonome avec création de fichiers
"""

import sys
import os
sys.path.append('/app')

import asyncio
from autonomous import AutonomousAgent

async def test_autonomous_with_files():
    """Test l'agent autonome avec une requête qui devrait créer des fichiers"""
    print("🧪 Test de l'agent autonome avec création de fichiers")
    print("="*60)
    
    agent = AutonomousAgent()
    await agent.initialize()
    
    # Requête de test qui devrait générer des fichiers
    request = "créer un test unitaire simple en Python pour une fonction qui additionne deux nombres"
    
    print(f"📝 Requête: {request}")
    print("🚀 Traitement en cours...")
    
    try:
        result = await agent.process_request(request)
        
        print("\n✅ Requête traitée!")
        print(f"📊 Statut: {result.get('status')}")
        print(f"⏱️  Durée: {result.get('duration')}")
        print(f"📈 Taux de succès: {result.get('success_rate', 0):.1f}%")
        
        # Vérifier si des fichiers ont été créés
        files_created = False
        if 'subtasks_results' in result:
            print("\n📄 Fichiers créés:")
            for i, st_result in enumerate(result['subtasks_results']):
                if st_result.get('created_files'):
                    files_created = True
                    print(f"\n  Sous-tâche {i+1}:")
                    for file in st_result['created_files']:
                        print(f"  - {file['path']} ({file['size']} octets)")
                
                if st_result.get('project_path'):
                    print(f"  📁 Projet: {st_result['project_path']}")
        
        if not files_created:
            print("\n⚠️  Aucun fichier créé")
        else:
            print("\n✅ Des fichiers ont été créés dans agent_workspace!")
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.cleanup()
        print("\n🧹 Nettoyage terminé")

if __name__ == "__main__":
    asyncio.run(test_autonomous_with_files())