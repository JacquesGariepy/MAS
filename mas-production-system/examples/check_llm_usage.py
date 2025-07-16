#!/usr/bin/env python3
"""
Script pour vérifier l'utilisation du LLM par les agents cognitifs.
Envoie des requêtes complexes nécessitant une réponse générée par le LLM.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


async def check_llm_integration():
    """Vérifier que le LLM est correctement intégré"""
    print("="*60)
    print("🧠 VÉRIFICATION DE L'INTÉGRATION LLM")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 1. Créer un utilisateur de test
        print("\n📋 Création d'un utilisateur de test...")
        
        timestamp = int(time.time())
        username = f"llm_test_{timestamp}"
        email = f"{username}@mas.ai"
        password = "password123"
        
        # Register
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
            print(f"❌ Erreur création utilisateur: {await register_resp.text()}")
            return
        
        # Login
        login_data = {"username": username, "password": password}
        login_resp = await session.post(
            f"{API_BASE_URL.replace('/api/v1', '')}/auth/token",
            data=login_data
        )
        
        if login_resp.status != 200:
            print(f"❌ Erreur connexion: {login_resp.status}")
            return
        
        token = (await login_resp.json())["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Utilisateur {username} créé et connecté")
        
        # 2. Créer un agent cognitif
        print("\n📋 Création d'un agent cognitif...")
        
        agent_config = {
            "name": "LLM Test Agent",
            "agent_type": "cognitive",
            "role": "Agent de test pour vérifier l'utilisation du LLM",
            "capabilities": ["analyse", "génération", "raisonnement"],
            "initial_beliefs": {
                "purpose": "test_llm",
                "llm_model": "qwen3-8b"
            },
            "initial_desires": ["répondre", "analyser", "générer"],
            "configuration": {
                "llm_enabled": True,
                "max_tokens": 500,
                "temperature": 0.7
            }
        }
        
        create_resp = await session.post(
            f"{API_BASE_URL}/agents",
            json=agent_config,
            headers=headers
        )
        
        if create_resp.status != 201:
            print(f"❌ Erreur création agent: {await create_resp.text()}")
            return
        
        agent = await create_resp.json()
        agent_id = agent["id"]
        print(f"✅ Agent cognitif créé: {agent['name']} (ID: {agent_id[:8]}...)")
        
        # 3. Démarrer l'agent
        print("\n📋 Démarrage de l'agent...")
        
        start_resp = await session.post(
            f"{API_BASE_URL}/agents/{agent_id}/start",
            headers=headers
        )
        
        if start_resp.status == 200:
            print("✅ Agent démarré avec succès")
        elif start_resp.status == 400:
            error = await start_resp.json()
            if "already" in error.get("detail", "").lower():
                print("✅ Agent déjà actif")
            else:
                print(f"❌ Erreur démarrage: {error.get('detail')}")
                return
        else:
            print(f"❌ Erreur HTTP {start_resp.status}")
            return
        
        # Attendre l'initialisation
        await asyncio.sleep(2)
        
        # 4. Envoyer des requêtes nécessitant le LLM
        print("\n📋 Test de requêtes LLM...")
        
        test_queries = [
            {
                "performative": "query-ref",
                "content": {
                    "query": "Explique les avantages et inconvénients de l'architecture microservices",
                    "context": "Nous développons une nouvelle application web"
                }
            },
            {
                "performative": "request",
                "content": {
                    "action": "analyze",
                    "data": "Les ventes ont augmenté de 15% ce trimestre mais les coûts ont augmenté de 20%",
                    "request": "Quelle est ton analyse de cette situation?"
                }
            },
            {
                "performative": "query-if",
                "content": {
                    "proposition": "Python est-il le meilleur langage pour le machine learning?",
                    "context": "Comparaison avec R, Julia et Scala"
                }
            }
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query['content'].get('query', query['content'].get('action', 'requête'))[:50]}...")
            
            # L'agent s'envoie le message à lui-même pour simplifier le test
            message_data = {
                "receiver_id": agent_id,
                "performative": query["performative"],
                "content": query["content"]
            }
            
            send_resp = await session.post(
                f"{API_BASE_URL}/agents/{agent_id}/messages",
                json=message_data,
                headers=headers
            )
            
            if send_resp.status == 201:
                print("   ✅ Requête envoyée")
            else:
                print(f"   ❌ Échec envoi: {await send_resp.text()}")
        
        # 5. Attendre le traitement
        print("\n⏳ Attente du traitement par le LLM (10 secondes)...")
        await asyncio.sleep(10)
        
        # 6. Récupérer et analyser les messages
        print("\n📋 Analyse des réponses...")
        
        messages_resp = await session.get(
            f"{API_BASE_URL}/agents/{agent_id}/messages",
            headers=headers
        )
        
        if messages_resp.status != 200:
            print(f"❌ Erreur récupération messages: {messages_resp.status}")
            return
        
        messages = (await messages_resp.json()).get("items", [])
        
        # Analyser les messages
        received_messages = [m for m in messages if m["receiver_id"] == agent_id]
        sent_messages = [m for m in messages if m["sender_id"] == agent_id and m["receiver_id"] != agent_id]
        
        print(f"\n📊 Statistiques:")
        print(f"   📥 Messages reçus: {len(received_messages)}")
        print(f"   📤 Réponses envoyées: {len(sent_messages)}")
        
        # Chercher des réponses générées par le LLM
        llm_responses = []
        
        for msg in messages:
            content = msg.get("content", {})
            if isinstance(content, dict):
                # Chercher des signes de génération LLM
                content_str = json.dumps(content)
                if any(indicator in content_str.lower() for indicator in [
                    "avantage", "inconvénient", "analyse", "microservice",
                    "python", "machine learning", "augment", "coût"
                ]):
                    if len(content_str) > 100:  # Réponse substantielle
                        llm_responses.append(msg)
        
        print(f"   🧠 Réponses LLM détectées: {len(llm_responses)}")
        
        # Afficher les réponses LLM
        if llm_responses:
            print("\n✅ SUCCÈS: Le LLM est utilisé!")
            print("\n📝 Exemples de réponses générées par le LLM:")
            
            for i, response in enumerate(llm_responses[:2], 1):
                print(f"\n   Réponse {i}:")
                print(f"   Type: {response['performative']}")
                content = response['content']
                if isinstance(content, dict):
                    for key, value in content.items():
                        print(f"   {key}: {str(value)[:200]}...")
                else:
                    print(f"   Contenu: {str(content)[:200]}...")
        else:
            print("\n⚠️  ATTENTION: Aucune réponse LLM détectée!")
            print("\n🔍 Diagnostic:")
            print("   1. Vérifiez que LMStudio est démarré")
            print("   2. Vérifiez que le modèle qwen3-8b est chargé")
            print("   3. Vérifiez l'URL: http://host.docker.internal:1234/v1")
            print("   4. Consultez les logs Docker: docker-compose logs core | grep -i llm")
        
        # 7. Vérifier la configuration
        print("\n📋 Configuration LLM attendue:")
        print("   Provider: lmstudio")
        print("   Model: qwen3-8b")
        print("   Base URL: http://host.docker.internal:1234/v1")
        print("   Dans Docker: host.docker.internal pointe vers l'hôte")
        
        # 8. Test de connectivité directe (optionnel)
        print("\n📋 Test de connectivité LMStudio...")
        try:
            # Tester depuis l'extérieur du conteneur
            test_url = "http://localhost:1234/v1/models"
            async with session.get(test_url, timeout=5) as resp:
                if resp.status == 200:
                    models = await resp.json()
                    print(f"   ✅ LMStudio accessible depuis l'hôte")
                    print(f"   📌 Modèles disponibles: {models}")
                else:
                    print(f"   ❌ LMStudio retourne le code {resp.status}")
        except Exception as e:
            print(f"   ❌ Impossible de contacter LMStudio: {type(e).__name__}")
            print("   ℹ️  C'est normal si le test s'exécute dans Docker")


async def main():
    """Point d'entrée principal"""
    print("🧠 Test d'intégration LLM dans MAS")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    await check_llm_integration()
    
    print("\n" + "="*60)
    print("✨ Test terminé")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())