# 🚀 Guide d'Installation Rapide - MAS Production System

## Problème : "externally-managed-environment"

Sur les systèmes récents (Ubuntu 23.04+, Debian 12+), Python est protégé pour éviter de casser le système. Voici comment installer le projet correctement.

## Solution : Utiliser un Environnement Virtuel

### Option 1 : Installation Manuelle (Recommandée)

```bash
# 1. Installer les prérequis système
sudo apt update
sudo apt install python3-venv python3-full python3-dev

# 2. Aller dans le répertoire du projet
cd /mnt/c/Users/admlocal/Documents/source/repos/MAS/mas-production-system

# 3. Créer l'environnement virtuel
python3 -m venv venv

# 4. Activer l'environnement virtuel
source venv/bin/activate

# 5. Mettre à jour pip
pip install --upgrade pip setuptools wheel

# 6. Installer les dépendances
cd services/core
pip install -r requirements.txt

# 7. Copier la configuration
cp .env.example .env
```

### Option 2 : Utiliser le Script d'Installation

```bash
# Depuis la racine du projet
./setup_dev.sh
```

### Option 3 : Utiliser pipx pour une Installation Isolée

```bash
# Installer pipx si nécessaire
sudo apt install pipx
pipx ensurepath

# Installer dans un environnement isolé
cd services/core
pipx install -e .
```

## Vérifier l'Installation

```bash
# Vérifier que l'environnement est activé
which python
# Devrait afficher : /path/to/project/venv/bin/python

# Vérifier les dépendances
pip list | grep fastapi
# Devrait afficher : fastapi 0.104.1
```

## Commandes Utiles

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Désactiver l'environnement virtuel
deactivate

# Réinstaller toutes les dépendances
pip install -r requirements.txt --force-reinstall

# Installer en mode développement
pip install -e .
```

## Lancer l'Application

Une fois l'environnement configuré :

```bash
# Activer l'environnement
source venv/bin/activate

# Lancer les services Docker
docker-compose up -d db redis

# Lancer l'application
cd services/core
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Erreur : "python3-venv is not installed"
```bash
sudo apt update
sudo apt install python3-venv python3-full
```

### Erreur : "No module named pip"
```bash
python3 -m ensurepip --upgrade
```

### Erreur : "Permission denied"
```bash
# Ne pas utiliser sudo avec pip dans un venv !
# Vérifier que vous êtes bien dans le venv :
which pip  # Doit pointer vers venv/bin/pip
```

### WSL et Chemins Windows
Si vous êtes sur WSL, privilégiez un répertoire Linux natif :
```bash
# Copier le projet dans le home WSL
cp -r /mnt/c/Users/admlocal/Documents/source/repos/MAS ~/
cd ~/MAS/mas-production-system
```

## Support

En cas de problème :
1. Vérifiez que vous avez bien activé l'environnement virtuel
2. Assurez-vous d'avoir Python 3.11+ : `python3 --version`
3. Consultez les logs : `tail -f logs/app.log`