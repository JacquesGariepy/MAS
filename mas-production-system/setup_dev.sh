#!/bin/bash

# Script de configuration de l'environnement de développement MAS

echo "🚀 Configuration de l'environnement de développement MAS..."

# Vérifier si python3-venv est installé
if ! dpkg -l | grep -q python3-venv; then
    echo "⚠️  python3-venv n'est pas installé. Installation requise:"
    echo "   sudo apt update && sudo apt install python3-venv python3-full"
    exit 1
fi

# Créer l'environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "📦 Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Installer les dépendances
echo "📦 Installation des dépendances..."
cd services/core
pip install -r requirements.txt

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  N'oubliez pas de configurer votre fichier .env !"
fi

echo "✅ Configuration terminée !"
echo ""
echo "Pour activer l'environnement virtuel, exécutez :"
echo "   source venv/bin/activate"
echo ""
echo "Pour lancer l'application :"
echo "   cd services/core"
echo "   uvicorn src.main:app --reload"