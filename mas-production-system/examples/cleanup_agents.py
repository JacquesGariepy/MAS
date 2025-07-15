#!/usr/bin/env python3
"""
Script pour lister et supprimer des agents (nettoyer pour les tests)
"""

import requests
import sys

API_URL = "http://localhost:8088"

def main():
    print("🧹 Nettoyage des agents\n")
    
    # 1. Login
    print("1️⃣ Connexion...")
    login_data = {
        "username": "test_user",
        "password": "password123"
    }
    
    response = requests.post(
        f"{API_URL}/auth/token",
        data=login_data
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur de connexion: {response.status_code}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Connecté")
    
    # 2. Lister les agents
    print("\n2️⃣ Liste des agents...")
    response = requests.get(
        f"{API_URL}/api/v1/agents",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur: {response.status_code}")
        return
        
    agents_data = response.json()
    agents = agents_data.get("items", [])
    total = agents_data.get("total", 0)
    
    print(f"📊 Total agents: {total}")
    
    if total == 0:
        print("✅ Aucun agent à supprimer")
        return
        
    # Afficher les agents
    print("\nAgents existants:")
    for i, agent in enumerate(agents):
        print(f"{i+1}. {agent['name']} (ID: {agent['id']}) - Status: {agent['status']}")
    
    # 3. Demander confirmation
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Mode automatique pour supprimer tous
        to_delete = agents
    else:
        print("\n⚠️  Voulez-vous supprimer des agents?")
        print("Options:")
        print("  1-N : Numéro de l'agent à supprimer")
        print("  all : Supprimer tous les agents")
        print("  q   : Quitter")
        
        choice = input("\nVotre choix: ").strip().lower()
        
        if choice == 'q':
            print("❌ Annulé")
            return
        elif choice == 'all':
            to_delete = agents
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(agents):
                    to_delete = [agents[idx]]
                else:
                    print("❌ Numéro invalide")
                    return
            except ValueError:
                print("❌ Choix invalide")
                return
    
    # 4. Supprimer les agents sélectionnés
    print(f"\n🗑️  Suppression de {len(to_delete)} agent(s)...")
    deleted = 0
    
    for agent in to_delete:
        response = requests.delete(
            f"{API_URL}/api/v1/agents/{agent['id']}",
            headers=headers
        )
        
        if response.status_code == 204:
            deleted += 1
            print(f"✅ Supprimé: {agent['name']}")
        else:
            print(f"❌ Échec suppression {agent['name']}: {response.status_code}")
    
    print(f"\n✅ {deleted} agent(s) supprimé(s)")
    
    # 5. Afficher le nombre restant
    response = requests.get(
        f"{API_URL}/api/v1/agents",
        headers=headers
    )
    
    if response.status_code == 200:
        remaining = response.json().get("total", 0)
        print(f"📊 Agents restants: {remaining}/10")

if __name__ == "__main__":
    main()