#!/usr/bin/env python3
"""
Démonstration MAS avec distribution active des messages pour déclencher LLM
"""

import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, List

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"


class MASDemo:
    def __init__(self):
        self.session = None
        self.users = {}
        self.agents = {}
        self.timestamp = int(time.time() * 1000) % 1000000
        
    async def setup(self):
        """Setup session and users"""
        self.session = aiohttp.ClientSession()
        
        # Create users
        print("📋 Création des utilisateurs...")
        for name in ["alice", "bob", "charlie"]:
            user_data = {
                "username": f"{name}_{self.timestamp}",
                "email": f"{name}_{self.timestamp}@mas.ai",
                "password": "password123"
            }
            
            # Register
            async with self.session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                if resp.status in [200, 201]:
                    print(f"✅ {name} créé")
                    
            # Login
            login_form = aiohttp.FormData()
            login_form.add_field('username', user_data["username"])
            login_form.add_field('password', user_data["password"])
            
            async with self.session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    self.users[name] = {
                        "username": user_data["username"],
                        "token": auth_resp["access_token"],
                        "headers": {"Authorization": f"Bearer {auth_resp['access_token']}"}
                    }
                    
    async def create_agents(self):
        """Create intelligent agents"""
        print("\n📋 Création des agents...")
        
        # Agent 1: Analyste IA (Cognitif)
        analyst_data = {
            "name": f"AnalysteIA_{self.timestamp}",
            "agent_type": "reactive",  # Cognitif
            "role": "ai_analyst",
            "capabilities": ["analysis", "research", "explanation"],
            "description": "Expert en IA qui analyse et explique des concepts",
            "initial_beliefs": {
                "expertise": ["machine learning", "deep learning", "NLP"],
                "goal": "expliquer clairement les concepts d'IA"
            }
        }
        
        async with self.session.post(
            f"{API_V1}/agents",
            json=analyst_data,
            headers=self.users["alice"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                self.agents["analyst"] = {
                    "id": agent_resp["id"],
                    "name": analyst_data["name"],
                    "owner": "alice"
                }
                print(f"✅ Analyste IA créé")
                
        # Agent 2: Assistant (Cognitif)
        assistant_data = {
            "name": f"Assistant_{self.timestamp}",
            "agent_type": "reactive",  # Cognitif
            "role": "assistant",
            "capabilities": ["conversation", "help", "task_execution"],
            "description": "Assistant qui aide avec diverses tâches",
            "initial_beliefs": {
                "helpful": True,
                "language": "français"
            }
        }
        
        async with self.session.post(
            f"{API_V1}/agents",
            json=assistant_data,
            headers=self.users["bob"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                self.agents["assistant"] = {
                    "id": agent_resp["id"],
                    "name": assistant_data["name"],
                    "owner": "bob"
                }
                print(f"✅ Assistant créé")
                
    async def start_agents(self):
        """Start all agents"""
        print("\n📋 Démarrage des agents...")
        for role, agent in self.agents.items():
            headers = self.users[agent["owner"]]["headers"]
            async with self.session.post(
                f"{API_V1}/agents/{agent['id']}/start",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    print(f"✅ {role.capitalize()} démarré")
                    
    async def trigger_llm_communication(self):
        """Send messages that require LLM processing"""
        print("\n📋 Communication nécessitant LLM")
        print("="*60)
        
        # Question complexe nécessitant le LLM
        print("\n🎯 Question complexe à l'Analyste IA")
        
        complex_message = {
            "sender_id": self.agents["assistant"]["id"],
            "receiver_id": self.agents["analyst"]["id"],
            "performative": "query",
            "content": {
                "question": "Peux-tu m'expliquer en détail la différence entre l'apprentissage supervisé et non supervisé en machine learning? Donne des exemples concrets pour chaque type et explique dans quels cas on utilise l'un plutôt que l'autre.",
                "context": {
                    "niveau": "intermédiaire",
                    "format": "explication détaillée"
                },
                "require_reasoning": True
            }
        }
        
        print(f"📤 Question: '{complex_message['content']['question'][:80]}...'")
        print("\n⚠️  SURVEILLEZ LMSTUDIO MAINTENANT! Une requête devrait apparaître.")
        
        async with self.session.post(
            f"{API_V1}/agents/{self.agents['assistant']['id']}/messages",
            json=complex_message,
            headers=self.users["bob"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                msg_resp = await resp.json()
                message_id = msg_resp['id']
                print(f"✅ Message envoyé (ID: {message_id})")
                
        # Attendre un peu
        print("\n⏳ Attente du traitement LLM (15 secondes)...")
        await asyncio.sleep(15)
        
        # Forcer la vérification des messages non lus
        print("\n📋 Vérification des messages non lus pour chaque agent...")
        
        for role, agent in self.agents.items():
            headers = self.users[agent["owner"]]["headers"]
            
            # Récupérer les messages de l'agent
            async with self.session.get(
                f"{API_V1}/agents/{agent['id']}/messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    
                    # Filtrer les messages reçus non lus
                    unread = [
                        m for m in messages 
                        if isinstance(m, dict) 
                        and m.get('receiver_id') == agent['id']
                        and not m.get('is_read', False)
                    ]
                    
                    if unread:
                        print(f"\n📨 {role.upper()} a {len(unread)} message(s) non lu(s)")
                        
                        # Marquer comme lus (simule le traitement)
                        for msg in unread:
                            if 'id' in msg:
                                async with self.session.put(
                                    f"{API_V1}/agents/{agent['id']}/messages/{msg['id']}/read",
                                    headers=headers
                                ) as read_resp:
                                    if read_resp.status == 200:
                                        print(f"   ✅ Message {msg['id']} marqué comme lu")
                                        # Ceci devrait déclencher le traitement par l'agent
                                        
    async def check_results(self):
        """Check for LLM responses"""
        print("\n📋 Recherche des réponses LLM...")
        
        await asyncio.sleep(5)  # Attendre encore un peu
        
        for role, agent in self.agents.items():
            headers = self.users[agent["owner"]]["headers"]
            
            async with self.session.get(
                f"{API_V1}/agents/{agent['id']}/messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    
                    # Chercher les réponses générées
                    for msg in messages:
                        if isinstance(msg, dict):
                            content = msg.get('content', {})
                            if isinstance(content, dict):
                                # Chercher des signes de réponse LLM
                                if any(key in content for key in ['response', 'answer', 'explanation', 'analysis']):
                                    print(f"\n🤖 RÉPONSE LLM TROUVÉE de {role}!")
                                    print(f"   Type: {msg.get('performative')}")
                                    
                                    # Afficher la réponse
                                    for key in ['response', 'answer', 'explanation', 'analysis']:
                                        if key in content:
                                            response_text = str(content[key])
                                            print(f"   {key.capitalize()}: {response_text[:200]}...")
                                            break
                                            
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
            
    async def run(self):
        """Run the complete demo"""
        print("="*80)
        print("🤖 DÉMONSTRATION MAS - COMMUNICATION LLM RÉELLE")
        print("="*80)
        
        try:
            await self.setup()
            await self.create_agents()
            await self.start_agents()
            await asyncio.sleep(3)  # Let agents initialize
            await self.trigger_llm_communication()
            await self.check_results()
            
            print("\n" + "="*80)
            print("📊 RÉSUMÉ")
            print("="*80)
            print(f"\n✅ Agents créés: {len(self.agents)}")
            print(f"\n🧠 Configuration LLM:")
            print(f"   Provider: {os.getenv('LLM_PROVIDER', 'unknown')}")
            print(f"   Model: {os.getenv('LLM_MODEL', 'unknown')}")
            print(f"   Base URL: {os.getenv('LLM_BASE_URL', 'unknown')}")
            
            print("\n⚠️  Si vous n'avez pas vu de requêtes dans LMStudio:")
            print("   - Vérifiez que LMStudio est bien démarré")
            print("   - Vérifiez que le modèle phi-4-mini-reasoning est chargé")
            print("   - Les agents peuvent nécessiter plus de temps pour traiter")
            
        finally:
            await self.cleanup()


async def main():
    demo = MASDemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())