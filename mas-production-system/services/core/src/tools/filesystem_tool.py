"""
Outil de système de fichiers pour les agents MAS
Permet aux agents de créer, lire et écrire des fichiers dans leur espace de travail
"""

import os
import json
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
import shutil
from datetime import datetime

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class FileSystemTool(BaseTool):
    """Outil pour les opérations sur le système de fichiers"""
    
    def __init__(self):
        super().__init__(
            name="filesystem",
            description="Outil pour créer, lire, écrire et organiser des fichiers"
        )
        # Définir le répertoire racine sécurisé
        self.workspace_root = Path("/app/agent_workspace")
        self.workspace_root.mkdir(exist_ok=True)
        
    def _validate_path(self, path_str: str) -> Optional[Path]:
        """Valide et normalise un chemin pour s'assurer qu'il est dans l'espace de travail"""
        try:
            # Convertir en Path absolu
            path = Path(path_str)
            
            # Si le chemin est relatif, le rendre relatif à workspace
            if not path.is_absolute():
                path = self.workspace_root / path
            
            # Résoudre le chemin et vérifier qu'il est dans workspace
            resolved = path.resolve()
            if not str(resolved).startswith(str(self.workspace_root)):
                logger.warning(f"Tentative d'accès hors de l'espace de travail: {path_str}")
                return None
                
            return resolved
            
        except Exception as e:
            logger.error(f"Erreur de validation du chemin {path_str}: {e}")
            return None
    
    async def create_agent_directory(self, agent_id: str, project_name: str) -> ToolResult:
        """Crée un répertoire pour un agent et son projet"""
        try:
            # Créer le chemin du projet
            project_path = self.workspace_root / "projects" / agent_id / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Créer la structure de base
            subdirs = ["src", "tests", "docs", "data"]
            for subdir in subdirs:
                (project_path / subdir).mkdir(exist_ok=True)
            
            # Créer un README
            readme_content = f"""# {project_name}

Créé par l'agent: {agent_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
- src/    : Code source
- tests/  : Tests unitaires
- docs/   : Documentation
- data/   : Données et ressources
"""
            (project_path / "README.md").write_text(readme_content, encoding='utf-8')
            
            return ToolResult(
                success=True,
                data={
                    "project_path": str(project_path),
                    "subdirs": subdirs,
                    "message": f"Projet '{project_name}' créé avec succès"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du répertoire: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def write_file(self, file_path: str, content: str, agent_id: Optional[str] = None) -> ToolResult:
        """Écrit du contenu dans un fichier"""
        try:
            # Valider le chemin
            path = self._validate_path(file_path)
            if not path:
                return ToolResult(
                    success=False,
                    error="Chemin invalide ou hors de l'espace de travail"
                )
            
            # Créer les répertoires parents si nécessaire
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le contenu
            path.write_text(content, encoding='utf-8')
            
            # Logger l'action
            logger.info(f"Fichier créé par {agent_id or 'unknown'}: {path}")
            
            return ToolResult(
                success=True,
                data={
                    "file_path": str(path),
                    "size": len(content),
                    "message": f"Fichier '{path.name}' créé avec succès"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du fichier: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def read_file(self, file_path: str) -> ToolResult:
        """Lit le contenu d'un fichier"""
        try:
            # Valider le chemin
            path = self._validate_path(file_path)
            if not path:
                return ToolResult(
                    success=False,
                    error="Chemin invalide ou hors de l'espace de travail"
                )
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"Le fichier n'existe pas: {file_path}"
                )
            
            # Lire le contenu
            content = path.read_text(encoding='utf-8')
            
            return ToolResult(
                success=True,
                data={
                    "file_path": str(path),
                    "content": content,
                    "size": len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def list_directory(self, dir_path: str = "") -> ToolResult:
        """Liste le contenu d'un répertoire"""
        try:
            # Valider le chemin
            path = self._validate_path(dir_path) if dir_path else self.workspace_root
            if not path:
                return ToolResult(
                    success=False,
                    error="Chemin invalide ou hors de l'espace de travail"
                )
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"Le répertoire n'existe pas: {dir_path}"
                )
            
            # Lister le contenu
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            return ToolResult(
                success=True,
                data={
                    "directory": str(path),
                    "items": items,
                    "count": len(items)
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du listage du répertoire: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def delete_file(self, file_path: str) -> ToolResult:
        """Supprime un fichier"""
        try:
            # Valider le chemin
            path = self._validate_path(file_path)
            if not path:
                return ToolResult(
                    success=False,
                    error="Chemin invalide ou hors de l'espace de travail"
                )
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"Le fichier n'existe pas: {file_path}"
                )
            
            # Supprimer le fichier
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            
            return ToolResult(
                success=True,
                data={
                    "deleted": str(path),
                    "message": f"'{path.name}' supprimé avec succès"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def copy_file(self, source: str, destination: str) -> ToolResult:
        """Copie un fichier ou répertoire"""
        try:
            # Valider les chemins
            src_path = self._validate_path(source)
            dst_path = self._validate_path(destination)
            
            if not src_path or not dst_path:
                return ToolResult(
                    success=False,
                    error="Chemins invalides ou hors de l'espace de travail"
                )
            
            if not src_path.exists():
                return ToolResult(
                    success=False,
                    error=f"La source n'existe pas: {source}"
                )
            
            # Copier
            if src_path.is_file():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
            else:
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            
            return ToolResult(
                success=True,
                data={
                    "source": str(src_path),
                    "destination": str(dst_path),
                    "message": "Copie réussie"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la copie: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def create_template(self, template_name: str, template_data: Dict[str, str]) -> ToolResult:
        """Crée un template réutilisable"""
        try:
            template_path = self.workspace_root / "templates" / template_name
            template_path.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder chaque fichier du template
            for file_name, content in template_data.items():
                file_path = template_path / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
            
            # Créer un manifest
            manifest = {
                "name": template_name,
                "created": datetime.now().isoformat(),
                "files": list(template_data.keys())
            }
            (template_path / "template.json").write_text(
                json.dumps(manifest, indent=2),
                encoding='utf-8'
            )
            
            return ToolResult(
                success=True,
                data={
                    "template_path": str(template_path),
                    "files_created": len(template_data),
                    "message": f"Template '{template_name}' créé avec succès"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du template: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def use_template(self, template_name: str, destination: str, variables: Optional[Dict[str, str]] = None) -> ToolResult:
        """Utilise un template pour créer des fichiers"""
        try:
            template_path = self.workspace_root / "templates" / template_name
            if not template_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Template non trouvé: {template_name}"
                )
            
            dst_path = self._validate_path(destination)
            if not dst_path:
                return ToolResult(
                    success=False,
                    error="Destination invalide"
                )
            
            # Copier le template
            shutil.copytree(template_path, dst_path, dirs_exist_ok=True)
            
            # Remplacer les variables si fournies
            if variables:
                for root, _, files in os.walk(dst_path):
                    for file in files:
                        if file != "template.json":
                            file_path = Path(root) / file
                            content = file_path.read_text(encoding='utf-8')
                            for key, value in variables.items():
                                content = content.replace(f"{{{{{key}}}}}", value)
                            file_path.write_text(content, encoding='utf-8')
            
            # Supprimer le manifest du template
            manifest_path = dst_path / "template.json"
            if manifest_path.exists():
                manifest_path.unlink()
            
            return ToolResult(
                success=True,
                data={
                    "destination": str(dst_path),
                    "template_used": template_name,
                    "message": "Template appliqué avec succès"
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation du template: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Exécute une action de l'outil"""
        actions = {
            "create_directory": self.create_agent_directory,
            "write": self.write_file,
            "read": self.read_file,
            "list": self.list_directory,
            "delete": self.delete_file,
            "copy": self.copy_file,
            "create_template": self.create_template,
            "use_template": self.use_template
        }
        
        if action not in actions:
            return ToolResult(
                success=False,
                error=f"Action inconnue: {action}. Actions disponibles: {list(actions.keys())}"
            )
        
        return await actions[action](**kwargs)