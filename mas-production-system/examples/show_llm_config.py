#!/usr/bin/env python3
"""
Script pour afficher toutes les informations de configuration LLM du système MAS
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'core'))

def load_env_file(path: str) -> Dict[str, str]:
    """Charger les variables d'environnement depuis un fichier .env"""
    env_vars = {}
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def get_llm_config_from_env():
    """Extraire la configuration LLM des variables d'environnement"""
    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "non défini"),
        "model": os.getenv("LLM_MODEL", "non défini"),
        "api_key": "***" if os.getenv("LLM_API_KEY") else "non défini",
        "base_url": os.getenv("LLM_BASE_URL", "non défini"),
        "temperature": os.getenv("LLM_TEMPERATURE", "non défini"),
        "max_tokens": os.getenv("LLM_MAX_TOKENS", "non défini"),
        
        # Configurations spécifiques par provider
        "openai": {
            "api_key": "***" if os.getenv("OPENAI_API_KEY") else "non défini",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": os.getenv("OPENAI_TEMPERATURE", "0.7"),
            "max_tokens": os.getenv("OPENAI_MAX_TOKENS", "4000"),
            "timeout": os.getenv("OPENAI_TIMEOUT", "30")
        },
        "ollama": {
            "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "non défini")
        },
        "lmstudio": {
            "base_url": os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        },
        "anthropic": {
            "api_key": "***" if os.getenv("ANTHROPIC_API_KEY") else "non défini",
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet"),
            "max_tokens": os.getenv("ANTHROPIC_MAX_TOKENS", "4000")
        }
    }
    return llm_config

