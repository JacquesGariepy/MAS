#!/usr/bin/env python3
"""
Exemple de création et utilisation d'un agent MAS v2.0
Démontre: authentification, création d'agent, envoi de requête, récupération de réponse
"""

import asyncio
import httpx
import json
from typing import Dict, Any
from datetime import datetime

# Configuration de l'API
API_BASE_URL = "http://localhost:8088"
API_VERSION = "api/v1"

class MASClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        
    async def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Enregistrer un nouvel utilisateur"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            if response.status_code == 201:
                print(f"✅ Utilisateur créé: {username}")
                return response.json()
            elif response.status_code == 400:
                print(f"ℹ️  Utilisateur déjà existant: {username}")
                return {"exists": True}
            else:
                response.raise_for_status()
    
    async def login(self, username: str, password: str) -> str:
        """Se connecter et obtenir un token JWT"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": username,
                    "password": password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            print(f"✅ Connecté en tant que: {username}")
            return self.token
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer un nouvel agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{API_VERSION}/agents/agents",
                headers=self.headers,
                json=agent_data
            )
            response.raise_for_status()
            agent = response.json()
            print(f"✅ Agent créé: {agent['name']} (ID: {agent['id']})")
            return agent
    
    async def list_agents(self) -> Dict[str, Any]:
        """Lister tous les agents de l'utilisateur"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{API_VERSION}/agents/agents",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Obtenir les détails d'un agent"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{API_VERSION}/agents/agents/{agent_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def start_agent(self, agent_id: str) -> Dict[str, Any]:
        """Démarrer un agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{API_VERSION}/agents/agents/{agent_id}/start",
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✅ Agent démarré: {agent_id}")
            return response.json()
    
    async def send_message_to_agent(self, agent_id: str, message: str) -> Dict[str, Any]:
        """Envoyer un message à un agent (via l'endpoint de tâches)"""
        async with httpx.AsyncClient() as client:
            # Créer une tâche pour l'agent
            task_data = {
                "title": f"Message: {message[:50]}...",
                "description": message,
                "task_type": "query",
                "priority": "high",
                "assigned_to": agent_id,
                "metadata": {
                    "message_type": "user_query",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await client.post(
                f"{self.base_url}/{API_VERSION}/tasks/tasks",
                headers=self.headers,
                json=task_data
            )
            response.raise_for_status()
            task = response.json()
            print(f"📨 Message envoyé à l'agent (Task ID: {task['id']})")
            return task
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Récupérer le résultat d'une tâche"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{API_VERSION}/tasks/tasks/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def add_agent_memory(self, agent_id: str, memory_content: str, memory_type: str = "experience") -> Dict[str, Any]:
        """Ajouter une mémoire à un agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{API_VERSION}/agents/agents/{agent_id}/memories",
                headers=self.headers,
                json={
                    "content": memory_content,
                    "memory_type": memory_type,
                    "importance": 0.8
                }
            )
            response.raise_for_status()
            print(f"💾 Mémoire ajoutée à l'agent")
            return response.json()
    
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Obtenir les métriques de performance d'un agent"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{API_VERSION}/agents/agents/{agent_id}/metrics",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

async def main():
    """Démonstration complète du système MAS"""
    
    print("🚀 Démonstration du Système Multi-Agents MAS v2.0")
    print("=" * 50)
    
    # Initialiser le client
    client = MASClient()
    
    # 1. Créer un utilisateur ou se connecter
    username = "demo_user"
    email = "demo@example.com"
    password = "demo_password_123"
    
    print("\n1️⃣ Authentification")
    await client.register_user(username, email, password)
    await client.login(username, password)
    
    # 2. Créer un agent assistant
    print("\n2️⃣ Création d'un agent assistant")
    agent_data = {
        "name": "Assistant Intelligent",
        "role": "Assistant personnel polyvalent",
        "agent_type": "COGNITIVE",
        "capabilities": [
            "natural_language_processing",
            "task_planning",
            "information_retrieval",
            "problem_solving"
        ],
        "initial_beliefs": {
            "purpose": "Aider l'utilisateur dans diverses tâches",
            "language": "français",
            "expertise": ["recherche", "analyse", "planification"]
        },
        "initial_desires": [
            "Comprendre les besoins de l'utilisateur",
            "Fournir des réponses pertinentes",
            "Apprendre et s'améliorer"
        ],
        "configuration": {
            "llm_model": "qwen3:4b",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "organization_id": None  # Sera défini automatiquement
    }
    
    agent = await client.create_agent(agent_data)
    agent_id = agent["id"]
    
    # 3. Démarrer l'agent
    print("\n3️⃣ Démarrage de l'agent")
    await client.start_agent(agent_id)
    
    # 4. Ajouter des mémoires initiales
    print("\n4️⃣ Ajout de mémoires à l'agent")
    await client.add_agent_memory(
        agent_id,
        "Je suis un assistant intelligent créé pour aider les utilisateurs dans leurs tâches quotidiennes",
        "belief"
    )
    await client.add_agent_memory(
        agent_id,
        "L'utilisateur préfère des réponses en français, claires et structurées",
        "preference"
    )
    
    # 5. Envoyer des requêtes à l'agent
    print("\n5️⃣ Envoi de requêtes à l'agent")
    
    queries = [
        "Bonjour, peux-tu te présenter et m'expliquer tes capacités ?",
        "Aide-moi à planifier une présentation sur l'intelligence artificielle",
        "Quels sont les avantages d'un système multi-agents ?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Requête {i}: {query}")
        
        # Envoyer la requête
        task = await client.send_message_to_agent(agent_id, query)
        task_id = task["id"]
        
        # Attendre et récupérer la réponse
        print("⏳ Attente de la réponse...")
        await asyncio.sleep(2)  # Attendre que l'agent traite la requête
        
        # Récupérer le résultat
        result = await client.get_task_result(task_id)
        
        if result["status"] == "completed":
            print(f"✅ Réponse: {result.get('result', 'Pas de réponse')}")
        else:
            print(f"⏳ Status: {result['status']}")
    
    # 6. Afficher les métriques de l'agent
    print("\n6️⃣ Métriques de performance de l'agent")
    metrics = await client.get_agent_metrics(agent_id)
    print(f"""
    📊 Métriques:
    - Actions totales: {metrics['total_actions']}
    - Taux de succès: {metrics['success_rate']*100:.1f}%
    - Messages traités: {metrics['total_messages']}
    - Temps de réponse moyen: {metrics['average_response_time']:.2f}s
    """)
    
    # 7. Lister tous les agents
    print("\n7️⃣ Liste de tous vos agents")
    agents_list = await client.list_agents()
    for agent in agents_list["items"]:
        print(f"- {agent['name']} ({agent['agent_type']}) - Status: {agent['status']}")
    
    print("\n✅ Démonstration terminée !")

if __name__ == "__main__":
    asyncio.run(main())