#!/usr/bin/env python3
"""
Exemple simple et direct de création d'agent et envoi de requête
"""

import requests
import time

# Configuration
API_URL = "http://localhost:8088"

def main():
    print("🤖 Exemple Simple MAS - Création d'Agent et Requête\n")
    
    # 1. Créer un utilisateur
    print("1️⃣ Création utilisateur...")
    register_data = {
        "username": "test_user",
        "email": "test@example.com", 
        "password": "password123"
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("✅ Utilisateur créé")
    elif response.status_code == 400:
        print("ℹ️  Utilisateur déjà existant")
    
    # 2. Se connecter
    print("\n2️⃣ Connexion...")
    login_data = {
        "username": "test_user",
        "password": "password123"
    }
    
    response = requests.post(
        f"{API_URL}/auth/token",
        data=login_data
    )
    token = response.json()["access_token"]
    print("✅ Token obtenu")
    
    # Headers avec token
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Créer un agent
    print("\n3️⃣ Création d'un agent assistant...")
    agent_data = {
        "name": "Mon Assistant IA",
        "role": "Assistant pour répondre aux questions",
        "agent_type": "cognitive",
        "capabilities": ["conversation", "analyse", "conseil"],
        "initial_beliefs": {
            "langue": "français",
            "domaine": "général"
        },
        "initial_desires": ["aider", "informer"],
        "configuration": {
            "temperature": 0.7
        },
        "organization_id": None
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/agents",
        json=agent_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"❌ Erreur lors de la création de l'agent: {response.status_code}")
        print(f"   Détails: {response.text}")
        return
        
    agent = response.json()
    agent_id = agent["id"]
    print(f"✅ Agent créé: {agent['name']} (ID: {agent_id})")
    
    # 4. Démarrer l'agent
    print("\n4️⃣ Démarrage de l'agent...")
    response = requests.post(
        f"{API_URL}/api/v1/agents/{agent_id}/start",
        headers=headers
    )
    print("✅ Agent démarré")
    
    # 5. Envoyer une requête (via une tâche)
    print("\n5️⃣ Envoi d'une question à l'agent...")
    question = "Qu'est-ce qu'un système multi-agents et quels sont ses avantages ?"
    
    task_data = {
        "title": "Question utilisateur",
        "description": question,
        "task_type": "query",
        "priority": "high",
        "assigned_to": agent_id
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/v1/tasks",
        json=task_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"❌ Erreur lors de la création de la tâche: {response.status_code}")
        print(f"   Détails: {response.text}")
        return
        
    task = response.json()
    task_id = task["id"]
    print(f"📨 Question envoyée: '{question}'")
    
    # 6. Attendre et récupérer la réponse
    print("\n6️⃣ Attente de la réponse...")
    time.sleep(3)  # Attendre que l'agent traite
    
    response = requests.get(
        f"{API_URL}/api/v1/v1/tasks/{task_id}",
        headers=headers
    )
    result = response.json()
    
    print(f"\n💬 Réponse de l'agent:")
    print("-" * 50)
    if result["status"] == "completed":
        print(result.get("result", "Pas de réponse"))
    else:
        print(f"Status: {result['status']}")
        print("(L'agent est peut-être encore en train de traiter)")
    
    # 7. Afficher les détails de l'agent
    print("\n7️⃣ Détails de l'agent:")
    response = requests.get(
        f"{API_URL}/api/v1/agents/{agent_id}",
        headers=headers
    )
    agent_details = response.json()
    print(f"""
    Nom: {agent_details['name']}
    Type: {agent_details['agent_type']}
    Rôle: {agent_details['role']}
    Croyances: {agent_details['beliefs']}
    Désirs: {agent_details['desires']}
    """)
    
    print("\n✅ Exemple terminé !")

if __name__ == "__main__":
    main()