# 🔧 Dépannage - Activation des Agents

## ❌ Erreur "All connection attempts failed"

### Problème
Le script ne peut pas se connecter à l'API depuis l'intérieur du conteneur.

### Solution
Le service `core` n'est pas démarré. Exécutez :

```bash
# 1. Vérifier l'état des services
docker-compose -f docker-compose.dev.yml ps

# 2. Démarrer TOUS les services (y compris core)
docker-compose -f docker-compose.dev.yml up -d

# 3. Attendre 30 secondes

# 4. Vérifier que core est démarré
docker-compose -f docker-compose.dev.yml ps core

# 5. Si core n'est pas "Up", vérifier les logs
docker-compose -f docker-compose.dev.yml logs core
```

## ❌ Le service core ne démarre pas

### Causes possibles

1. **Erreur de migration de base de données**
   ```bash
   # Exécuter les migrations manuellement
   docker-compose -f docker-compose.dev.yml exec core alembic upgrade head
   ```

2. **Port déjà utilisé**
   ```bash
   # Vérifier si le port 8088 est libre
   lsof -i :8088
   # ou
   netstat -an | grep 8088
   ```

3. **Erreur de build**
   ```bash
   # Reconstruire l'image
   docker-compose -f docker-compose.dev.yml build --no-cache core
   ```

## ✅ Script de démarrage complet

Utilisez ce script pour tout démarrer correctement :

```bash
chmod +x start_and_test.sh
./start_and_test.sh
```

## 🔍 Vérifications utiles

### État des services
```bash
docker-compose -f docker-compose.dev.yml ps
```

### Logs du service core
```bash
docker-compose -f docker-compose.dev.yml logs -f core
```

### Test de l'API (depuis l'hôte)
```bash
curl http://localhost:8088/docs
```

### Exécuter un test dans le conteneur
```bash
docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_all_agent_types.py
```

## 📝 Notes importantes

1. **URLs dans les scripts** : Les scripts détectent automatiquement s'ils sont dans Docker
   - Dans Docker : `http://core:8000/api/v1`
   - En local : `http://localhost:8088/api/v1`

2. **Le service core DOIT être démarré** avec `docker-compose up -d`

3. **Port 8088** : C'est le port exposé par docker-compose.dev.yml (pas 8000)