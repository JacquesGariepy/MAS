# 🚀 MAS Production System - Quick Start

## 📋 Démarrage en 3 étapes

### 1️⃣ Cloner et configurer
```bash
git clone <repository-url>
cd mas-production-system
cp .env.example .env  # Pas besoin de modifier pour Ollama
```

### 2️⃣ Lancer avec Docker (Ollama inclus)
```bash
docker-compose -f docker-compose.ollama.yml up -d
```

### 3️⃣ Vérifier que tout fonctionne
```bash
# API disponible sur
curl http://localhost:8000/health

# Documentation interactive
open http://localhost:8000/docs
```

## 🎯 C'est tout !

L'application est maintenant prête avec :
- ✅ API REST complète
- ✅ Base de données PostgreSQL
- ✅ Cache Redis
- ✅ LLM Ollama (modèle llama2)
- ✅ Documentation Swagger

## 📁 Structure simplifiée

```
mas-production-system/
├── docker-compose.ollama.yml  # 🐳 Tout-en-un avec Ollama
├── docker-compose.dev.yml     # 🐳 Pour OpenAI/LM Studio
├── .env.example              # 📝 Configuration template
├── services/core/            # 💻 Code source
│   ├── src/                 # Code Python
│   ├── tests/               # Tests
│   └── requirements.txt     # Dépendances
├── docs/                    # 📚 Documentation
└── config/                  # ⚙️ Configurations
```

## 🔧 Commandes utiles

```bash
# Voir les logs
docker-compose -f docker-compose.ollama.yml logs -f

# Arrêter
docker-compose -f docker-compose.ollama.yml down

# Reset complet
docker-compose -f docker-compose.ollama.yml down -v
```

## 💡 Prochaines étapes

1. Explorer l'API : http://localhost:8000/docs
2. Créer un agent : voir les exemples dans la doc Swagger
3. Lire la documentation complète : `DEVELOPMENT.md`

## ❓ Aide

- Configuration LLM : voir `LLM-SETUP.md`
- Guide Ollama : voir `OLLAMA-QUICKSTART.md`
- Configuration détaillée : voir `CONFIG-GUIDE.md`
- Développement : voir `DEVELOPMENT.md`