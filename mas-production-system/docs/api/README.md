# 📋 API Documentation

## OpenAPI Specification

Le fichier [`openapi.yaml`](./openapi.yaml) contient la spécification complète de l'API REST du système MAS.

### Pourquoi ce fichier est ici ?

1. **Séparation des préoccupations** : La spécification API est de la documentation, pas du code source
2. **Standard de l'industrie** : Les specs OpenAPI sont généralement dans `/docs/api/`
3. **Facilité d'accès** : Les outils de documentation (Swagger UI, ReDoc) cherchent souvent dans ce répertoire
4. **Versioning** : Permet de maintenir plusieurs versions de l'API dans des sous-dossiers

### Utilisation

#### Visualiser la documentation

1. **En ligne (après lancement de l'app)** :
   - Swagger UI : http://localhost:8000/docs
   - ReDoc : http://localhost:8000/redoc

2. **Avec un outil local** :
   ```bash
   # Avec Swagger UI local
   docker run -p 8080:8080 -e SWAGGER_JSON=/api/openapi.yaml -v $(pwd):/api swaggerapi/swagger-ui
   
   # Avec ReDoc
   npx redoc-cli serve openapi.yaml
   ```

3. **VS Code** : Installer l'extension "OpenAPI (Swagger) Editor"

### Structure de l'API

L'API suit les principes REST avec :

- **Authentification** : JWT Bearer tokens ou API Keys
- **Versioning** : `/api/v1/` prefix
- **Pagination** : Standardisée sur tous les endpoints de liste
- **Filtrage** : Query parameters pour filtrer les résultats
- **Erreurs** : Format standardisé avec codes HTTP appropriés

### Endpoints principaux

| Resource | Description |
|----------|-------------|
| `/agents` | Gestion des agents (CRUD, start/stop) |
| `/organizations` | Gestion des organisations |
| `/messages` | Communication inter-agents |
| `/negotiations` | Protocoles de négociation |
| `/auctions` | Système d'enchères |
| `/tools` | Exécution d'outils |

### Génération de code client

Vous pouvez générer des clients dans plusieurs langages :

```bash
# Python
openapi-generator generate -i openapi.yaml -g python -o ./client/python

# TypeScript
openapi-generator generate -i openapi.yaml -g typescript-axios -o ./client/typescript

# Go
openapi-generator generate -i openapi.yaml -g go -o ./client/go
```

### Contribution

Pour modifier l'API :
1. Éditer `openapi.yaml`
2. Valider avec : `npx swagger-cli validate openapi.yaml`
3. Tester les changements
4. Mettre à jour les clients si nécessaire