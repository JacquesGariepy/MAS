#!/usr/bin/env python3
"""
Script pour corriger la table tasks en se connectant directement à PostgreSQL
"""

import subprocess
import os

print("🔧 Correction de la table tasks...\n")

# Script SQL pour corriger la table
sql_script = """
-- Afficher la structure actuelle
\\echo 'Structure actuelle de la table tasks:'
\\d tasks

-- Vérifier et ajouter les colonnes manquantes
DO $$
BEGIN
    -- Ajouter owner_id si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='owner_id') THEN
        RAISE NOTICE 'Ajout de owner_id...';
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
        RAISE NOTICE 'Ajout de title...';
        ALTER TABLE tasks ADD COLUMN title VARCHAR(200) DEFAULT 'Task';
        UPDATE tasks SET title = 'Task ' || id::text WHERE title = 'Task';
        ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;
    END IF;
    
    -- Ajouter task_type si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_type') THEN
        RAISE NOTICE 'Ajout de task_type...';
        ALTER TABLE tasks ADD COLUMN task_type VARCHAR(50) DEFAULT 'general';
        ALTER TABLE tasks ALTER COLUMN task_type SET NOT NULL;
    END IF;
    
    -- Ajouter assigned_to si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='assigned_to') THEN
        RAISE NOTICE 'Ajout de assigned_to...';
        ALTER TABLE tasks ADD COLUMN assigned_to UUID;
        ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_to 
            FOREIGN KEY (assigned_to) REFERENCES agents(id) ON DELETE SET NULL;
    END IF;
    
    -- Ajouter task_metadata si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='task_metadata') THEN
        RAISE NOTICE 'Ajout de task_metadata...';
        ALTER TABLE tasks ADD COLUMN task_metadata JSONB DEFAULT '{}';
    END IF;
    
    -- Ajouter updated_at si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='updated_at') THEN
        RAISE NOTICE 'Ajout de updated_at...';
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
        RAISE NOTICE 'Conversion de priority en string...';
        ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR(20) 
        USING CASE 
            WHEN priority <= 3 THEN 'low' 
            WHEN priority <= 6 THEN 'medium' 
            WHEN priority <= 8 THEN 'high' 
            ELSE 'critical' 
        END;
    END IF;
END $$;

-- Définir une valeur par défaut pour priority si NULL
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL;

-- Ajouter les nouvelles contraintes
ALTER TABLE tasks ADD CONSTRAINT check_task_priority 
    CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    
ALTER TABLE tasks ADD CONSTRAINT check_task_status_new 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'));

-- Afficher la structure finale
\\echo ''
\\echo 'Structure finale de la table tasks:'
\\d tasks
"""

# Sauvegarder le script SQL
with open('/tmp/fix_tasks.sql', 'w') as f:
    f.write(sql_script)

print("1️⃣ Script SQL créé")

# Exécuter via psql directement (port 5433 pour MAS)
# Utiliser PGPASSWORD pour éviter le prompt de mot de passe
env = os.environ.copy()
env['PGPASSWORD'] = 'mas_password'

cmd = [
    "psql",
    "-h", "localhost",
    "-p", "5433",
    "-U", "mas_user", 
    "-d", "mas_db",
    "-f", "/tmp/fix_tasks.sql"
]

print("2️⃣ Exécution de la migration...")

try:
    # Essayer d'abord avec psql directement
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0 and "psql: command not found" in result.stderr:
        # Si psql n'est pas installé, utiliser Docker
        print("   psql non trouvé, utilisation de Docker...")
        
        # Copier le fichier dans le conteneur
        subprocess.run(["docker", "cp", "/tmp/fix_tasks.sql", "mas-production-system-db-1:/tmp/fix_tasks.sql"])
        
        # Exécuter dans le conteneur
        cmd = [
            "docker", "exec", "mas-production-system-db-1",
            "psql", "-U", "mas_user", "-d", "mas_db", "-f", "/tmp/fix_tasks.sql"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
    
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
try:
    os.remove('/tmp/fix_tasks.sql')
    # Nettoyer aussi dans le conteneur si nécessaire
    subprocess.run(["docker", "exec", "mas-production-system-db-1", "rm", "-f", "/tmp/fix_tasks.sql"], capture_output=True)
except:
    pass

print("\n✨ Terminé! Vous pouvez maintenant tester la création de tâches.")