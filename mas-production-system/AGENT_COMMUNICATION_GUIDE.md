# Guide de Communication des Agents MAS

## 🚀 Points Clés sur le Statut des Agents

### Statuts des Agents

Les agents MAS peuvent avoir les statuts suivants :

1. **`idle`** (😴) - Agent créé mais inactif (statut par défaut)
2. **`working`** (✅) - Agent actif et prêt à communiquer  
3. **`error`** (❌) - Agent en erreur

### ⚠️ Important : Les agents doivent être démarrés !

**Les agents sont créés avec le statut `idle` par défaut et DOIVENT être démarrés pour pouvoir :**
- Recevoir et traiter des messages
- Exécuter des tâches
- Utiliser le LLM (pour les agents cognitifs)
- Communiquer entre eux

## 🔧 Démarrage des Agents

### Option 1 : Script de Démarrage Rapide

```bash
# Démarrer TOUS les agents en une commande
python examples/start_all_agents.py
```

### Option 2 : Script de Vérification Complet

```bash
# Vérifier le statut et démarrer les agents inactifs
python examples/ensure_agents_active.py

# Avec test de communication
python examples/ensure_agents_active.py --test
```

### Option 3 : Via l'API REST

```bash
# Démarrer un agent spécifique
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/start \
  -H "Authorization: Bearer {token}"
```

### Option 4 : Dans votre code Python

```python
# Après avoir créé un agent
response = requests.post(
    f"{API_BASE_URL}/agents/{agent_id}/start",
    headers={"Authorization": f"Bearer {token}"}
)
```

## 🧠 Agents Cognitifs et LLM

Les agents cognitifs nécessitent une configuration LLM pour fonctionner :

1. **Vérifier la configuration LLM** :
   ```bash
   # Dans le fichier .env
   LLM_API_KEY=your-api-key
   LLM_MODEL=gpt-3.5-turbo  # ou autre modèle
   ```

2. **Si le LLM n'est pas configuré** :
   - Les agents cognitifs ne pourront pas traiter les messages
   - Ils resteront en statut `error` ou ne répondront pas

## 📊 Vérification du Statut

### Via les Logs Docker

```bash
# Voir les logs des agents
docker-compose logs core | grep -i "agent.*start"

# Suivre en temps réel
docker-compose logs -f core | grep -i "agent"
```

### Via l'API

```python
# Lister tous les agents avec leur statut
response = requests.get(
    f"{API_BASE_URL}/agents",
    headers={"Authorization": f"Bearer {token}"}
)
agents = response.json()["items"]

for agent in agents:
    print(f"{agent['name']}: {agent['status']}")
```

## 🚨 Dépannage

### Problème : Les agents ne communiquent pas

1. **Vérifier le statut** :
   ```bash
   python examples/ensure_agents_active.py
   ```

2. **Vérifier les logs** :
   ```bash
   docker-compose logs core --tail=100 | grep -i error
   ```

3. **Vérifier le LLM** (pour agents cognitifs) :
   - La variable `LLM_API_KEY` est-elle définie ?
   - Le modèle LLM est-il accessible ?

### Problème : Agent reste en `idle` après démarrage

- Vérifier les permissions de l'utilisateur
- Vérifier que le service est bien démarré
- Consulter les logs pour des erreurs

### Problème : Agent passe en `error`

- Vérifier la configuration de l'agent
- Pour les agents cognitifs : vérifier le LLM
- Vérifier les ressources système

## 📝 Exemple Complet

```python
import asyncio
import aiohttp

async def setup_and_communicate():
    """Exemple complet : créer, démarrer et faire communiquer des agents"""
    
    # 1. Créer des agents
    agents = await create_agents()  # Votre fonction
    
    # 2. Démarrer TOUS les agents
    for agent in agents:
        await start_agent(agent["id"])
    
    # 3. Vérifier qu'ils sont actifs
    active_agents = await get_active_agents()
    print(f"✅ {len(active_agents)} agents actifs")
    
    # 4. Faire communiquer les agents
    await send_message(
        sender_id=agents[0]["id"],
        receiver_id=agents[1]["id"],
        content="Bonjour, commençons le travail!"
    )
```

## 🎯 Bonnes Pratiques

1. **Toujours démarrer les agents après création**
2. **Vérifier le statut avant d'envoyer des messages**
3. **Gérer les erreurs de démarrage gracieusement**
4. **Monitorer les logs pour détecter les problèmes**
5. **Pour les démos : utiliser `start_all_agents.py` au début**

## 🔗 Scripts Utiles

- `examples/start_all_agents.py` - Démarrage rapide de tous les agents
- `examples/ensure_agents_active.py` - Vérification et démarrage intelligent
- `examples/mas_ultimate_100_agents_fixed.py` - Démo complète avec démarrage automatique
- `examples/check_agent_activity.py` - Visualisation de l'activité des agents

---

💡 **Conseil** : Pour les démonstrations, exécutez toujours `python examples/start_all_agents.py` après avoir créé vos agents pour garantir qu'ils sont tous actifs et prêts à communiquer !