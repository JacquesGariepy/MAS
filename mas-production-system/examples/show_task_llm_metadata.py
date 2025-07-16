#!/usr/bin/env python3
"""
Script pour afficher les métadonnées LLM des tâches et agents
"""

import subprocess
import json
from datetime import datetime

print("🔍 ANALYSE DES MÉTADONNÉES LLM DANS LE SYSTÈME MAS\n")
print("=" * 80)

# 1. Examiner la configuration des agents
print("\n🤖 CONFIGURATION LLM DES AGENTS")
print("-" * 40)

sql_agents = """
SELECT 
    a.id,
    a.name,
    a.agent_type,
    a.configuration,
    a.beliefs,
    u.username as owner
FROM agents a
JOIN users u ON a.owner_id = u.id
WHERE a.is_active = true
ORDER BY a.created_at DESC
LIMIT 10;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_agents]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 6:
            agent_id = parts[0]
            name = parts[1]
            agent_type = parts[2]
            config = parts[3]
            beliefs = parts[4]
            owner = parts[5]
            
            print(f"\n🤖 Agent: {name} ({agent_type})")
            print(f"   ID: {agent_id}")
            print(f"   Propriétaire: {owner}")
            
            # Afficher la configuration LLM
            if config and config != '{}':
                try:
                    config_json = json.loads(config)
                    print("   📋 Configuration LLM:")
                    for key, value in config_json.items():
                        if key in ['temperature', 'model', 'provider', 'max_tokens', 'reasoning_depth']:
                            print(f"      - {key}: {value}")
                except:
                    print(f"   📋 Configuration: {config[:100]}...")
            else:
                print("   📋 Configuration: Par défaut (non personnalisée)")
            
            # Afficher les beliefs liées au LLM
            if beliefs and beliefs != '{}':
                try:
                    beliefs_json = json.loads(beliefs)
                    if any(k in beliefs_json for k in ['langue', 'domaine', 'style']):
                        print("   🧠 Beliefs pertinentes:")
                        for key, value in beliefs_json.items():
                            if key in ['langue', 'domaine', 'style']:
                                print(f"      - {key}: {value}")
                except:
                    pass

# 2. Examiner les métadonnées des tâches
print("\n\n📋 MÉTADONNÉES LLM DES TÂCHES")
print("-" * 40)

sql_tasks = """
SELECT 
    t.id,
    t.title,
    t.task_type,
    t.status,
    t.task_metadata,
    t.result,
    a.name as agent_name,
    t.created_at,
    t.completed_at
FROM tasks t
LEFT JOIN agents a ON t.assigned_to = a.id
ORDER BY t.created_at DESC;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_tasks]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 9:
            task_id = parts[0]
            title = parts[1]
            task_type = parts[2]
            status = parts[3]
            task_metadata = parts[4]
            result = parts[5]
            agent_name = parts[6] if parts[6] else "Non assigné"
            created_at = parts[7]
            completed_at = parts[8] if parts[8] else "En cours"
            
            print(f"\n📌 Tâche: {title}")
            print(f"   ID: {task_id}")
            print(f"   Type: {task_type} | Status: {status}")
            print(f"   Agent: {agent_name}")
            
            # Afficher les métadonnées de la tâche
            if task_metadata and task_metadata != '{}':
                try:
                    metadata_json = json.loads(task_metadata)
                    if metadata_json:
                        print("   🔧 Métadonnées de tâche:")
                        for key, value in metadata_json.items():
                            print(f"      - {key}: {value}")
                except:
                    print(f"   🔧 Métadonnées: {task_metadata[:100]}...")
            
            # Si la tâche est complétée, examiner le résultat
            if status == 'completed' and result:
                try:
                    result_json = json.loads(result)
                    if isinstance(result_json, dict):
                        print("   ✅ Résultat avec métadonnées:")
                        # Chercher les métadonnées LLM dans le résultat
                        llm_keys = ['model', 'provider', 'temperature', 'tokens_used', 
                                   'confidence', 'sources', 'timestamp', 'processing_time']
                        for key in llm_keys:
                            if key in result_json:
                                print(f"      - {key}: {result_json[key]}")
                except:
                    pass

# 3. Examiner les logs d'audit pour les appels LLM
print("\n\n📊 LOGS D'AUDIT LLM (si disponibles)")
print("-" * 40)

sql_audit = """
SELECT 
    action,
    details,
    created_at
FROM audit_logs
WHERE action LIKE '%llm%' OR action LIKE '%LLM%'
ORDER BY created_at DESC
LIMIT 10;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_audit]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    if lines and lines[0]:
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 3:
                action = parts[0]
                details = parts[1]
                created_at = parts[2]
                
                print(f"\n🔍 Action: {action}")
                print(f"   Date: {created_at}")
                if details:
                    try:
                        details_json = json.loads(details)
                        print("   Détails:")
                        for key, value in details_json.items():
                            print(f"      - {key}: {value}")
                    except:
                        print(f"   Détails: {details[:100]}...")
    else:
        print("   ❌ Aucun log d'audit LLM trouvé")

# 4. Configuration actuelle du système
print("\n\n⚙️ CONFIGURATION LLM ACTUELLE DU SYSTÈME")
print("-" * 40)

# Lire les variables d'environnement depuis le conteneur
env_vars = ["LLM_PROVIDER", "LLM_MODEL", "LLM_TEMPERATURE", "LLM_MAX_TOKENS", "LLM_BASE_URL"]
print("Variables d'environnement dans le conteneur core:")

for var in env_vars:
    cmd = ["docker", "exec", "mas-production-system-core-1", "sh", "-c", f"echo ${var}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        value = result.stdout.strip()
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: non défini")

# 5. Résumé des métadonnées disponibles
print("\n\n📈 RÉSUMÉ DES MÉTADONNÉES DISPONIBLES")
print("-" * 40)

print("""
Le système MAS stocke les métadonnées LLM à plusieurs niveaux:

1. **Configuration des agents** (table: agents, colonne: configuration)
   - temperature: Contrôle la créativité (0.0-1.0)
   - model: Modèle LLM spécifique à utiliser
   - provider: Provider LLM (openai, ollama, lmstudio)
   - max_tokens: Limite de tokens pour les réponses
   - reasoning_depth: Profondeur du raisonnement
   - system_prompt: Prompt système personnalisé

2. **Métadonnées des tâches** (table: tasks, colonne: task_metadata)
   - Paramètres de la requête
   - Context de l'exécution
   - Références aux agents

3. **Résultats des tâches** (table: tasks, colonne: result)
   - response: La réponse générée
   - confidence: Niveau de confiance (0.0-1.0)
   - sources: Sources d'information utilisées
   - timestamp: Horodatage de la génération
   - tokens_used: Nombre de tokens consommés
   - processing_time: Temps de traitement

4. **Logs d'audit** (table: audit_logs)
   - Trace complète des appels LLM
   - Métriques de performance
   - Erreurs et réessais

5. **Variables d'environnement**
   - LLM_PROVIDER: Provider principal
   - LLM_MODEL: Modèle par défaut
   - LLM_TEMPERATURE: Température par défaut
   - LLM_MAX_TOKENS: Limite de tokens
   - LLM_BASE_URL: URL de l'API
""")

print("\n" + "=" * 80)
print("✨ Analyse des métadonnées terminée")