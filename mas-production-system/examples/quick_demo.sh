#!/bin/bash
# Exemple rapide d'utilisation de l'API MAS avec curl
# Assurez-vous que l'API est en cours d'exécution sur http://localhost:8088

API_URL="http://localhost:8088"
USERNAME="demo_user"
EMAIL="demo@example.com"
PASSWORD="demo_password_123"

echo "🚀 Démonstration rapide MAS v2.0"
echo "================================"

# 1. Enregistrer un utilisateur
echo -e "\n1️⃣ Création de l'utilisateur..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "'$USERNAME'",
    "email": "'$EMAIL'",
    "password": "'$PASSWORD'"
  }')

echo "Réponse: $REGISTER_RESPONSE"

# 2. Se connecter et obtenir un token
echo -e "\n2️⃣ Connexion..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
echo "Token obtenu: ${TOKEN:0:20}..."

# 3. Créer un agent
echo -e "\n3️⃣ Création d'un agent..."
AGENT_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/agents/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent Assistant",
    "role": "Assistant intelligent pour démonstration",
    "agent_type": "COGNITIVE",
    "capabilities": ["chat", "analysis", "planning"],
    "initial_beliefs": {
      "language": "français",
      "purpose": "démonstration"
    },
    "initial_desires": ["aider", "apprendre"],
    "configuration": {
      "llm_model": "qwen3:4b",
      "temperature": 0.7
    },
    "organization_id": null
  }')

AGENT_ID=$(echo $AGENT_RESPONSE | grep -o '"id":"[^"]*' | sed 's/"id":"//')
echo "Agent créé avec ID: $AGENT_ID"

# 4. Démarrer l'agent
echo -e "\n4️⃣ Démarrage de l'agent..."
START_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/agents/agents/$AGENT_ID/start" \
  -H "Authorization: Bearer $TOKEN")
echo "Status: $(echo $START_RESPONSE | grep -o '"status":"[^"]*' | sed 's/"status":"//')"

# 5. Ajouter une mémoire
echo -e "\n5️⃣ Ajout d'une mémoire à l'agent..."
MEMORY_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/agents/agents/$AGENT_ID/memories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Je suis un agent de démonstration créé pour montrer les capacités du système MAS",
    "memory_type": "belief",
    "importance": 0.9
  }')
echo "Mémoire ajoutée"

# 6. Créer une tâche (requête) pour l'agent
echo -e "\n6️⃣ Envoi d'une requête à l'agent..."
TASK_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tasks/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Question de démonstration",
    "description": "Bonjour, peux-tu expliquer ce qu est un système multi-agents ?",
    "task_type": "query",
    "priority": "high",
    "assigned_to": "'$AGENT_ID'"
  }')

TASK_ID=$(echo $TASK_RESPONSE | grep -o '"id":"[^"]*' | sed 's/"id":"//')
echo "Tâche créée avec ID: $TASK_ID"

# 7. Attendre et récupérer le résultat
echo -e "\n7️⃣ Récupération du résultat..."
sleep 3
RESULT_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/tasks/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Status de la tâche: $(echo $RESULT_RESPONSE | grep -o '"status":"[^"]*' | sed 's/"status":"//')"
echo "Résultat: $(echo $RESULT_RESPONSE | grep -o '"result":"[^"]*' | sed 's/"result":"//')"

# 8. Obtenir les métriques
echo -e "\n8️⃣ Métriques de l'agent..."
METRICS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/agents/agents/$AGENT_ID/metrics" \
  -H "Authorization: Bearer $TOKEN")
echo "Métriques: $METRICS_RESPONSE"

echo -e "\n✅ Démonstration terminée !"