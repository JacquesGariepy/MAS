#!/usr/bin/env python3
"""
Script pour exécuter directement les modifications SQL nécessaires
pour corriger la table tasks
"""

import asyncio
import asyncpg
from datetime import datetime

DATABASE_URL = "postgresql://mas_user:mas_password@localhost:5433/mas_db"

async def fix_tasks_table():
    """Corrige la structure de la table tasks"""
    
    print("🔧 Correction de la table tasks...\n")
    
    # Connexion à la base de données
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # 1. Vérifier la structure actuelle
        print("1️⃣ Vérification de la structure actuelle...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position;
        """)
        
        print("Colonnes actuelles:")
        for col in columns:
            print(f"   - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # 2. Vérifier si owner_id existe
        has_owner_id = any(col['column_name'] == 'owner_id' for col in columns)
        
        if not has_owner_id:
            print("\n2️⃣ Ajout de la colonne owner_id...")
            
            # Ajouter owner_id
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN owner_id UUID;
            """)
            
            # Mettre à jour avec un owner par défaut (premier utilisateur)
            first_user = await conn.fetchrow("SELECT id FROM users LIMIT 1")
            if first_user:
                await conn.execute("""
                    UPDATE tasks 
                    SET owner_id = $1 
                    WHERE owner_id IS NULL;
                """, first_user['id'])
                
                # Rendre la colonne NOT NULL
                await conn.execute("""
                    ALTER TABLE tasks 
                    ALTER COLUMN owner_id SET NOT NULL;
                """)
                
                # Ajouter la clé étrangère
                await conn.execute("""
                    ALTER TABLE tasks 
                    ADD CONSTRAINT fk_tasks_owner_id 
                    FOREIGN KEY (owner_id) 
                    REFERENCES users(id) 
                    ON DELETE CASCADE;
                """)
                
                print("✅ Colonne owner_id ajoutée")
        
        # 3. Vérifier et ajouter les colonnes manquantes
        print("\n3️⃣ Vérification des autres colonnes...")
        
        # Ajouter title si manquant
        if not any(col['column_name'] == 'title' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN title VARCHAR(200) DEFAULT 'Task';
            """)
            await conn.execute("""
                UPDATE tasks SET title = 'Task ' || id::text WHERE title = 'Task';
            """)
            await conn.execute("""
                ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;
            """)
            print("✅ Colonne title ajoutée")
        
        # Ajouter task_type si manquant
        if not any(col['column_name'] == 'task_type' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN task_type VARCHAR(50) DEFAULT 'general';
            """)
            await conn.execute("""
                ALTER TABLE tasks ALTER COLUMN task_type SET NOT NULL;
            """)
            print("✅ Colonne task_type ajoutée")
        
        # Ajouter assigned_to si manquant
        if not any(col['column_name'] == 'assigned_to' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN assigned_to UUID;
            """)
            await conn.execute("""
                ALTER TABLE tasks 
                ADD CONSTRAINT fk_tasks_assigned_to 
                FOREIGN KEY (assigned_to) 
                REFERENCES agents(id) 
                ON DELETE SET NULL;
            """)
            print("✅ Colonne assigned_to ajoutée")
        
        # Renommer metadata en task_metadata si nécessaire
        if any(col['column_name'] == 'metadata' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                RENAME COLUMN metadata TO task_metadata;
            """)
            print("✅ Colonne metadata renommée en task_metadata")
        elif not any(col['column_name'] == 'task_metadata' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN task_metadata JSONB DEFAULT '{}';
            """)
            print("✅ Colonne task_metadata ajoutée")
        
        # Ajouter updated_at si manquant
        if not any(col['column_name'] == 'updated_at' for col in columns):
            await conn.execute("""
                ALTER TABLE tasks 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
            """)
            print("✅ Colonne updated_at ajoutée")
        
        # 4. Mettre à jour les contraintes
        print("\n4️⃣ Mise à jour des contraintes...")
        
        # Supprimer l'ancienne contrainte de priority si elle existe
        await conn.execute("""
            ALTER TABLE tasks 
            DROP CONSTRAINT IF EXISTS check_priority_range;
        """)
        
        # Changer le type de priority si nécessaire
        priority_type = next((col['data_type'] for col in columns if col['column_name'] == 'priority'), None)
        if priority_type and priority_type == 'integer':
            # Convertir priority de integer à string
            await conn.execute("""
                ALTER TABLE tasks 
                ALTER COLUMN priority TYPE VARCHAR(20) 
                USING CASE 
                    WHEN priority <= 3 THEN 'low' 
                    WHEN priority <= 6 THEN 'medium' 
                    WHEN priority <= 8 THEN 'high' 
                    ELSE 'critical' 
                END;
            """)
            print("✅ Type de priority converti en string")
        
        # Ajouter la nouvelle contrainte
        await conn.execute("""
            ALTER TABLE tasks 
            ADD CONSTRAINT check_task_priority 
            CHECK (priority IN ('low', 'medium', 'high', 'critical'));
        """)
        
        # Mettre à jour la contrainte de status
        await conn.execute("""
            ALTER TABLE tasks 
            DROP CONSTRAINT IF EXISTS check_task_status;
        """)
        await conn.execute("""
            ALTER TABLE tasks 
            ADD CONSTRAINT check_task_status_new 
            CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'));
        """)
        
        print("✅ Contraintes mises à jour")
        
        # 5. Vérifier la structure finale
        print("\n5️⃣ Structure finale de la table tasks:")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position;
        """)
        
        for col in final_columns:
            print(f"   - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        print("\n✅ Table tasks corrigée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_tasks_table())