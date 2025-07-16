#!/usr/bin/env python3
"""
Script pour visualiser toute l'activité du système MAS
"""

import subprocess
import json
from datetime import datetime

print("📊 VISUALISATION COMPLÈTE DE L'ACTIVITÉ MAS\n")
print("=" * 80)

# 1. Afficher tous les utilisateurs
print("\n👥 UTILISATEURS")
print("-" * 40)

sql_users = """
SELECT username, email, created_at, agent_quota
FROM users
ORDER BY created_at DESC
LIMIT 10;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_users]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 4:
            print(f"👤 {parts[0]:<15} Email: {parts[1]:<30} Quota: {parts[3]}")

# 2. Afficher tous les agents
print("\n\n🤖 AGENTS ACTIFS")
print("-" * 40)

sql_agents = """
SELECT 
    a.id,
    a.name,
    a.agent_type,
    a.status,
    u.username as owner,
    a.created_at
FROM agents a
JOIN users u ON a.owner_id = u.id
WHERE a.is_active = true
ORDER BY a.created_at DESC
LIMIT 20;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_agents]
result = subprocess.run(cmd, capture_output=True, text=True)

agents = []
if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 6:
            agent_id = parts[0]
            agents.append(agent_id)
            print(f"🤖 {parts[1]:<20} Type: {parts[2]:<10} Status: {parts[3]:<12} Owner: {parts[4]}")
            print(f"   ID: {agent_id}")

# 3. Afficher toutes les tâches avec leurs résultats
print("\n\n📋 TOUTES LES TÂCHES")
print("-" * 40)

sql_tasks = """
SELECT 
    t.id,
    t.title,
    t.description,
    t.task_type,
    t.status,
    t.priority,
    t.result,
    a.name as agent_name,
    u.username as owner,
    t.created_at,
    t.completed_at
FROM tasks t
LEFT JOIN agents a ON t.assigned_to = a.id
JOIN users u ON t.owner_id = u.id
ORDER BY t.created_at DESC;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_tasks]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 11:
            task_id = parts[0]
            title = parts[1]
            description = parts[2][:100] + "..." if len(parts[2]) > 100 else parts[2]
            task_type = parts[3]
            status = parts[4]
            priority = parts[5]
            result = parts[6]
            agent_name = parts[7] if parts[7] else "Non assigné"
            owner = parts[8]
            created_at = parts[9]
            completed_at = parts[10] if parts[10] else "En cours"
            
            # Icône selon le status
            status_icon = {
                'completed': '✅',
                'pending': '⏳',
                'in_progress': '🔄',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(status, '❓')
            
            print(f"\n{status_icon} Tâche: {title}")
            print(f"   ID: {task_id}")
            print(f"   Description: {description}")
            print(f"   Type: {task_type} | Priorité: {priority}")
            print(f"   Agent: {agent_name} | Propriétaire: {owner}")
            print(f"   Créée: {created_at}")
            
            if status == 'completed':
                print(f"   Complétée: {completed_at}")
                
            # Afficher le résultat si présent
            if result and result != '':
                try:
                    result_json = json.loads(result)
                    print(f"   💬 Résultat:")
                    
                    if isinstance(result_json, dict):
                        if 'response' in result_json:
                            response_text = result_json['response']
                            # Afficher les premières lignes
                            lines = response_text.split('\\n')
                            for i, line in enumerate(lines[:5]):
                                print(f"      {line}")
                            if len(lines) > 5:
                                print(f"      ... ({len(lines)-5} lignes supplémentaires)")
                                
                        elif 'result' in result_json:
                            print(f"      {result_json['result']}")
                        else:
                            # Afficher les clés disponibles
                            print(f"      Données: {', '.join(result_json.keys())}")
                    else:
                        print(f"      {str(result_json)[:200]}...")
                except:
                    print(f"      {result[:200]}...")

# 4. Afficher les messages entre agents
print("\n\n💬 MESSAGES ENTRE AGENTS (derniers 10)")
print("-" * 40)

sql_messages = """
SELECT 
    m.performative,
    s.name as sender,
    r.name as receiver,
    m.created_at
FROM messages m
JOIN agents s ON m.sender_id = s.id
JOIN agents r ON m.receiver_id = r.id
ORDER BY m.created_at DESC
LIMIT 10;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_messages]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    lines = result.stdout.strip().split('\n')
    if lines and lines[0]:
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 4:
                print(f"📨 {parts[0]:<10} {parts[1]} → {parts[2]} ({parts[3]})")
    else:
        print("   Aucun message trouvé")

# 5. Statistiques globales
print("\n\n📈 STATISTIQUES GLOBALES")
print("-" * 40)

sql_stats = """
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM agents WHERE is_active = true) as active_agents,
    (SELECT COUNT(*) FROM tasks) as total_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'completed') as completed_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'pending') as pending_tasks,
    (SELECT COUNT(*) FROM messages) as total_messages;
"""

cmd = ["docker", "exec", "mas-production-system-db-1", "psql", "-U", "user", "-d", "mas", "-t", "-A", "-c", sql_stats]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    parts = result.stdout.strip().split('|')
    if len(parts) >= 6:
        print(f"👥 Utilisateurs: {parts[0]}")
        print(f"🤖 Agents actifs: {parts[1]}")
        print(f"📋 Total tâches: {parts[2]}")
        print(f"✅ Tâches complétées: {parts[3]}")
        print(f"⏳ Tâches en attente: {parts[4]}")
        print(f"💬 Messages échangés: {parts[5]}")

print("\n" + "=" * 80)
print("✨ Fin de la visualisation")