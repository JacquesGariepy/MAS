#!/usr/bin/env python3
"""
Script pour réinitialiser l'environnement de test
Crée de nouveaux utilisateurs avec des quotas frais
"""

import requests

API_URL = "http://localhost:8088"

def create_test_users():
    """Crée plusieurs utilisateurs de test avec des quotas frais"""
    
    print("🔄 Création d'utilisateurs de test avec quotas frais\n")
    
    users_created = []
    
    # Créer test_user20 à test_user29
    for i in range(20, 30):
        username = f"test_user{i}"
        register_data = {
            "username": username,
            "email": f"test{i}@example.com",
            "password": "password123"
        }
        
        print(f"Création de {username}...", end=" ")
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        
        if response.status_code == 201:
            print("✅")
            users_created.append(username)
        elif response.status_code == 400:
            print("(déjà existant)")
        else:
            print(f"❌ Erreur {response.status_code}")
    
    print(f"\n✅ Utilisateurs disponibles avec quota frais:")
    for user in users_created:
        print(f"   - {user} (quota: 10 agents)")
    
    print("\n💡 Utilisez ces comptes pour vos tests:")
    print(f"   Username: test_userXX")
    print(f"   Password: password123")
    print(f"   Quota: 10 agents par utilisateur")
    
    # Exemple d'utilisation
    if users_created:
        print(f"\n📝 Exemple avec {users_created[0]}:")
        print(f"""
import requests

# Login
response = requests.post("{API_URL}/auth/token", 
    data={{"username": "{users_created[0]}", "password": "password123"}})
token = response.json()["access_token"]

# Créer un agent
headers = {{"Authorization": f"Bearer {{token}}"}}
agent_data = {{
    "name": "Mon Agent",
    "role": "Assistant",
    "agent_type": "cognitive",
    "capabilities": ["conversation"]
}}
response = requests.post("{API_URL}/api/v1/agents", json=agent_data, headers=headers)
print(response.json())
""")

def show_current_status():
    """Affiche le statut actuel de test_user"""
    print("\n📊 Statut de test_user (principal):")
    
    # Login
    response = requests.post(
        f"{API_URL}/auth/token",
        data={"username": "test_user", "password": "password123"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Lister les agents
        response = requests.get(f"{API_URL}/api/v1/agents", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   Agents: {data.get('total', 0)}/10")
            print(f"   Quota atteint: {'Oui ⚠️' if data.get('total', 0) >= 10 else 'Non ✅'}")
    else:
        print("   ❌ Impossible de se connecter")

if __name__ == "__main__":
    show_current_status()
    print("\n" + "="*50 + "\n")
    create_test_users()