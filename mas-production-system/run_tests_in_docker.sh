#!/bin/bash

echo "🐳 Exécution des tests dans le conteneur Docker"
echo "=============================================="

# 1. Redémarrer les conteneurs pour charger les nouveaux volumes et code
echo ""
echo "🔄 Redémarrage des conteneurs Docker..."
docker-compose down
docker-compose up -d --build

# 2. Attendre que les services soient prêts
echo ""
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

# 3. Vérifier l'état des services
echo ""
echo "🔍 Vérification de l'état des services..."
docker-compose ps

# 4. Exécuter le test dans le conteneur
echo ""
echo "🧪 Exécution du test des types d'agents dans le conteneur..."
echo ""
docker-compose exec core python /app/examples/test_all_agent_types.py

echo ""
echo "✅ Test terminé !"
echo ""
echo "Pour exécuter d'autres tests dans le conteneur :"
echo "  docker-compose exec core python /app/examples/test_message_endpoint_simple.py"
echo "  docker-compose exec core python /app/examples/mas_complete_cycle_demo_fixed.py"
echo ""
echo "Pour voir les logs du serveur :"
echo "  docker-compose logs -f core"