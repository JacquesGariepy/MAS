# 🔧 Guide de Résolution des Conflits de Dépendances

## 🚨 Problème : ResolutionImpossible

L'erreur `ResolutionImpossible` se produit quand pip ne peut pas trouver un ensemble de versions compatibles pour toutes les bibliothèques.

### Cause identifiée

Conflit entre FastAPI et Pydantic :
- FastAPI 0.104.1 → Nécessite une version spécifique de Pydantic
- Pydantic 2.5.0 → Peut ne pas être compatible avec cette version de FastAPI

## ✅ Solution

### Option 1 : Utiliser requirements-fixed.txt (Recommandé)

```bash
# Remplacer le Dockerfile.dev pour utiliser requirements-fixed.txt
cd services/core
docker-compose -f ../../docker-compose.dev.yml build core
```

Le fichier `requirements-fixed.txt` contient :
- FastAPI 0.110.0 (compatible avec Pydantic v2)
- Pydantic 2.5.3
- Toutes les autres dépendances avec des versions compatibles

### Option 2 : Utiliser constraints.txt

```dockerfile
# Dans Dockerfile.dev
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
```

### Option 3 : Build en deux étapes

1. D'abord les dépendances essentielles :
```bash
docker-compose -f docker-compose.dev.yml build core --build-arg REQUIREMENTS=requirements-core.txt
```

2. Puis les dépendances complètes si nécessaire.

## 📋 Commandes utiles

### Tester localement
```bash
# Tester la résolution des dépendances
cd services/core
./test-deps.sh
```

### Rebuild Docker
```bash
# Nettoyer et reconstruire
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache core
docker-compose -f docker-compose.dev.yml up
```

### Vérifier les conflits
```bash
# Dans un conteneur temporaire
docker run --rm -it python:3.11-slim bash
pip install pip-tools
echo "fastapi==0.110.0" > requirements.in
echo "pydantic==2.5.3" >> requirements.in
pip-compile requirements.in
```

## 🎯 Bonnes pratiques

1. **Séparer les dépendances** :
   - `requirements.txt` : Production uniquement
   - `requirements-dev.txt` : Outils de développement
   - `requirements-fixed.txt` : Versions verrouillées et testées

2. **Utiliser pip-tools** :
   ```bash
   pip install pip-tools
   pip-compile requirements.in -o requirements.txt
   ```

3. **Tester avant de déployer** :
   ```bash
   pip install -r requirements.txt --dry-run
   ```

## 🔍 Diagnostic

Si le problème persiste :

1. **Voir les conflits détaillés** :
   ```bash
   pip install -r requirements.txt --verbose
   ```

2. **Utiliser pipdeptree** :
   ```bash
   pip install pipdeptree
   pipdeptree --warn silence | grep -E "fastapi|pydantic"
   ```

3. **Vérifier les dépendances transitives** :
   ```bash
   pip show fastapi | grep Requires
   pip show pydantic | grep Required-by
   ```

## 📦 Versions testées et fonctionnelles

| Package | Version | Notes |
|---------|---------|-------|
| fastapi | 0.110.0 | Support complet Pydantic v2 |
| pydantic | 2.5.3 | Compatible avec FastAPI 0.110+ |
| uvicorn | 0.27.0 | Serveur ASGI |
| sqlalchemy | 2.0.23 | ORM async |
| redis | 5.0.1 | Inclut le support async natif |

## 🚀 Solution rapide

```bash
# 1. Arrêter les conteneurs
docker-compose -f docker-compose.dev.yml down

# 2. Copier le requirements-fixed.txt
cp services/core/requirements-fixed.txt services/core/requirements.txt

# 3. Reconstruire
docker-compose -f docker-compose.dev.yml build --no-cache core

# 4. Lancer
docker-compose -f docker-compose.dev.yml up
```

## ❓ Support

Si le problème persiste après avoir suivi ce guide :
1. Vérifier les logs complets : `docker-compose logs core`
2. Essayer avec Python 3.12 : Modifier `FROM python:3.12-slim` dans Dockerfile.dev
3. Créer une issue avec les logs complets