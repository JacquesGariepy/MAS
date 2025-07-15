# Guide d'utilisation des Agents et Swarms MAS

Ce guide explique comment lancer des agents et des swarms dans le système MAS pour chaque mode de développement.

## 📋 Prérequis

1. Avoir exécuté `./scripts/setup_dev.sh` avec succès
2. Les services doivent être en cours d'exécution
3. L'API doit être accessible sur `http://localhost:8000`

## 🚀 Mode 1 : Docker (Tout en conteneurs)

### Vérifier l'état des services
```bash
docker-compose -f docker-compose.dev.yml ps
```

### Accéder à l'API
```bash
# Dans votre navigateur (⚠️ Note: Le port a changé à 8080)
http://localhost:8080/docs

# Ou avec curl
curl http://localhost:8080/health
```

### Lancer un Agent Simple

#### Via l'API REST (curl)
```bash
# Créer un agent
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyAgent",
    "type": "cognitive",
    "config": {
      "llm_provider": "ollama",
      "model": "qwen3:4b",
      "temperature": 0.7
    }
  }'

# Envoyer une requête à l'agent
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this code and suggest improvements",
    "context": {
      "code": "def hello(): print(\"hello world\")"
    }
  }'
```

#### Via Python (depuis l'extérieur du conteneur)
```python
import requests

# Configuration de base (⚠️ Note: Le port a changé à 8080)
API_URL = "http://localhost:8080"

# Créer un agent
response = requests.post(
    f"{API_URL}/api/v1/agents",
    json={
        "name": "PythonAgent",
        "type": "cognitive",
        "config": {
            "llm_provider": "ollama",
            "model": "qwen3:4b"
        }
    }
)
agent = response.json()
agent_id = agent["id"]

# Utiliser l'agent
task_response = requests.post(
    f"{API_URL}/api/v1/agents/{agent_id}/execute",
    json={
        "task": "Write a Python function to calculate fibonacci",
        "max_iterations": 5
    }
)
result = task_response.json()
print(result)
```

### Lancer un Swarm

#### Via l'API REST
```bash
# Créer un swarm
curl -X POST "http://localhost:8000/api/v1/swarms" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DevSwarm",
    "agents": [
      {
        "name": "Architect",
        "type": "cognitive",
        "role": "system_design"
      },
      {
        "name": "Developer",
        "type": "cognitive", 
        "role": "implementation"
      },
      {
        "name": "Tester",
        "type": "cognitive",
        "role": "testing"
      }
    ],
    "topology": "hierarchical"
  }'

# Exécuter une tâche avec le swarm
curl -X POST "http://localhost:8000/api/v1/swarms/{swarm_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a REST API for user management with authentication",
    "strategy": "collaborative",
    "max_rounds": 10
  }'
```

### Accès aux logs
```bash
# Voir les logs du service core
docker-compose -f docker-compose.dev.yml logs -f core

# Voir tous les logs
docker-compose -f docker-compose.dev.yml logs -f
```

## 🔧 Mode 2 : Hybride (DB/Redis Docker, App locale)

### Démarrer les services de support
```bash
# Démarrer seulement DB et Redis
docker-compose -f docker-compose.dev.yml up -d db redis

# Si vous utilisez Ollama
docker-compose -f docker-compose.ollama.yml up -d ollama
```

### Configurer l'environnement Python local
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Se placer dans le répertoire core
cd services/core

# Variables d'environnement
export DATABASE_URL="postgresql://user:pass@localhost:5432/mas"
export REDIS_URL="redis://localhost:6380/0"  # Note: port 6380
export LLM_PROVIDER="ollama"
export LLM_BASE_URL="http://localhost:11434"
export LLM_MODEL="qwen3:4b"
```

### Lancer l'application localement
```bash
# Exécuter les migrations
alembic upgrade head

