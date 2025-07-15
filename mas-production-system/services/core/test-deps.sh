#!/bin/bash
# Script pour tester la résolution des dépendances

echo "🔍 Test de résolution des dépendances..."
echo "======================================="

# Créer un environnement virtuel temporaire
echo "📦 Création d'un environnement virtuel temporaire..."
python3 -m venv test-env
source test-env/bin/activate

# Mettre à jour pip
echo "🔧 Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Tester les dépendances
echo "🧪 Test avec requirements-fixed.txt..."
pip install -r requirements-fixed.txt --dry-run

if [ $? -eq 0 ]; then
    echo "✅ Résolution réussie!"
    echo ""
    echo "📋 Installation réelle..."
    pip install -r requirements-fixed.txt
    
    echo ""
    echo "📊 Versions installées:"
    pip list | grep -E "(fastapi|pydantic|uvicorn|sqlalchemy|redis)"
else
    echo "❌ Échec de la résolution des dépendances"
    echo ""
    echo "🔍 Tentative avec constraints.txt..."
    pip install -r requirements-fixed.txt -c constraints.txt --dry-run
fi

# Nettoyer
deactivate
rm -rf test-env

echo ""
echo "✨ Test terminé"