def get_agent_config_from_api(api_url: str, token: str) -> Optional[Dict[str, Any]]:
    """Récupérer la configuration des agents via l'API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Récupérer la liste des agents
        response = requests.get(f"{api_url}/api/v1/agents", headers=headers)
        if response.status_code == 200:
            agents_data = response.json()
            agents_config = []
            
            for agent in agents_data.get('items', []):
                agent_id = agent['id']
                # Récupérer les détails de chaque agent
                detail_response = requests.get(
                    f"{api_url}/api/v1/agents/{agent_id}", 
                    headers=headers
                )
                if detail_response.status_code == 200:
                    agent_detail = detail_response.json()
                    agents_config.append({
                        "id": agent_id,
                        "name": agent.get('name'),
                        "type": agent.get('agent_type'),
                        "configuration": agent_detail.get('configuration', {}),
                        "beliefs": agent_detail.get('beliefs', {}),
                        "metadata": agent_detail.get('metadata', {})
                    })
            
            return agents_config
    except Exception as e:
        print(f"Erreur lors de la récupération des agents: {e}")
        return None

def display_llm_configuration():
    """Afficher toutes les informations de configuration LLM"""
    print("🔧 CONFIGURATION LLM DU SYSTÈME MAS")
    print("=" * 60)
    
    # 1. Variables d'environnement
    print("\n📍 1. VARIABLES D'ENVIRONNEMENT")
    print("-" * 40)
    
    # Charger depuis différents fichiers .env
    env_files = [
        ".env",
        ".env.example",
        "services/core/.env",
        "services/core/.env.example"
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"\n  Fichier: {env_file}")
            env_vars = load_env_file(env_file)
            llm_vars = {k: v for k, v in env_vars.items() 
                       if any(x in k for x in ['LLM', 'OPENAI', 'OLLAMA', 'ANTHROPIC', 'LMSTUDIO'])}
            for key, value in llm_vars.items():
                if 'KEY' in key:
                    value = '***' if value else 'non défini'
                print(f"    {key}: {value}")
    
    # 2. Configuration actuelle
    print("\n\n📍 2. CONFIGURATION ACTUELLE (variables d'environnement)")
    print("-" * 40)
    current_config = get_llm_config_from_env()
    
    print(f"\n  Provider principal: {current_config['provider']}")
    print(f"  Model: {current_config['model']}")
    print(f"  Temperature: {current_config['temperature']}")
    print(f"  Max tokens: {current_config['max_tokens']}")
    
    # 3. Configuration par provider
    print("\n\n📍 3. CONFIGURATION PAR PROVIDER")
    print("-" * 40)
    
    for provider, config in current_config.items():
        if isinstance(config, dict):
            print(f"\n  {provider.upper()}:")
            for key, value in config.items():
                print(f"    {key}: {value}")
    
    # 4. Structure de configuration des agents
    print("\n\n📍 4. STRUCTURE DE CONFIGURATION DES AGENTS")
    print("-" * 40)
    print("""
  Les agents peuvent avoir ces configurations LLM dans leur champ 'configuration':
  {
    "temperature": 0.7,           # Créativité de la réponse (0.0-1.0)
    "reasoning_depth": 3,         # Profondeur du raisonnement
    "max_tokens": 4000,           # Nombre max de tokens
    "model": "gpt-4o-mini",       # Modèle LLM spécifique
    "provider": "openai",         # Provider LLM spécifique
    "system_prompt": "...",       # Prompt système personnalisé
    "response_format": "json",    # Format de réponse attendu
    "planning_horizon": 5,        # Horizon de planification
    "reflection_frequency": 10,   # Fréquence de réflexion
    "learning_rate": 0.1,         # Taux d'apprentissage
    "exploration_rate": 0.2,      # Taux d'exploration
    "confidence_threshold": 0.7   # Seuil de confiance
  }
  """)
    
    # 5. Valeurs par défaut du système
    print("\n\n📍 5. VALEURS PAR DÉFAUT (depuis config.py)")
    print("-" * 40)
    print("""
  Provider par défaut: lmstudio (peut être openai, ollama, lmstudio)
  Température par défaut: 0.7
  Max tokens par défaut: 4000
  Timeout par défaut: 30 secondes
  
  OpenAI:
    - Modèle par défaut: gpt-4o-mini
    - Temperature: 0.7
    - Max tokens: 4000
    
  Ollama:
    - Host par défaut: http://localhost:11434
    - Modèle: défini par OLLAMA_MODEL
    
  LM Studio:
    - URL par défaut: http://localhost:1234/v1
    
  Anthropic:
    - Modèle par défaut: claude-3-sonnet
    - Max tokens: 4000
  """)
    
    # 6. Utilisation dans le code
    print("\n\n📍 6. UTILISATION DANS LE CODE")
    print("-" * 40)
    print("""
  Le service LLM (llm_service.py) utilise ces configurations:
  
  1. Au démarrage: 
     - Charge les settings depuis config.py
     - Utilise LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, etc.
  
  2. Par agent:
     - Chaque agent peut override avec son champ 'configuration'
     - Les agents cognitifs utilisent le service LLM pour:
       * Percevoir et interpréter l'environnement
       * Raisonner sur les actions
       * Planifier les tâches
       * Apprendre de l'expérience
  
  3. Métadonnées stockées:
     - Chaque requête LLM est trackée (track_llm_request)
     - Métriques: tokens utilisés, succès/échec, modèle
     - Les résultats sont stockés dans task_metadata
  """)
    
    # 7. Exemple de connexion API
    print("\n\n📍 7. EXEMPLE D'AGENTS CONFIGURÉS (nécessite l'API en cours d'exécution)")
    print("-" * 40)
    
    api_url = "http://localhost:8088"
    try:
        # Tenter une connexion simple
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ API accessible")
            print("  Pour voir les agents configurés, authentifiez-vous et utilisez:")
            print(f"  GET {api_url}/api/v1/agents")
        else:
            print("  ⚠️ API accessible mais retourne un code d'erreur")
    except:
        print("  ❌ API non accessible (démarrez avec 'docker-compose up')")
    
    print("\n" + "=" * 60)
    print("✅ Analyse de configuration terminée")

def main():
    """Point d'entrée principal"""
    display_llm_configuration()
    
    # Afficher aussi où ces infos sont stockées dans la DB
    print("\n\n📍 8. STOCKAGE EN BASE DE DONNÉES")
    print("-" * 40)
    print("""
  Table: agents
  - configuration (JSONB): Contient les paramètres LLM spécifiques
  - beliefs (JSONB): Peut contenir des préférences LLM
  
  Table: tasks  
  - task_metadata (JSONB): Contient les résultats et métriques LLM
  
  Table: memories
  - memory_metadata (JSONB): Peut contenir le contexte LLM utilisé
  
  Table: audit_logs
  - details (JSONB): Trace les appels LLM et leurs paramètres
  """)

if __name__ == "__main__":
    main()