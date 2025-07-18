#!/usr/bin/env python3
"""
Démonstration MAS : Équipe de recherche collaborative

Scénario plus simple : Une équipe d'agents travaille ensemble pour analyser
et résoudre un problème de recherche complexe en utilisant leurs spécialités.

Agents:
- Chercheur Principal (Cognitive) : Dirige la recherche
- Analyste de Données (Cognitive) : Analyse les données
- Expert Domaine (Hybrid) : Apporte l'expertise métier
- Assistant de Recherche (Reflexive) : Tâches de support
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

API_BASE_URL = "http://localhost:8000/api/v1"

class ResearchTeamDemo:
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.messages_sent = []
        self.research_topic = {
            "title": "Impact de l'IA sur la productivité en entreprise",
            "objectives": [
                "Analyser les tendances actuelles",
                "Identifier les secteurs les plus impactés",
                "Proposer des recommandations"
            ],
            "data_sources": ["études académiques", "rapports industrie", "enquêtes terrain"]
        }
        
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
            print(f"❌ Erreur création utilisateur {username}")
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
                          owner: str, agent_data: Dict) -> Dict:
        """Créer et démarrer un agent"""
        token = self.users.get(owner)
        if not token:
            print(f"❌ Token manquant pour {owner}")
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Créer l'agent
        create_resp = await session.post(
            f"{API_BASE_URL}/agents",
            json=agent_data,
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
            else:
                print(f"❌ Erreur démarrage agent: {start_resp.status}")
                return agent
        else:
            error_text = await create_resp.text()
            print(f"❌ Erreur création agent: {create_resp.status} - {error_text}")
            return None
            
    async def send_message(self, session: aiohttp.ClientSession,
                          sender_id: str, receiver_id: str,
                          performative: str, content: Dict,
                          sender_token: str) -> bool:
        """Envoyer un message entre agents"""
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
            self.messages_sent.append({
                "from": sender_id,
                "to": receiver_id,
                "type": performative,
                "content": content
            })
            return True
        return False
        
    async def get_agent_messages(self, session: aiohttp.ClientSession,
                                agent_id: str, owner_token: str) -> Dict:
        """Récupérer les messages d'un agent"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        inbox_resp = await session.get(
            f"{API_BASE_URL}/agents/{agent_id}/messages/inbox",
            headers=headers
        )
        
        sent_resp = await session.get(
            f"{API_BASE_URL}/agents/{agent_id}/messages/sent",
            headers=headers
        )
        
        inbox = {"items": []}
        sent = {"items": []}
        
        if inbox_resp.status == 200:
            inbox = await inbox_resp.json()
        if sent_resp.status == 200:
            sent = await sent_resp.json()
            
        return {"inbox": inbox, "sent": sent}
        
    async def run_demo(self):
        """Exécuter la démonstration"""
        print("="*80)
        print("🔬 DÉMONSTRATION MAS : Équipe de Recherche Collaborative")
        print("="*80)
        print(f"\n📚 Sujet de recherche: {self.research_topic['title']}")
        print("\n🎯 Objectifs:")
        for obj in self.research_topic['objectives']:
            print(f"   • {obj}")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Créer l'équipe de recherche
            print("\n\n👥 PHASE 1: Constitution de l'équipe de recherche")
            print("-"*60)
            
            unique_id = str(int(time.time()))[-6:]
            
            # Créer les utilisateurs
            team_members = [
                ("lead_researcher", "lead@research.ai", "research123"),
                ("data_analyst", "analyst@research.ai", "analysis123"),
                ("domain_expert", "expert@research.ai", "expertise123"),
                ("research_assistant", "assistant@research.ai", "assist123")
            ]
            
            for username, email, password in team_members:
                user_key = username
                username_unique = f"{username}_{unique_id}"
                email_unique = email.replace("@", f"_{unique_id}@")
                
                print(f"\n👤 Création: {username_unique}")
                token = await self.create_user_and_login(
                    session, username_unique, email_unique, password
                )
                if token:
                    self.users[user_key] = token
                    print(f"   ✅ Connecté")
                    
            # Phase 2: Créer les agents
            print("\n\n🤖 PHASE 2: Création des agents spécialisés")
            print("-"*60)
            
            # Chercheur principal (Cognitive)
            lead_config = {
                "name": f"LeadResearcher_{unique_id}",
                "agent_type": "cognitive",
                "role": "Chercheur principal - Direction de la recherche",
                "capabilities": ["research_planning", "synthesis", "coordination"],
                "beliefs": json.dumps({
                    "research_topic": self.research_topic,
                    "methodology": "mixed_methods",
                    "team_size": 4
                }),
                "desires": json.dumps([
                    "complete_research",
                    "publish_findings",
                    "coordinate_team"
                ]),
                "intentions": json.dumps([
                    "define_research_plan",
                    "assign_tasks",
                    "synthesize_results"
                ])
            }
            
            print(f"\n🔬 Création: {lead_config['name']}")
            print(f"   Type: {lead_config['agent_type']}")
            lead_agent = await self.create_agent(session, "lead_researcher", lead_config)
            if lead_agent:
                self.agents["lead_researcher"] = lead_agent
                print(f"   ✅ Agent créé et actif")
                
            # Analyste de données (Cognitive)
            analyst_config = {
                "name": f"DataAnalyst_{unique_id}",
                "agent_type": "cognitive",
                "role": "Analyste de données - Analyse quantitative",
                "capabilities": ["data_analysis", "statistics", "visualization"],
                "beliefs": json.dumps({
                    "tools": ["Python", "R", "SQL"],
                    "methods": ["regression", "clustering", "timeseries"]
                }),
                "desires": json.dumps([
                    "find_patterns",
                    "validate_hypotheses",
                    "create_insights"
                ]),
                "intentions": json.dumps([
                    "collect_data",
                    "analyze_trends",
                    "report_findings"
                ])
            }
            
            print(f"\n📊 Création: {analyst_config['name']}")
            print(f"   Type: {analyst_config['agent_type']}")
            analyst_agent = await self.create_agent(session, "data_analyst", analyst_config)
            if analyst_agent:
                self.agents["data_analyst"] = analyst_agent
                print(f"   ✅ Agent créé et actif")
                
            # Expert domaine (Hybrid)
            expert_config = {
                "name": f"DomainExpert_{unique_id}",
                "agent_type": "hybrid",
                "role": "Expert domaine - Expertise métier IA et productivité",
                "capabilities": ["domain_knowledge", "trend_analysis", "advisory"],
                "beliefs": json.dumps({
                    "expertise": "AI_productivity",
                    "experience_years": 10,
                    "sectors": ["tech", "finance", "manufacturing"]
                }),
                "desires": json.dumps([
                    "share_expertise",
                    "validate_findings",
                    "provide_context"
                ])
            }
            
            print(f"\n🎓 Création: {expert_config['name']}")
            print(f"   Type: {expert_config['agent_type']}")
            expert_agent = await self.create_agent(session, "domain_expert", expert_config)
            if expert_agent:
                self.agents["domain_expert"] = expert_agent
                print(f"   ✅ Agent créé et actif")
                
            # Assistant de recherche (Reflexive)
            assistant_config = {
                "name": f"ResearchAssistant_{unique_id}",
                "agent_type": "reflexive",
                "role": "Assistant de recherche - Support et documentation",
                "capabilities": ["documentation", "scheduling", "communication"]
            }
            
            print(f"\n📝 Création: {assistant_config['name']}")
            print(f"   Type: {assistant_config['agent_type']}")
            assistant_agent = await self.create_agent(session, "research_assistant", assistant_config)
            if assistant_agent:
                self.agents["research_assistant"] = assistant_agent
                print(f"   ✅ Agent créé et actif")
                
            # Phase 3: Collaboration de recherche
            print("\n\n🔄 PHASE 3: Processus de recherche collaborative")
            print("-"*60)
            
            # Le chercheur principal lance le projet
            if "lead_researcher" in self.agents and "data_analyst" in self.agents:
                lead = self.agents["lead_researcher"]
                analyst = self.agents["data_analyst"]
                
                print(f"\n📨 {lead['name']} → {analyst['name']}")
                print("   📋 Demande d'analyse des données disponibles")
                
                await self.send_message(
                    session,
                    lead['id'],
                    analyst['id'],
                    "request",
                    {
                        "task": "analyze_data",
                        "focus": "AI adoption trends",
                        "sectors": ["technology", "finance", "healthcare"],
                        "timeframe": "2020-2024"
                    },
                    self.users["lead_researcher"]
                )
                
            # Le chercheur consulte l'expert
            if "lead_researcher" in self.agents and "domain_expert" in self.agents:
                lead = self.agents["lead_researcher"]
                expert = self.agents["domain_expert"]
                
                print(f"\n📨 {lead['name']} → {expert['name']}")
                print("   🤔 Consultation sur les tendances observées")
                
                await self.send_message(
                    session,
                    lead['id'],
                    expert['id'],
                    "query",
                    {
                        "question": "Quels sont les principaux facteurs d'adoption de l'IA?",
                        "context": "Étude sur la productivité",
                        "need": "expertise sectorielle"
                    },
                    self.users["lead_researcher"]
                )
                
            await asyncio.sleep(2)
            
            # L'analyste partage ses résultats
            if "data_analyst" in self.agents and "lead_researcher" in self.agents:
                analyst = self.agents["data_analyst"]
                lead = self.agents["lead_researcher"]
                
                print(f"\n📨 {analyst['name']} → {lead['name']}")
                print("   📊 Résultats de l'analyse préliminaire")
                
                await self.send_message(
                    session,
                    analyst['id'],
                    lead['id'],
                    "inform",
                    {
                        "findings": {
                            "adoption_rate": "73% des entreprises tech",
                            "productivity_gain": "+28% en moyenne",
                            "main_applications": ["automatisation", "analyse prédictive", "support client"]
                        },
                        "confidence": 0.85,
                        "sample_size": 500
                    },
                    self.users["data_analyst"]
                )
                
            # L'expert propose des insights
            if "domain_expert" in self.agents and "lead_researcher" in self.agents:
                expert = self.agents["domain_expert"]
                lead = self.agents["lead_researcher"]
                
                print(f"\n📨 {expert['name']} → {lead['name']}")
                print("   💡 Insights et recommandations d'expert")
                
                await self.send_message(
                    session,
                    expert['id'],
                    lead['id'],
                    "propose",
                    {
                        "insights": [
                            "L'adoption dépend fortement de la maturité digitale",
                            "Les gains sont maximaux avec une stratégie intégrée",
                            "La formation est un facteur critique de succès"
                        ],
                        "recommendations": [
                            "Focus sur les cas d'usage à ROI rapide",
                            "Investir dans la formation continue",
                            "Mesurer l'impact sur la satisfaction employés"
                        ]
                    },
                    self.users["domain_expert"]
                )
                
            # Le chercheur demande à l'assistant de documenter
            if "lead_researcher" in self.agents and "research_assistant" in self.agents:
                lead = self.agents["lead_researcher"]
                assistant = self.agents["research_assistant"]
                
                print(f"\n📨 {lead['name']} → {assistant['name']}")
                print("   📝 Demande de documentation des résultats")
                
                await self.send_message(
                    session,
                    lead['id'],
                    assistant['id'],
                    "request",
                    {
                        "action": "document_findings",
                        "sections": ["methodology", "results", "recommendations"],
                        "format": "research_paper"
                    },
                    self.users["lead_researcher"]
                )
                
            # L'assistant confirme
            if "research_assistant" in self.agents and "lead_researcher" in self.agents:
                assistant = self.agents["research_assistant"]
                lead = self.agents["lead_researcher"]
                
                print(f"\n📨 {assistant['name']} → {lead['name']}")
                print("   ✅ Confirmation de la documentation")
                
                await self.send_message(
                    session,
                    assistant['id'],
                    lead['id'],
                    "accept",
                    {
                        "task": "documentation",
                        "status": "in_progress",
                        "estimated_completion": "2_hours"
                    },
                    self.users["research_assistant"]
                )
                
            # Phase 4: Synthèse des résultats
            print("\n\n📊 PHASE 4: Synthèse et résultats")
            print("-"*60)
            
            await asyncio.sleep(3)
            
            # Vérifier les messages de chaque agent
            for role, agent in self.agents.items():
                if role not in self.users:
                    continue
                    
                messages = await self.get_agent_messages(
                    session, agent['id'], self.users[role]
                )
                
                print(f"\n📧 {agent['name']}:")
                print(f"   📥 Messages reçus: {len(messages['inbox']['items'])}")
                print(f"   📤 Messages envoyés: {len(messages['sent']['items'])}")
                
                # Afficher quelques messages reçus
                if messages['inbox']['items']:
                    for msg in messages['inbox']['items'][:2]:
                        sender_name = "Unknown"
                        for r, a in self.agents.items():
                            if a['id'] == msg.get('sender_id'):
                                sender_name = a['name']
                                break
                        print(f"      • De: {sender_name} ({msg['performative']})")
                        
            # Résumé de la recherche
            print("\n\n📋 RÉSULTATS DE LA RECHERCHE COLLABORATIVE")
            print("="*80)
            print("\n🔍 Principales découvertes:")
            print("   • 73% des entreprises tech ont adopté l'IA")
            print("   • Gain de productivité moyen: +28%")
            print("   • Applications principales: automatisation, prédictif, support")
            
            print("\n💡 Insights clés:")
            print("   • La maturité digitale est critique")
            print("   • Une stratégie intégrée maximise les gains")
            print("   • La formation est essentielle")
            
            print("\n📌 Recommandations:")
            print("   • Prioriser les cas d'usage à ROI rapide")
            print("   • Investir dans la formation continue")
            print("   • Mesurer l'impact humain")
            
            print("\n\n🎯 DÉMONSTRATION RÉUSSIE")
            print("="*80)
            print(f"✅ Équipe créée: {len(self.agents)} agents spécialisés")
            print(f"✅ Messages échangés: {len(self.messages_sent)}")
            print(f"✅ Types d'agents: Cognitive, Hybrid, Reflexive")
            print(f"✅ Collaboration: Multi-agents coordonnée")
            
            print("\n🚀 Capacités démontrées:")
            print("   • Communication inter-agents sophistiquée")
            print("   • Spécialisation des rôles")
            print("   • Workflow de recherche complet")
            print("   • Synthèse collaborative des résultats")

async def main():
    demo = ResearchTeamDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🔬 MAS - Démonstration d'équipe de recherche collaborative")
    print("   Cette démo illustre comment des agents spécialisés")
    print("   collaborent pour mener une recherche complexe.")
    print()
    
    asyncio.run(main())