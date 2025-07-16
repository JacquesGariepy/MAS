# 🚀 Activation de TOUS les Types d'Agents MAS v2.0

## 📋 Vue d'ensemble

Le système MAS v2.0 supporte maintenant **TOUS les types d'agents** :

1. **Agents Cognitifs (reactive)** - Raisonnement basé sur LLM
2. **Agents Réflexifs (reflexive)** - Réponses rapides basées sur des règles
3. **Agents Hybrides (hybrid)** - Combinaison adaptative des deux modes

## 🔧 Fichiers Créés/Modifiés

### Nouveaux Fichiers
- `services/core/src/agents/types/reflexive_agent.py` - Implémentation des agents réflexifs
- `services/core/src/agents/types/hybrid_agent.py` - Implémentation des agents hybrides
- `services/core/src/agents/agent_factory.py` - Factory pour créer tous les types

### Fichiers Modifiés
- `services/core/src/api/agents.py` - Ajout du endpoint POST `/agents/{agent_id}/messages`
- `services/core/src/schemas/messages.py` - Schémas pour les messages FIPA-ACL

## 🚀 Étapes d'Activation

### 1. Redémarrer le serveur Core
```bash
# Option 1: Redémarrer uniquement le service core
docker-compose restart core

# Option 2: Reconstruire et redémarrer
docker-compose down
docker-compose up -d --build core
```

### 2. Vérifier l'activation
```bash
# Exécuter le test complet
python3 examples/test_all_agent_types.py

# Ou le test simple des messages
python3 examples/test_message_endpoint_simple.py
```

### 3. Exécuter la démo complète
```bash
python3 examples/mas_complete_cycle_demo_fixed.py
```

## 📊 Types d'Agents Détaillés

### 🧠 Agents Cognitifs (reactive)
```python
{
    "name": "StrategicPlanner",
    "role": "Strategic Analysis",
    "agent_type": "reactive",
    "capabilities": ["reasoning", "planning", "analysis"],
    "configuration": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}
```

### ⚡ Agents Réflexifs (reflexive)
```python
{
    "name": "QuickResponder",
    "role": "Fast Response",
    "agent_type": "reflexive",
    "capabilities": ["fast_response", "rule_execution"],
    "reactive_rules": {
        "alert_rule": {
            "condition": {"alert_level": "high"},
            "action": {"type": "notify", "content": "Alert!"}
        }
    }
}
```

### 🔄 Agents Hybrides (hybrid)
```python
{
    "name": "AdaptiveCoordinator",
    "role": "Adaptive Coordination",
    "agent_type": "hybrid",
    "capabilities": ["coordination", "adaptation"],
    "configuration": {
        "complexity_threshold": 0.6,
        "learning_rate": 0.1
    },
    "reactive_rules": {
        "simple_task": {
            "condition": {"complexity": "low"},
            "action": {"type": "execute", "content": "Quick execution"}
        }
    }
}
```

## 💬 Communication Inter-Agents

Le nouveau endpoint permet la communication FIPA-ACL entre tous les types d'agents :

```python
# POST /api/v1/agents/{agent_id}/messages
{
    "receiver_id": "uuid-of-receiver",
    "performative": "request",  # ou inform, propose, accept, reject, query, subscribe
    "content": {
        "action": "analyze_data",
        "params": {"dataset": "sales_2024"}
    },
    "conversation_id": "uuid-for-tracking"
}
```

## 🧪 Scripts de Test

### Test Complet
`examples/test_all_agent_types.py`
- Crée 3 utilisateurs
- Crée 2 agents de chaque type
- Teste la communication entre tous les types
- Vérifie les mémoires et messages

### Test Simple
`examples/test_message_endpoint_simple.py`
- Test direct du endpoint de messages
- Création d'agents cognitifs et réflexifs
- Envoi et réception de messages

### Démo Complète
`examples/mas_complete_cycle_demo_fixed.py`
- Cycle complet avec tous les types d'agents
- Communication multi-agents
- Création de tâches et mémoires

## ⚠️ Notes Importantes

1. **Redémarrage Requis** : Le serveur DOIT être redémarré après l'ajout des nouveaux types d'agents
2. **Ordre de Création** : Les agents peuvent être créés dans n'importe quel ordre
3. **Communication** : Tous les types d'agents peuvent communiquer entre eux
4. **Règles Réactives** : Les agents réflexifs et hybrides utilisent des règles pour les réponses rapides

## 🎯 Vérification du Succès

Si tout fonctionne correctement, vous devriez voir :
- ✅ Création réussie d'agents réflexifs et hybrides
- ✅ Messages envoyés entre différents types d'agents
- ✅ Pas d'erreurs 500 lors de la création d'agents
- ✅ Le résumé montre des agents de tous les types

## 🐛 Dépannage

Si les agents réflexifs/hybrides ne fonctionnent pas :
1. Vérifier que les fichiers sont bien créés dans `services/core/src/agents/types/`
2. S'assurer que le serveur a été redémarré
3. Vérifier les logs : `docker-compose logs -f core`
4. Exécuter le test de factory : `python3 examples/test_agent_factory.py`