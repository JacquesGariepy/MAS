# Guide : Création de Fichiers par les Agents MAS

## Vue d'ensemble

Les agents MAS peuvent maintenant créer, lire et organiser des fichiers dans un espace de travail partagé entre Docker et l'hôte local.

## Configuration

### 1. Structure des Répertoires

```
mas-production-system/
└── agent_workspace/          # Répertoire partagé host/Docker
    ├── projects/            # Projets créés par les agents
    │   └── [agent-id]/     # Répertoire unique par agent
    │       └── [project]/  # Projets de l'agent
    ├── shared/             # Ressources partagées
    ├── templates/          # Templates réutilisables
    └── outputs/            # Rapports et logs
```

### 2. Volume Docker

Le répertoire `agent_workspace` est monté dans Docker :
- **Hôte** : `./agent_workspace`
- **Docker** : `/app/agent_workspace`

Configuré dans `docker-compose.dev.yml` :
```yaml
volumes:
  - ./agent_workspace:/app/agent_workspace
```

## Utilisation du FileSystemTool

### 1. Créer un Projet

```python
from src.tools.filesystem_tool import FileSystemTool

tool = FileSystemTool()

# Créer un projet pour un agent
result = await tool.create_agent_directory(
    agent_id="agent-123",
    project_name="mon_projet"
)
# Crée : /app/agent_workspace/projects/agent-123/mon_projet/
#        avec les sous-répertoires : src/, tests/, docs/, data/
```

### 2. Écrire un Fichier

```python
# Écrire du code Python
code = '''def main():
    print("Hello from agent!")
'''

result = await tool.write_file(
    file_path="projects/agent-123/mon_projet/src/main.py",
    content=code,
    agent_id="agent-123"
)
```

### 3. Lire un Fichier

```python
result = await tool.read_file(
    file_path="projects/agent-123/mon_projet/src/main.py"
)
print(result.data['content'])
```

### 4. Lister un Répertoire

```python
result = await tool.list_directory(
    dir_path="projects/agent-123/mon_projet"
)
for item in result.data['items']:
    print(f"{item['type']}: {item['name']}")
```

### 5. Utiliser des Templates

```python
# Créer un template
template_data = {
    "main.py": "# Code template",
    "README.md": "# Project {{name}}"
}

await tool.create_template("python_basic", template_data)

# Utiliser le template
await tool.use_template(
    template_name="python_basic",
    destination="projects/agent-123/new_project",
    variables={"name": "My Project"}
)
```

## Exemple : Agent Générateur de Code

```python
#!/usr/bin/env python3
import asyncio
from src.services.llm_service import LLMService
from src.tools.filesystem_tool import FileSystemTool

class CodeGeneratorAgent:
    def __init__(self):
        self.agent_id = "codegen-001"
        self.llm = LLMService()
        self.fs = FileSystemTool()
    
    async def generate_project(self, description: str):
        # 1. Créer le projet
        await self.fs.create_agent_directory(
            self.agent_id, 
            "generated_app"
        )
        
        # 2. Générer le code avec LLM
        prompt = f"Générer le code Python pour: {description}"
        response = await self.llm.generate(prompt)
        
        # 3. Sauvegarder le code
        await self.fs.write_file(
            f"projects/{self.agent_id}/generated_app/src/app.py",
            response['response'],
            self.agent_id
        )
```

## Accès aux Fichiers

### Depuis l'Hôte Local
```bash
# Les fichiers sont directement accessibles
ls ./agent_workspace/projects/
cat ./agent_workspace/projects/agent-123/project/src/main.py
```

### Depuis Docker
```bash
# Exécuter dans le container
docker-compose -f docker-compose.dev.yml exec core \
    ls /app/agent_workspace/projects/

# Ou utiliser le Python dans Docker
docker-compose -f docker-compose.dev.yml exec core \
    python /app/examples/agent_code_generator.py
```

## Sécurité

1. **Validation des Chemins** : Tous les chemins sont validés pour rester dans `agent_workspace`
2. **Isolation par Agent** : Chaque agent a son propre répertoire
3. **Permissions** : Les fichiers héritent des permissions du volume Docker

## Exemples Fournis

### 1. Test Simple
```bash
docker-compose -f docker-compose.dev.yml exec core \
    python /app/examples/test_filesystem_simple.py
```

### 2. Agent Générateur de Code
```bash
docker-compose -f docker-compose.dev.yml exec core \
    python /app/examples/agent_code_generator.py
```

## Intégration dans vos Agents

Pour ajouter la capacité de création de fichiers à vos agents :

1. **Importer le Tool** :
   ```python
   from src.tools.filesystem_tool import FileSystemTool
   ```

2. **Initialiser dans l'Agent** :
   ```python
   class MonAgent:
       def __init__(self):
           self.fs_tool = FileSystemTool()
   ```

3. **Utiliser dans les Actions** :
   ```python
   async def handle_create_file(self, content):
       result = await self.fs_tool.write_file(
           f"projects/{self.agent_id}/output.txt",
           content
       )
   ```

## Bonnes Pratiques

1. **Organisation** : Créer un répertoire par projet dans `projects/[agent-id]/`
2. **Nommage** : Utiliser des noms descriptifs pour les fichiers et projets
3. **Documentation** : Toujours créer un README.md dans chaque projet
4. **Logs** : Sauvegarder les rapports dans `outputs/`
5. **Templates** : Créer des templates pour les structures récurrentes

## Troubleshooting

### Erreur : "Chemin invalide ou hors de l'espace de travail"
- Vérifier que le chemin est relatif ou commence par `/app/agent_workspace/`

### Les fichiers ne sont pas visibles localement
- Vérifier que le volume est bien monté : `docker-compose ps`
- Redémarrer le container : `docker-compose up -d --force-recreate core`

### Permission denied
- Vérifier les permissions du répertoire `agent_workspace`
- Sous Windows/WSL, les permissions sont généralement 777

## Prochaines Étapes

1. **Exécution de Scripts** : Ajouter la capacité d'exécuter les scripts créés
2. **Versioning** : Intégrer Git pour versionner les projets
3. **Collaboration** : Permettre aux agents de partager des ressources
4. **Templates Avancés** : Créer des templates pour différents frameworks