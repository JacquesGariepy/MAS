#!/bin/bash

echo "📋 Derniers logs d'erreur du service core :"
echo "=========================================="
echo ""

# Afficher les 50 dernières lignes des logs, en filtrant les erreurs
docker-compose -f docker-compose.dev.yml logs --tail=50 core | grep -E "(ERROR|Failed|Exception|Traceback)" -A 5 -B 2

echo ""
echo "Pour voir tous les logs en temps réel :"
echo "docker-compose -f docker-compose.dev.yml logs -f core"