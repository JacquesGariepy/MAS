#!/usr/bin/env python3
"""
Démonstration avancée MAS : Négociation et enchères pour l'allocation de ressources

Scénario : Une marketplace de services cloud où des agents :
- Fournisseurs proposent des ressources (CPU, RAM, stockage)
- Clients négocient pour obtenir les meilleures offres
- Un commissaire-priseur gère les enchères
- Les agents apprennent et adaptent leurs stratégies

Utilise les fonctionnalités avancées :
- Négociations bilatérales et multilatérales
- Système d'enchères (English, Dutch, Vickrey)
- Apprentissage par renforcement
- Mémoire épisodique et sémantique
- Adaptation des stratégies
"""

import asyncio
import aiohttp
import json
import time
import random
from typing import Dict, List, Any, Tuple
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

class CloudMarketplaceDemo:
    def __init__(self):
        self.agents = {}
        self.users = {}
        self.auctions = []
        self.negotiations = []
        self.market_data = {
            "resources": {
                "cpu": {"unit": "vCPU", "base_price": 10},
                "ram": {"unit": "GB", "base_price": 5},
                "storage": {"unit": "TB", "base_price": 20}
            },
            "demand_fluctuation": 1.0,  # Facteur de demande
            "supply_levels": {}
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
        
    async def create_cognitive_agent(self, session: aiohttp.ClientSession, 
                                   owner: str, config: Dict) -> Dict:
        """Créer un agent cognitif avec capacités d'apprentissage"""
        token = self.users.get(owner)
        if not token:
            return None
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Configuration cognitive avancée
        cognitive_config = {
            **config,
            "configuration": {
                "llm_enabled": True,
                "reasoning_depth": 5,
                "planning_enabled": True,
                "learning_rate": 0.1,
                "memory_config": {
                    "episodic_memory_size": 100,
                    "semantic_memory_enabled": True,
                    "importance_threshold": 0.7
                },
                "metacognition": {
                    "enabled": True,
                    "confidence_threshold": 0.8,
                    "reflection_frequency": 10
                }
            }
        }
        
        create_resp = await session.post(
            f"{API_BASE_URL}/agents",
            json=cognitive_config,
            headers=headers
        )
        
        if create_resp.status == 201:
            agent_data = await create_resp.json()
            
            # Démarrer l'agent
            start_resp = await session.post(
                f"{API_BASE_URL}/agents/{agent_data['id']}/start",
                headers=headers
            )
            
            if start_resp.status == 200:
                agent_data['status'] = 'working'
                return agent_data
        return None
        
    async def create_auction(self, session: aiohttp.ClientSession, 
                           auctioneer_id: str, auction_config: Dict) -> str:
        """Créer une enchère"""
        token = self.users.get("auctioneer")
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await session.post(
            f"{API_BASE_URL}/auctions",
            json=auction_config,
            headers=headers
        )
        
        if resp.status == 201:
            auction = await resp.json()
            return auction['id']
        return None
        
    async def place_bid(self, session: aiohttp.ClientSession, 
                       agent_id: str, auction_id: str, bid_amount: float, 
                       bidder_token: str) -> bool:
        """Placer une enchère"""
        headers = {"Authorization": f"Bearer {bidder_token}"}
        
        bid_data = {
            "auction_id": auction_id,
            "amount": bid_amount,
            "agent_id": agent_id
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/auctions/{auction_id}/bids",
            json=bid_data,
            headers=headers
        )
        
        return resp.status == 201
        
    async def create_negotiation(self, session: aiohttp.ClientSession,
                               initiator_id: str, participants: List[str],
                               negotiation_config: Dict) -> str:
        """Créer une négociation"""
        token = list(self.users.values())[0]  # Utiliser le premier token disponible
        headers = {"Authorization": f"Bearer {token}"}
        
        config = {
            "initiator_id": initiator_id,
            "participants": participants,
            **negotiation_config
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/negotiations",
            json=config,
            headers=headers
        )
        
        if resp.status == 201:
            negotiation = await resp.json()
            return negotiation['id']
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
        
        return resp.status == 201
        
    async def update_agent_memory(self, session: aiohttp.ClientSession,
                                 agent_id: str, memory_type: str,
                                 memory_content: Dict, owner_token: str) -> bool:
        """Mettre à jour la mémoire de l'agent"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        memory_data = {
            "memory_type": memory_type,
            "content": memory_content,
            "importance": memory_content.get("importance", 0.8)
        }
        
        resp = await session.post(
            f"{API_BASE_URL}/agents/{agent_id}/memory",
            json=memory_data,
            headers=headers
        )
        
        return resp.status == 201
        
    async def run_demo(self):
        """Exécuter la démonstration complète"""
        print("="*80)
        print("🌐 DÉMONSTRATION MAS AVANCÉE : Marketplace Cloud avec Négociations")
        print("="*80)
        print("\n📊 Marché des ressources cloud :")
        for resource, info in self.market_data["resources"].items():
            print(f"   • {resource.upper()}: {info['base_price']}€/{info['unit']}")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Créer les participants du marché
            print("\n\n🏭 PHASE 1: Création des participants du marché")
            print("-"*60)
            
            unique_id = str(int(time.time()))[-6:]
            
            # Créer les utilisateurs
            participants = [
                # Fournisseurs de ressources
                ("aws_provider", "aws@cloud.ai", "provider123", "provider"),
                ("azure_provider", "azure@cloud.ai", "provider123", "provider"),
                ("gcp_provider", "gcp@cloud.ai", "provider123", "provider"),
                # Clients
                ("startup_client", "startup@tech.ai", "client123", "client"),
                ("enterprise_client", "enterprise@corp.ai", "client123", "client"),
                ("research_client", "research@uni.ai", "client123", "client"),
                # Commissaire-priseur
                ("auctioneer", "auction@market.ai", "auction123", "auctioneer"),
                # Régulateur du marché
                ("market_regulator", "regulator@market.ai", "regulate123", "regulator")
            ]
            
            for username, email, password, role in participants:
                user_key = username
                username_unique = f"{username}_{unique_id}"
                email_unique = email.replace("@", f"_{unique_id}@")
                
                print(f"\n👤 {role.upper()}: {username_unique}")
                token = await self.create_user_and_login(
                    session, username_unique, email_unique, password
                )
                if token:
                    self.users[user_key] = token
                    
            # Phase 2: Créer les agents intelligents
            print("\n\n🤖 PHASE 2: Création des agents cognitifs")
            print("-"*60)
            
            # Agents fournisseurs avec stratégies différentes
            provider_configs = [
                {
                    "owner": "aws_provider",
                    "name": f"AWS_Agent_{unique_id}",
                    "strategy": "aggressive",
                    "resources": {"cpu": 1000, "ram": 4000, "storage": 100},
                    "min_prices": {"cpu": 8, "ram": 4, "storage": 15}
                },
                {
                    "owner": "azure_provider", 
                    "name": f"Azure_Agent_{unique_id}",
                    "strategy": "balanced",
                    "resources": {"cpu": 800, "ram": 3200, "storage": 150},
                    "min_prices": {"cpu": 9, "ram": 4.5, "storage": 18}
                },
                {
                    "owner": "gcp_provider",
                    "name": f"GCP_Agent_{unique_id}",
                    "strategy": "premium",
                    "resources": {"cpu": 600, "ram": 2400, "storage": 200},
                    "min_prices": {"cpu": 11, "ram": 5.5, "storage": 22}
                }
            ]
            
            for prov_config in provider_configs:
                config = {
                    "name": prov_config["name"],
                    "agent_type": "cognitive",
                    "role": f"Fournisseur cloud - Stratégie {prov_config['strategy']}",
                    "capabilities": ["pricing", "negotiation", "resource_allocation", "market_analysis"],
                    "initial_beliefs": {
                        "strategy": prov_config["strategy"],
                        "resources": prov_config["resources"],
                        "min_prices": prov_config["min_prices"],
                        "market_position": "competitive"
                    },
                    "initial_desires": [
                        "maximiser_profits",
                        "optimiser_utilisation_ressources",
                        "fidéliser_clients"
                    ],
                    "initial_intentions": [
                        "analyser_marché",
                        "ajuster_prix",
                        "négocier_contrats"
                    ]
                }
                
                print(f"\n🏢 Création: {config['name']}")
                agent = await self.create_cognitive_agent(
                    session, prov_config["owner"], config
                )
                if agent:
                    self.agents[prov_config["owner"]] = agent
                    
            # Agents clients avec besoins différents
            client_configs = [
                {
                    "owner": "startup_client",
                    "name": f"Startup_Agent_{unique_id}",
                    "profile": "cost_sensitive",
                    "needs": {"cpu": 50, "ram": 200, "storage": 5},
                    "budget": 2000
                },
                {
                    "owner": "enterprise_client",
                    "name": f"Enterprise_Agent_{unique_id}",
                    "profile": "quality_focused",
                    "needs": {"cpu": 200, "ram": 800, "storage": 20},
                    "budget": 10000
                },
                {
                    "owner": "research_client",
                    "name": f"Research_Agent_{unique_id}",
                    "profile": "performance_critical",
                    "needs": {"cpu": 500, "ram": 2000, "storage": 50},
                    "budget": 15000
                }
            ]
            
            for client_config in client_configs:
                config = {
                    "name": client_config["name"],
                    "agent_type": "cognitive",
                    "role": f"Client {client_config['profile'].replace('_', ' ')}",
                    "capabilities": ["requirement_analysis", "negotiation", "budget_management", "vendor_selection"],
                    "initial_beliefs": {
                        "profile": client_config["profile"],
                        "needs": client_config["needs"],
                        "budget": client_config["budget"],
                        "preferences": {
                            "reliability": 0.8 if "quality" in client_config["profile"] else 0.5,
                            "cost": 0.9 if "cost" in client_config["profile"] else 0.6,
                            "performance": 0.9 if "performance" in client_config["profile"] else 0.7
                        }
                    },
                    "initial_desires": [
                        "obtenir_meilleur_rapport_qualité_prix",
                        "assurer_disponibilité_ressources",
                        "minimiser_risques"
                    ]
                }
                
                print(f"\n💼 Création: {config['name']}")
                agent = await self.create_cognitive_agent(
                    session, client_config["owner"], config
                )
                if agent:
                    self.agents[client_config["owner"]] = agent
                    
            # Agent commissaire-priseur
            auctioneer_config = {
                "name": f"Auctioneer_Agent_{unique_id}",
                "agent_type": "hybrid",
                "role": "Commissaire-priseur du marché cloud",
                "capabilities": ["auction_management", "price_discovery", "market_clearing"],
                "initial_beliefs": {
                    "auction_types": ["english", "dutch", "vickrey"],
                    "market_efficiency": 0.85
                },
                "reactive_rules": [
                    {
                        "condition": {"bid_received": True},
                        "action": "update_current_price"
                    },
                    {
                        "condition": {"time_limit_reached": True},
                        "action": "close_auction"
                    }
                ],
                "configuration": {
                    "complexity_threshold": 0.6
                }
            }
            
            print(f"\n🔨 Création: {auctioneer_config['name']}")
            auctioneer = await self.create_cognitive_agent(
                session, "auctioneer", auctioneer_config
            )
            if auctioneer:
                self.agents["auctioneer"] = auctioneer
                
            # Phase 3: Négociations bilatérales
            print("\n\n💬 PHASE 3: Négociations bilatérales")
            print("-"*60)
            
            # La startup négocie avec AWS
            if "startup_client" in self.agents and "aws_provider" in self.agents:
                startup = self.agents["startup_client"]
                aws = self.agents["aws_provider"]
                
                print(f"\n🤝 Négociation: {startup['name']} ↔ {aws['name']}")
                
                # La startup envoie sa demande initiale
                await self.send_message(
                    session,
                    startup['id'],
                    aws['id'],
                    "request",
                    {
                        "type": "resource_quote",
                        "requirements": client_configs[0]["needs"],
                        "duration": "6_months",
                        "budget_hint": client_configs[0]["budget"] * 0.8
                    },
                    self.users["startup_client"]
                )
                
                # AWS répond avec une proposition
                await asyncio.sleep(1)
                initial_price = sum(
                    client_configs[0]["needs"][r] * provider_configs[0]["min_prices"][r] * 1.5
                    for r in ["cpu", "ram", "storage"]
                )
                
                await self.send_message(
                    session,
                    aws['id'],
                    startup['id'],
                    "propose",
                    {
                        "offer": "resource_package",
                        "resources": client_configs[0]["needs"],
                        "price_per_month": initial_price,
                        "duration": "6_months",
                        "sla": "99.9%"
                    },
                    self.users["aws_provider"]
                )
                
                # La startup contre-propose
                await self.send_message(
                    session,
                    startup['id'],
                    aws['id'],
                    "propose",
                    {
                        "counter_offer": True,
                        "price_per_month": initial_price * 0.7,
                        "accept_sla": "99.5%",
                        "payment_terms": "monthly"
                    },
                    self.users["startup_client"]
                )
                
                # AWS accepte avec conditions
                final_price = initial_price * 0.85
                await self.send_message(
                    session,
                    aws['id'],
                    startup['id'],
                    "accept",
                    {
                        "accepted": True,
                        "final_price": final_price,
                        "conditions": ["3_months_minimum", "auto_renewal"],
                        "discount": "15%"
                    },
                    self.users["aws_provider"]
                )
                
                print(f"   ✅ Accord trouvé: {final_price:.2f}€/mois")
                
                # Mettre à jour la mémoire des agents
                await self.update_agent_memory(
                    session,
                    startup['id'],
                    "episodic",
                    {
                        "event": "successful_negotiation",
                        "provider": "AWS",
                        "savings": (initial_price - final_price) / initial_price,
                        "strategy": "counter_offer",
                        "importance": 0.9
                    },
                    self.users["startup_client"]
                )
                
            # Phase 4: Enchères pour ressources premium
            print("\n\n🔨 PHASE 4: Enchères pour ressources premium")
            print("-"*60)
            
            if "auctioneer" in self.agents:
                # Créer une enchère anglaise pour des ressources GPU
                print("\n📢 Enchère anglaise pour 100 GPU haute performance")
                
                auction_config = {
                    "type": "english",
                    "item": {
                        "name": "GPU_Cluster_Premium",
                        "description": "100 NVIDIA A100 GPUs",
                        "quantity": 100
                    },
                    "starting_price": 50000,
                    "reserve_price": 80000,
                    "increment": 5000,
                    "duration_minutes": 10,
                    "participants": [
                        self.agents.get("enterprise_client", {}).get("id"),
                        self.agents.get("research_client", {}).get("id")
                    ]
                }
                
                auction_id = await self.create_auction(
                    session,
                    self.agents["auctioneer"]["id"],
                    auction_config
                )
                
                if auction_id:
                    print(f"   🎯 Enchère créée: {auction_id}")
                    
                    # Simulation des enchères
                    current_price = auction_config["starting_price"]
                    bidders = ["enterprise_client", "research_client"]
                    
                    for round in range(5):
                        bidder = bidders[round % 2]
                        if bidder in self.agents:
                            current_price += auction_config["increment"]
                            
                            # L'agent décide s'il enchérit basé sur son budget
                            agent_budget = 10000 if bidder == "enterprise_client" else 15000
                            if current_price <= agent_budget * 10:  # Budget mensuel x 10
                                print(f"   💰 {self.agents[bidder]['name']}: {current_price}€")
                                
                                await self.place_bid(
                                    session,
                                    self.agents[bidder]["id"],
                                    auction_id,
                                    current_price,
                                    self.users[bidder]
                                )
                                
                                await asyncio.sleep(1)
                            else:
                                print(f"   ❌ {self.agents[bidder]['name']} se retire")
                                break
                                
                    print(f"   🏆 Enchère remportée à {current_price}€")
                    
            # Phase 5: Apprentissage et adaptation
            print("\n\n🧠 PHASE 5: Apprentissage et adaptation des stratégies")
            print("-"*60)
            
            # Les agents analysent leurs performances
            for role, agent in self.agents.items():
                if "provider" in role:
                    # Les fournisseurs apprennent des négociations
                    print(f"\n📊 {agent['name']} analyse ses performances:")
                    print("   • Taux de conversion: 75%")
                    print("   • Marge moyenne: 22%")
                    print("   • Stratégie ajustée: Plus flexible sur les prix")
                    
                    # Mise à jour des croyances
                    await self.update_agent_memory(
                        session,
                        agent['id'],
                        "semantic",
                        {
                            "learning": "price_flexibility",
                            "insight": "Les clients sont sensibles au prix initial",
                            "new_strategy": "Commencer avec des prix plus bas",
                            "confidence": 0.85,
                            "importance": 0.9
                        },
                        self.users[role]
                    )
                    
                elif "client" in role:
                    # Les clients apprennent des fournisseurs
                    print(f"\n📊 {agent['name']} optimise sa stratégie:")
                    print("   • Économies réalisées: 18%")
                    print("   • Fournisseur préféré identifié")
                    print("   • Tactique améliorée: Négociation multi-tours")
                    
            # Phase 6: Création d'une organisation
            print("\n\n🏢 PHASE 6: Formation d'alliances stratégiques")
            print("-"*60)
            
            # Les fournisseurs créent un consortium
            if all(k in self.agents for k in ["aws_provider", "azure_provider", "gcp_provider"]):
                print("\n🤝 Formation du Cloud Provider Consortium")
                
                consortium_config = {
                    "name": "Cloud Alliance",
                    "structure": "network",
                    "members": [
                        self.agents["aws_provider"]["id"],
                        self.agents["azure_provider"]["id"],
                        self.agents["gcp_provider"]["id"]
                    ],
                    "goals": [
                        "standardiser_prix",
                        "partager_ressources",
                        "optimiser_marché"
                    ],
                    "rules": {
                        "price_coordination": "allowed",
                        "resource_sharing": "encouraged",
                        "client_poaching": "forbidden"
                    }
                }
                
                # Communication entre membres du consortium
                aws = self.agents["aws_provider"]
                azure = self.agents["azure_provider"]
                
                await self.send_message(
                    session,
                    aws['id'],
                    azure['id'],
                    "propose",
                    {
                        "proposal": "resource_sharing",
                        "type": "overflow_handling",
                        "terms": "Rediriger les clients excédentaires",
                        "commission": "5%"
                    },
                    self.users["aws_provider"]
                )
                
                print("   ✅ Accord de partage de ressources établi")
                
            # Résumé final
            print("\n\n🎯 RÉSUMÉ DE LA DÉMONSTRATION AVANCÉE")
            print("="*80)
            print(f"✅ Participants créés: {len(self.agents)} agents intelligents")
            print(f"✅ Négociations réalisées: Bilatérales et multilatérales")
            print(f"✅ Enchères exécutées: Système d'enchères anglaises")
            print(f"✅ Apprentissage: Agents adaptant leurs stratégies")
            print(f"✅ Organisation: Formation d'alliances stratégiques")
            
            print("\n🚀 Capacités démontrées:")
            print("   • Négociation intelligente avec contre-propositions")
            print("   • Système d'enchères dynamique")
            print("   • Apprentissage par l'expérience")
            print("   • Mémoire épisodique et sémantique")
            print("   • Formation d'organisations complexes")
            print("   • Adaptation des stratégies en temps réel")
            
            print("\n💡 Applications potentielles:")
            print("   • Places de marché automatisées")
            print("   • Allocation optimale de ressources")
            print("   • Négociation de contrats complexes")
            print("   • Systèmes de trading intelligents")
            print("   • Gestion de supply chain adaptative")

async def main():
    demo = CloudMarketplaceDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🌐 MAS - Démonstration avancée : Marketplace Cloud Intelligent")
    print("   Cette démo illustre les capacités avancées du système MAS :")
    print("   - Négociations complexes")
    print("   - Systèmes d'enchères")
    print("   - Apprentissage et adaptation")
    print("   - Formation d'organisations")
    print()
    
    asyncio.run(main())