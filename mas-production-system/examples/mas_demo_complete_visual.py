#!/usr/bin/env python3
"""
Démonstration MAS complète avec visualisation claire de toutes les interactions.
Montre vraiment les agents qui travaillent ensemble sur un projet concret.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

class VisualMASDemo:
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.communications = []
        
    async def create_user_and_login(self, session: aiohttp.ClientSession, 
                                   username: str, email: str, password: str) -> str:
        """Créer un utilisateur et obtenir le token"""
        register_data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        register_resp = await session.post(
            f"{API_BASE_URL.replace('/api/v1', '')}/auth/register",
            json=register_data
        )
        
        if register_resp.status not in [201, 400]:
            return None
            
        login_data = {"username": username, "password": password}
        login_resp = await session.post(
            f"{API_BASE_URL.replace('/api/v1', '')}/auth/token",
            data=login_data
        )
        
        if login_resp.status == 200:
            token_data = await login_resp.json()
            return token_data["access_token"]
        return None
        
    async def create_agent(self, session: aiohttp.ClientSession, 
                          owner: str, config: Dict) -> Dict:
        """Créer et démarrer un agent"""
        token = self.users.get(owner)
        if not token:
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        
        create_resp = await session.post(
            f"{API_BASE_URL}/agents",
            json=config,
            headers=headers
        )
        
        if create_resp.status == 201:
            agent = await create_resp.json()
            
            # Démarrer l'agent
            start_resp = await session.post(
                f"{API_BASE_URL}/agents/{agent['id']}/start",
                headers=headers
            )
            
            if start_resp.status == 200:
                agent['status'] = 'working'
                return agent
        return None
        
    async def send_and_track_message(self, session: aiohttp.ClientSession,
                                    sender_id: str, receiver_id: str,
                                    performative: str, content: Dict,
                                    sender_token: str, sender_name: str,
                                    receiver_name: str, description: str):
        """Envoyer un message et suivre visuellement"""
        print(f"\n{'='*60}")
        print(f"💬 {description}")
        print(f"📤 {sender_name} → 📥 {receiver_name}")
        print(f"🏷️ Type: {performative}")
        print(f"📝 Message: {json.dumps(content, indent=2, ensure_ascii=False)}")
        
        headers = {"Authorization": f"Bearer {sender_token}"}
        
        message_data = {
            "receiver_id": receiver_id,
            "performative": performative,
            "content": content
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/agents/{sender_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if resp.status == 201:
            print(f"✅ Message envoyé avec succès!")
            self.communications.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "from": sender_name,
                "to": receiver_name,
                "type": performative,
                "description": description
            })
        else:
            print(f"❌ Échec envoi: {resp.status}")
            
        print("="*60)
        
    async def check_messages(self, session: aiohttp.ClientSession):
        """Vérifier et afficher les messages de tous les agents"""
        print("\n\n📮 ÉTAT DES BOÎTES DE RÉCEPTION")
        print("="*80)
        
        for role, agent in self.agents.items():
            token = self.users.get(role)
            if not token:
                continue
                
            headers = {"Authorization": f"Bearer {token}"}
            
            # Essayer l'endpoint inbox
            inbox_resp = await session.get(
                f"{API_BASE_URL}/agents/{agent['id']}/messages/inbox",
                headers=headers
            )
            
            if inbox_resp.status == 200:
                inbox_data = await inbox_resp.json()
                messages = inbox_data.get('items', [])
                
                print(f"\n📧 {agent['name']}:")
                print(f"   📥 Messages reçus: {len(messages)}")
                
                if messages:
                    for msg in messages[:3]:  # Afficher max 3 messages
                        # Trouver l'expéditeur
                        sender_name = "Unknown"
                        for r, a in self.agents.items():
                            if a['id'] == msg.get('sender_id'):
                                sender_name = a['name']
                                break
                        
                        print(f"\n   📌 De: {sender_name}")
                        print(f"      Type: {msg['performative']}")
                        print(f"      Contenu: {str(msg.get('content', {}))[:100]}...")
            else:
                # Essayer l'endpoint messages simple
                messages_resp = await session.get(
                    f"{API_BASE_URL}/agents/{agent['id']}/messages",
                    headers=headers
                )
                
                if messages_resp.status == 200:
                    messages = await messages_resp.json()
                    if isinstance(messages, list):
                        print(f"\n📧 {agent['name']}:")
                        print(f"   📥 Messages: {len(messages)}")
                        
    async def run_demo(self):
        """Démonstration complète avec visualisation"""
        print("🎯 DÉMONSTRATION MAS : SIMULATION D'UN PROJET DE RECHERCHE")
        print("="*80)
        print("\n📚 Contexte: Une équipe d'agents collabore pour analyser")
        print("   l'impact de l'IA sur différents secteurs d'activité")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Créer l'équipe
            print("\n\n👥 PHASE 1: CRÉATION DE L'ÉQUIPE")
            print("-"*60)
            
            unique_id = str(int(time.time()))[-6:]
            
            # Créer 3 utilisateurs
            users = [
                ("researcher", "researcher@mas.ai", "research123"),
                ("analyst", "analyst@mas.ai", "analyst123"),
                ("coordinator", "coordinator@mas.ai", "coord123")
            ]
            
            for username, email, password in users:
                username_full = f"{username}_{unique_id}"
                email_full = email.replace("@", f"_{unique_id}@")
                
                print(f"👤 Création utilisateur: {username_full}")
                token = await self.create_user_and_login(
                    session, username_full, email_full, password
                )
                if token:
                    self.users[username] = token
                    print(f"   ✅ Connecté")
                    
            # Phase 2: Créer les agents
            print("\n\n🤖 PHASE 2: CRÉATION DES AGENTS")
            print("-"*60)
            
            # Agent chercheur (Cognitive)
            researcher_config = {
                "name": f"AIResearcher_{unique_id}",
                "agent_type": "cognitive",
                "role": "Chercheur spécialisé en IA",
                "capabilities": ["research", "analysis", "synthesis"],
                "beliefs": json.dumps({
                    "expertise": "artificial_intelligence",
                    "focus": "business_impact"
                }),
                "desires": json.dumps([
                    "understand_ai_adoption",
                    "identify_trends"
                ])
            }
            
            print(f"\n🔬 Création: {researcher_config['name']}")
            researcher = await self.create_agent(session, "researcher", researcher_config)
            if researcher:
                self.agents["researcher"] = researcher
                print(f"   ✅ Agent cognitif créé")
                
            # Agent analyste (Cognitive)
            analyst_config = {
                "name": f"DataAnalyst_{unique_id}",
                "agent_type": "cognitive",
                "role": "Analyste de données sectorielles",
                "capabilities": ["data_analysis", "statistics", "reporting"],
                "beliefs": json.dumps({
                    "sectors": ["finance", "santé", "industrie"],
                    "metrics": ["productivité", "ROI", "adoption"]
                }),
                "desires": json.dumps([
                    "quantify_impact",
                    "compare_sectors"
                ])
            }
            
            print(f"\n📊 Création: {analyst_config['name']}")
            analyst = await self.create_agent(session, "analyst", analyst_config)
            if analyst:
                self.agents["analyst"] = analyst
                print(f"   ✅ Agent cognitif créé")
                
            # Agent coordinateur (Hybrid)
            coordinator_config = {
                "name": f"ProjectCoordinator_{unique_id}",
                "agent_type": "hybrid",
                "role": "Coordinateur de projet",
                "capabilities": ["coordination", "planning", "reporting"],
                "beliefs": json.dumps({
                    "project": "AI_impact_study",
                    "deadline": "2_weeks"
                }),
                "desires": json.dumps([
                    "complete_project",
                    "coordinate_team"
                ]),
                "reactive_rules": {
                    "progress_check": {
                        "condition": {"time_elapsed": "24h"},
                        "action": "request_status"
                    }
                },
                "cognitive_threshold": 0.6
            }
            
            print(f"\n🎯 Création: {coordinator_config['name']}")
            coordinator = await self.create_agent(session, "coordinator", coordinator_config)
            if coordinator:
                self.agents["coordinator"] = coordinator
                print(f"   ✅ Agent hybride créé")
                
            # Phase 3: Collaboration
            print("\n\n🔄 PHASE 3: COLLABORATION EN ACTION")
            print("-"*60)
            
            await asyncio.sleep(2)
            
            # 1. Le coordinateur lance le projet
            if all(k in self.agents for k in ["coordinator", "researcher"]):
                await self.send_and_track_message(
                    session,
                    self.agents["coordinator"]["id"],
                    self.agents["researcher"]["id"],
                    "request",
                    {
                        "task": "research_ai_impact",
                        "sectors": ["finance", "santé", "industrie"],
                        "deadline": "1_week",
                        "deliverable": "rapport synthétique"
                    },
                    self.users["coordinator"],
                    self.agents["coordinator"]["name"],
                    self.agents["researcher"]["name"],
                    "Le coordinateur demande une recherche sur l'impact de l'IA"
                )
                
            await asyncio.sleep(2)
            
            # 2. Le chercheur demande des données à l'analyste
            if all(k in self.agents for k in ["researcher", "analyst"]):
                await self.send_and_track_message(
                    session,
                    self.agents["researcher"]["id"],
                    self.agents["analyst"]["id"],
                    "query",
                    {
                        "request": "sector_data",
                        "metrics": ["productivity_gains", "cost_reduction", "employee_satisfaction"],
                        "timeframe": "2020-2024"
                    },
                    self.users["researcher"],
                    self.agents["researcher"]["name"],
                    self.agents["analyst"]["name"],
                    "Le chercheur demande des données sectorielles"
                )
                
            await asyncio.sleep(2)
            
            # 3. L'analyste partage ses résultats
            if all(k in self.agents for k in ["analyst", "researcher"]):
                await self.send_and_track_message(
                    session,
                    self.agents["analyst"]["id"],
                    self.agents["researcher"]["id"],
                    "inform",
                    {
                        "analysis_results": {
                            "finance": {"productivity": "+35%", "adoption": "82%"},
                            "santé": {"productivity": "+28%", "adoption": "65%"},
                            "industrie": {"productivity": "+42%", "adoption": "71%"}
                        },
                        "key_finding": "L'industrie montre les gains les plus importants"
                    },
                    self.users["analyst"],
                    self.agents["analyst"]["name"],
                    self.agents["researcher"]["name"],
                    "L'analyste partage les résultats de son analyse"
                )
                
            await asyncio.sleep(2)
            
            # 4. Le chercheur propose des conclusions
            if all(k in self.agents for k in ["researcher", "coordinator"]):
                await self.send_and_track_message(
                    session,
                    self.agents["researcher"]["id"],
                    self.agents["coordinator"]["id"],
                    "propose",
                    {
                        "conclusions": [
                            "L'IA a un impact significatif sur la productivité",
                            "L'industrie est le secteur le plus transformé",
                            "La formation est clé pour l'adoption"
                        ],
                        "recommendations": [
                            "Investir dans la formation IA",
                            "Prioriser l'automatisation industrielle",
                            "Mesurer l'impact humain"
                        ]
                    },
                    self.users["researcher"],
                    self.agents["researcher"]["name"],
                    self.agents["coordinator"]["name"],
                    "Le chercheur propose ses conclusions au coordinateur"
                )
                
            await asyncio.sleep(2)
            
            # 5. Le coordinateur accepte et planifie la suite
            if all(k in self.agents for k in ["coordinator", "researcher", "analyst"]):
                await self.send_and_track_message(
                    session,
                    self.agents["coordinator"]["id"],
                    self.agents["researcher"]["id"],
                    "accept",
                    {
                        "status": "conclusions_approved",
                        "next_steps": [
                            "Finaliser le rapport",
                            "Préparer la présentation",
                            "Planifier la diffusion"
                        ],
                        "feedback": "Excellent travail d'équipe!"
                    },
                    self.users["coordinator"],
                    self.agents["coordinator"]["name"],
                    self.agents["researcher"]["name"],
                    "Le coordinateur valide les conclusions"
                )
                
            # Phase 4: Vérification des messages
            await asyncio.sleep(3)
            await self.check_messages(session)
            
            # Résumé final
            print("\n\n🏁 RÉSUMÉ DE LA COLLABORATION")
            print("="*80)
            print(f"\n✅ Agents créés: {len(self.agents)}")
            print(f"✅ Communications réussies: {len(self.communications)}")
            
            print("\n📋 Flux de travail démontré:")
            for i, comm in enumerate(self.communications, 1):
                print(f"   {i}. [{comm['time']}] {comm['from']} → {comm['to']} ({comm['type']})")
                print(f"      └─ {comm['description']}")
                
            print("\n🎯 Résultats du projet:")
            print("   • Impact IA quantifié par secteur")
            print("   • Industrie identifiée comme secteur clé (+42% productivité)")
            print("   • Recommandations stratégiques formulées")
            print("   • Rapport final en préparation")
            
            print("\n💡 Capacités démontrées:")
            print("   • Agents cognitifs pour analyse complexe")
            print("   • Agent hybride pour coordination adaptative")
            print("   • Communication multi-types (request, query, inform, propose, accept)")
            print("   • Workflow collaboratif complet")
            print("   • Résolution de problème en équipe")

async def main():
    demo = VisualMASDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🚀 Démonstration MAS avec visualisation complète")
    print("   Montre comment des agents collaborent sur un projet réel\n")
    
    asyncio.run(main())