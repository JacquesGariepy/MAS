#!/usr/bin/env python3
"""
Script de débogage pour vérifier l'état de l'API
"""

import httpx
import os
import asyncio

# Configuration adaptative
if os.path.exists('/.dockerenv'):
    API_BASE_URL = "http://core:8000"
else:
    API_BASE_URL = "http://localhost:8088"


async def debug_api():
    """Vérifier l'état de l'API et les routes disponibles"""
    async with httpx.AsyncClient() as client:
        print("🔍 Débogage de l'API MAS")
        print("=" * 50)
        print(f"URL de base: {API_BASE_URL}")
        print()
        
        # 1. Test de base - accès à la racine
        print("1️⃣ Test de la racine /")
        try:
            response = await client.get(f"{API_BASE_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Contenu: {response.json()}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 2. Test de /docs
        print("\n2️⃣ Test de /docs")
        try:
            response = await client.get(f"{API_BASE_URL}/docs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Documentation API accessible")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 3. Test de /api/v1
        print("\n3️⃣ Test de /api/v1")
        try:
            response = await client.get(f"{API_BASE_URL}/api/v1")
            print(f"   Status: {response.status_code}")
            if response.status_code != 404:
                print(f"   Contenu: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 4. Test de l'endpoint d'authentification
        print("\n4️⃣ Test de /api/v1/auth/register")
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/auth/register",
                json={
                    "username": "test_debug",
                    "email": "debug@test.com",
                    "password": "debug12345"
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code != 404:
                print(f"   Réponse: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 5. Test de /auth/register (sans /api/v1)
        print("\n5️⃣ Test de /auth/register (sans préfixe api/v1)")
        try:
            response = await client.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    "username": "test_debug2",
                    "email": "debug2@test.com",
                    "password": "debug12345"
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code != 404:
                print(f"   Réponse: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 6. Lister toutes les routes disponibles via OpenAPI
        print("\n6️⃣ Récupération du schéma OpenAPI")
        try:
            response = await client.get(f"{API_BASE_URL}/openapi.json")
            if response.status_code == 200:
                openapi = response.json()
                print("   ✅ Schéma OpenAPI récupéré")
                print("\n   📋 Routes disponibles:")
                if "paths" in openapi:
                    for path, methods in openapi["paths"].items():
                        for method in methods:
                            print(f"      {method.upper()} {path}")
                else:
                    print("   ⚠️ Pas de routes dans le schéma")
            else:
                print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Débogage terminé")
        print("\n💡 Si les routes /api/v1/* renvoient 404, vérifiez :")
        print("   1. Que le routeur est bien monté dans main.py")
        print("   2. Que les migrations ont été exécutées")
        print("   3. Les logs du serveur : docker-compose -f docker-compose.dev.yml logs core")


if __name__ == "__main__":
    asyncio.run(debug_api())