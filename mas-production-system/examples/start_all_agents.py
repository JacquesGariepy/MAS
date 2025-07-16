#!/usr/bin/env python3
"""
Script rapide pour démarrer tous les agents en une seule commande.
Usage: python start_all_agents.py
"""

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@mas.ai"
ADMIN_PASSWORD = "securepassword123"


async def start_all_agents():
    """Démarrer tous les agents disponibles"""
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        async with session.post(f"{API_BASE_URL}/auth/login", data=login_data) as resp:
            if resp.status != 200:
                print(f"❌ Login échoué: {await resp.text()}")
                return
            token = (await resp.json())["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Lister les agents
        async with session.get(f"{API_BASE_URL}/agents", headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Impossible de lister les agents: {await resp.text()}")
                return
            agents = (await resp.json()).get("items", [])
        
        if not agents:
            print("⚠️  Aucun agent trouvé!")
            return
        
        print(f"🚀 Démarrage de {len(agents)} agents...")
        
        # Démarrer chaque agent
        started = 0
        already_active = 0
        failed = 0
        
        for agent in agents:
            agent_id = agent["id"]
            name = agent["name"]
            status = agent["status"]
            
            if status == "working":
                print(f"✅ {name} - Déjà actif")
                already_active += 1
                continue
            
            try:
                async with session.post(f"{API_BASE_URL}/agents/{agent_id}/start", headers=headers) as resp:
                    if resp.status == 200:
                        print(f"▶️  {name} - Démarré avec succès!")
                        started += 1
                    elif resp.status == 400:
                        error = await resp.json()
                        if "already" in error.get("detail", "").lower():
                            print(f"✅ {name} - Déjà actif")
                            already_active += 1
                        else:
                            print(f"❌ {name} - {error.get('detail', 'Erreur')}")
                            failed += 1
                    else:
                        print(f"❌ {name} - Erreur HTTP {resp.status}")
                        failed += 1
            except Exception as e:
                print(f"❌ {name} - Exception: {str(e)}")
                failed += 1
        
        print(f"\n📊 Résumé:")
        print(f"   ✅ Démarrés: {started}")
        print(f"   ✅ Déjà actifs: {already_active}")
        print(f"   ❌ Échecs: {failed}")
        print(f"   📈 Total actifs: {started + already_active}/{len(agents)}")


if __name__ == "__main__":
    print("🤖 MAS - Démarrage de tous les agents\n")
    asyncio.run(start_all_agents())
    print("\n✨ Terminé!")