#!/usr/bin/env python3
"""
Script complet pour corriger la table tasks en supprimant les colonnes obsolètes
et en ajoutant les nouvelles colonnes nécessaires
"""

import subprocess
import os

print("🔧 Correction complète de la table tasks...\n")

# Script SQL pour corriger la table
sql_script = """
-- 1. Supprimer les contraintes obsolètes
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_priority_range;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_task_status;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_task_status_new;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_task_priority;

-- 2. Supprimer les colonnes obsolètes qui causent des problèmes
DO $$
BEGIN
    -- Supprimer requirements si elle existe
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='requirements') THEN
        ALTER TABLE tasks DROP COLUMN requirements;
        RAISE NOTICE 'Colonne requirements supprimée';
    END IF;
    
    -- Supprimer organization_id si elle existe
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='organization_id') THEN
        ALTER TABLE tasks DROP COLUMN organization_id;
        RAISE NOTICE 'Colonne organization_id supprimée';
    END IF;
    
    -- Supprimer deadline si elle existe
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='deadline') THEN
        ALTER TABLE tasks DROP COLUMN deadline;
        RAISE NOTICE 'Colonne deadline supprimée';
    END IF;
    
    -- Supprimer assigned_agents si elle existe
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='assigned_agents') THEN
        ALTER TABLE tasks DROP COLUMN assigned_agents;
        RAISE NOTICE 'Colonne assigned_agents supprimée';
    END IF;
    
    -- Supprimer started_at si elle existe
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='tasks' AND column_name='started_at') THEN
        ALTER TABLE tasks DROP COLUMN started_at;
        RAISE NOTICE 'Colonne started_at supprimée';
    END IF;
END $$;

-- 3. Ajouter les colonnes manquantes
DO $$
BEGIN
    -- Ajouter owner_id si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='owner_id') THEN
        ALTER TABLE tasks ADD COLUMN owner_id UUID;
        UPDATE tasks SET owner_id = (SELECT id FROM users LIMIT 1) WHERE owner_id IS NULL;
        ALTER TABLE tasks ALTER COLUMN owner_id SET NOT NULL;
        ALTER TABLE tasks ADD CONSTRAINT fk_tasks_owner_id 
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
        RAISE NOTICE 'Colonne owner_id ajoutée';
    END IF;
    
    -- Ajouter title si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='title') THEN
        ALTER TABLE tasks ADD COLUMN title VARCHAR(200) DEFAULT 'Task';
        UPDATE tasks SET title = 'Task ' || id::text WHERE title = 'Task';
        ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;
        RAISE NOTICE 'Colonne title ajoutée';
    END IF;
    
    -- Ajouter task_type si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_type') THEN
        ALTER TABLE tasks ADD COLUMN task_type VARCHAR(50) DEFAULT 'general';
        ALTER TABLE tasks ALTER COLUMN task_type SET NOT NULL;
        RAISE NOTICE 'Colonne task_type ajoutée';
    END IF;
    
    -- Ajouter assigned_to si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='assigned_to') THEN
        ALTER TABLE tasks ADD COLUMN assigned_to UUID;
        ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_to 
            FOREIGN KEY (assigned_to) REFERENCES agents(id) ON DELETE SET NULL;
        RAISE NOTICE 'Colonne assigned_to ajoutée';
    END IF;
    
    -- Ajouter task_metadata si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_metadata') THEN
        ALTER TABLE tasks ADD COLUMN task_metadata JSONB DEFAULT '{}';
        RAISE NOTICE 'Colonne task_metadata ajoutée';
    END IF;
    
    -- Ajouter updated_at si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='updated_at') THEN
        ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Colonne updated_at ajoutée';
    END IF;
END $$;

-- 4. Convertir priority si nécessaire
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
        RAISE NOTICE 'Type de priority converti en string';
    END IF;
END $$;

-- 5. Mettre à jour les valeurs NULL
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL;

-- 6. Ajouter les nouvelles contraintes
ALTER TABLE tasks ADD CONSTRAINT check_task_priority 
    CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    
ALTER TABLE tasks ADD CONSTRAINT check_task_status_new 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'));

-- 7. Afficher la structure finale
\\echo ''
\\echo 'Structure finale de la table tasks:'
\\echo '-----------------------------------'
SELECT 
    column_name,
    data_type,
    CASE 
        WHEN is_nullable = 'YES' THEN 'NULL'
        ELSE 'NOT NULL'
    END as nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
ORDER BY ordinal_position;
"""

# Sauvegarder le script SQL
with open('/tmp/fix_tasks_complete.sql', 'w') as f:
    f.write(sql_script)

print("1️⃣ Script SQL créé")

# Exécuter via Docker avec les variables d'environnement
cmd = [
    "docker", "exec", "-i", "mas-production-system-db-1", 
    "sh", "-c", "PGPASSWORD=mas_password psql -U mas_user -d mas_db"
]

print("2️⃣ Exécution de la correction complète...")

try:
    with open('/tmp/fix_tasks_complete.sql', 'r') as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Correction exécutée avec succès!")
        print("\nRésultat:")
        print(result.stdout)
    else:
        print("❌ Erreur lors de la correction:")
        print(result.stderr)
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n3️⃣ Nettoyage...")
os.remove('/tmp/fix_tasks_complete.sql')

print("\n✨ Terminé! La table tasks devrait maintenant être correctement configurée.")