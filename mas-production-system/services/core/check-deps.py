#!/usr/bin/env python3
"""
Script pour vérifier les conflits de dépendances
"""
import subprocess
import sys

def check_dependency_conflicts():
    """Vérifie les conflits de dépendances avec pip-compile"""
    print("🔍 Analyse des dépendances...")
    
    # Essayer d'installer pip-tools
    subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools"], capture_output=True)
    
    # Créer un requirements.in avec les dépendances de base
    with open("requirements.in", "w") as f:
        f.write("""# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
redis==5.0.1
aioredis==2.0.1
alembic==1.13.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.2
pyyaml==6.0.1
prometheus_client==0.19.0
""")
    
    print("\n📦 Résolution des dépendances avec pip-compile...")
    result = subprocess.run(
        [sys.executable, "-m", "piptools", "compile", "requirements.in", "-o", "requirements-resolved.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Dépendances résolues avec succès!")
        print("\n📄 Fichier requirements-resolved.txt créé")
        with open("requirements-resolved.txt", "r") as f:
            print(f.read()[:500] + "...")
    else:
        print("❌ Erreur lors de la résolution:")
        print(result.stderr)

if __name__ == "__main__":
    check_dependency_conflicts()