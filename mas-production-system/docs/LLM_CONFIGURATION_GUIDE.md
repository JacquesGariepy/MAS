# Guide de Configuration LLM pour MAS

## Vue d'ensemble

Le système MAS (Multi-Agent System) utilise des LLMs (Large Language Models) pour permettre aux agents cognitifs de raisonner, planifier et communiquer. Ce guide détaille où et comment les informations de configuration LLM sont stockées et utilisées.

## 1. Sources de Configuration

### 1.1 Variables d'Environnement

Les configurations LLM principales sont définies via des variables d'environnement :

```bash
# Provider principal (openai, ollama, lmstudio)
LLM_PROVIDER=lmstudio

# Configuration générale
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=your-api-key
LLM_MODEL=qwen3-8b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4000

# Configurations spécifiques par provider
# OpenAI
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=30

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:4b

# LM Studio
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-3-sonnet
ANTHROPIC_MAX_TOKENS=4000
```

### 1.2 Fichier de Configuration (config.py)

Le fichier `services/core/src/config.py` centralise toutes les configurations avec des valeurs par défaut :

```python
class Settings(BaseSettings):
    # LLM Providers
    LLM_PROVIDER: str = "lmstudio"
    LLM_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000
    
    # Provider-specific settings
    LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
    OLLAMA_HOST: str = "http://localhost:11434"
    OPENAI_MODEL: str = "gpt-4o-mini"
    # ...
```

## 2. Stockage en Base de Données

### 2.1 Table `agents`

Chaque agent peut avoir sa propre configuration LLM dans le champ `configuration` (JSONB) :

```json
{
  "temperature": 0.7,
  "reasoning_depth": 3,
  "max_tokens": 4000,
  "model": "gpt-4o-mini",
  "provider": "openai",
  "system_prompt": "You are a helpful assistant",
  "response_format": "json",
  "planning_horizon": 5,
  "reflection_frequency": 10,
  "learning_rate": 0.1,
  "exploration_rate": 0.2,
  "confidence_threshold": 0.7
}
```

### 2.2 Table `tasks`

Les métadonnées des tâches (`task_metadata` JSONB) peuvent contenir :
- Résultats des appels LLM
- Métriques (tokens utilisés, temps de réponse)
- Prompts utilisés
- Configurations spécifiques

### 2.3 Table `memories`

Les mémoires peuvent stocker le contexte LLM dans `memory_metadata` :
- Embeddings générés
- Contexte de génération
- Modèle utilisé

### 2.4 Table `audit_logs`

Les logs d'audit tracent tous les appels LLM avec leurs paramètres dans le champ `details`.

## 3. Utilisation dans le Code

### 3.1 Service LLM (llm_service.py)

Le service LLM centralise toutes les interactions avec les modèles :

```python
class LLMService:
    def __init__(self):
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
```

### 3.2 Agents Cognitifs

Les agents cognitifs utilisent le service LLM pour :
- **Percevoir** : Interpréter l'environnement
- **Raisonner** : Analyser et décider
- **Planifier** : Créer des plans d'action
- **Apprendre** : Améliorer leurs performances

## 4. Priorité des Configurations

L'ordre de priorité pour les configurations LLM est :

1. **Configuration par agent** (champ `configuration` de l'agent)
2. **Variables d'environnement** spécifiques (ex: `OPENAI_MODEL`)
3. **Variables d'environnement** générales (ex: `LLM_MODEL`)
4. **Valeurs par défaut** dans `config.py`

## 5. Scripts Utilitaires

### 5.1 Afficher la Configuration

```bash
python examples/show_llm_config.py
```

Affiche toutes les sources de configuration LLM.

### 5.2 Extraire les Métadonnées

```bash
python examples/extract_llm_metadata.py
```

Extrait les configurations LLM des agents et tâches en cours.

### 5.3 Exporter la Configuration

```bash
python examples/extract_llm_metadata.py --export
```

Exporte toute la configuration dans un fichier JSON.

## 6. Exemples de Configuration

### 6.1 Agent avec OpenAI

```python
agent_data = {
    "name": "Assistant OpenAI",
    "role": "Assistant général",
    "agent_type": "cognitive",
    "configuration": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.5,
        "max_tokens": 2000,
        "system_prompt": "You are a professional assistant."
    }
}
```

### 6.2 Agent avec Ollama Local

```python
agent_data = {
    "name": "Assistant Local",
    "role": "Analyste",
    "agent_type": "cognitive",
    "configuration": {
        "provider": "ollama",
        "model": "llama2:13b",
        "temperature": 0.3,
        "reasoning_depth": 5
    }
}
```

### 6.3 Agent avec LM Studio

```python
agent_data = {
    "name": "Expert Technique",
    "role": "Développeur",
    "agent_type": "cognitive",
    "configuration": {
        "provider": "lmstudio",
        "temperature": 0.2,
        "response_format": "json",
        "max_tokens": 8000
    }
}
```

## 7. Monitoring et Métriques

Chaque appel LLM est tracké avec :
- **Modèle utilisé**
- **Tokens d'entrée/sortie**
- **Temps de réponse**
- **Succès/Échec**
- **Coût estimé** (pour les providers payants)

Ces métriques sont accessibles via :
- Les logs d'application
- Les métriques Prometheus (si activé)
- L'API de monitoring

## 8. Bonnes Pratiques

1. **Sécurité** : Ne jamais commiter les clés API
2. **Performance** : Ajuster `max_tokens` selon les besoins
3. **Coût** : Surveiller l'utilisation des tokens pour les providers payants
4. **Température** : 
   - 0.0-0.3 : Tâches analytiques précises
   - 0.4-0.7 : Usage général équilibré
   - 0.8-1.0 : Tâches créatives

## 9. Dépannage

### Problèmes Courants

1. **"LLM API error"** : Vérifier les clés API et l'URL de base
2. **"Timeout"** : Augmenter `OPENAI_TIMEOUT` ou réduire `max_tokens`
3. **"Model not found"** : Vérifier que le modèle est disponible chez le provider
4. **Réponses incohérentes** : Ajuster la température et le system prompt

### Logs de Débogage

Activer les logs détaillés :
```python
DEBUG=True
DATABASE_ECHO=True  # Pour voir les requêtes SQL
```

## 10. Intégration avec Docker

Pour utiliser des LLMs locaux avec Docker :

```yaml
# docker-compose.yml
services:
  mas-api:
    environment:
      - LLM_PROVIDER=lmstudio
      - LLM_BASE_URL=http://host.docker.internal:1234/v1
```

Note : Utiliser `host.docker.internal` pour accéder aux services locaux depuis Docker.