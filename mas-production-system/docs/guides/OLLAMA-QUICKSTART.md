# 🦙 Ollama Quick Start avec Docker

## 🚀 Démarrage Rapide (2 options)

### Option 1 : Ollama dans Docker (Recommandé)

```bash
# 1. Lancer tout le stack avec Ollama inclus
docker-compose -f docker-compose.ollama.yml up -d

# 2. Le modèle llama2 sera téléchargé automatiquement
# Vérifier les logs
docker-compose -f docker-compose.ollama.yml logs -f ollama-setup

# 3. C'est tout ! L'API est sur http://localhost:8000
```

### Option 2 : Ollama sur votre machine + Docker pour le reste

```bash
# 1. Installer Ollama sur votre système
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Télécharger un modèle
ollama pull llama2
# ou d'autres modèles : mistral, mixtral, codellama, etc.

# 3. Lancer Ollama (il démarre automatiquement après l'installation)
# Vérifier qu'il tourne
curl http://localhost:11434/api/tags

# 4. Configurer .env
echo "LLM_PROVIDER=ollama" > .env
echo "LLM_BASE_URL=http://host.docker.internal:11434" >> .env
echo "LLM_MODEL=llama2" >> .env

# 5. Lancer les services (sans Ollama dans Docker)
docker-compose -f docker-compose.dev.yml up -d
```

## 🎮 Avec GPU NVIDIA

### Pour Ollama dans Docker avec GPU

1. **Installer NVIDIA Container Toolkit**
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. **Modifier docker-compose.ollama.yml**
```yaml
# Décommenter ces lignes dans le service ollama
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

3. **Lancer avec GPU**
```bash
docker-compose -f docker-compose.ollama.yml up -d
```

## 📊 Modèles Populaires

| Modèle | Taille | Usage | Commande |
|--------|---------|--------|----------|
| `llama2` | 3.8GB | Général | `ollama pull llama2` |
| `mistral` | 4.1GB | Rapide & bon | `ollama pull mistral` |
| `mixtral` | 26GB | Très puissant | `ollama pull mixtral` |
| `codellama` | 3.8GB | Code | `ollama pull codellama` |
| `phi` | 1.6GB | Petit & rapide | `ollama pull phi` |

### Changer de modèle

```bash
# Dans .env
OLLAMA_MODEL=mistral

# Ou directement
OLLAMA_MODEL=mistral docker-compose -f docker-compose.ollama.yml up -d
```

## 🔧 Commandes Utiles

### Gestion des modèles
```bash
# Lister les modèles installés
docker exec ollama ollama list

# Télécharger un nouveau modèle
docker exec ollama ollama pull mistral

# Supprimer un modèle
docker exec ollama ollama rm llama2

# Tester un modèle directement
docker exec -it ollama ollama run llama2 "Hello, how are you?"
```

### Monitoring
```bash
# Voir l'utilisation GPU (si NVIDIA)
nvidia-smi

# Logs Ollama
docker-compose -f docker-compose.ollama.yml logs -f ollama

# Vérifier que Ollama répond
curl http://localhost:11434/api/tags

# Tester via l'API MAS
curl http://localhost:8000/health
```

## 🎯 Configuration dans MAS

Le système est pré-configuré pour Ollama. L'agent va utiliser :
- Provider : `ollama`
- URL : `http://ollama:11434` (communication inter-containers)
- Modèle : `llama2` (ou celui configuré dans OLLAMA_MODEL)

### Exemple d'appel API
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Assistant",
    "role": "helper",
    "agent_type": "cognitive",
    "capabilities": ["analyze", "generate"]
  }'
```

## 📈 Performance

### Recommandations
- **CPU only** : Modèles < 7B paramètres (phi, llama2-7b)
- **GPU 8GB** : Modèles jusqu'à 13B (llama2-13b, mistral)
- **GPU 16GB+** : Grands modèles (mixtral, llama2-70b quantizé)

### Optimisation mémoire
```bash
# Limiter la mémoire Docker
docker update --memory="8g" ollama
```

## 🔍 Troubleshooting

### "Ollama is not running"
```bash
# Vérifier le statut
docker ps | grep ollama

# Redémarrer
docker-compose -f docker-compose.ollama.yml restart ollama
```

### "Model not found"
```bash
# Télécharger le modèle
docker exec ollama ollama pull llama2
```

### Lenteur
- Vérifier la RAM disponible : `docker stats`
- Utiliser un modèle plus petit : `phi` ou `tinyllama`
- Activer le GPU si disponible

## 🌐 Accès depuis l'extérieur

Pour accéder à Ollama depuis d'autres machines :
```yaml
# Dans docker-compose.ollama.yml
ollama:
  ports:
    - "0.0.0.0:11434:11434"  # Écoute sur toutes les interfaces
```

⚠️ **Sécurité** : En production, utilisez un reverse proxy avec authentification.

---

**Rappel** : Avec cette configuration, tout est dans Docker. Pas besoin d'installer quoi que ce soit sur votre système ! 🐳🦙