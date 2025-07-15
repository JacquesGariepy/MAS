# Structure du Projet MAS Production System

## Vue d'ensemble
Ce projet implémente un système multi-agents (MAS) v2.0 complet avec architecture BDI, prêt pour la production.

## Structure des fichiers créés

### Racine du projet
- `README.md` - Documentation principale du projet
- `Makefile` - Commandes de build et déploiement
- `docker-compose.yml` - Configuration Docker pour développement local

### Configuration (/config)
- `config.yaml` - Configuration principale de l'application
- `staging.env` - Variables d'environnement pour staging
- `production.env` - Variables d'environnement pour production

### Scripts (/scripts)
- `deploy.sh` - Script de déploiement automatisé
- `health-checks.sh` - Script de vérification de santé

### Infrastructure (/infrastructure)
#### Terraform (/infrastructure/terraform)
- `main.tf` - Configuration infrastructure AWS (VPC, EKS, RDS, etc.)

#### Kubernetes (/infrastructure/kubernetes)
- `/deployments/core-service.yaml` - Déploiement du service principal
- `/monitoring/prometheus-values.yaml` - Configuration Prometheus
- `/monitoring/alerts.yaml` - Règles d'alerting

### Service Core (/services/core)
- `Dockerfile` - Image Docker du service
- `requirements.txt` - Dépendances Python
- `alembic.ini` - Configuration Alembic pour migrations

#### Code source (/services/core/src)
- `main.py` - Point d'entrée FastAPI
- `config.py` - Configuration avec Pydantic
- `cache.py` - Client Redis
- `message_broker.py` - Broker de messages

##### API (/services/core/src/api)
- `agents.py` - Endpoints REST pour agents

##### Core (/services/core/src/core/agents)
- `base_agent.py` - Classe abstraite BDI
- `cognitive_agent.py` - Agent cognitif avec LLM

##### Database (/services/core/src/database)
- `models.py` - Modèles SQLAlchemy

##### Middleware (/services/core/src/middleware)
- `security.py` - Sécurité, auth, rate limiting

##### Schemas (/services/core/src/schemas)
- `agents.py` - Schémas Pydantic

##### Services (/services/core/src/services)
- `agent_service.py` - Logique métier agents

##### Tools (/services/core/src/tools)
- `coding_tools.py` - Outils pour agents coding

##### Utils (/services/core/src/utils)
- `logger.py` - Configuration logging
- `pagination.py` - Utilitaire pagination

##### Migrations (/services/core/src/alembic/versions)
- `001_initial_schema.py` - Schéma initial DB

### Documentation (/docs/api)
- `openapi.yaml` - Spécification OpenAPI complète

### GitHub Actions (/.github/workflows)
Note: Ces fichiers doivent être créés manuellement car ils commencent par un point:
- `ci.yml` - Pipeline CI (lint, test, build, security)
- `cd.yml` - Pipeline CD (deploy staging/prod)

## Fichiers __init__.py créés
Tous les packages Python ont leur fichier `__init__.py` pour être correctement importables.

## Prochaines étapes
1. Copier les workflows CI/CD dans `.github/workflows/`
2. Configurer les secrets GitHub Actions
3. Adapter les variables d'environnement
4. Lancer avec `docker-compose up`
5. Exécuter les migrations: `alembic upgrade head`
6. Déployer avec `make deploy-staging` ou `make deploy-prod`

## Notes importantes
- Le système utilise LM Studio par défaut (configurable)
- PostgreSQL pour persistence, Redis pour cache
- Kubernetes pour orchestration en production
- Terraform pour infrastructure as code
- Monitoring avec Prometheus/Grafana
- Sécurité renforcée (JWT, API keys, rate limiting)