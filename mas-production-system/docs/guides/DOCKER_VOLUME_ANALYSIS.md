# Analyse Configuration Docker MAS - Volumes et Permissions

## Vue d'ensemble de la configuration Docker

Le système MAS utilise Docker Compose pour orchestrer plusieurs services avec des volumes montés permettant le développement hot-reload et la persistance des données.

## Services et Volumes

### 1. Service Core (Application principale)

**Configuration dans docker-compose.dev.yml:**
```yaml
core:
  build:
    context: ./services/core
    dockerfile: Dockerfile.dev
  ports:
    - "8088:8000"
  volumes:
    - ./services/core/src:/app/src      # Code source
    - ./services/core/alembic.ini:/app/alembic.ini  # Config migrations
    - ./logs:/app/logs                  # Logs partagés
    - ./examples:/app/examples          # Scripts de test
```

**Analyse des volumes:**
- `/app/src` : Code source monté en lecture/écriture avec hot-reload
- `/app/logs` : Répertoire de logs partagé entre host et container
- `/app/examples` : Scripts d'exemple accessibles depuis le container
- `/app/alembic.ini` : Fichier de configuration des migrations DB

### 2. Service Database (PostgreSQL)

**Configuration:**
```yaml
db:
  image: postgres:15-alpine
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

**Volume nommé** : `postgres-data` pour la persistance des données

### 3. Service Redis

**Configuration:**
```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis-data:/data
```

**Volume nommé** : `redis-data` pour la persistance du cache

## Mapping des Répertoires Host ↔ Container

| Répertoire Host | Répertoire Container | Type | Usage |
|-----------------|---------------------|------|-------|
| `./services/core/src` | `/app/src` | Bind mount | Code source avec hot-reload |
| `./logs` | `/app/logs` | Bind mount | Logs partagés |
| `./examples` | `/app/examples` | Bind mount | Scripts de test/démo |
| `./services/core/alembic.ini` | `/app/alembic.ini` | Bind mount | Config migrations |

## Permissions et Accessibilité

### Permissions observées:

1. **Sur l'hôte (WSL2):**
   - Tous les répertoires : `drwxrwxrwx` (777)
   - Propriétaire : `admlocal:admlocal`
   - UID/GID : 1000:1000

2. **Dans le container:**
   - User : `root` (UID 0)
   - `/app` : propriété root avec permissions 755
   - Volumes montés : conservent les permissions de l'hôte (777)

### Tests d'écriture effectués:

✅ **Écriture réussie dans:**
- `/app/logs` : Les agents peuvent créer des fichiers de log
- `/app/examples` : Les agents peuvent créer des scripts
- `/app/agent_workspace` : Nouveau répertoire créé avec succès

## Zones d'écriture pour les Agents

Les agents MAS peuvent écrire dans les zones suivantes:

### 1. **Logs** (`/app/logs`)
- Fichiers de log des agents autonomes
- Rapports d'exécution (format Markdown)
- Traces d'activité

**Exemple de fichiers créés:**
```
autonomous_agent_20250718_140047.log
rapport_c667a166-7b3c-4b4e-96be-51f1f810bd1f_20250718_144336.md
```

### 2. **Examples** (`/app/examples`)
- Scripts de démonstration générés
- Cas de test créés dynamiquement
- Exemples de code produits par les agents

### 3. **Agent Workspace** (à créer)
Recommandation : Créer un volume dédié pour l'espace de travail des agents:

```yaml
volumes:
  - ./agent_workspace:/app/agent_workspace
```

Cela permettrait aux agents de:
- Stocker des fichiers temporaires
- Créer des projets générés
- Sauvegarder des artefacts de travail

### 4. **Répertoires système** (non recommandé)
Les agents ont techniquement accès root dans le container, mais devraient éviter:
- `/app/src` : Code source de l'application
- `/app/alembic` : Fichiers de migration
- Répertoires système (`/etc`, `/usr`, etc.)

## Configuration Docker de développement

**Dockerfile.dev principales caractéristiques:**
- Base image : `python:3.11-slim`
- Working directory : `/app`
- User : `root` (par défaut)
- Création du répertoire logs : `RUN mkdir -p /app/logs`

## Recommandations d'amélioration

### 1. Sécurité - Utiliser un utilisateur non-root
```dockerfile
# Dans Dockerfile.dev
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser
```

### 2. Volume dédié pour les agents
```yaml
# Dans docker-compose.dev.yml
volumes:
  - ./agent_workspace:/app/agent_workspace
  - ./agent_projects:/app/projects
```

### 3. Permissions explicites
```yaml
# Script d'initialisation
command: >
  sh -c "
    mkdir -p /app/agent_workspace /app/projects
    chmod 755 /app/agent_workspace /app/projects
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
  "
```

### 4. Variables d'environnement pour les chemins
```yaml
environment:
  - AGENT_WORKSPACE_PATH=/app/agent_workspace
  - AGENT_LOGS_PATH=/app/logs
  - AGENT_PROJECTS_PATH=/app/projects
```

## Conclusion

La configuration Docker actuelle permet aux agents d'écrire dans plusieurs répertoires grâce aux volumes montés. Les permissions sont très permissives (777) ce qui facilite le développement mais devrait être restreint en production. Les agents peuvent créer des fichiers dans `/app/logs` et `/app/examples`, et ont la capacité de créer de nouveaux répertoires dans le container.

Pour une meilleure organisation, il est recommandé de créer des volumes dédiés aux espaces de travail des agents plutôt que de les laisser écrire n'importe où dans le système de fichiers du container.