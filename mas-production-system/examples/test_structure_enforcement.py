#!/usr/bin/env python3
"""
Test de l'application de la structure de projet
Vérifie que les agents respectent la structure établie
"""

import asyncio
import sys
import os
sys.path.append('/app')

from autonomous_fixed import AutonomousAgent
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_structure_enforcement():
    """Tester que les agents respectent la structure du projet"""
    print("\n" + "="*80)
    print("🧪 TEST DE L'APPLICATION DE LA STRUCTURE DE PROJET")
    print("="*80)
    
    # Créer l'agent autonome
    agent = AutonomousAgent()
    await agent.initialize()
    
    # Requête de test qui génère plusieurs fichiers
    test_request = """
    Créer une calculatrice Python simple avec:
    1. Un module principal avec les opérations de base (addition, soustraction, multiplication, division)
    2. Un test unitaire pour vérifier les opérations
    3. Un service API simple pour exposer la calculatrice
    4. Un modèle de données pour stocker l'historique des calculs
    5. Un utilitaire pour formater les résultats
    6. Une documentation README
    """
    
    print("\n📝 Requête de test:")
    print(test_request)
    print("\n🚀 Traitement en cours...\n")
    
    # Traiter la requête
    result = await agent.process_request(test_request)
    
    # Vérifier les résultats
    print("\n" + "="*60)
    print("📊 RÉSULTATS DU TEST")
    print("="*60)
    
    if result['status'] == 'completed':
        print(f"✅ Requête complétée avec succès")
        print(f"📁 Projet créé dans: {result.get('project_path', 'N/A')}")
        
        # Analyser la structure des fichiers créés
        all_files = []
        for subtask_result in result.get('subtasks_results', []):
            if subtask_result.get('created_files'):
                all_files.extend(subtask_result['created_files'])
        
        print(f"\n📄 Fichiers créés ({len(all_files)}):")
        
        # Vérifier que les fichiers sont dans la bonne structure
        structure_ok = True
        for file_info in all_files:
            path = file_info['path']
            print(f"  - {path}")
            
            # Vérifications de structure
            if 'task_' in path:
                print(f"    ❌ ERREUR: Chemin contient 'task_' (structure non respectée)")
                structure_ok = False
            
            # Vérifier les emplacements appropriés
            if path.endswith('.py') and not path.startswith(('src/', 'tests/', 'scripts/')):
                if path not in ['setup.py', 'main.py']:  # Exceptions à la racine
                    print(f"    ⚠️  Fichier Python hors structure standard")
            
            if 'test' in path.lower() and not path.startswith('tests/'):
                print(f"    ❌ ERREUR: Test pas dans tests/")
                structure_ok = False
            
            if any(x in path.lower() for x in ['model', 'service', 'util', 'core']) and path.endswith('.py'):
                if not path.startswith('src/'):
                    print(f"    ❌ ERREUR: Code source pas dans src/")
                    structure_ok = False
        
        print(f"\n🏗️ Validation de la structure:")
        if structure_ok:
            print("✅ La structure du projet est respectée!")
        else:
            print("❌ Des problèmes de structure ont été détectés")
        
        # Afficher l'arborescence du projet si possible
        if result.get('project_path'):
            print(f"\n📂 Arborescence du projet:")
            try:
                for root, dirs, files in os.walk(result['project_path']):
                    level = root.replace(result['project_path'], '').count(os.sep)
                    indent = ' ' * 2 * level
                    print(f'{indent}{os.path.basename(root)}/')
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        print(f'{subindent}{file}')
            except Exception as e:
                print(f"Erreur lors de l'affichage de l'arborescence: {e}")
    
    else:
        print(f"❌ Erreur lors du traitement: {result.get('error', 'Erreur inconnue')}")
    
    # Nettoyer
    await agent.cleanup()
    print("\n✅ Test terminé")

if __name__ == "__main__":
    print("\n💡 Ce test vérifie que les agents respectent la structure de projet établie")
    print("   au lieu de créer des répertoires task_* séparés.")
    
    asyncio.run(test_structure_enforcement())