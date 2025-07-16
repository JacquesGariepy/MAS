#!/bin/bash

echo "🔍 Vérification des services Docker..."
echo ""

# Vérifier les conteneurs en cours
echo "📦 Conteneurs en cours d'exécution :"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📋 Tous les conteneurs (y compris arrêtés) :"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔧 Pour démarrer le service core :"
echo "  docker-compose -f docker-compose.dev.yml up -d core"
echo ""
echo "📊 Pour voir les logs du core :"
echo "  docker-compose -f docker-compose.dev.yml logs core"