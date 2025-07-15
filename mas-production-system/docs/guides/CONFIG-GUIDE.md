# 📋 Guide de Configuration - MAS Production System

## 🎯 Vue d'ensemble des fichiers de configuration

### Hiérarchie de priorité (du plus prioritaire au moins prioritaire) :

1. **Variables d'environnement** (directes ou via `.env`)
2. **config/config.yaml** (configuration par défaut)
3. **Valeurs par défaut dans le code** (`src/config.py`)

## 📁 Fichiers de Configuration

### 1️⃣ `.env` (PRIORITAIRE) 
**But** : Variables sensibles et spécifiques à l'environnement
**Utilisé par** : Docker Compose et l'application

```bash
# .env - NE JAMAIS COMMITER CE FICHIER
LLM_API_KEY=sk-xxxxxxxxxxxxx
DATABASE_URL=postgresql://user:password@localhost:5432/mas
SECRET_KEY=your-secret-key-production
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 2️⃣ `docker-compose.dev.yml`
**But** : Configuration Docker pour le développement
**Utilise** : Les variables du `.env`

```yaml
environment:
  - LLM_API_KEY=${LLM_API_KEY}  # Lit depuis .env
  - DATABASE_URL=postgresql://user:pass@db:5432/mas  # Override pour Docker
```

### 3️⃣ `config/config.yaml`
**But** : Configuration par défaut de l'application (non sensible)
**Utilisé quand** : Aucune variable d'environnement n'est définie

```yaml
app:
  name: mas-system
  environment: production

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 4000
```

### 4️⃣ `config/staging.env` et `config/production.env`
**But** : Variables pour les déploiements CI/CD
**Utilisé par** : Scripts de déploiement (`scripts/deploy.sh`)

```bash
# config/production.env
API_URL=https://api.mas-system.com
CLUSTER_NAME=mas-prod
AWS_REGION=us-east-1
```

### 5️⃣ `services/core/.env.example`
**But** : Template documenté pour créer votre `.env`
**Usage** : `cp .env.example .env` puis éditer

## 🔄 Comment ça marche ?

### Avec Docker (Recommandé)

```mermaid
.env (racine)
    ↓
docker-compose.dev.yml (lit les variables)
    ↓
Container (passe les variables)
    ↓
src/config.py (lit les env vars)
    ↓
Si pas trouvé → config/config.yaml
    ↓
Si pas trouvé → Valeurs par défaut
```

### Sans Docker

```mermaid
.env (dans services/core/)
    ↓
export $(cat .env | xargs)
    ↓
src/config.py (lit les env vars)
    ↓
Si pas trouvé → config/config.yaml
    ↓
Si pas trouvé → Valeurs par défaut
```

## 📝 Exemples Pratiques

### Développement avec Docker

1. **Créer `.env` à la racine** :
```bash
# Minimal pour dev
LLM_API_KEY=sk-xxxxxxxx
```

2. **Lancer Docker** :
```bash
docker-compose -f docker-compose.dev.yml up
```

Docker va :
- Lire `LLM_API_KEY` depuis `.env`
- Utiliser les valeurs hardcodées pour `DATABASE_URL`, `REDIS_URL`
- Le conteneur utilisera ces variables

### Production

1. **Variables dans le cloud** (AWS Secrets, K8s Secrets, etc.)
2. **Pas de `.env` commité**
3. **config.yaml** pour les valeurs non-sensibles par défaut

## ⚙️ Configuration dans le Code

Dans `src/config.py` :

```python
class Settings(BaseSettings):
    # 1. D'abord cherche LLM_API_KEY dans l'environnement
    LLM_API_KEY: Optional[str] = None
    
    # 2. Si pas trouvé, cherche dans config.yaml
    # 3. Sinon utilise la valeur par défaut (None)
    
    class Config:
        env_file = ".env"  # Charge .env si présent
        env_file_encoding = 'utf-8'
        
    @validator('LLM_API_KEY')
    def validate_llm_key(cls, v):
        if not v and cls.LLM_PROVIDER == "openai":
            raise ValueError("LLM_API_KEY required for OpenAI")
        return v
```

## 🎯 Quelle config pour quel cas ?

| Cas d'usage | Fichier à utiliser | Exemple |
|-------------|-------------------|---------|
| Clés API secrètes | `.env` | `LLM_API_KEY=sk-xxx` |
| URLs de service en dev | `docker-compose.dev.yml` | `DATABASE_URL=postgresql://db:5432/mas` |
| Config app par défaut | `config/config.yaml` | `temperature: 0.7` |
| Déploiement staging | `config/staging.env` | `CLUSTER_NAME=staging` |
| Déploiement prod | Variables K8s/AWS Secrets | Via ConfigMap/Secrets |

## 🚨 Règles Importantes

1. **JAMAIS** commiter `.env` (ajouter au `.gitignore`)
2. **TOUJOURS** utiliser `.env` pour les secrets
3. **config.yaml** uniquement pour config non-sensible
4. **Variables d'environnement** ont toujours priorité

## 💡 Tips

### Voir toutes les configs actives
```python
# Dans l'app
from src.config import get_settings
settings = get_settings()
print(settings.dict())  # Affiche toute la config
```

### Débugger les variables
```bash
# Dans Docker
docker-compose -f docker-compose.dev.yml exec core env | grep LLM

# Local
env | grep LLM
```

### Override temporaire
```bash
# Override pour un run
LLM_MODEL=gpt-3.5-turbo docker-compose up
```

## 📊 Exemple Complet

```bash
# 1. Structure
mas-production-system/
├── .env                    # 🔐 Secrets (git ignored)
├── config/
│   ├── config.yaml        # 📋 Defaults non-sensibles
│   ├── staging.env        # 🚀 Deploy staging
│   └── production.env     # 🚀 Deploy prod
└── services/core/
    ├── .env.example       # 📝 Template
    └── src/config.py      # ⚙️ Lit tout ça

# 2. Contenu .env
LLM_API_KEY=sk-real-key
SENTRY_DSN=https://real-sentry-url

# 3. Docker lit .env et passe au container
# 4. L'app utilise les variables
```

---

**Résumé** : `.env` pour les secrets, `docker-compose` pour l'orchestration, `config.yaml` pour les defaults, et les variables d'environnement ont toujours priorité ! 🎯