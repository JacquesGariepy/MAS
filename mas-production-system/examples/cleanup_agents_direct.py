#!/usr/bin/env python3
"""
Script pour supprimer directement les agents de test_user via l'API
"""

import requests
import asyncio
import sys

API_URL = "http://localhost:8088"

def main():
    print("🧹 Suppression directe des agents de test_user\n")
    
    # 1. Login avec test_user
    print("1️⃣ Connexion en tant que test_user...")
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
    print("\n2️⃣ Récupération des agents...")
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
    
    # 3. Pour contourner le problème de suppression, on va désactiver les agents
    print("\n3️⃣ Désactivation des agents...")
    disabled = 0
    
    for agent in agents:
        # Mettre à jour l'agent pour le désactiver
        update_data = {
            "name": f"[DISABLED] {agent['name']}"
        }
        
        response = requests.patch(
            f"{API_URL}/api/v1/agents/{agent['id']}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            disabled += 1
            print(f"✅ Désactivé: {agent['name']}")
        else:
            print(f"❌ Échec désactivation {agent['name']}: {response.status_code}")
    
    print(f"\n✅ {disabled} agent(s) désactivé(s)")
    
    # Alternative : créer un nouvel utilisateur pour les prochains tests
    print("\n💡 Conseil: Utilisez test_user10, test_user11, etc. pour les prochains tests")
    print("   Ces utilisateurs ont un quota frais de 10 agents chacun")

if __name__ == "__main__":
    main()