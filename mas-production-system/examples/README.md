# 📚 Exemples d'utilisation du système MAS v2.0

Ce dossier contient plusieurs exemples pour vous aider à démarrer avec le système Multi-Agents.

## 🚀 Prérequis

Assurez-vous que l'API MAS est en cours d'exécution :

```bash
cd ..
docker-compose -f docker-compose.dev.yml up -d
```

L'API doit être accessible sur : http://localhost:8088/docs

## 📂 Exemples disponibles

### 1. `simple_agent_example.py` - Exemple Python simple

L'exemple le plus direct pour commencer. Montre :
- Création d'un utilisateur
- Authentification
- Création d'un agent
- Envoi d'une question
- Récupération de la réponse

**Utilisation :**
```bash
python simple_agent_example.py
```

### 2. `agent_demo.py` - Démonstration complète

Exemple avancé avec client asynchrone. Démontre :
- Gestion complète du cycle de vie d'un agent
- Ajout de mémoires
- Envoi de multiples requêtes
- Récupération des métriques
- Gestion des erreurs

**Utilisation :**
```bash
python agent_demo.py
```

### 3. `quick_demo.sh` - Script bash avec curl

Pour tester rapidement l'API sans Python. Utilise curl pour :
- Créer un utilisateur et s'authentifier
- Créer et démarrer un agent
- Envoyer une requête
- Afficher les résultats

**Utilisation :**
```bash
./quick_demo.sh
```

## 📝 Flux typique d'utilisation

1. **Authentification**
   ```python
   # Créer utilisateur
   POST /auth/register
   
   # Se connecter
   POST /auth/token
   ```

2. **Création d'agent**
   ```python
   # Créer agent avec configuration
   POST /api/v1/agents/agents
   
   # Démarrer l'agent
   POST /api/v1/agents/agents/{id}/start
   ```

3. **Interaction avec l'agent**
   ```python
   # Créer une tâche (question)
   POST /api/v1/tasks/tasks
   
   # Récupérer la réponse
   GET /api/v1/tasks/tasks/{id}
   ```

## 🔧 Configuration des agents

Les agents peuvent être de différents types :
- `COGNITIVE` : Pour le traitement du langage et raisonnement
- `REACTIVE` : Pour des réponses rapides à des stimuli
- `DELIBERATIVE` : Pour la planification complexe
- `HYBRID` : Combinaison des approches

## 💡 Conseils

1. **Token JWT** : Le token expire après un certain temps. Reconnectez-vous si nécessaire.

2. **Types de tâches** : 
   - `query` : Questions directes
   - `analysis` : Analyse de données
   - `planning` : Planification
   - `execution` : Actions

3. **Mémoires** : Les agents peuvent stocker différents types de mémoires :
   - `belief` : Croyances sur le monde
   - `experience` : Expériences passées
   - `preference` : Préférences utilisateur
   - `knowledge` : Connaissances factuelles

## 🐛 Résolution de problèmes

Si vous obtenez une erreur :

1. **401 Unauthorized** : Le token a expiré, reconnectez-vous
2. **404 Not Found** : Vérifiez l'URL et l'ID de l'agent
3. **500 Server Error** : Vérifiez les logs Docker : `docker logs mas-production-system-core-1`

## 📖 Documentation complète

Pour plus d'informations, consultez :
- API Docs : http://localhost:8088/docs
- Guide d'architecture : `../docs/architecture/README.md`
- Configuration : `../docs/guides/CONFIG-GUIDE.md`