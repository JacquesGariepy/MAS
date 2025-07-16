#!/usr/bin/env python3
"""
Script pour installer les dépendances nécessaires aux exemples
"""

import subprocess
import sys

def install_package(package):
    """Installer un package Python"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    print("📦 Installation des dépendances pour les exemples MAS...")
    print("-" * 50)
    
    packages = [
        "httpx==0.25.2",
        "asyncio",
        "pydantic==2.5.3"
    ]
    
    for package in packages:
        try:
            print(f"Installation de {package}...")
            install_package(package)
            print(f"✅ {package} installé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'installation de {package}: {e}")
    
    print("\n✅ Installation terminée !")
    print("\nVous pouvez maintenant exécuter les scripts de test :")
    print("  python3 test_all_agent_types.py")
    print("  python3 mas_complete_cycle_demo_fixed.py")

if __name__ == "__main__":
    main()