# 🚀 Guide Rapide - Activation de TOUS les Types d'Agents

## 📋 Commandes Rapides (Développement avec Docker)

### 1. Utiliser le script de test automatisé
```bash
# Méthode recommandée - tout est dans Docker
chmod +x test_agents_dev.sh
./test_agents_dev.sh
```

### 2. Ou manuellement avec docker-compose de développement
```bash
# Redémarrer avec le docker-compose de développement
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build

# Attendre 30 secondes

# Exécuter les tests DANS le conteneur (pas besoin d'installer httpx localement)
docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_all_agent_types.py
```

### 3. L'API est accessible sur le port 8088
```
http://localhost:8088/docs
```

## 🎯 Résultat Attendu

Si tout fonctionne correctement, vous devriez voir :

```
📊 Résumé des agents créés:
   - Total: 6
   - Cognitifs (reactive): 2
   - Réflexifs: 2
   - Hybrides: 2

✅ Message envoyé: Cognitive -> Reflexive
✅ Message envoyé: Reflexive -> Hybrid
✅ Message envoyé: Hybrid -> Cognitive

🎉 SUCCÈS: Tous les types d'agents sont maintenant fonctionnels!
```

## ⚠️ Troubleshooting

### Erreur "ModuleNotFoundError: No module named 'httpx'"
```bash
pip3 install httpx==0.25.2
```

### Erreur "L'API MAS n'est pas accessible"
```bash
# Vérifier que les conteneurs sont en cours d'exécution
docker-compose ps

# Redémarrer si nécessaire
docker-compose down
docker-compose up -d
```

### Erreur 500 lors de la création d'agents
```bash
# Le serveur n'a pas été redémarré après l'ajout des nouveaux types
docker-compose restart core

# Vérifier les logs
docker-compose logs -f core
```

## 📝 Scripts de Test Disponibles

1. **test_all_agent_types.py** - Test complet de tous les types
2. **test_message_endpoint_simple.py** - Test simple du endpoint de messages
3. **mas_complete_cycle_demo_fixed.py** - Démo complète du cycle MAS
4. **test_agent_factory.py** - Test unitaire de la factory d'agents

## 🔍 Vérification Manuelle

Pour vérifier manuellement que tout fonctionne :

1. Accéder à la documentation API : http://localhost:8000/docs
2. Créer un utilisateur via `/auth/register`
3. Se connecter via `/auth/login`
4. Créer des agents avec différents types :
   - `agent_type: "reactive"` (cognitif)
   - `agent_type: "reflexive"` (règles)
   - `agent_type: "hybrid"` (adaptatif)
5. Envoyer des messages via `POST /api/v1/agents/{agent_id}/messages`