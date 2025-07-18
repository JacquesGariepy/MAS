#!/usr/bin/env python3
"""
Test complet du système MAS avec communication LLM réelle
"""

import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, List, Optional

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"


class MASCompleteLLMTest:
    def __init__(self):
        self.session = None
        self.users = {}
        self.agents = {}
        self.messages_sent = []
        self.timestamp = int(time.time() * 1000) % 1000000
        
    async def setup(self):
        """Configuration initiale"""
        self.session = aiohttp.ClientSession()
        print("="*80)
        print("🤖 TEST COMPLET MAS - COMMUNICATION LLM RÉELLE")
        print("="*80)
        print("\n📢 Ce test va démontrer:")
        print("   1. Création de 3 agents intelligents")
        print("   2. Communication complexe nécessitant LLM")
        print("   3. Raisonnement et réponses générées par LMStudio")
        print("\n⚠️  SURVEILLEZ LMSTUDIO - Les requêtes vont apparaître!")
        print("="*80)
        
    async def create_users(self):
        """Créer les utilisateurs"""
        print("\n📋 Phase 1: Création des utilisateurs...")
        
        users_data = {
            "alice": {"role": "Chef de Projet", "email": "alice@mas.ai"},
            "bob": {"role": "Architecte Logiciel", "email": "bob@mas.ai"},
            "charlie": {"role": "Expert IA", "email": "charlie@mas.ai"}
        }
        
        for name, info in users_data.items():
            user_data = {
                "username": f"{name}_{self.timestamp}",
                "email": f"{name}_{self.timestamp}@mas.ai",
                "password": "password123"
            }
            
            # Register
            async with self.session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                if resp.status in [200, 201]:
                    print(f"✅ {name.capitalize()} créé ({info['role']})")
                    
            # Login
            login_form = aiohttp.FormData()
            login_form.add_field('username', user_data["username"])
            login_form.add_field('password', user_data["password"])
            
            async with self.session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    self.users[name] = {
                        "username": user_data["username"],
                        "role": info["role"],
                        "token": auth_resp["access_token"],
                        "headers": {"Authorization": f"Bearer {auth_resp['access_token']}"}
                    }
                    
    async def create_intelligent_agents(self):
        """Créer des agents avec capacités cognitives avancées"""
        print("\n📋 Phase 2: Création des agents intelligents...")
        
        # Agent 1: Chef de Projet (Alice) - Cognitif
        chef_data = {
            "name": f"ChefProjet_{self.timestamp}",
            "agent_type": "reactive",  # Cognitif
            "role": "project_manager",
            "capabilities": ["planning", "coordination", "decision_making", "risk_assessment"],
            "description": "Chef de projet expert en méthodologies agiles et gestion d'équipe",
            "initial_beliefs": {
                "methodology": "Agile/Scrum",
                "team_size": 3,
                "project": "Système de recommandation IA",
                "deadline": "3 mois",
                "budget": "100k€"
            },
            "initial_desires": ["livrer_projet", "optimiser_ressources", "minimiser_risques"],
            "configuration": {
                "reasoning_depth": 5,
                "planning_horizon": 10
            }
        }
        
        async with self.session.post(
            f"{API_V1}/agents",
            json=chef_data,
            headers=self.users["alice"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                self.agents["chef"] = {
                    "id": agent_resp["id"],
                    "name": chef_data["name"],
                    "owner": "alice",
                    "type": "cognitive"
                }
                print(f"✅ Chef de Projet créé (Agent Cognitif)")
                
        # Agent 2: Architecte Logiciel (Bob) - Cognitif
        architecte_data = {
            "name": f"Architecte_{self.timestamp}",
            "agent_type": "reactive",  # Cognitif
            "role": "software_architect",
            "capabilities": ["system_design", "technology_selection", "performance_optimization"],
            "description": "Architecte senior spécialisé en systèmes distribués et IA",
            "initial_beliefs": {
                "expertise": ["microservices", "event-driven", "machine learning"],
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes"],
                "patterns": ["CQRS", "Event Sourcing", "Domain-Driven Design"]
            },
            "initial_desires": ["concevoir_architecture_scalable", "assurer_performance", "maintenir_qualité"]
        }
        
        async with self.session.post(
            f"{API_V1}/agents",
            json=architecte_data,
            headers=self.users["bob"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                self.agents["architecte"] = {
                    "id": agent_resp["id"],
                    "name": architecte_data["name"],
                    "owner": "bob",
                    "type": "cognitive"
                }
                print(f"✅ Architecte Logiciel créé (Agent Cognitif)")
                
        # Agent 3: Expert IA (Charlie) - Hybride
        expert_ia_data = {
            "name": f"ExpertIA_{self.timestamp}",
            "agent_type": "hybrid",
            "role": "ai_expert",
            "capabilities": ["ml_modeling", "algorithm_selection", "data_analysis", "model_optimization"],
            "description": "Expert en IA spécialisé en systèmes de recommandation et NLP",
            "reactive_rules": {
                "performance_issue": "Analyser immédiatement les métriques et proposer optimisations",
                "data_quality": "Vérifier la qualité des données avant tout entraînement",
                "model_selection": "Comparer au moins 3 approches différentes"
            },
            "cognitive_threshold": 0.6,
            "initial_beliefs": {
                "algorithms": ["collaborative_filtering", "content_based", "hybrid_approaches"],
                "frameworks": ["TensorFlow", "PyTorch", "Scikit-learn"],
                "metrics": ["precision", "recall", "F1-score", "RMSE"]
            }
        }
        
        async with self.session.post(
            f"{API_V1}/agents",
            json=expert_ia_data,
            headers=self.users["charlie"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                self.agents["expert"] = {
                    "id": agent_resp["id"],
                    "name": expert_ia_data["name"],
                    "owner": "charlie",
                    "type": "hybrid"
                }
                print(f"✅ Expert IA créé (Agent Hybride)")
                
    async def start_all_agents(self):
        """Démarrer tous les agents"""
        print("\n📋 Phase 3: Démarrage des agents...")
        
        for role, agent in self.agents.items():
            headers = self.users[agent["owner"]]["headers"]
            async with self.session.post(
                f"{API_V1}/agents/{agent['id']}/start",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    print(f"✅ {role.capitalize()} démarré et prêt")
                    
        # Attendre l'initialisation
        print("\n⏳ Initialisation des agents (5 secondes)...")
        await asyncio.sleep(5)
        
    async def complex_scenario_1(self):
        """Scénario 1: Planification du projet"""
        print("\n🎯 Scénario 1: Planification initiale du projet")
        print("-" * 60)
        
        # Chef demande à l'Architecte une proposition d'architecture
        message = {
            "sender_id": self.agents["chef"]["id"],
            "receiver_id": self.agents["architecte"]["id"],
            "performative": "request",
            "content": {
                "action": "proposer_architecture",
                "context": {
                    "projet": "Système de recommandation pour e-commerce",
                    "contraintes": [
                        "100k utilisateurs actifs/jour",
                        "Temps de réponse < 200ms",
                        "Scalabilité horizontale requise",
                        "Intégration avec système existant"
                    ],
                    "délai": "3 mois",
                    "équipe": "3 développeurs seniors"
                },
                "question": "Peux-tu proposer une architecture technique détaillée avec les composants principaux, les technologies recommandées et une estimation de l'effort de développement?"
            }
        }
        
        print(f"📤 Chef → Architecte: Demande d'architecture")
        print(f"   Projet: {message['content']['context']['projet']}")
        print(f"   Contraintes: {len(message['content']['context']['contraintes'])} définies")
        
        resp = await self._send_message(message, "alice")
        if resp:
            self.messages_sent.append(resp['id'])
            print(f"   ✅ Message envoyé (ID: {resp['id'][:8]}...)")
            print("   🧠 LMSTUDIO devrait recevoir une requête maintenant!")
            
    async def complex_scenario_2(self):
        """Scénario 2: Consultation sur les algorithmes IA"""
        print("\n🎯 Scénario 2: Sélection des algorithmes de recommandation")
        print("-" * 60)
        
        # Architecte consulte l'Expert IA
        message = {
            "sender_id": self.agents["architecte"]["id"],
            "receiver_id": self.agents["expert"]["id"],
            "performative": "query",
            "content": {
                "question": "Pour un système de recommandation e-commerce avec 100k utilisateurs, quels algorithmes recommandes-tu? Compare les approches collaborative filtering, content-based et hybride en termes de performance, scalabilité et cold start problem.",
                "données_disponibles": [
                    "Historique d'achats (2 ans)",
                    "Évaluations produits (1-5 étoiles)",
                    "Données comportementales (clics, temps passé)",
                    "Métadonnées produits (catégories, prix, descriptions)"
                ],
                "métriques_cibles": {
                    "precision": ">0.8",
                    "temps_calcul": "<200ms",
                    "couverture_catalogue": ">60%"
                }
            }
        }
        
        print(f"📤 Architecte → Expert IA: Consultation algorithmes")
        print(f"   Données: {len(message['content']['données_disponibles'])} sources")
        print(f"   Question technique complexe nécessitant analyse approfondie")
        
        resp = await self._send_message(message, "bob")
        if resp:
            self.messages_sent.append(resp['id'])
            print(f"   ✅ Message envoyé (ID: {resp['id'][:8]}...)")
            print("   🧠 Nouvelle requête LLM en cours!")
            
    async def complex_scenario_3(self):
        """Scénario 3: Analyse de risques"""
        print("\n🎯 Scénario 3: Analyse des risques du projet")
        print("-" * 60)
        
        # Expert IA informe le Chef des risques techniques
        message = {
            "sender_id": self.agents["expert"]["id"],
            "receiver_id": self.agents["chef"]["id"],
            "performative": "inform",
            "content": {
                "type": "analyse_risques",
                "risques_identifiés": [
                    {
                        "risque": "Cold start problem",
                        "impact": "Nouveaux utilisateurs sans recommandations pertinentes",
                        "probabilité": "haute",
                        "mitigation": "Implémenter système hybride avec règles métier"
                    },
                    {
                        "risque": "Scalabilité des calculs",
                        "impact": "Dégradation performance avec croissance utilisateurs",
                        "probabilité": "moyenne",
                        "mitigation": "Architecture lambda avec pré-calculs batch"
                    },
                    {
                        "risque": "Biais dans les recommandations",
                        "impact": "Réduction diversité et satisfaction utilisateur",
                        "probabilité": "moyenne",
                        "mitigation": "Algorithmes de diversification et tests A/B"
                    }
                ],
                "recommandation": "Prévoir 20% de temps supplémentaire pour gestion des risques",
                "demande_décision": "Valider l'approche hybride malgré complexité accrue?"
            }
        }
        
        print(f"📤 Expert IA → Chef: Rapport d'analyse des risques")
        print(f"   Risques identifiés: {len(message['content']['risques_identifiés'])}")
        print(f"   Demande de décision stratégique")
        
        resp = await self._send_message(message, "charlie")
        if resp:
            self.messages_sent.append(resp['id'])
            print(f"   ✅ Message envoyé (ID: {resp['id'][:8]}...)")
            print("   🧠 Le Chef doit analyser et prendre une décision!")
            
    async def _send_message(self, message_data: dict, sender_user: str) -> Optional[dict]:
        """Envoyer un message et retourner la réponse"""
        try:
            headers = self.users[sender_user]["headers"]
            sender_id = message_data["sender_id"]
            
            async with self.session.post(
                f"{API_V1}/agents/{sender_id}/messages",
                json=message_data,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                else:
                    print(f"   ❌ Erreur envoi: {resp.status}")
                    return None
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            return None
            
    async def wait_and_check_responses(self):
        """Attendre et vérifier les réponses LLM"""
        print("\n📋 Phase 4: Surveillance de l'activité des agents...")
        
        # Attendre que les agents traitent les messages
        max_wait = 60  # Maximum 60 secondes
        check_interval = 3  # Vérifier toutes les 3 secondes
        activity_detected = False
        message_history = {}  # Track messages per agent
        llm_responses_count = 0
        
        for elapsed in range(0, max_wait, check_interval):
            print(f"\r⏳ Surveillance de l'activité... {elapsed}/{max_wait}s", end="", flush=True)
            
            # Vérifier les messages de chaque agent
            new_activity = False
            for role, agent in self.agents.items():
                headers = self.users[agent["owner"]]["headers"]
                agent_id = agent['id']
                
                try:
                    async with self.session.get(
                        f"{API_V1}/agents/{agent_id}/messages",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            messages = await resp.json()
                            
                            # Count messages for this agent
                            current_count = len(messages) if isinstance(messages, list) else len(messages.get('items', []))
                            previous_count = message_history.get(agent_id, 0)
                            
                            if current_count > previous_count:
                                new_activity = True
                                activity_detected = True
                                message_history[agent_id] = current_count
                                
                                # Check for LLM-generated responses
                                message_list = messages if isinstance(messages, list) else messages.get('items', [])
                                for msg in message_list[previous_count:]:  # Only check new messages
                                    if isinstance(msg, dict):
                                        content = msg.get('content', {})
                                        if isinstance(content, dict):
                                            # Look for signs of LLM responses
                                            llm_indicators = ['response', 'answer', 'analysis', 'recommendation', 
                                                            'proposal', 'evaluation', 'suggestion', 'explanation']
                                            if any(indicator in content for indicator in llm_indicators):
                                                llm_responses_count += 1
                                                print(f"\n   🤖 Réponse LLM détectée de {role}!")
                except Exception as e:
                    pass
            
            if new_activity:
                total_messages = sum(message_history.values())
                print(f"\r✅ Activité en cours! Messages: {total_messages} | Réponses LLM: {llm_responses_count}     ")
                # Donner plus de temps pour traiter après activité
                await asyncio.sleep(check_interval * 2)
            else:
                await asyncio.sleep(check_interval)
                
        # Résumé final
        if activity_detected:
            total_messages = sum(message_history.values())
            print(f"\n✅ Traitement terminé! Total messages: {total_messages} | Réponses LLM: {llm_responses_count}")
        else:
            print("\n⚠️  Aucune activité détectée. Vérifiez que LMStudio est actif.")
        
        print("\n📋 Phase 5: Vérification des réponses générées par LLM...")
        print("="*60)
        
        responses_found = 0
        
        for role, agent in self.agents.items():
            headers = self.users[agent["owner"]]["headers"]
            
            print(f"\n📊 Messages de {role.upper()}:")
            
            async with self.session.get(
                f"{API_V1}/agents/{agent['id']}/messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    
                    # Séparer messages reçus et envoyés
                    received = []
                    sent = []
                    
                    for msg in messages:
                        if isinstance(msg, dict):
                            if msg.get('receiver_id') == agent['id']:
                                received.append(msg)
                            elif msg.get('sender_id') == agent['id']:
                                sent.append(msg)
                    
                    print(f"   📥 Messages reçus: {len(received)}")
                    print(f"   📤 Messages envoyés: {len(sent)}")
                    
                    # Afficher les messages envoyés et reçus
                    if sent:
                        print(f"\n   📤 Messages envoyés:")
                        for msg in sent[:3]:  # Afficher les 3 premiers
                            print(f"      - À: {self._get_agent_name(msg.get('receiver_id'))}")
                            print(f"        Type: {msg.get('performative')}")
                            if isinstance(msg.get('content'), dict):
                                print(f"        Action: {msg['content'].get('action', 'N/A')}")
                    
                    if received:
                        print(f"\n   📥 Messages reçus:")
                        for msg in received[:3]:  # Afficher les 3 premiers
                            print(f"      - De: {self._get_agent_name(msg.get('sender_id'))}")
                            print(f"        Type: {msg.get('performative')}")
                            
                    # Chercher les réponses générées par LLM
                    for msg in messages:
                        if isinstance(msg, dict):
                            content = msg.get('content', {})
                            if isinstance(content, dict):
                                # Indicateurs de réponse LLM
                                llm_indicators = [
                                    'response', 'answer', 'analysis', 'recommendation',
                                    'proposal', 'evaluation', 'suggestion', 'explanation'
                                ]
                                
                                for indicator in llm_indicators:
                                    if indicator in content:
                                        responses_found += 1
                                        print(f"\n   🤖 RÉPONSE LLM DÉTECTÉE!")
                                        print(f"      Type: {msg.get('performative')}")
                                        print(f"      De: {self._get_agent_name(msg.get('sender_id'))}")
                                        print(f"      Vers: {self._get_agent_name(msg.get('receiver_id'))}")
                                        
                                        response_text = str(content[indicator])
                                        print(f"      {indicator.capitalize()}:")
                                        # Afficher les premières lignes de la réponse
                                        lines = response_text.split('\n')
                                        for i, line in enumerate(lines[:5]):
                                            if line.strip():
                                                print(f"         {line.strip()}")
                                        if len(lines) > 5:
                                            print(f"         ... ({len(lines)-5} lignes supplémentaires)")
                                        break
                                        
        return responses_found
        
    def _get_agent_name(self, agent_id: str) -> str:
        """Obtenir le nom d'un agent par son ID"""
        for role, agent in self.agents.items():
            if agent['id'] == agent_id:
                return f"{role.capitalize()} ({agent['name']})"
        return "Unknown"
        
    async def generate_summary(self, responses_found: int, total_cycles: int = 1):
        """Générer un résumé de l'exécution"""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DE L'EXÉCUTION")
        print("="*80)
        
        print(f"\n✅ Utilisateurs créés: {len(self.users)}")
        print(f"✅ Agents créés: {len(self.agents)}")
        print(f"✅ Cycles exécutés: {total_cycles}")
        print(f"✅ Messages envoyés total: {len(self.messages_sent)} ({len(self.messages_sent)//total_cycles if total_cycles > 0 else 0} par cycle)")
        print(f"✅ Réponses LLM détectées: {responses_found}")
        
        print(f"\n🧠 Configuration LLM:")
        print(f"   Provider: {os.getenv('LLM_PROVIDER', 'unknown')}")
        print(f"   Model: {os.getenv('LLM_MODEL', 'unknown')}")
        print(f"   Base URL: {os.getenv('LLM_BASE_URL', 'unknown')}")
        
        if responses_found > 0:
            print("\n🎉 SUCCÈS! Les agents ont communiqué via LLM!")
            print("   ✅ Les messages ont été traités par les agents cognitifs")
            print("   ✅ LMStudio a généré des réponses intelligentes")
            print("   ✅ La communication inter-agents fonctionne parfaitement")
        else:
            print("\n⚠️  Aucune réponse LLM détectée")
            print("   Vérifiez que:")
            print("   - LMStudio est démarré avec le modèle chargé")
            print("   - Les agents ont eu assez de temps pour traiter")
            print("   - Le service de livraison des messages fonctionne")
            
    async def cleanup(self):
        """Nettoyage"""
        if self.session:
            await self.session.close()
            
    async def run(self):
        """Exécuter le test complet en boucle continue"""
        try:
            await self.setup()
            await self.create_users()
            await self.create_intelligent_agents()
            await self.start_all_agents()
            
            print("\n🔄 DÉMARRAGE DU MODE BOUCLE CONTINUE")
            print("   Appuyez sur Ctrl+C pour arrêter\n")
            
            cycle_count = 0
            
            while True:
                try:
                    cycle_count += 1
                    print(f"\n{'='*80}")
                    print(f"🔁 CYCLE #{cycle_count}")
                    print(f"{'='*80}")
                    
                    # Exécuter les scénarios
                    await self.complex_scenario_1()
                    await asyncio.sleep(5)
                    
                    await self.complex_scenario_2()
                    await asyncio.sleep(5)
                    
                    await self.complex_scenario_3()
                    
                    # Vérifier les résultats
                    responses_found = await self.wait_and_check_responses()
                    
                    # Afficher un résumé rapide du cycle
                    print(f"\n📊 Résumé du cycle #{cycle_count}:")
                    print(f"   - Messages envoyés: 3")
                    print(f"   - Réponses LLM détectées: {responses_found}")
                    print(f"   - Agents actifs: {len(self.agents)}")
                    
                    # Pause entre les cycles
                    print(f"\n⏸️  Pause de 10 secondes avant le prochain cycle...")
                    await asyncio.sleep(10)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interruption détectée - Arrêt du test...")
                    break
                except Exception as e:
                    print(f"\n❌ Erreur dans le cycle #{cycle_count}: {str(e)}")
                    print("   Tentative de continuer dans 5 secondes...")
                    await asyncio.sleep(5)
            
            # Générer le résumé final avec le nombre total de cycles
            await self.generate_summary(responses_found, cycle_count)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption détectée - Nettoyage en cours...")
        finally:
            await self.cleanup()


async def main():
    test = MASCompleteLLMTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())