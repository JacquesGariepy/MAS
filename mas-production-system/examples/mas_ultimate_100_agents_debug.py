#!/usr/bin/env python3
"""
Version de débogage du script mas_ultimate_100_agents.py
Ajoute des logs détaillés pour identifier le problème de création d'utilisateurs
"""

import requests
import json
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

# Configuration
API_URL = "http://localhost:8088"
TARGET_AGENTS = 100
AGENTS_PER_USER = 10  # Quota par utilisateur

# Statistiques globales
stats = {
    "users_created": 0,
    "agents_created": 0,
    "tasks_created": 0,
    "tasks_completed": 0,
    "messages_sent": 0,
    "memories_stored": 0,
    "negotiations_created": 0,
    "auctions_created": 0,
    "organizations_created": 0,
    "active": True
}

# Lock pour l'affichage thread-safe
print_lock = threading.Lock()

def safe_print(message):
    """Print thread-safe"""
    with print_lock:
        print(message)

class MAS100AgentsDemo:
    def __init__(self):
        self.base_url = API_URL
        self.users = {}
        self.all_agents = []
        self.tasks = {}
        self.organizations = {}
        
    def create_user_batch(self, start_index, count):
        """Crée un batch d'utilisateurs avec débogage détaillé"""
        created_users = []
        
        safe_print(f"\n🔍 DEBUG: Création de batch - Index: {start_index}, Count: {count}")
        
        for i in range(start_index, start_index + count):
            username = f"user_{int(time.time())}_{i}"
            email = f"{username}@mas100.com"
            password = "demo123"
            
            safe_print(f"\n🔍 DEBUG: Tentative de création d'utilisateur {i}")
            safe_print(f"   - Username: {username}")
            safe_print(f"   - Email: {email}")
            
            # Enregistrement
            try:
                safe_print(f"   - Envoi de la requête d'enregistrement...")
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json={"username": username, "email": email, "password": password}
                )
                
                safe_print(f"   - Statut de réponse enregistrement: {response.status_code}")
                safe_print(f"   - Contenu de la réponse: {response.text}")
                
                if response.status_code in [201, 400]:
                    # Connexion
                    safe_print(f"   - Tentative de connexion...")
                    response = requests.post(
                        f"{self.base_url}/auth/token",
                        data={"username": username, "password": password}
                    )
                    
                    safe_print(f"   - Statut de réponse connexion: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        safe_print(f"   - Données de connexion: {list(response_data.keys())}")
                        
                        if "access_token" in response_data:
                            token = response_data["access_token"]
                            self.users[username] = {
                                "token": token,
                                "agents": [],
                                "agent_count": 0
                            }
                            created_users.append(username)
                            stats["users_created"] += 1
                            safe_print(f"   ✅ Utilisateur {username} créé avec succès!")
                        else:
                            safe_print(f"   ❌ Pas de token dans la réponse: {response_data}")
                    else:
                        safe_print(f"   ❌ Échec de connexion: {response.text}")
                else:
                    safe_print(f"   ❌ Échec d'enregistrement avec code: {response.status_code}")
                    safe_print(f"   ❌ Détails: {response.text}")
                    
            except Exception as e:
                safe_print(f"   ❌ Exception lors de la création: {type(e).__name__}: {e}")
                import traceback
                safe_print(f"   ❌ Traceback: {traceback.format_exc()}")
        
        safe_print(f"\n🔍 DEBUG: Batch terminé - Utilisateurs créés: {len(created_users)}")
        return created_users
    
    def test_single_user_creation(self):
        """Test de création d'un seul utilisateur"""
        safe_print("\n🧪 TEST: Création manuelle d'un utilisateur")
        
        username = f"test_user_{int(time.time())}"
        email = f"{username}@test.com"
        password = "test123"
        
        safe_print(f"   - Username: {username}")
        safe_print(f"   - Email: {email}")
        
        # Test 1: Vérifier l'endpoint d'enregistrement
        try:
            safe_print("\n   📍 Test de l'endpoint /auth/register")
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "email": email, "password": password}
            )
            safe_print(f"   - Code: {response.status_code}")
            safe_print(f"   - Headers: {dict(response.headers)}")
            safe_print(f"   - Body: {response.text}")
        except Exception as e:
            safe_print(f"   ❌ Erreur: {e}")
        
        # Test 2: Vérifier l'endpoint de token
        try:
            safe_print("\n   📍 Test de l'endpoint /auth/token")
            response = requests.post(
                f"{self.base_url}/auth/token",
                data={"username": username, "password": password}
            )
            safe_print(f"   - Code: {response.status_code}")
            safe_print(f"   - Body: {response.text}")
        except Exception as e:
            safe_print(f"   ❌ Erreur: {e}")
    
    def test_api_endpoints(self):
        """Test de disponibilité des endpoints"""
        safe_print("\n🧪 TEST: Vérification des endpoints API")
        
        endpoints = [
            ("/docs", "GET"),
            ("/auth/register", "POST"),
            ("/auth/token", "POST"),
            ("/api/v1/agents", "GET"),
        ]
        
        for endpoint, method in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url)
                else:
                    response = requests.options(url)  # OPTIONS pour vérifier l'existence
                
                safe_print(f"   - {method} {endpoint}: {response.status_code}")
                
            except Exception as e:
                safe_print(f"   - {method} {endpoint}: ❌ {type(e).__name__}")
    
    def run_debug_demo(self):
        """Version de débogage de la démonstration"""
        safe_print("\n🔍 DÉMONSTRATION DEBUG - 100 AGENTS")
        safe_print("="*80)
        
        # Test préliminaires
        self.test_api_endpoints()
        self.test_single_user_creation()
        
        # Tentative de création normale avec plus de logs
        safe_print("\n📋 Tentative de création d'utilisateurs avec débogage complet")
        
        users_needed = 2  # Commencer avec seulement 2 pour le test
        safe_print(f"   Tentative de création de {users_needed} utilisateurs...")
        
        # Essai séquentiel d'abord
        safe_print("\n   🔄 Essai séquentiel (pas de threads)")
        created_users = self.create_user_batch(0, users_needed)
        
        safe_print(f"\n📊 Résultat final:")
        safe_print(f"   - Utilisateurs créés: {len(created_users)}")
        safe_print(f"   - Liste: {created_users}")
        safe_print(f"   - Stats globales: {stats['users_created']}")
        
        # Si ça marche, tenter avec des threads
        if created_users:
            safe_print("\n   🔄 Essai avec threads")
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(self.create_user_batch, 100, 2)
                batch = future.result()
                safe_print(f"   - Batch thread résultat: {batch}")

def main():
    """Point d'entrée principal"""
    print("🔍 DÉMONSTRATION DEBUG - 100 AGENTS")
    print("   Mode débogage activé pour identifier les problèmes")
    print()
    
    # Vérifier l'API
    try:
        response = requests.get(f"{API_URL}/docs")
        print(f"✅ API accessible - Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Impossible de se connecter à l'API: {e}")
        return
    
    # Lancer la démo debug
    demo = MAS100AgentsDemo()
    demo.run_debug_demo()

if __name__ == "__main__":
    main()