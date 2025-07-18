#!/usr/bin/env python3
"""
Moniteur en temps réel de l'activité MAS
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"

class MASMonitor:
    def __init__(self):
        self.session = None
        self.token = None
        
    async def setup(self):
        """Configuration initiale"""
        self.session = aiohttp.ClientSession()
        
        # Créer un utilisateur de monitoring
        user_data = {
            "username": f"monitor_{int(datetime.now().timestamp())}",
            "email": f"monitor_{int(datetime.now().timestamp())}@mas.ai",
            "password": "monitor123"
        }
        
        # Register
        async with self.session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
            if resp.status in [200, 201]:
                print("✅ Utilisateur de monitoring créé")
                
        # Login
        login_form = aiohttp.FormData()
        login_form.add_field('username', user_data["username"])
        login_form.add_field('password', user_data["password"])
        
        async with self.session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
            if resp.status == 200:
                auth_resp = await resp.json()
                self.token = auth_resp["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Authentification réussie")
                
    async def get_all_agents(self):
        """Récupérer tous les agents actifs"""
        async with self.session.get(f"{API_V1}/agents?per_page=100", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('items', [])
        return []
        
    async def get_agent_messages(self, agent_id):
        """Récupérer les messages d'un agent"""
        async with self.session.get(
            f"{API_V1}/agents/{agent_id}/messages?message_type=all&per_page=10",
            headers=self.headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('items', [])
        return []
        
    async def monitor_loop(self):
        """Boucle de monitoring"""
        print("\n" + "="*80)
        print("🔍 MONITEUR MAS EN TEMPS RÉEL")
        print("="*80)
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                
                # Clear screen (optionnel)
                # print("\033[2J\033[H")
                
                print(f"\n{'='*60}")
                print(f"📊 CYCLE #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                
                # Récupérer tous les agents
                agents = await self.get_all_agents()
                print(f"\n👥 Agents actifs: {len(agents)}")
                
                for agent in agents:
                    print(f"\n🤖 {agent['name']} ({agent['agent_type']}) - Status: {agent['status']}")
                    
                    # Récupérer les messages
                    messages = await self.get_agent_messages(agent['id'])
                    
                    if messages:
                        print(f"   📨 Messages récents:")
                        for msg in messages[:3]:  # Afficher les 3 derniers
                            direction = "📤 Envoyé à" if msg['sender_id'] == agent['id'] else "📥 Reçu de"
                            other_agent = msg['receiver_id'] if msg['sender_id'] == agent['id'] else msg['sender_id']
                            
                            print(f"      {direction} {other_agent[:8]}...")
                            print(f"         Type: {msg['performative']}")
                            
                            # Afficher le contenu
                            content = msg.get('content', {})
                            if isinstance(content, dict):
                                if 'action' in content:
                                    print(f"         Action: {content['action']}")
                                elif 'question' in content:
                                    print(f"         Question: {content['question'][:50]}...")
                                elif 'response' in content:
                                    print(f"         🤖 RÉPONSE LLM DÉTECTÉE!")
                                    print(f"         Réponse: {str(content['response'])[:100]}...")
                
                # Vérifier la configuration LLM
                print(f"\n🧠 Configuration LLM:")
                print(f"   Provider: {os.getenv('LLM_PROVIDER', 'unknown')}")
                print(f"   Model: {os.getenv('LLM_MODEL', 'unknown')}")
                print(f"   Base URL: {os.getenv('LLM_BASE_URL', 'unknown')}")
                
                # Pause avant le prochain cycle
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Arrêt du monitoring...")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {str(e)}")
                await asyncio.sleep(5)
                
    async def cleanup(self):
        """Nettoyage"""
        if self.session:
            await self.session.close()
            
    async def run(self):
        """Exécuter le moniteur"""
        try:
            await self.setup()
            await self.monitor_loop()
        finally:
            await self.cleanup()

async def main():
    monitor = MASMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())