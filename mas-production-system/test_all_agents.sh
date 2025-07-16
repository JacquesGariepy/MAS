#!/bin/bash

echo "🚀 Test de TOUS les types d'agents MAS v2.0"
echo "==========================================="
echo ""
echo "Ce script va :"
echo "1. Reconstruire les conteneurs avec les nouveaux types d'agents"
echo "2. Exécuter les tests depuis l'intérieur du conteneur Docker"
echo ""

# 1. Rebuild avec le Dockerfile de développement
echo "🔨 Reconstruction des conteneurs..."
docker-compose down
docker-compose build --no-cache core

# 2. Démarrer les services
echo ""
echo "🚀 Démarrage des services..."
docker-compose up -d

# 3. Attendre que tout soit prêt
echo ""
echo "⏳ Attente du démarrage complet (30 secondes)..."
for i in {30..1}; do
    echo -ne "\r   $i secondes restantes..."
    sleep 1
done
echo -e "\r   ✅ Prêt !                    "

# 4. Vérifier que l'API est accessible
echo ""
echo "🔍 Vérification de l'API..."
docker-compose exec core curl -s http://localhost:8000/docs > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API accessible"
else
    echo "❌ API non accessible"
    echo "Vérifiez les logs avec: docker-compose logs core"
    exit 1
fi

# 5. Exécuter les tests
echo ""
echo "🧪 Exécution des tests..."
echo ""

# Test 1: Factory d'agents
echo "=== Test 1: Factory d'agents ==="
docker-compose exec core python /app/examples/test_agent_factory.py

echo ""
echo "=== Test 2: Endpoint de messages simple ==="
docker-compose exec core python /app/examples/test_message_endpoint_simple.py

echo ""
echo "=== Test 3: Test complet de tous les types d'agents ==="
docker-compose exec core python /app/examples/test_all_agent_types.py

echo ""
echo "✅ Tests terminés !"
echo ""
echo "Pour exécuter la démo complète :"
echo "  docker-compose exec core python /app/examples/mas_complete_cycle_demo_fixed.py"
echo ""
echo "Pour voir les logs en temps réel :"
echo "  docker-compose logs -f core"