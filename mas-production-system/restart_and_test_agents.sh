#!/bin/bash

echo "🔄 Redémarrage du service avec les corrections"
echo "=============================================="
echo ""

# 1. Redémarrer juste le service core pour charger les changements
echo "🔄 Redémarrage du service core..."
docker-compose -f docker-compose.dev.yml restart core

# 2. Attendre que le service soit prêt
echo ""
echo "⏳ Attente du redémarrage (20 secondes)..."
for i in {20..1}; do
    echo -ne "\r   $i secondes restantes..."
    sleep 1
done
echo -e "\r   ✅ Service redémarré !      "

# 3. Test direct de la factory
echo ""
echo "🧪 Test 1: Factory d'agents (direct)"
echo "------------------------------------"
docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_direct_factory.py

# 4. Test API simple
echo ""
echo "🧪 Test 2: API Simple"
echo "--------------------"
docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_api_simple.py

# 5. Test complet
echo ""
echo "🧪 Test 3: Test Complet de Tous les Agents"
echo "-----------------------------------------"
docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_all_agent_types.py

echo ""
echo "✅ Tests terminés !"
echo ""
echo "Si les agents ne se créent toujours pas, vérifiez les logs :"
echo "docker-compose -f docker-compose.dev.yml logs --tail=50 core | grep -i error"