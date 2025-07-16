#!/bin/bash

echo "🔄 Script de redémarrage et test du système MAS"
echo "=============================================="

# 1. Installer les dépendances pour les exemples
echo ""
echo "📦 Installation des dépendances pour les exemples..."
cd examples
pip3 install -r requirements.txt
cd ..

# 2. Redémarrer les conteneurs Docker
echo ""
echo "🐳 Redémarrage des conteneurs Docker..."
docker-compose down
docker-compose up -d --build

# 3. Attendre que les services soient prêts
echo ""
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

# 4. Vérifier l'état des services
echo ""
echo "🔍 Vérification de l'état des services..."
docker-compose ps

# 5. Vérifier l'API
echo ""
echo "🌐 Vérification de l'API..."
curl -s http://localhost:8000/docs > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API accessible sur http://localhost:8000"
else
    echo "❌ API non accessible"
    echo "Vérifiez les logs avec: docker-compose logs -f core"
    exit 1
fi

# 6. Exécuter le test
echo ""
echo "🧪 Exécution du test des types d'agents..."
echo ""
cd examples
python3 test_all_agent_types.py

echo ""
echo "✅ Script terminé !"