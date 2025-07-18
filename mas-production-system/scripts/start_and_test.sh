#!/bin/bash

echo "🚀 Démarrage et test du système MAS avec tous les agents"
echo "========================================================"
echo ""

COMPOSE_FILE="docker-compose.dev.yml"

# 1. Vérifier l'état actuel
echo "📊 État actuel des services :"
docker-compose -f $COMPOSE_FILE ps

# 2. Démarrer TOUS les services (y compris core)
echo ""
echo "🔄 Démarrage de tous les services..."
docker-compose -f $COMPOSE_FILE up -d

# 3. Attendre que core soit prêt
echo ""
echo "⏳ Attente du démarrage du service core..."
for i in {30..1}; do
    echo -ne "\r   $i secondes restantes..."
    sleep 1
done
echo -e "\r   ✅ Services démarrés !      "

# 4. Vérifier que core est bien démarré
echo ""
echo "🔍 Vérification des services :"
docker-compose -f $COMPOSE_FILE ps

# 5. Vérifier les logs de core pour voir s'il y a des erreurs
echo ""
echo "📋 Dernières lignes des logs de core :"
docker-compose -f $COMPOSE_FILE logs --tail=20 core

# 6. Tester la connexion à l'API
echo ""
echo "🌐 Test de l'API..."
curl -s http://localhost:8088/docs > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API accessible sur http://localhost:8088"
    
    # 7. Exécuter le test
    echo ""
    echo "🧪 Exécution du test des agents..."
    docker-compose -f $COMPOSE_FILE exec core python /app/examples/test_all_agent_types.py
else
    echo "❌ API non accessible"
    echo ""
    echo "🔍 Vérification du statut du conteneur core :"
    docker-compose -f $COMPOSE_FILE ps core
    echo ""
    echo "📋 Logs d'erreur de core :"
    docker-compose -f $COMPOSE_FILE logs core | grep -i error
fi