# Démarrer l'application
uvicorn src.main:app --reload --port 8000
```

### Utiliser les Agents/Swarms

#### Via un script Python local
```python
# test_agent.py
import asyncio
from src.services.agent_service import AgentService
from src.core.agents.cognitive_agent import CognitiveAgent

async def test_agent():
    # Initialiser le service
    agent_service = AgentService()
    
    # Créer un agent
    agent = await agent_service.create_agent(
        name="LocalAgent",
        agent_type="cognitive",
        config={
            "llm_provider": "ollama",
            "model": "qwen3:4b",
            "temperature": 0.7
        }
    )
    
    # Exécuter une tâche
    result = await agent.execute_task(
        "Write a Python function to sort a list",
        context={"requirements": "Use quicksort algorithm"}
    )
    
    print(result)

# Exécuter
asyncio.run(test_agent())
```

#### Via pytest
```bash
# Créer un test
# tests/test_my_agent.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_create_and_use_agent():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer un agent
        response = await client.post(
            "/api/v1/agents",
            json={
                "name": "TestAgent",
                "type": "cognitive"
            }
        )
        assert response.status_code == 201
        agent_data = response.json()
        
        # Utiliser l'agent
        task_response = await client.post(
            f"/api/v1/agents/{agent_data['id']}/execute",
            json={"task": "Hello world"}
        )
        assert task_response.status_code == 200

# Exécuter le test
pytest tests/test_my_agent.py -v
```

### Débugger avec VS Code
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug MAS API",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.main:app",
                "--reload",
                "--port", "8000"
            ],
            "cwd": "${workspaceFolder}/services/core",
            "env": {
                "DATABASE_URL": "postgresql://user:pass@localhost:5432/mas",
                "REDIS_URL": "redis://localhost:6380/0",
                "LLM_PROVIDER": "ollama",
                "LLM_BASE_URL": "http://localhost:11434"
            }
        }
    ]
}
```

## 💻 Mode 3 : Local (Tout en local)

### Prérequis locaux
```bash
# Installer PostgreSQL
sudo apt install postgresql postgresql-contrib

# Installer Redis
sudo apt install redis-server

# Démarrer les services
sudo service postgresql start
sudo service redis-server start

# Créer la base de données
sudo -u postgres createdb mas
sudo -u postgres psql -c "CREATE USER user WITH PASSWORD 'pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mas TO user;"
```

### Configuration Ollama locale
```bash
# Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Démarrer Ollama
ollama serve

# Dans un autre terminal, télécharger un modèle
ollama pull qwen3:4b
```

### Variables d'environnement (.env local)
```bash
# services/core/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/mas
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3:4b
ENVIRONMENT=development
DEBUG=true
```

### Lancer l'application
```bash
cd services/core
source ../../venv/bin/activate
alembic upgrade head
uvicorn src.main:app --reload
```

### Utiliser les Agents via CLI

#### Créer un CLI pour les agents
```python
# services/core/src/cli.py
import click
import asyncio
from src.services.agent_service import AgentService

@click.group()
def cli():
    """MAS CLI for agent management"""
    pass

@cli.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--type', default='cognitive', help='Agent type')
@click.option('--task', required=True, help='Task to execute')
def run_agent(name, type, task):
    """Run a single agent with a task"""
    async def _run():
        service = AgentService()
        agent = await service.create_agent(name, type)
        result = await agent.execute_task(task)
        print(f"Result: {result}")
    
    asyncio.run(_run())

@cli.command()
@click.option('--name', required=True, help='Swarm name')
@click.option('--agents', default=3, help='Number of agents')
@click.option('--task', required=True, help='Task for swarm')
def run_swarm(name, agents, task):
    """Run a swarm with a task"""
    async def _run():
        from src.services.swarm_service import SwarmService
        service = SwarmService()
        
        # Create swarm
        swarm = await service.create_swarm(
            name=name,
            agent_count=agents,
            topology="mesh"
        )
        
        # Execute task
        result = await swarm.execute_collaborative_task(task)
        print(f"Swarm Result: {result}")
    
    asyncio.run(_run())

if __name__ == '__main__':
    cli()
```

