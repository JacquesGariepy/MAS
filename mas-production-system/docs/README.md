# 📚 Documentation MAS Production System

## 🏗️ Architecture
- [API OpenAPI Specification](./api/openapi.yaml) - Spécification complète de l'API REST

## 📖 Guides

### Démarrage Rapide
- [Quick Start](./guides/README_QUICKSTART.md) - Démarrer en 3 minutes avec Docker
- [Installation Complète](./guides/INSTALL.md) - Guide d'installation détaillé
- [Docker Quick Start](./guides/DOCKER-QUICKSTART.md) - Utilisation avec Docker

### Configuration
- [Configuration Guide](./guides/CONFIG-GUIDE.md) - Comprendre la hiérarchie des configurations
- [LLM Setup](./guides/LLM-SETUP.md) - Configurer OpenAI, Ollama ou LM Studio
- [Ollama Quick Start](./guides/OLLAMA-QUICKSTART.md) - Guide spécifique pour Ollama

### Développement
- [Development Guide](./guides/DEVELOPMENT.md) - Guide complet pour les développeurs
- [Project Structure](./guides/STRUCTURE.md) - Organisation du projet
- [Project Status](./guides/PROJECT_STATUS.md) - État actuel et roadmap

## 🔗 Liens Rapides

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Documentation principale du projet |
| [CHANGELOG.md](../CHANGELOG.md) | Historique des versions |
| [API Docs](http://localhost:8000/docs) | Documentation interactive (après lancement) |

## 📂 Organisation

```
docs/
├── README.md           # Ce fichier
├── api/
│   └── openapi.yaml   # Spécification OpenAPI
├── guides/            # Guides d'utilisation
│   ├── README_QUICKSTART.md
│   ├── INSTALL.md
│   ├── DEVELOPMENT.md
│   ├── CONFIG-GUIDE.md
│   ├── LLM-SETUP.md
│   └── ...
└── architecture/      # Diagrammes et docs techniques (à venir)
```

## 🚀 Par où commencer ?

1. **Nouveau utilisateur** → [Quick Start](./guides/README_QUICKSTART.md)
2. **Développeur** → [Development Guide](./guides/DEVELOPMENT.md)
3. **DevOps** → [Docker Guide](./guides/DOCKER-QUICKSTART.md)
4. **API** → [OpenAPI Spec](./api/openapi.yaml)