#!/usr/bin/env python3
"""
Test simple de création d'utilisateur
Pour identifier le problème exact
"""

import requests
import json
import time

API_URL = "http://localhost:8088"

def test_user_creation():
    """Test complet de création d'utilisateur"""
    print("🧪 TEST DE CRÉATION D'UTILISATEUR")
    print("="*50)
    
    # Données de test
    username = f"test_{int(time.time())}"
    email = f"{username}@test.com"
    password = "password123"
    
    print(f"\n📝 Données de test:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    # 1. Test de l'endpoint d'enregistrement
    print("\n1️⃣ Test d'enregistrement (/auth/register)")
    print("   URL:", f"{API_URL}/auth/register")
    print("   Méthode: POST")
    print("   Body:", json.dumps({"username": username, "email": email, "password": password}, indent=2))
    
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"username": username, "email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n   ➡️ Réponse:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body: {response.text}")
        
        # Analyser la réponse
        if response.status_code == 201:
            print("   ✅ Enregistrement réussi!")
        elif response.status_code == 400:
            print("   ⚠️ Erreur 400 - Utilisateur peut-être déjà existant")
        elif response.status_code == 422:
            print("   ❌ Erreur 422 - Validation échouée")
            try:
                error_detail = response.json()
                print("   Détails:", json.dumps(error_detail, indent=2))
            except:
                pass
        else:
            print(f"   ❌ Code inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {type(e).__name__}: {e}")
        return
    
    # 2. Test de connexion
    print("\n2️⃣ Test de connexion (/auth/token)")
    print("   URL:", f"{API_URL}/auth/token")
    print("   Méthode: POST")
    print("   Content-Type: application/x-www-form-urlencoded")
    
    try:
        # Note: /auth/token utilise form data, pas JSON
        response = requests.post(
            f"{API_URL}/auth/token",
            data={
                "username": username,
                "password": password
            }
        )
        
        print(f"\n   ➡️ Réponse:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body: {response.text[:500]}...")  # Limiter la sortie
        
        if response.status_code == 200:
            print("   ✅ Connexion réussie!")
            try:
                data = response.json()
                if "access_token" in data:
                    print(f"   Token: {data['access_token'][:50]}...")
                    return data["access_token"]
            except:
                pass
        elif response.status_code == 401:
            print("   ❌ Erreur 401 - Authentification échouée")
        else:
            print(f"   ❌ Code inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {type(e).__name__}: {e}")
    
    return None

def test_with_token(token):
    """Test avec le token obtenu"""
    print("\n3️⃣ Test avec token")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test de récupération d'agents
    try:
        response = requests.get(
            f"{API_URL}/api/v1/agents",
            headers=headers
        )
        
        print(f"   GET /api/v1/agents: {response.status_code}")
        if response.status_code == 200:
            agents = response.json()
            print(f"   Nombre d'agents: {len(agents)}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_alternate_endpoints():
    """Test d'endpoints alternatifs"""
    print("\n4️⃣ Test d'endpoints alternatifs")
    
    # Essayer différentes variantes
    endpoints = [
        "/api/v1/auth/register",
        "/api/auth/register",
        "/register",
        "/api/v1/users",
        "/users/register"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{API_URL}{endpoint}"
            response = requests.options(url)
            print(f"   OPTIONS {endpoint}: {response.status_code}")
        except:
            print(f"   OPTIONS {endpoint}: ❌ Erreur de connexion")

if __name__ == "__main__":
    # Test principal
    token = test_user_creation()
    
    if token:
        test_with_token(token)
    
    # Tests supplémentaires
    test_alternate_endpoints()
    
    print("\n✅ Tests terminés!")