-- Script pour corriger la table tasks

-- 1. Ajouter les colonnes manquantes
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS owner_id UUID;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS title VARCHAR(200);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(50);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assigned_to UUID;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_metadata JSONB DEFAULT '{}';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- 2. Mettre à jour les valeurs par défaut
UPDATE tasks SET owner_id = (SELECT id FROM users LIMIT 1) WHERE owner_id IS NULL;
UPDATE tasks SET title = 'Task ' || id::text WHERE title IS NULL;
UPDATE tasks SET task_type = 'general' WHERE task_type IS NULL;

-- 3. Rendre les colonnes obligatoires NOT NULL
ALTER TABLE tasks ALTER COLUMN owner_id SET NOT NULL;
ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;
ALTER TABLE tasks ALTER COLUMN task_type SET NOT NULL;

-- 4. Ajouter les clés étrangères
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_owner_id 
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_to 
    FOREIGN KEY (assigned_to) REFERENCES agents(id) ON DELETE SET NULL;

-- 5. Supprimer les anciennes contraintes
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_priority_range;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_task_status;

-- 6. Convertir priority de integer à string
ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR(20) 
USING CASE 
    WHEN priority <= 3 THEN 'low' 
    WHEN priority <= 6 THEN 'medium' 
    WHEN priority <= 8 THEN 'high' 
    ELSE 'critical' 
END;

-- 7. Mettre à jour les NULL
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL;

-- 8. Ajouter les nouvelles contraintes
ALTER TABLE tasks ADD CONSTRAINT check_task_priority 
    CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    
ALTER TABLE tasks ADD CONSTRAINT check_task_status_new 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'));

-- 9. Afficher la structure finale
\echo 'Structure finale de la table tasks:'
\d tasks