# Guide de Développement - MAS Production System

## 🚀 Configuration de l'Environnement de Développement

### Prérequis
- Python 3.11+
- Docker et Docker Compose
- PostgreSQL 15+
- Redis 7+
- Git

### Installation Rapide

1. **Cloner le repository**
```bash
git clone <repository-url>
cd mas-production-system
```

2. **Créer un environnement virtuel Python**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
cd services/core
pip install -r requirements.txt
pip install -e .  # Installation en mode développement
```

4. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Lancer les services de base**
```bash
# Depuis la racine du projet
docker-compose up -d db redis
```

6. **Exécuter les migrations**
```bash
cd services/core
alembic upgrade head
```

7. **Lancer l'application**
```bash
# Mode développement avec rechargement automatique
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Structure du Projet

```
mas-production-system/
├── services/
│   └── core/                    # Service principal
│       ├── src/
│       │   ├── api/             # Endpoints REST
│       │   ├── core/            # Logique métier (agents)
│       │   ├── database/        # Modèles et connexion DB
│       │   ├── middleware/      # Sécurité, logging, etc.
│       │   ├── schemas/         # Schémas Pydantic
│       │   ├── services/        # Services (LLM, embeddings, etc.)
│       │   ├── tools/           # Outils pour agents
│       │   └── utils/           # Utilitaires
│       ├── tests/               # Tests unitaires
│       ├── alembic/             # Migrations DB
│       └── requirements.txt     # Dépendances Python
├── infrastructure/              # IaC (Terraform, K8s)
├── scripts/                     # Scripts de déploiement
├── docs/                        # Documentation
└── docker-compose.yml          # Config Docker local
```

## 🔧 Configuration

### Variables d'Environnement Essentielles

```env
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mas_db

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM (choisir un provider)
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4-turbo-preview

# Ou pour LM Studio (local)
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
```

## 🧪 Tests

### Exécuter les Tests
```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_auth.py -v

# Tests marqués
pytest -m "not slow"  # Exclure les tests lents
```

### Structure des Tests
- `tests/test_*.py` - Tests unitaires
- `tests/integration/` - Tests d'intégration
- `tests/e2e/` - Tests end-to-end

## 🛠️ Développement

### Standards de Code
- **Formatter**: Black (`black src/`)
- **Linter**: Flake8 (`flake8 src/`)
- **Type Checker**: MyPy (`mypy src/`)

### Commandes Make Utiles
```bash
make install      # Installer les dépendances
make test         # Lancer les tests
make lint         # Vérifier le code
make format       # Formater le code
make run          # Lancer l'application
make docker-build # Construire l'image Docker
```

### Workflow Git
1. Créer une branche feature: `git checkout -b feature/ma-feature`
2. Commiter avec messages clairs
3. Pousser et créer une PR
4. Attendre la review et les tests CI

## 🐛 Debugging

### Logs
- Application: `logs/app.log`
- Accès: Structurés en JSON
- Niveau: Configurable via `LOG_LEVEL`

### Outils de Debug
```python
# Breakpoint Python
import pdb; pdb.set_trace()

# Ou avec IPython
import IPython; IPython.embed()
```

### Monitoring Local
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Health: http://localhost:8000/health

## 🚀 Lancer un Swarm d'Agents

### Via API
```bash
# Créer un agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DevAgent",
    "role": "developer",
    "agent_type": "cognitive",
    "capabilities": ["code_generate", "code_test"]
  }'

# Démarrer l'agent
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/start
```

### Via Code Python
```python
from src.core.agents import AgentFactory, get_agent_runtime

# Créer et démarrer un agent
agent = AgentFactory.create_agent(
    agent_type="cognitive",
    agent_id=uuid4(),
    name="MyAgent",
    role="assistant",
    capabilities=["analyze", "generate"]
)

runtime = get_agent_runtime()
await runtime.start_agent(agent)
```

## 📚 Documentation des Modules

### Auth (`src/auth.py`)
- Authentification JWT
- Gestion des utilisateurs
- Vérification des quotas

### Cache (`src/cache.py`)
- Client Redis async
- Opérations get/set/delete
- TTL et expiration

### Database (`src/database/`)
- SQLAlchemy async
- Modèles: User, Agent, Organization, Message
- Migrations Alembic

### Services
- **LLMService**: Intégration avec OpenAI/LM Studio
- **EmbeddingService**: Recherche sémantique avec FAISS
- **ToolService**: Gestion des outils d'agents

### Agents
- **BaseAgent**: Classe abstraite BDI
- **CognitiveAgent**: Agent avec raisonnement LLM
- **AgentFactory**: Création d'agents
- **AgentRuntime**: Gestion du cycle de vie

## 🔒 Sécurité

### Authentification
- JWT pour les API
- API Keys pour les intégrations
- Rate limiting configurable

### Best Practices
- Ne jamais commiter de secrets
- Utiliser des variables d'environnement
- Valider toutes les entrées
- Sanitizer les sorties

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

### Checklist PR
- [ ] Tests passent
- [ ] Code formaté (Black)
- [ ] Lint clean (Flake8)
- [ ] Documentation à jour
- [ ] Changelog mis à jour

## 📞 Support

- Issues: GitHub Issues
- Documentation: `/docs`
- Logs: Vérifier `logs/app.log`
- Monitoring: Prometheus/Grafana

## 🎯 Troubleshooting

### Erreurs Communes

1. **ImportError**: Vérifier le PYTHONPATH
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/services/core
```

2. **Database Connection**: Vérifier PostgreSQL
```bash
docker-compose ps
docker-compose logs db
```

3. **Redis Connection**: Vérifier Redis
```bash
docker-compose exec redis redis-cli ping
```

4. **LLM Timeout**: Augmenter le timeout
```python
LLM_TIMEOUT=120  # secondes
```

## 📈 Performance

### Optimisations
- Connection pooling (DB/Redis)
- Async/await partout
- Caching des embeddings
- Batch processing

### Profiling
```python
# Avec cProfile
python -m cProfile -o profile.stats src/main.py

# Analyser avec snakeviz
snakeviz profile.stats
```

---

Pour plus d'informations, consulter la documentation complète dans `/docs`.