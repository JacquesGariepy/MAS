# Agent Workspace

Ce répertoire est l'espace de travail partagé entre l'hôte et les agents Docker.

## Structure

```
agent_workspace/
├── projects/       # Projets créés par les agents
│   └── [agent-id]/[project-name]/
├── shared/         # Ressources partagées entre agents
├── templates/      # Templates de code réutilisables
└── outputs/        # Fichiers de sortie et rapports
```

## Utilisation

Les agents peuvent :
- Créer leurs propres répertoires dans `projects/`
- Partager des ressources dans `shared/`
- Utiliser les templates dans `templates/`
- Générer des rapports dans `outputs/`

## Permissions

- Tous les fichiers créés ici sont accessibles depuis l'hôte
- Les agents ont les permissions complètes dans ce répertoire
- Les modifications sont persistantes