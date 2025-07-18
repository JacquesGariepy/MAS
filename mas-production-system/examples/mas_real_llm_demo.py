#!/usr/bin/env python3
"""
Démonstration réelle du système MAS avec communication LLM entre agents
"""

import asyncio
import aiohttp
import json
import time
import os

API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"


async def main():
    print("="*80)
    print("🤖 DÉMONSTRATION RÉELLE MAS - COMMUNICATION LLM")
    print("="*80)
    print("\n📢 Cette démo va créer 3 agents qui communiquent vraiment via LMStudio:")
    print("   1. Un Chef de Projet (cognitif)")
    print("   2. Un Développeur (cognitif)")  
    print("   3. Un Testeur (hybride)")
    print("\n⚠️  SURVEILLEZ LMSTUDIO POUR VOIR LES REQUÊTES EN TEMPS RÉEL!")
    
    async with aiohttp.ClientSession() as session:
        timestamp = int(time.time() * 1000) % 1000000
        
        # 1. Créer 3 utilisateurs
        print("\n📋 Phase 1: Création des utilisateurs...")
        users = {}
        for name in ["alice", "bob", "charlie"]:
            user_data = {
                "username": f"{name}_{timestamp}",
                "email": f"{name}_{timestamp}@mas.ai",
                "password": "password123"
            }
            
            # Register
            async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                if resp.status in [200, 201]:
                    print(f"✅ {name} créé")
                    
            # Login
            login_form = aiohttp.FormData()
            login_form.add_field('username', user_data["username"])
            login_form.add_field('password', user_data["password"])
            
            async with session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
                if resp.status == 200:
                    auth_resp = await resp.json()
                    users[name] = {
                        "username": user_data["username"],
                        "token": auth_resp["access_token"],
                        "headers": {"Authorization": f"Bearer {auth_resp['access_token']}"}
                    }
                    
        # 2. Créer les agents
        print("\n📋 Phase 2: Création des agents intelligents...")
        
        agents = {}
        
        # Chef de Projet (Alice) - Agent Cognitif
        chef_data = {
            "name": f"ChefProjet_{timestamp}",
            "agent_type": "reactive",  # Type cognitif dans le système
            "role": "project_manager",
            "capabilities": ["planning", "coordination", "decision_making"],
            "description": "Chef de projet IA qui coordonne le développement",
            "initial_beliefs": {
                "project": "Développer une application web",
                "deadline": "2 semaines",
                "team_size": 3
            },
            "initial_desires": ["planifier", "coordonner", "livrer_projet"]
        }
        
        async with session.post(
            f"{API_V1}/agents", 
            json=chef_data,
            headers=users["alice"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                agents["chef"] = {
                    "id": agent_resp["id"],
                    "name": chef_data["name"],
                    "owner": "alice"
                }
                print(f"✅ Chef de Projet créé (cognitif)")
                
        # Développeur (Bob) - Agent Cognitif
        dev_data = {
            "name": f"Developpeur_{timestamp}",
            "agent_type": "reactive",  # Type cognitif
            "role": "developer",
            "capabilities": ["coding", "architecture", "problem_solving"],
            "description": "Développeur senior qui implémente les solutions",
            "initial_beliefs": {
                "languages": ["Python", "JavaScript", "SQL"],
                "experience": "5 ans",
                "speciality": "backend"
            },
            "initial_desires": ["coder", "optimiser", "résoudre_problèmes"]
        }
        
        async with session.post(
            f"{API_V1}/agents",
            json=dev_data,
            headers=users["bob"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                agents["dev"] = {
                    "id": agent_resp["id"],
                    "name": dev_data["name"],
                    "owner": "bob"
                }
                print(f"✅ Développeur créé (cognitif)")
                
        # Testeur (Charlie) - Agent Hybride
        testeur_data = {
            "name": f"Testeur_{timestamp}",
            "agent_type": "hybrid",
            "role": "qa_engineer", 
            "capabilities": ["testing", "validation", "reporting"],
            "description": "Testeur QA qui valide le code et trouve les bugs",
            "reactive_rules": {
                "bug_found": "Reporter immédiatement au développeur",
                "test_passed": "Valider et documenter",
                "urgent": "Prioriser les tests critiques"
            },
            "cognitive_threshold": 0.6,
            "initial_beliefs": {
                "test_coverage_target": "80%",
                "automation_level": "high"
            }
        }
        
        async with session.post(
            f"{API_V1}/agents",
            json=testeur_data,
            headers=users["charlie"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                agent_resp = await resp.json()
                agents["testeur"] = {
                    "id": agent_resp["id"],
                    "name": testeur_data["name"],
                    "owner": "charlie"
                }
                print(f"✅ Testeur créé (hybride)")
                
        # 3. Démarrer tous les agents
        print("\n📋 Phase 3: Démarrage des agents...")
        for role, agent in agents.items():
            headers = users[agent["owner"]]["headers"]
            async with session.post(
                f"{API_V1}/agents/{agent['id']}/start",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    print(f"✅ {role.capitalize()} démarré")
                    
        # Attendre que les agents soient prêts
        await asyncio.sleep(3)
        
        # 4. Scénario de communication réel
        print("\n📋 Phase 4: Communication intelligente entre agents")
        print("="*60)
        
        # Message 1: Chef -> Développeur (Demande de planification)
        print("\n🎯 Scénario 1: Le Chef demande au Développeur de planifier une fonctionnalité")
        message1 = {
            "sender_id": agents["chef"]["id"],
            "receiver_id": agents["dev"]["id"],
            "performative": "request",
            "content": {
                "action": "planifier_fonctionnalité",
                "description": "Nous devons implémenter un système d'authentification avec JWT. Peux-tu analyser les besoins techniques et me proposer une architecture avec une estimation du temps nécessaire?",
                "contraintes": ["Sécurité maximale", "Compatible mobile", "Performance optimale"],
                "deadline": "Cette semaine"
            }
        }
        
        print(f"📤 Chef → Développeur: Demande d'analyse technique")
        print(f"   Message: '{message1['content']['description'][:100]}...'")
        
        async with session.post(
            f"{API_V1}/agents/{agents['chef']['id']}/messages",
            json=message1,
            headers=users["alice"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                print("   ✅ Message envoyé - LMStudio devrait recevoir une requête!")
                
        # Attendre le traitement
        await asyncio.sleep(5)
        
        # Message 2: Développeur -> Testeur (Demande de stratégie de test)
        print("\n🎯 Scénario 2: Le Développeur consulte le Testeur sur la stratégie de test")
        message2 = {
            "sender_id": agents["dev"]["id"],
            "receiver_id": agents["testeur"]["id"],
            "performative": "query",
            "content": {
                "question": "Pour un système d'authentification JWT avec les endpoints /login, /register, /refresh et /logout, quelle serait ta stratégie de test? Quels cas critiques devrions-nous couvrir?",
                "context": {
                    "technologie": "FastAPI + PostgreSQL",
                    "sécurité": "Haute priorité"
                }
            }
        }
        
        print(f"📤 Développeur → Testeur: Consultation sur stratégie de test")
        print(f"   Question: '{message2['content']['question'][:100]}...'")
        
        async with session.post(
            f"{API_V1}/agents/{agents['dev']['id']}/messages",
            json=message2,
            headers=users["bob"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                print("   ✅ Message envoyé - Nouveau traitement LLM en cours!")
                
        # Attendre
        await asyncio.sleep(5)
        
        # Message 3: Testeur -> Chef (Rapport de risques)
        print("\n🎯 Scénario 3: Le Testeur informe le Chef des risques identifiés")
        message3 = {
            "sender_id": agents["testeur"]["id"],
            "receiver_id": agents["chef"]["id"],
            "performative": "inform",
            "content": {
                "type": "rapport_risques",
                "risques_identifies": [
                    "Attaques par force brute sur /login",
                    "Token JWT exposés si mal configurés",
                    "Session hijacking possible"
                ],
                "recommandations": "Implémenter rate limiting et monitoring",
                "priorité": "haute"
            }
        }
        
        print(f"📤 Testeur → Chef: Rapport de risques")
        print(f"   Risques: {len(message3['content']['risques_identifies'])} identifiés")
        
        async with session.post(
            f"{API_V1}/agents/{agents['testeur']['id']}/messages",
            json=message3,
            headers=users["charlie"]["headers"]
        ) as resp:
            if resp.status in [200, 201]:
                print("   ✅ Message envoyé")
                
        # 5. Vérifier les messages reçus et les réponses
        print("\n📋 Phase 5: Analyse des communications")
        print("="*60)
        
        await asyncio.sleep(10)  # Laisser le temps aux agents de traiter
        
        for role, agent in agents.items():
            owner = agent["owner"]
            headers = users[owner]["headers"]
            
            print(f"\n📊 Messages de {role.upper()}:")
            
            async with session.get(
                f"{API_V1}/agents/{agent['id']}/messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    
                    received = [m for m in messages if isinstance(m, dict) and m.get('receiver_id') == agent['id']]
                    sent = [m for m in messages if isinstance(m, dict) and m.get('sender_id') == agent['id']]
                    
                    print(f"   📥 Reçus: {len(received)}")
                    print(f"   📤 Envoyés: {len(sent)}")
                    
                    # Afficher les réponses générées par LLM
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get('performative') == 'inform':
                            content = msg.get('content', {})
                            if isinstance(content, dict) and 'response' in content:
                                print(f"\n   🤖 Réponse LLM détectée:")
                                print(f"      {str(content.get('response', ''))[:200]}...")
        
        # 6. Résumé
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
        print("="*80)
        
        print(f"\n✅ Agents créés: {len(agents)}")
        print(f"✅ Messages envoyés nécessitant LLM: 3")
        print(f"\n🧠 Configuration LLM:")
        print(f"   Provider: {os.getenv('LLM_PROVIDER', 'unknown')}")
        print(f"   Model: {os.getenv('LLM_MODEL', 'unknown')}")
        print(f"   Base URL: {os.getenv('LLM_BASE_URL', 'unknown')}")
        
        print("\n⚠️  IMPORTANT: Vérifiez LMStudio pour voir:")
        print("   - Les requêtes de raisonnement du Chef de Projet")
        print("   - Les analyses techniques du Développeur")
        print("   - Les évaluations du Testeur")
        
    print("\n" + "="*80)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())