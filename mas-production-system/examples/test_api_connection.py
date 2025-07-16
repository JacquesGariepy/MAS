#!/usr/bin/env python3
"""
Test de connexion et diagnostique de l'API MAS
"""

import requests
import json
import time

API_URL = "http://localhost:8088"

def test_api_connection():
    """Test complet de l'API"""
    print("🧪 TEST DE CONNEXION API MAS")
    print("="*50)
    
    # 1. Test de base
    print("\n1️⃣ Test de connexion de base")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        print(f"   GET /docs: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API accessible!")
        else:
            print("   ❌ API répond mais avec erreur")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API")
        print("   Vérifiez que le serveur est démarré avec: docker-compose up")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {type(e).__name__}: {e}")
        return False
    
    # 2. Test des endpoints disponibles
    print("\n2️⃣ Test des endpoints")
    endpoints = [
        ("/", "GET"),
        ("/docs", "GET"),
        ("/openapi.json", "GET"),
        ("/auth/register", "OPTIONS"),
        ("/auth/token", "OPTIONS"),
        ("/api/v1/agents", "OPTIONS"),
    ]
    
    for endpoint, method in endpoints:
        try:
            url = f"{API_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=2)
            else:
                response = requests.options(url, timeout=2)
            print(f"   {method} {endpoint}: {response.status_code}")
        except:
            print(f"   {method} {endpoint}: ❌ Erreur")
    
    # 3. Test du schéma OpenAPI
    print("\n3️⃣ Analyse du schéma OpenAPI")
    try:
        response = requests.get(f"{API_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            print(f"   Titre: {openapi.get('info', {}).get('title', 'N/A')}")
            print(f"   Version: {openapi.get('info', {}).get('version', 'N/A')}")
            
            # Lister les paths
            print("\n   Endpoints disponibles:")
            for path, methods in openapi.get('paths', {}).items():
                for method in methods:
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        print(f"      {method.upper()} {path}")
    except:
        print("   ❌ Impossible de récupérer le schéma OpenAPI")
    
    return True

def test_user_creation_simple():
    """Test simple de création d'utilisateur"""
    print("\n\n4️⃣ Test de création d'utilisateur")
    
    username = f"test_{int(time.time())}"
    user_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "password123"
    }
    
    print(f"   Données: {json.dumps(user_data, indent=2)}")
    
    # Enregistrement
    print("\n   📍 Enregistrement")
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 201:
            print("   ✅ Utilisateur créé!")
        elif response.status_code == 400:
            print("   ⚠️ Utilisateur déjà existant")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None
    
    # Connexion
    print("\n   📍 Connexion")
    try:
        # Note: OAuth2PasswordRequestForm attend des form data
        response = requests.post(
            f"{API_URL}/auth/token",
            data={  # data, pas json!
                "username": username,
                "password": "password123"
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("   ✅ Connexion réussie!")
            print(f"   Token: {token_data.get('access_token', '')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"   ❌ Erreur: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return None

def test_with_token(token):
    """Test avec authentification"""
    print("\n\n5️⃣ Test avec authentification")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /auth/me
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers=headers,
            timeout=5
        )
        print(f"   GET /auth/me: {response.status_code}")
        if response.status_code == 200:
            user_info = response.json()
            print(f"   User: {user_info}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test agents
    try:
        response = requests.get(
            f"{API_URL}/api/v1/agents",
            headers=headers,
            timeout=5
        )
        print(f"   GET /api/v1/agents: {response.status_code}")
        if response.status_code == 200:
            agents = response.json()
            print(f"   Nombre d'agents: {len(agents)}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def main():
    """Tests principaux"""
    print("🔍 DIAGNOSTIC COMPLET DE L'API MAS")
    print("="*70)
    
    # Test de connexion
    if not test_api_connection():
        print("\n❌ L'API n'est pas accessible. Arrêt des tests.")
        return
    
    # Test de création d'utilisateur
    token = test_user_creation_simple()
    
    # Tests avec token si succès
    if token:
        test_with_token(token)
    
    print("\n\n✅ Tests terminés!")
    print("\n💡 Conseils:")
    print("   - Si l'API n'est pas accessible, vérifiez docker-compose")
    print("   - Si l'enregistrement échoue, vérifiez les logs du serveur")
    print("   - Si la connexion échoue, vérifiez le format des données")

if __name__ == "__main__":
    main()