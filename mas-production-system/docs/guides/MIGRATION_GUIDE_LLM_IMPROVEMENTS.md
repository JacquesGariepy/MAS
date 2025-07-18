# Guide de Migration : Améliorations du Service LLM et des Agents

## 🎯 Objectif

Ce guide explique comment appliquer les améliorations développées pour résoudre les problèmes de communication entre les agents et le LLM phi-4.

## 🔍 Problèmes Résolus

### 1. **Timeouts et Déconnexions**
- ❌ Ancien : Timeout de 30 secondes causant des déconnexions fréquentes
- ✅ Nouveau : Timeouts adaptatifs (60s-600s) selon la complexité de la tâche

### 2. **Prompts Non Structurés**
- ❌ Ancien : Injection directe de JSON, pas de format clair
- ✅ Nouveau : Templates structurés avec exemples et validation

### 3. **Gestion d'Erreur Faible**
- ❌ Ancien : Échec complet en cas d'erreur
- ✅ Nouveau : Retry intelligent, fallback, et récupération gracieuse

### 4. **Réponses Inconsistantes**
- ❌ Ancien : Format JSON non validé, réponses vides
- ✅ Nouveau : Validation de schéma, réponses structurées garanties

## 📋 Étapes de Migration

### Étape 1 : Sauvegarder la Configuration Actuelle

```bash
# Sauvegarder les fichiers actuels
cd /mnt/c/Users/admlocal/Documents/source/repos/MAS/mas-production-system

# Créer un dossier de backup
mkdir -p backups/$(date +%Y%m%d)

# Sauvegarder la configuration
cp config/config.yaml backups/$(date +%Y%m%d)/
cp services/core/src/services/llm_service.py backups/$(date +%Y%m%d)/
cp services/core/src/agents/types/*.py backups/$(date +%Y%m%d)/
```

### Étape 2 : Appliquer la Nouvelle Configuration

```bash
# Remplacer la configuration
cp config/config_improved.yaml config/config.yaml

# Vérifier les changements principaux
grep -E "timeout|retry|streaming" config/config.yaml
```

### Étape 3 : Mettre à Jour le Service LLM

```bash
# Remplacer le service LLM
cp services/core/src/services/llm_service_improved.py \
   services/core/src/services/llm_service.py

# Ou garder les deux versions en parallèle pour tester
```

### Étape 4 : Ajouter les Templates de Prompts

```bash
# Copier le fichier de templates
cp services/core/src/agents/templates.py \
   services/core/src/agents/templates.py
```

### Étape 5 : Mettre à Jour les Agents

#### Option A : Remplacement Complet (Recommandé pour tests)

```bash
# Mettre à jour l'agent hybride
cp services/core/src/agents/types/hybrid_agent_improved.py \
   services/core/src/agents/types/hybrid_agent.py

# Mettre à jour l'agent cognitif
cp services/core/src/core/agents/cognitive_agent_improved.py \
   services/core/src/core/agents/cognitive_agent.py
```

#### Option B : Migration Progressive

```python
# Dans hybrid_agent.py, ajouter au début :
from ..templates import build_agent_prompt, get_task_prompt
from ...services.llm_service_improved import ImprovedLLMService

# Modifier __init__ pour utiliser le service amélioré :
def __init__(self, agent_data: Agent, db: AsyncSession):
    super().__init__(agent_data, db)
    self.llm_service = ImprovedLLMService()  # Au lieu de LLMService
```

### Étape 6 : Mettre à Jour les Variables d'Environnement

```bash
# Dans docker-compose.dev.yml, vérifier :
environment:
  - LLM_API_KEY=${LLM_API_KEY}
  - OPENAI_TIMEOUT=300  # Nouveau timeout par défaut
  - ENABLE_STREAMING=true
  - ADAPTIVE_TIMEOUTS=true
```

### Étape 7 : Redémarrer les Services

```bash
# Arrêter les services
docker-compose -f docker-compose.dev.yml down

# Reconstruire avec les nouvelles configurations
docker-compose -f docker-compose.dev.yml build --no-cache

# Redémarrer
docker-compose -f docker-compose.dev.yml up -d

# Vérifier les logs
docker-compose -f docker-compose.dev.yml logs -f core
```

## 🧪 Tests de Validation

### Test 1 : Vérifier les Timeouts

```bash
# Exécuter le script de test
docker-compose -f docker-compose.dev.yml exec core \
  python /app/examples/test_improved_agents.py
```

### Test 2 : Tester avec une Tâche Complexe

```bash
# Exécuter la démo améliorée
docker-compose -f docker-compose.dev.yml exec core \
  python /app/examples/mas_web_app_builder_demo_fixed.py
```

### Test 3 : Vérifier les Logs LLM

```bash
# Surveiller les appels LLM
docker-compose -f docker-compose.dev.yml exec core \
  tail -f /app/logs/llm_requests.log | grep -E "timeout|retry|streaming"
```

## 📊 Métriques à Surveiller

### Avant Migration
- Taux de timeout : ~30-40%
- Temps de réponse moyen : Variable
- Taux d'erreur JSON : ~15%
- Réponses vides : Fréquentes

### Après Migration (Attendu)
- Taux de timeout : <5%
- Temps de réponse moyen : Stable
- Taux d'erreur JSON : <2%
- Réponses vides : Rares

## 🚨 Rollback si Nécessaire

Si des problèmes surviennent :

```bash
# Restaurer la configuration
cp backups/$(date +%Y%m%d)/config.yaml config/
cp backups/$(date +%Y%m%d)/llm_service.py services/core/src/services/
cp backups/$(date +%Y%m%d)/*.py services/core/src/agents/types/

# Redémarrer
docker-compose -f docker-compose.dev.yml restart
```

## 📝 Checklist de Migration

- [ ] Backup des fichiers actuels
- [ ] Application de la nouvelle configuration
- [ ] Mise à jour du service LLM
- [ ] Ajout des templates de prompts
- [ ] Mise à jour des agents (hybrid et cognitive)
- [ ] Configuration des variables d'environnement
- [ ] Rebuild des containers Docker
- [ ] Tests de validation
- [ ] Monitoring des métriques
- [ ] Documentation des changements

## 🎯 Bénéfices Attendus

1. **Performance** : Réduction drastique des timeouts
2. **Fiabilité** : Réponses consistantes et structurées
3. **Maintenabilité** : Prompts centralisés et réutilisables
4. **Debuggabilité** : Logs détaillés et traçabilité
5. **Scalabilité** : Adaptation automatique à la charge

## 💡 Conseils

1. **Testez d'abord en développement** avant la production
2. **Surveillez les logs** pendant les premières heures
3. **Ajustez les timeouts** selon vos besoins spécifiques
4. **Documentez tout changement** de configuration

## 🆘 Support

En cas de problème :
1. Vérifier les logs : `docker-compose logs core`
2. Consulter les métriques : Port 9090
3. Revenir au backup si nécessaire
4. Ajuster les timeouts dans `config.yaml`

---

**Note** : Cette migration améliore significativement la robustesse du système. Les agents seront plus fiables et les communications avec le LLM plus stables.