#### Utiliser le CLI
```bash
# Agent simple
python -m src.cli run-agent --name "CodeBot" --task "Write a hello world in Python"

# Swarm
python -m src.cli run-swarm --name "DevTeam" --agents 5 --task "Design a microservice architecture"
```

## 📊 Exemples de requêtes complexes

### Swarm pour développement complet
```python
# Requête POST à /api/v1/swarms/execute
{
    "swarm_config": {
        "name": "FullStackSwarm",
        "agents": [
            {"name": "Architect", "role": "design", "expertise": ["system_design", "patterns"]},
            {"name": "Backend", "role": "backend", "expertise": ["python", "fastapi", "postgresql"]},
            {"name": "Frontend", "role": "frontend", "expertise": ["react", "typescript"]},
            {"name": "DevOps", "role": "deployment", "expertise": ["docker", "kubernetes"]},
            {"name": "QA", "role": "testing", "expertise": ["pytest", "selenium"]}
        ],
        "topology": "hierarchical",
        "coordinator": "Architect"
    },
    "task": {
        "description": "Create a complete task management system",
        "requirements": [
            "User authentication with JWT",
            "CRUD operations for tasks",
            "Real-time notifications",
            "REST API with OpenAPI docs",
            "React frontend with Material-UI",
            "Docker deployment ready",
            "95% test coverage"
        ],
        "deliverables": [
            "System architecture document",
            "API implementation",
            "Frontend application", 
            "Docker compose setup",
            "Test suite",
            "Deployment guide"
        ]
    },
    "execution_config": {
        "max_rounds": 20,
        "strategy": "iterative",
        "checkpoints": true,
        "parallel_execution": true
    }
}
```

### Agent avec outils personnalisés
```python
# Requête POST à /api/v1/agents/execute
{
    "agent_config": {
        "name": "DataAnalyst",
        "type": "cognitive",
        "tools": [
            "code_executor",
            "web_search",
            "file_manager",
            "database_query"
        ],
        "memory": {
            "type": "vector",
            "size": 1000
        }
    },
    "task": {
        "description": "Analyze sales data and create visualizations",
        "data_source": "postgresql://localhost/sales",
        "requirements": [
            "Statistical analysis",
            "Trend identification",
            "Matplotlib visualizations",
            "Executive summary"
        ]
    }
}
```

## 🔍 Monitoring et Debugging

### Voir les métriques Prometheus
```bash
# Mode Docker
http://localhost:8000/metrics

# Mode Local/Hybride
curl http://localhost:8000/metrics
```

### Logs structurés
```python
# Les logs sont dans /app/logs (Docker) ou services/core/logs (local)
tail -f services/core/logs/mas.log | jq '.'
```

### Health checks
```bash
# Vérifier la santé de l'API
curl http://localhost:8000/health

# Vérifier les dépendances
curl http://localhost:8000/health/dependencies
```

## 🆘 Troubleshooting

### Port Redis 6380
Le port Redis a été changé à 6380 pour éviter les conflits. Mettez à jour vos configurations :
```python
REDIS_URL = "redis://localhost:6380/0"  # Au lieu de 6379
```

### Erreurs de connexion LLM
```bash
# Vérifier Ollama
curl http://localhost:11434/api/tags

# Vérifier OpenAI (remplacer YOUR_KEY)
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

### Problèmes de mémoire
```bash
# Augmenter la mémoire Docker
# Docker Desktop > Settings > Resources > Memory : 8GB minimum
```

## 📚 Ressources supplémentaires

- API Documentation : http://localhost:8000/docs
- Architecture : /docs/architecture/
- Examples : /services/core/tests/
- Config Guide : /docs/guides/CONFIG-GUIDE.md