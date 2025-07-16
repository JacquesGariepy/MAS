#!/usr/bin/env python3
"""
Script pour vérifier la structure exacte de la table tasks
"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://mas_user:mas_password@localhost:5433/mas_db"

async def check_structure():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Vérifier les colonnes et leurs contraintes
        columns = await conn.fetch("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position;
        """)
        
        print("📋 Structure de la table tasks:\n")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']: <20} {col['data_type']: <20} {nullable}{default}")
        
        # Vérifier spécifiquement la colonne requirements
        print("\n🔍 Recherche de la colonne 'requirements':")
        req_col = [col for col in columns if col['column_name'] == 'requirements']
        if req_col:
            col = req_col[0]
            print(f"  TROUVÉE: {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        else:
            print("  ❌ Colonne 'requirements' NON TROUVÉE")
        
        # Vérifier les contraintes
        print("\n📌 Contraintes de la table:")
        constraints = await conn.fetch("""
            SELECT 
                conname AS constraint_name,
                pg_get_constraintdef(oid) AS constraint_def
            FROM pg_constraint
            WHERE conrelid = 'tasks'::regclass
            ORDER BY conname;
        """)
        
        for con in constraints:
            print(f"  {con['constraint_name']}: {con['constraint_def']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_structure())