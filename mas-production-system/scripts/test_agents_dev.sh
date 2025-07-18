#!/bin/bash

echo "🚀 Test de TOUS les types d'agents avec Docker Dev"
echo "=================================================="
echo ""

# Utiliser le docker-compose de développement
COMPOSE_FILE="docker-compose.dev.yml"

echo "📋 Utilisation de $COMPOSE_FILE"
echo ""

# 1. Arrêter les services existants
echo "🛑 Arrêt des services existants..."
docker-compose -f $COMPOSE_FILE down
docker-compose down  # Arrêter aussi l'autre si actif

# 2. Construire avec le Dockerfile de développement
echo ""
echo "🔨 Construction du conteneur de développement..."
docker-compose -f $COMPOSE_FILE build core

# 3. Démarrer les services
echo ""
echo "🚀 Démarrage des services..."
docker-compose -f $COMPOSE_FILE up -d

# 4. Attendre que tout soit prêt
echo ""
echo "⏳ Attente du démarrage complet..."
echo "   Note: L'API sera disponible sur le port 8088"
for i in {30..1}; do
    echo -ne "\r   $i secondes restantes..."
    sleep 1
done
echo -e "\r   ✅ Services démarrés !      "

# 5. Exécuter les migrations
echo ""
echo "🗄️ Exécution des migrations de base de données..."
docker-compose -f $COMPOSE_FILE exec core alembic upgrade head

# 6. Vérifier que l'API est accessible
echo ""
echo "🔍 Vérification de l'API sur le port 8088..."
curl -s http://localhost:8088/docs > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API accessible sur http://localhost:8088"
else
    echo "❌ API non accessible"
    echo "Vérifiez les logs avec: docker-compose -f $COMPOSE_FILE logs core"
    exit 1
fi

# 7. Exécuter les tests dans le conteneur
echo ""
echo "🧪 Exécution des tests..."
echo ""

# Test de la factory d'agents (local au conteneur)
echo "=== Test 1: Factory d'agents (interne) ==="
docker-compose -f $COMPOSE_FILE exec core python -c "
import sys
sys.path.append('/app')
from src.agents.agent_factory import AgentFactory
from uuid import uuid4

print('Types d\'agents disponibles:', AgentFactory.get_available_types())

# Test cognitive
cognitive = AgentFactory.create_agent(
    agent_type='reactive',
    agent_id=uuid4(),
    name='TestCognitive',
    role='Tester'
)
print(f'✅ Agent cognitif créé: {cognitive.__class__.__name__}')

# Test reflexive
reflexive = AgentFactory.create_agent(
    agent_type='reflexive',
    agent_id=uuid4(),
    name='TestReflexive',
    role='Tester',
    reactive_rules={'test': {'condition': {}, 'action': {}}}
)
print(f'✅ Agent réflexif créé: {reflexive.__class__.__name__}')

# Test hybrid
hybrid = AgentFactory.create_agent(
    agent_type='hybrid',
    agent_id=uuid4(),
    name='TestHybrid',
    role='Tester'
)
print(f'✅ Agent hybride créé: {hybrid.__class__.__name__}')
"

echo ""
echo "=== Test 2: API et Messages ==="
docker-compose -f $COMPOSE_FILE exec core python /app/examples/test_message_endpoint_simple.py

echo ""
echo "=== Test 3: Test complet de tous les agents ==="
docker-compose -f $COMPOSE_FILE exec core python /app/examples/test_all_agent_types.py

echo ""
echo "✅ Tests terminés !"
echo ""
echo "📝 Commandes utiles :"
echo "  - Voir les logs: docker-compose -f $COMPOSE_FILE logs -f core"
echo "  - Exécuter la démo: docker-compose -f $COMPOSE_FILE exec core python /app/examples/mas_complete_cycle_demo_fixed.py"
echo "  - Accéder à l'API: http://localhost:8088/docs"
echo "  - Arrêter les services: docker-compose -f $COMPOSE_FILE down"
echo ""
echo "🔧 Services optionnels (avec --profile tools) :"
echo "  - PgAdmin: http://localhost:5050 (admin@mas.local / admin)"
echo "  - RedisInsight: http://localhost:8001"