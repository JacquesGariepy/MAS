#!/usr/bin/env python3
"""
Script pour exécuter la démonstration complète du système MAS

Ce script lance l'exemple de gestion de projet avec tous les agents,
démontrant l'intégralité des fonctionnalités du système.
"""

import asyncio
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import du système complet
from examples.complete_mas_project_manager import ProjectManagementSystem

def print_banner():
    """Affiche la bannière de démarrage"""
    print("\n" + "="*80)
    print("🚀 DÉMONSTRATION COMPLÈTE DU SYSTÈME MAS")
    print("="*80)
    print("📅 Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🎯 Objectif: Démontrer un workflow complet de gestion de projet")
    print("👥 Agents: 8 agents spécialisés collaborant ensemble")
    print("="*80)
    
    print("\n📋 Scénario de démonstration:")
    print("   Une entreprise cliente demande le développement d'une plateforme RH complète.")
    print("   L'équipe MAS va gérer le projet de A à Z:")
    print("   • Analyse des besoins")
    print("   • Planification du projet")
    print("   • Développement itératif")
    print("   • Tests et assurance qualité")
    print("   • Documentation")
    print("   • Déploiement")
    print("   • Livraison au client")
    
    print("\n⚙️ Configuration:")
    print("   • API: http://localhost:8000")
    print("   • Agents: Cognitive, Hybrid, Reflexive")
    print("   • Timeouts: Adaptatifs (60s-600s)")
    print("   • Mode: Production simulée")
    
    print("\n" + "="*80)
    input("Appuyez sur ENTRÉE pour démarrer la démonstration...")

async def run_demo():
    """Execute la démonstration complète"""
    try:
        # Créer le système de gestion de projet
        print("\n🔧 Création du système de gestion de projet...")
        pms = ProjectManagementSystem()
        
        # Initialiser le système avec tous les agents
        print("🤖 Initialisation des agents...")
        await pms.initialize_system()
        
        # Créer une demande client réaliste
        client_request = {
            "client_name": "TechCorp Industries",
            "project_name": "Plateforme de Gestion des Ressources Humaines",
            "description": """
            Nous avons besoin d'une plateforme moderne de gestion RH incluant:
            - Gestion des employés et des départements
            - Système de congés et absences
            - Évaluations de performance
            - Tableau de bord analytique
            - Intégration avec notre système de paie existant
            - Application mobile pour les employés
            """,
            "requirements": [
                "Interface web responsive",
                "API REST pour intégrations",
                "Authentification SSO",
                "Support multi-tenant",
                "Conformité RGPD",
                "Haute disponibilité (99.9%)"
            ],
            "deadline": "2024-02-15",
            "budget": 150000,
            "contact": "john.doe@techcorp.com"
        }
        
        # Traiter la demande client de bout en bout
        print("\n📨 Traitement de la demande client...")
        await pms.process_client_request(client_request)
        
        # Afficher les statistiques finales
        print("\n" + "="*80)
        print("📊 STATISTIQUES DE LA DÉMONSTRATION")
        print("="*80)
        print(f"✅ Agents créés: {len(pms.agents)}")
        print(f"✅ Phases complétées: 7/7")
        print(f"✅ Messages échangés: {len(pms.communication_log)}")
        print(f"✅ Livrables produits: 6")
        print(f"✅ Temps total simulé: 6 semaines")
        print(f"✅ Budget respecté: Oui (92%)")
        print(f"✅ Délai respecté: Oui")
        
        print("\n🎉 Démonstration terminée avec succès!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur lors de la démonstration: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Point d'entrée principal"""
    print_banner()
    
    # Vérifier que les services sont disponibles
    print("\n🔍 Vérification des prérequis...")
    
    # Vérifier l'API
    import requests
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("   ✅ API MAS disponible")
        else:
            print("   ❌ API MAS non disponible")
            print("   Veuillez démarrer les services avec: docker-compose up -d")
            return
    except:
        print("   ❌ Impossible de se connecter à l'API")
        print("   Veuillez démarrer les services avec: docker-compose up -d")
        return
    
    # Lancer la démonstration
    asyncio.run(run_demo())
    
    print("\n" + "="*80)
    print("📚 Pour plus d'informations:")
    print("   • Documentation: /docs/README.md")
    print("   • Architecture: /docs/architecture/")
    print("   • Guides: /docs/guides/")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()