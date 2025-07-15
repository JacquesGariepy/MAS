#!/usr/bin/env python3
"""
Exemple de création d'agent et interaction directe (sans tâches)
"""

import requests
import json
import time

API_URL = "http://localhost:8088"

def main():
    print("🤖 Exemple MAS - Création et Gestion d'Agent\n")
    
    # 1. Authentification
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
    
    # 2. Créer un agent
    print("\n2️⃣ Création d'un agent cognitif...")
    agent_data = {
        "name": "Assistant Cognitif",
        "role": "Assistant pour analyse et conseil",
        "agent_type": "cognitive",
        "capabilities": ["conversation", "analyse", "conseil"],
        "initial_beliefs": {
            "expertise": "généraliste",
            "mode": "professionnel"
        },
        "initial_desires": ["aider", "analyser", "conseiller"],
        "configuration": {
            "temperature": 0.7,
            "reasoning_depth": 3
        }
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/agents",
        json=agent_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"❌ Erreur création agent: {response.status_code}")
        print(f"   Détails: {response.text}")
        return
        
    agent = response.json()
    agent_id = agent["id"]
    print(f"✅ Agent créé: {agent['name']}")
    print(f"   ID: {agent_id}")
    print(f"   Type: {agent['agent_type']}")
    print(f"   Capacités: {', '.join(agent['capabilities'])}")
    
    # 3. Lister les agents
    print("\n3️⃣ Liste des agents...")
    response = requests.get(
        f"{API_URL}/api/v1/agents",
        headers=headers
    )
    
    if response.status_code == 200:
        agents_list = response.json()
        print(f"✅ Total agents: {agents_list['total']}")
        for agent_item in agents_list['items']:
            print(f"   - {agent_item['name']} ({agent_item['agent_type']}) - Status: {agent_item['status']}")
    
    # 4. Obtenir les détails de l'agent
    print(f"\n4️⃣ Détails de l'agent {agent_id}...")
    response = requests.get(
        f"{API_URL}/api/v1/agents/{agent_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        details = response.json()
        print(f"✅ Agent détaillé:")
        print(f"   Croyances: {json.dumps(details['beliefs'], indent=6)}")
        print(f"   Désirs: {details['desires']}")
        print(f"   Intentions: {details['intentions']}")
    
    # 5. Mettre à jour l'agent
    print("\n5️⃣ Mise à jour de l'agent...")
    update_data = {
        "role": "Expert en intelligence artificielle",
        "configuration": {
            "temperature": 0.8,
            "reasoning_depth": 5
        }
    }
    
    response = requests.patch(
        f"{API_URL}/api/v1/agents/{agent_id}",
        json=update_data,
        headers=headers
    )
    
    if response.status_code == 200:
        updated = response.json()
        print(f"✅ Agent mis à jour: {updated['role']}")
    
    # 6. Ajouter une mémoire
    print("\n6️⃣ Ajout de mémoire à l'agent...")
    memory_data = {
        "content": "L'utilisateur s'intéresse aux systèmes multi-agents",
        "memory_type": "semantic",
        "importance": 0.8
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/agents/{agent_id}/memories",
        json=memory_data,
        headers=headers
    )
    
    if response.status_code == 201:
        memory = response.json()
        print(f"✅ Mémoire ajoutée: {memory['content']}")
    else:
        print(f"ℹ️  Ajout mémoire: {response.status_code}")
    
    # 7. Obtenir les métriques
    print("\n7️⃣ Métriques de l'agent...")
    response = requests.get(
        f"{API_URL}/api/v1/agents/{agent_id}/metrics",
        headers=headers
    )
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"✅ Métriques:")
        print(f"   Actions totales: {metrics.get('total_actions', 0)}")
        print(f"   Taux de réussite: {metrics.get('success_rate', 0):.1%}")
    
    print("\n✨ Démonstration terminée!")
    print(f"   Agent ID: {agent_id}")
    print("   L'agent est créé et configuré, prêt à être utilisé.")

if __name__ == "__main__":
    main()