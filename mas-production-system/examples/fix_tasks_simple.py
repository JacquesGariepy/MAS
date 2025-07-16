#!/usr/bin/env python3
"""
Script simple pour corriger la table tasks en utilisant les outils disponibles
"""

import requests

# Exécuter une migration directement dans le conteneur
print("🔧 Correction de la table tasks via Docker...\n")

import subprocess

# Script SQL pour corriger la table
sql_script = """
-- Vérifier et ajouter les colonnes manquantes
DO $$
BEGIN
    -- Ajouter owner_id si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='owner_id') THEN
        ALTER TABLE tasks ADD COLUMN owner_id UUID;
        
        -- Mettre à jour avec le premier user disponible
        UPDATE tasks SET owner_id = (SELECT id FROM users LIMIT 1) WHERE owner_id IS NULL;
        
        -- Rendre NOT NULL et ajouter FK
        ALTER TABLE tasks ALTER COLUMN owner_id SET NOT NULL;
        ALTER TABLE tasks ADD CONSTRAINT fk_tasks_owner_id 
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    
    -- Ajouter title si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='title') THEN
        ALTER TABLE tasks ADD COLUMN title VARCHAR(200) DEFAULT 'Task';
        UPDATE tasks SET title = 'Task ' || id::text WHERE title = 'Task';
        ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;
    END IF;
    
    -- Ajouter task_type si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_type') THEN
        ALTER TABLE tasks ADD COLUMN task_type VARCHAR(50) DEFAULT 'general';
        ALTER TABLE tasks ALTER COLUMN task_type SET NOT NULL;
    END IF;
    
    -- Ajouter assigned_to si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='assigned_to') THEN
        ALTER TABLE tasks ADD COLUMN assigned_to UUID;
        ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_to 
            FOREIGN KEY (assigned_to) REFERENCES agents(id) ON DELETE SET NULL;
    END IF;
    
    -- Ajouter task_metadata si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_metadata') THEN
        ALTER TABLE tasks ADD COLUMN task_metadata JSONB DEFAULT '{}';
    END IF;
    
    -- Ajouter updated_at si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='updated_at') THEN
        ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Mettre à jour les contraintes
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_priority_range;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_task_status;

-- Si priority est un integer, le convertir en string
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='priority' 
               AND data_type='integer') THEN
        ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR(20) 
        USING CASE 
            WHEN priority <= 3 THEN 'low' 
            WHEN priority <= 6 THEN 'medium' 
            WHEN priority <= 8 THEN 'high' 
            ELSE 'critical' 
        END;
    END IF;
END $$;

-- Ajouter les nouvelles contraintes
ALTER TABLE tasks ADD CONSTRAINT check_task_priority 
    CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    
ALTER TABLE tasks ADD CONSTRAINT check_task_status_new 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'));

-- Afficher la structure finale
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tasks' 
ORDER BY ordinal_position;
"""

# Sauvegarder le script SQL
with open('/tmp/fix_tasks.sql', 'w') as f:
    f.write(sql_script)

print("1️⃣ Script SQL créé")

# Exécuter via Docker
cmd = [
    "docker", "exec", "-i", "mas-production-system-db-1", 
    "psql", "-h", "localhost", "-U", "mas_user", "-d", "mas_db"
]

print("2️⃣ Exécution de la migration...")

try:
    with open('/tmp/fix_tasks.sql', 'r') as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Migration exécutée avec succès!")
        print("\nRésultat:")
        print(result.stdout)
    else:
        print("❌ Erreur lors de la migration:")
        print(result.stderr)
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n3️⃣ Nettoyage...")
import os
os.remove('/tmp/fix_tasks.sql')

print("\n✨ Terminé! Vous pouvez maintenant tester la création de tâches.")