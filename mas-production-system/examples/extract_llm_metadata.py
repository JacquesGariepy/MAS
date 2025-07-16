#!/usr/bin/env python3
"""
Script pour extraire les métadonnées LLM depuis une instance MAS en cours d'exécution
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

API_URL = "http://localhost:8088"

def login(username: str = "test_user", password: str = "password123") -> Optional[str]:
    """Se connecter et obtenir un token"""
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception as e:
        print(f"Erreur de connexion: {e}")
    return None

def get_agents_llm_config(token: str) -> List[Dict[str, Any]]:
    """Récupérer la configuration LLM de tous les agents"""
    headers = {"Authorization": f"Bearer {token}"}
    agents_config = []
    
    try:
        # Récupérer la liste des agents
        response = requests.get(f"{API_URL}/api/v1/agents", headers=headers)
        if response.status_code == 200:
            agents_data = response.json()
            
            for agent in agents_data.get('items', []):
                agent_id = agent['id']
                
                # Récupérer les détails complets de l'agent
                detail_response = requests.get(
                    f"{API_URL}/api/v1/agents/{agent_id}", 
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    details = detail_response.json()
                    
                    # Extraire la configuration LLM
                    config = {
                        "agent_id": agent_id,
                        "agent_name": agent['name'],
                        "agent_type": agent['agent_type'],
                        "role": agent['role'],
                        "status": agent['status'],
                        "llm_configuration": details.get('configuration', {}),
                        "beliefs": details.get('beliefs', {}),
                        "created_at": agent['created_at']
                    }
                    
                    # Chercher des infos LLM dans les beliefs
                    llm_beliefs = {k: v for k, v in details.get('beliefs', {}).items() 
                                  if any(term in k.lower() for term in ['llm', 'model', 'temperature', 'ai'])}
                    if llm_beliefs:
                        config['llm_from_beliefs'] = llm_beliefs
                    
                    agents_config.append(config)
                    
    except Exception as e:
        print(f"Erreur lors de la récupération des agents: {e}")
    
    return agents_config

def get_tasks_llm_metadata(token: str) -> List[Dict[str, Any]]:
    """Récupérer les métadonnées LLM des tâches"""
    headers = {"Authorization": f"Bearer {token}"}
    tasks_metadata = []
    
    try:
        # Récupérer la liste des tâches
        response = requests.get(f"{API_URL}/api/v1/tasks", headers=headers)
        if response.status_code == 200:
            tasks_data = response.json()
            
            for task in tasks_data.get('items', []):
                task_id = task['id']
                
                # Récupérer les détails de la tâche
                detail_response = requests.get(
                    f"{API_URL}/api/v1/tasks/{task_id}",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    details = detail_response.json()
                    
                    # Extraire les métadonnées LLM
                    metadata = details.get('task_metadata', {})
                    llm_metadata = {k: v for k, v in metadata.items()
                                   if any(term in str(k).lower() for term in ['llm', 'model', 'token', 'prompt', 'response'])}
                    
                    if llm_metadata or details.get('result'):
                        task_info = {
                            "task_id": task_id,
                            "title": task['title'],
                            "type": task['task_type'],
                            "status": task['status'],
                            "assigned_to": task.get('assigned_to'),
                            "llm_metadata": llm_metadata,
                            "result": details.get('result'),
                            "created_at": task['created_at']
                        }
                        tasks_metadata.append(task_info)
                        
    except Exception as e:
        print(f"Erreur lors de la récupération des tâches: {e}")
    
    return tasks_metadata

def display_llm_metadata():
    """Afficher toutes les métadonnées LLM extraites"""
    print("🔍 EXTRACTION DES MÉTADONNÉES LLM DU SYSTÈME MAS")
    print("=" * 70)
    
    # Se connecter
    token = login()
    if not token:
        print("\n❌ Impossible de se connecter à l'API")
        print("   Assurez-vous que l'API est en cours d'exécution avec:")
        print("   docker-compose up")
        return
    
    print("\n✅ Connecté avec succès")
    
    # 1. Configuration des agents
    print("\n\n📤 1. CONFIGURATION LLM DES AGENTS")
    print("-" * 50)
    
    agents_config = get_agents_llm_config(token)
    
    if not agents_config:
        print("  Aucun agent trouvé")
    else:
        for i, agent in enumerate(agents_config, 1):
            print(f"\n  Agent #{i}: {agent['agent_name']}")
            print(f"    Type: {agent['agent_type']}")
            print(f"    Rôle: {agent['role']}")
            print(f"    Status: {agent['status']}")
            print(f"    ID: {agent['agent_id']}")
            
            if agent['llm_configuration']:
                print("    Configuration LLM:")
                for key, value in agent['llm_configuration'].items():
                    print(f"      - {key}: {value}")
            else:
                print("    Configuration LLM: Aucune (utilise les valeurs par défaut)")
            
            if agent.get('llm_from_beliefs'):
                print("    Infos LLM dans beliefs:")
                for key, value in agent['llm_from_beliefs'].items():
                    print(f"      - {key}: {value}")
    
    # 2. Métadonnées des tâches
    print("\n\n📊 2. MÉTADONNÉES LLM DES TÂCHES")
    print("-" * 50)
    
    tasks_metadata = get_tasks_llm_metadata(token)
    
    if not tasks_metadata:
        print("  Aucune tâche avec métadonnées LLM trouvée")
    else:
        for i, task in enumerate(tasks_metadata, 1):
            print(f"\n  Tâche #{i}: {task['title']}")
            print(f"    Type: {task['type']}")
            print(f"    Status: {task['status']}")
            print(f"    ID: {task['task_id']}")
            
            if task['llm_metadata']:
                print("    Métadonnées LLM:")
                for key, value in task['llm_metadata'].items():
                    if isinstance(value, (dict, list)):
                        print(f"      - {key}: {json.dumps(value, indent=8)}")
                    else:
                        print(f"      - {key}: {value}")
            
            if task['result'] and isinstance(task['result'], dict):
                # Chercher des infos LLM dans le résultat
                llm_in_result = {k: v for k, v in task['result'].items()
                                if any(term in str(k).lower() for term in ['llm', 'model', 'token'])}
                if llm_in_result:
                    print("    Infos LLM dans le résultat:")
                    for key, value in llm_in_result.items():
                        print(f"      - {key}: {value}")
    
    # 3. Résumé des configurations
    print("\n\n📈 3. RÉSUMÉ DES CONFIGURATIONS LLM UTILISÉES")
    print("-" * 50)
    
    # Collecter toutes les configurations uniques
    providers = set()
    models = set()
    temperatures = set()
    
    for agent in agents_config:
        config = agent['llm_configuration']
        if config.get('provider'):
            providers.add(config['provider'])
        if config.get('model'):
            models.add(config['model'])
        if config.get('temperature'):
            temperatures.add(config['temperature'])
    
    print(f"\n  Providers utilisés: {', '.join(providers) if providers else 'Aucun (utilise défaut)'}")
    print(f"  Modèles utilisés: {', '.join(models) if models else 'Aucun (utilise défaut)'}")
    print(f"  Températures utilisées: {', '.join(map(str, temperatures)) if temperatures else 'Aucune (utilise défaut)'}")
    
    print("\n" + "=" * 70)
    print("✅ Extraction terminée")

def export_llm_config(token: str, output_file: str = "llm_config_export.json"):
    """Exporter toute la configuration LLM dans un fichier JSON"""
    export_data = {
        "export_date": datetime.now().isoformat(),
        "agents": get_agents_llm_config(token),
        "tasks": get_tasks_llm_metadata(token)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Configuration exportée dans: {output_file}")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        token = login()
        if token:
            export_llm_config(token)
        else:
            print("❌ Impossible de se connecter pour l'export")
    else:
        display_llm_metadata()
        print("\n💡 Astuce: Utilisez --export pour exporter la configuration dans un fichier JSON")

if __name__ == "__main__":
    main()