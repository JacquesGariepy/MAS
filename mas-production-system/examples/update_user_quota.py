#!/usr/bin/env python3
"""
Met à jour le quota d'agents de l'utilisateur directement dans la base de données
"""

import psycopg2
from psycopg2 import sql

# Configuration de la base de données
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "mas_db",
    "user": "mas_user",
    "password": "mas_password"
}

def update_user_quota(username: str, new_quota: int):
    """Met à jour le quota d'agents pour un utilisateur"""
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Mettre à jour le quota
        query = sql.SQL("""
            UPDATE users 
            SET agent_quota = %s 
            WHERE username = %s
            RETURNING id, username, agent_quota
        """)
        
        cur.execute(query, (new_quota, username))
        result = cur.fetchone()
        
        if result:
            user_id, username, quota = result
            print(f"✅ Quota mis à jour pour {username}")
            print(f"   ID: {user_id}")
            print(f"   Nouveau quota: {quota}")
            conn.commit()
        else:
            print(f"❌ Utilisateur '{username}' non trouvé")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("📊 Mise à jour du quota d'agents\n")
    
    # Mettre à jour le quota pour test_user
    update_user_quota("test_user", 50)
    
    # Mettre à jour aussi pour test_user2, test_user3, test_user4
    for i in range(2, 5):
        update_user_quota(f"test_user{i}", 50)