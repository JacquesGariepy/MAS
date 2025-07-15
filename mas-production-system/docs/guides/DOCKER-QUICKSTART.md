# 🐳 Docker Quick Start Guide

## Pourquoi Docker ?

Avec Docker, vous n'avez **PAS BESOIN** de :
- ❌ Installer Python localement
- ❌ Créer un environnement virtuel
- ❌ Gérer les dépendances avec pip
- ❌ Configurer PostgreSQL ou Redis

Tout est inclus dans les conteneurs ! 🎉

## 🚀 Démarrage Rapide (2 minutes)

### 1. Configuration minimale

```bash
# Créer le fichier .env avec votre clé API
echo "LLM_API_KEY=your-openai-key-here" > .env
```

### 2. Lancer l'application

```bash
# Démarrer tous les services
docker-compose -f docker-compose.dev.yml up

# Ou en arrière-plan
docker-compose -f docker-compose.dev.yml up -d
```

C'est tout ! L'application est maintenant accessible sur http://localhost:8000

## 📋 Commandes Utiles

```bash
# Voir les logs
docker-compose -f docker-compose.dev.yml logs -f

# Voir les logs d'un service spécifique
docker-compose -f docker-compose.dev.yml logs -f core

# Arrêter les services
docker-compose -f docker-compose.dev.yml down

# Arrêter et supprimer les volumes (reset complet)
docker-compose -f docker-compose.dev.yml down -v

# Reconstruire l'image après modification du Dockerfile
docker-compose -f docker-compose.dev.yml build

# Exécuter une commande dans le conteneur
docker-compose -f docker-compose.dev.yml exec core bash
```

## 🔧 Services Disponibles

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | API FastAPI principale |
| Docs | http://localhost:8000/docs | Documentation Swagger |
| PostgreSQL | localhost:5432 | Base de données (user: `user`, pass: `pass`) |
| Redis | localhost:6379 | Cache et message broker |

### Outils optionnels (avec `--profile tools`)

```bash
# Lancer avec les outils d'administration
docker-compose -f docker-compose.dev.yml --profile tools up
```

| Outil | URL | Credentials |
|-------|-----|-------------|
| PgAdmin | http://localhost:5050 | admin@mas.local / admin |
| RedisInsight | http://localhost:8001 | - |

## 🛠️ Développement avec Docker

### Hot Reload Automatique

Les fichiers sources sont montés en volume, donc toute modification dans :
- `services/core/src/` 
- `services/core/alembic/`

Est automatiquement rechargée sans redémarrer Docker !

### Débugger dans le Conteneur

```bash
# Accéder au shell du conteneur
docker-compose -f docker-compose.dev.yml exec core bash

# Une fois dans le conteneur
python -m pytest  # Lancer les tests
alembic history   # Voir l'historique des migrations
```

### Voir les Logs en Temps Réel

```bash
# Tous les services
docker-compose -f docker-compose.dev.yml logs -f

# Seulement l'API
docker-compose -f docker-compose.dev.yml logs -f core
```

## 🔍 Troubleshooting

### Port déjà utilisé
```bash
# Erreur: bind: address already in use
# Solution: Changer le port dans docker-compose.dev.yml
ports:
  - "8001:8000"  # Utiliser 8001 au lieu de 8000
```

### Database connection refused
```bash
# Attendre que la DB soit prête
docker-compose -f docker-compose.dev.yml logs db

# Vérifier l'état
docker-compose -f docker-compose.dev.yml ps
```

### Rebuild après changement de requirements.txt
```bash
docker-compose -f docker-compose.dev.yml build --no-cache core
docker-compose -f docker-compose.dev.yml up
```

## 🎯 Workflow de Développement Recommandé

1. **Éditer le code** dans votre IDE favori
2. **Voir les changements** instantanément (hot reload)
3. **Consulter les logs** : `docker-compose logs -f core`
4. **Tester l'API** : http://localhost:8000/docs

## 🔗 Intégration avec LM Studio

Si vous utilisez LM Studio localement :

```bash
# Dans .env
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_API_KEY=not-needed
```

`host.docker.internal` permet au conteneur d'accéder à votre machine hôte.

## 📊 Monitoring

```bash
# Statistiques des conteneurs
docker stats

# Santé des services
docker-compose -f docker-compose.dev.yml ps
```

---

**Rappel** : Avec Docker, tout est isolé et reproductible. Pas besoin de toucher à votre système ! 🐳