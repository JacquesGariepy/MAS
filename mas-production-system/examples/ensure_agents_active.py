#!/usr/bin/env python3
"""
Script pour s'assurer que les agents sont démarrés et actifs pour la communication.

Les agents sont créés avec le statut 'idle' par défaut et doivent être démarrés
pour pouvoir traiter les messages, surtout les agents cognitifs qui utilisent le LLM.
"""

import asyncio
import aiohttp
import json
import sys
from typing import List, Dict, Any

# Configuration API
API_BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@mas.ai"
ADMIN_PASSWORD = "securepassword123"


async def get_auth_token(session: aiohttp.ClientSession) -> str:
    """Obtenir le token d'authentification"""
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    async with session.post(f"{API_BASE_URL}/auth/login", data=login_data) as response:
        if response.status != 200:
            raise Exception(f"Login failed: {await response.text()}")
        
        result = await response.json()
        return result["access_token"]


async def list_agents(session: aiohttp.ClientSession, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Lister tous les agents"""
    async with session.get(f"{API_BASE_URL}/agents", headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Failed to list agents: {await response.text()}")
        
        result = await response.json()
        return result.get("items", [])


async def start_agent(session: aiohttp.ClientSession, headers: Dict[str, str], agent_id: str) -> Dict[str, Any]:
    """Démarrer un agent"""
    try:
        async with session.post(f"{API_BASE_URL}/agents/{agent_id}/start", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result["agent"]
            elif response.status == 400:
                # L'agent est peut-être déjà actif
                error = await response.json()
                print(f"⚠️  Agent {agent_id} : {error.get('detail', 'Déjà actif')}")
                return None
            else:
                raise Exception(f"Failed to start agent: {await response.text()}")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de l'agent {agent_id}: {str(e)}")
        return None


async def ensure_agents_active():
    """S'assurer que tous les agents sont actifs"""
    print("\n🔍 Vérification du statut des agents...\n")
    
    async with aiohttp.ClientSession() as session:
        # Authentification
        try:
            token = await get_auth_token(session)
            headers = {"Authorization": f"Bearer {token}"}
        except Exception as e:
            print(f"❌ Erreur d'authentification: {str(e)}")
            return
        
        # Lister les agents
        try:
            agents = await list_agents(session, headers)
            if not agents:
                print("⚠️  Aucun agent trouvé.")
                return
            
            print(f"📊 {len(agents)} agents trouvés:\n")
            
            # Statistiques
            idle_agents = []
            working_agents = []
            error_agents = []
            
            for agent in agents:
                agent_id = agent["id"]
                name = agent["name"]
                agent_type = agent["type"]
                status = agent["status"]
                
                if status == "idle":
                    idle_agents.append(agent)
                elif status == "working":
                    working_agents.append(agent)
                elif status == "error":
                    error_agents.append(agent)
                
                status_icon = {
                    "idle": "😴",
                    "working": "✅",
                    "error": "❌"
                }.get(status, "❓")
                
                print(f"{status_icon} {name} ({agent_type}) - Status: {status}")
            
            print(f"\n📈 Résumé:")
            print(f"   - Actifs (working): {len(working_agents)}")
            print(f"   - Inactifs (idle): {len(idle_agents)}")
            print(f"   - En erreur: {len(error_agents)}")
            
            # Démarrer les agents inactifs
            if idle_agents:
                print(f"\n🚀 Démarrage de {len(idle_agents)} agents inactifs...")
                
                for agent in idle_agents:
                    agent_id = agent["id"]
                    name = agent["name"]
                    print(f"\n   ▶️  Démarrage de {name}...", end=" ")
                    
                    result = await start_agent(session, headers, agent_id)
                    if result:
                        print("✅ Démarré avec succès!")
                        print(f"      Status: {result.get('status', 'unknown')}")
                    else:
                        print("⚠️  Déjà actif ou erreur")
                
                print("\n✨ Tous les agents ont été traités!")
                
                # Vérifier à nouveau le statut
                print("\n🔄 Vérification finale des statuts...")
                agents = await list_agents(session, headers)
                
                active_count = sum(1 for a in agents if a["status"] == "working")
                print(f"\n✅ {active_count}/{len(agents)} agents sont maintenant actifs!")
                
                # Afficher les agents qui nécessitent une attention particulière
                cognitive_agents = [a for a in agents if a["type"] == "cognitive"]
                if cognitive_agents:
                    print(f"\n🧠 Agents cognitifs (nécessitent LLM):")
                    for agent in cognitive_agents:
                        status_icon = "✅" if agent["status"] == "working" else "⚠️"
                        print(f"   {status_icon} {agent['name']} - {agent['status']}")
                    
                    # Vérifier si le LLM est configuré
                    if any(a["status"] != "working" for a in cognitive_agents):
                        print("\n⚠️  Certains agents cognitifs ne sont pas actifs!")
                        print("   Vérifiez que LLM_API_KEY est configuré dans le .env")
            else:
                print("\n✅ Tous les agents sont déjà actifs!")
                
        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification des agents: {str(e)}")


async def test_agent_communication(session: aiohttp.ClientSession, headers: Dict[str, str], agent_id: str):
    """Tester la communication avec un agent"""
    print(f"\n📨 Test d'envoi de message à l'agent {agent_id}...")
    
    message_data = {
        "content": "Bonjour, peux-tu confirmer que tu es actif et prêt à communiquer?",
        "sender_id": agent_id,  # L'agent s'envoie un message à lui-même pour test
        "receiver_id": agent_id
    }
    
    try:
        async with session.post(
            f"{API_BASE_URL}/agents/{agent_id}/messages",
            headers=headers,
            json=message_data
        ) as response:
            if response.status == 201:
                result = await response.json()
                print("✅ Message envoyé avec succès!")
                print(f"   ID du message: {result['message']['id']}")
                return True
            else:
                error = await response.text()
                print(f"❌ Échec de l'envoi: {error}")
                return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False


async def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🤖 MAS - Vérification et Activation des Agents")
    print("=" * 60)
    
    # S'assurer que les agents sont actifs
    await ensure_agents_active()
    
    # Optionnel : tester la communication
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("\n" + "=" * 60)
        print("🧪 Mode Test - Communication avec les agents")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            token = await get_auth_token(session)
            headers = {"Authorization": f"Bearer {token}"}
            
            agents = await list_agents(session, headers)
            working_agents = [a for a in agents if a["status"] == "working"]
            
            if working_agents:
                # Tester avec le premier agent actif
                test_agent = working_agents[0]
                await test_agent_communication(session, headers, test_agent["id"])
            else:
                print("⚠️  Aucun agent actif trouvé pour le test!")
    
    print("\n✨ Terminé!")


if __name__ == "__main__":
    asyncio.run(main())