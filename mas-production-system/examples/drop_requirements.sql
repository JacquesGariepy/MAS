-- Supprimer les colonnes obsolètes qui causent des erreurs
ALTER TABLE tasks DROP COLUMN IF EXISTS requirements;
ALTER TABLE tasks DROP COLUMN IF EXISTS organization_id;
ALTER TABLE tasks DROP COLUMN IF EXISTS deadline;
ALTER TABLE tasks DROP COLUMN IF EXISTS assigned_agents;
ALTER TABLE tasks DROP COLUMN IF EXISTS started_at;