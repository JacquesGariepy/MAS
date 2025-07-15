# 🤖 Configuration LLM : LM Studio vs Ollama vs OpenAI

## 📋 Vue d'ensemble

| Provider | Où ça tourne ? | Besoin Docker ? | Gratuit ? | Config |
|----------|---------------|-----------------|-----------|---------|
| **OpenAI** | ☁️ Cloud | ❌ Non | 💰 Payant | Simple |
| **LM Studio** | 💻 Sur votre PC | ❌ Non | ✅ Gratuit | Moyen |
| **Ollama** | 💻 Sur votre PC | 🔄 Optionnel | ✅ Gratuit | Simple |

## 🎯 Configuration pour chaque provider

### 1️⃣ OpenAI (Plus simple)

```bash
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini

# C'est tout ! OpenAI est dans le cloud
```

### 2️⃣ LM Studio (Sur votre machine)

**Étape 1 : Installer LM Studio sur votre PC (pas dans Docker)**
- Télécharger : https://lmstudio.ai/
- Lancer LM Studio
- Télécharger un modèle (ex: Mistral, Llama 2)
- Démarrer le serveur local (port 1234 par défaut)

**Étape 2 : Configurer .env**
```bash
# .env
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_API_KEY=not-needed
LLM_MODEL=local-model
```

**Important** : `host.docker.internal` permet à Docker d'accéder à votre PC

### 3️⃣ Ollama (Option A : Sur votre machine)

**Étape 1 : Installer Ollama sur votre PC**
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Télécharger depuis https://ollama.ai/download
```

**Étape 2 : Télécharger un modèle**
```bash
ollama pull llama2
# ou
ollama pull mistral
```

**Étape 3 : Configurer .env**
```bash
# .env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://host.docker.internal:11434
LLM_API_KEY=not-needed
LLM_MODEL=llama2
```

### 3️⃣ Ollama (Option B : Dans Docker) 🐳

**Ajouter Ollama au docker-compose.dev.yml :**

```yaml
version: '3.8'
services:
  # ... vos autres services ...

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]  # Si vous avez un GPU NVIDIA
    # Pour CPU seulement, retirer la section deploy

  core:
    # ... votre service core ...
    environment:
      - LLM_PROVIDER=ollama
      - LLM_BASE_URL=http://ollama:11434  # Nom du service Docker
      - LLM_MODEL=llama2
    depends_on:
      - ollama
      - db
      - redis

volumes:
  ollama-data:  # Pour persister les modèles téléchargés
```

**Télécharger un modèle dans Ollama Docker :**
```bash
# Après docker-compose up
docker-compose exec ollama ollama pull llama2
```

## 🔧 Docker Compose Complet avec Options

```yaml
# docker-compose.llm.yml - Exemple avec toutes les options

version: '3.8'
services:
  core:
    build:
      context: ./services/core
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      # Option 1 : OpenAI (dans le cloud)
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
      
      # Option 2 : LM Studio (sur votre PC)
      # - LLM_PROVIDER=lmstudio
      # - LLM_BASE_URL=http://host.docker.internal:1234/v1
      # - LLM_MODEL=local-model
      
      # Option 3 : Ollama (dans Docker)
      # - LLM_PROVIDER=ollama
      # - LLM_BASE_URL=http://ollama:11434
      # - LLM_MODEL=llama2
      
      # Reste de la config
      - DATABASE_URL=postgresql://user:pass@db:5432/mas
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      # - ollama  # Décommenter si vous utilisez Ollama dans Docker

  # Service Ollama optionnel (décommenter pour l'utiliser)
  # ollama:
  #   image: ollama/ollama:latest
  #   ports:
  #     - "11434:11434"
  #   volumes:
  #     - ollama-data:/root/.ollama
  #   environment:
  #     - OLLAMA_MODELS=/root/.ollama/models

  db:
    image: postgres:15-alpine
    # ... reste de la config ...

  redis:
    image: redis:7-alpine
    # ... reste de la config ...

volumes:
  postgres-data:
  redis-data:
  ollama-data:  # Pour Ollama si utilisé
```

## 📊 Comparaison des approches

### LM Studio / Ollama sur votre PC (hors Docker)
**✅ Avantages :**
- Utilise directement votre GPU
- Pas de duplication de modèles
- Plus simple à gérer
- Interface graphique (LM Studio)

**❌ Inconvénients :**
- Doit être lancé manuellement
- Configuration différente selon l'OS

### Ollama dans Docker
**✅ Avantages :**
- Tout est dans Docker
- Démarrage automatique
- Reproductible

**❌ Inconvénients :**
- Plus complexe avec GPU
- Modèles dupliqués
- Plus de RAM nécessaire

## 🚀 Recommandations

1. **Pour débuter** → OpenAI (simple mais payant)
2. **Pour du gratuit simple** → Ollama sur votre PC
3. **Pour plus de contrôle** → LM Studio sur votre PC
4. **Pour tout dans Docker** → Ollama dans Docker

## 🔍 Vérifier la connexion

```bash
# Tester la connexion au LLM
curl http://localhost:8000/health

# Voir les logs
docker-compose logs -f core | grep LLM

# Tester directement le LLM
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# LM Studio (doit être lancé)
curl http://localhost:1234/v1/models

# Ollama
curl http://localhost:11434/api/tags
```

## 📝 Exemples de .env

### Pour OpenAI
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini
```

### Pour LM Studio
```bash
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_API_KEY=not-needed
LLM_MODEL=TheBloke/Mistral-7B-Instruct-v0.2-GGUF
```

### Pour Ollama (local)
```bash
LLM_PROVIDER=ollama
LLM_BASE_URL=http://host.docker.internal:11434
LLM_API_KEY=not-needed
LLM_MODEL=mistral
```

### Pour Ollama (Docker)
```bash
LLM_PROVIDER=ollama
LLM_BASE_URL=http://ollama:11434
LLM_API_KEY=not-needed
LLM_MODEL=llama2
```

---

**Note** : `host.docker.internal` fonctionne sur Docker Desktop (Windows/Mac). Sur Linux, utilisez l'IP de votre machine ou configurez le réseau Docker.