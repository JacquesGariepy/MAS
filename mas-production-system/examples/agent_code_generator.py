#!/usr/bin/env python3
"""
Agent qui génère du code et le sauvegarde dans l'espace de travail
"""

import sys
import os
sys.path.append('/app')

import asyncio
import json
from uuid import uuid4
from datetime import datetime

from src.core.agents import AgentFactory, get_agent_runtime
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CodeGeneratorAgent:
    """Agent spécialisé dans la génération de code"""
    
    def __init__(self):
        self.agent_id = str(uuid4())
        self.name = f"CodeGen-{self.agent_id[:8]}"
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        self.workspace_path = f"/app/agent_workspace/projects/{self.agent_id}"
        
    async def generate_code(self, request: str, project_name: str = "generated_project"):
        """Génère du code basé sur une requête"""
        logger.info(f"Agent {self.name} - Génération de code pour: {request}")
        
        try:
            # 1. Créer l'espace de travail du projet
            filesystem_tool = self.tool_service.get_tool("filesystem")
            if not filesystem_tool:
                raise Exception("FileSystemTool non disponible")
            
            # Créer le répertoire du projet
            result = await filesystem_tool.execute(
                action="create_directory",
                agent_id=self.agent_id,
                project_name=project_name
            )
            
            if not result.success:
                raise Exception(f"Erreur création répertoire: {result.error}")
            
            project_path = result.data["project_path"]
            logger.info(f"Projet créé dans: {project_path}")
            
            # 2. Analyser la requête avec le LLM
            analysis_prompt = f"""Analyser cette requête de génération de code:
            
Requête: {request}

Déterminer:
1. Le langage de programmation approprié
2. Les fichiers à créer
3. La structure du projet
4. Les dépendances nécessaires

Répondre en JSON:
{{
    "language": "python|javascript|java|etc",
    "files_to_create": [
        {{"filename": "main.py", "description": "Point d'entrée principal"}},
        ...
    ],
    "dependencies": ["liste des dépendances"],
    "project_structure": "description de la structure"
}}"""

            analysis_result = await self.llm_service.generate(
                prompt=analysis_prompt,
                json_response=True
            )
            
            if not analysis_result.get('success'):
                raise Exception("Erreur lors de l'analyse de la requête")
            
            analysis = analysis_result['response']
            logger.info(f"Analyse complétée: {analysis}")
            
            # 3. Générer le code pour chaque fichier
            generated_files = []
            
            for file_spec in analysis.get('files_to_create', []):
                filename = file_spec['filename']
                description = file_spec['description']
                
                # Générer le code avec le LLM
                code_prompt = f"""Générer le code complet pour ce fichier:

Projet: {request}
Fichier: {filename}
Description: {description}
Langage: {analysis.get('language', 'python')}

Générer uniquement le code, sans explications. Le code doit être complet et fonctionnel."""

                code_result = await self.llm_service.generate(
                    prompt=code_prompt,
                    json_response=False
                )
                
                if code_result.get('success'):
                    code_content = code_result['response']
                    
                    # Déterminer le sous-répertoire
                    if filename.endswith(('.py', '.js', '.java', '.cpp', '.go')):
                        subdir = "src"
                    elif filename.endswith(('_test.py', '.test.js', 'Test.java')):
                        subdir = "tests"
                    elif filename.endswith(('.md', '.txt', '.rst')):
                        subdir = "docs"
                    else:
                        subdir = "src"
                    
                    # Sauvegarder le fichier
                    file_path = f"projects/{self.agent_id}/{project_name}/{subdir}/{filename}"
                    
                    save_result = await filesystem_tool.execute(
                        action="write",
                        file_path=file_path,
                        content=code_content,
                        agent_id=self.agent_id
                    )
                    
                    if save_result.success:
                        generated_files.append({
                            "filename": filename,
                            "path": save_result.data["file_path"],
                            "size": save_result.data["size"]
                        })
                        logger.info(f"Fichier généré: {filename}")
                    else:
                        logger.error(f"Erreur sauvegarde {filename}: {save_result.error}")
                
            # 4. Créer un fichier requirements/package.json si nécessaire
            if analysis.get('dependencies'):
                if analysis.get('language') == 'python':
                    requirements = "\n".join(analysis['dependencies'])
                    await filesystem_tool.execute(
                        action="write",
                        file_path=f"projects/{self.agent_id}/{project_name}/requirements.txt",
                        content=requirements,
                        agent_id=self.agent_id
                    )
                elif analysis.get('language') == 'javascript':
                    package_json = {
                        "name": project_name,
                        "version": "1.0.0",
                        "description": request,
                        "dependencies": {dep: "latest" for dep in analysis['dependencies']}
                    }
                    await filesystem_tool.execute(
                        action="write",
                        file_path=f"projects/{self.agent_id}/{project_name}/package.json",
                        content=json.dumps(package_json, indent=2),
                        agent_id=self.agent_id
                    )
            
            # 5. Créer un README pour le projet
            readme_content = f"""# {project_name}

## Description
{request}

## Structure du projet
{analysis.get('project_structure', 'Structure standard')}

## Fichiers générés
{chr(10).join([f"- {f['filename']}" for f in generated_files])}

## Dépendances
{chr(10).join([f"- {dep}" for dep in analysis.get('dependencies', [])])}

## Utilisation
Consultez les fichiers générés pour les instructions spécifiques.

---
Généré par l'agent: {self.name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await filesystem_tool.execute(
                action="write",
                file_path=f"projects/{self.agent_id}/{project_name}/README.md",
                content=readme_content,
                agent_id=self.agent_id
            )
            
            # 6. Générer un rapport
            report = {
                "success": True,
                "agent": self.name,
                "project_name": project_name,
                "project_path": project_path,
                "language": analysis.get('language'),
                "files_generated": generated_files,
                "total_files": len(generated_files),
                "dependencies": analysis.get('dependencies', [])
            }
            
            # Sauvegarder le rapport
            report_path = f"outputs/report_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await filesystem_tool.execute(
                action="write",
                file_path=report_path,
                content=json.dumps(report, indent=2),
                agent_id=self.agent_id
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }

async def main():
    """Fonction principale de démonstration"""
    print("🤖 Agent Générateur de Code")
    print("="*50)
    
    agent = CodeGeneratorAgent()
    print(f"Agent créé: {agent.name}")
    
    # Exemples de requêtes
    examples = [
        "Créer une API REST simple en Python avec FastAPI pour gérer une liste de tâches",
        "Créer une calculatrice en Python avec interface graphique tkinter",
        "Créer un script Python pour analyser des fichiers CSV et générer des graphiques",
        "Créer une application web de chat en temps réel avec Node.js et Socket.io"
    ]
    
    print("\n📝 Exemples de requêtes:")
    for i, ex in enumerate(examples, 1):
        print(f"{i}. {ex}")
    
    # Requête interactive ou exemple
    try:
        choice = input("\nChoisir un exemple (1-4) ou entrer votre requête: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(examples):
            request = examples[int(choice) - 1]
        else:
            request = choice
        
        project_name = input("Nom du projet (défaut: generated_project): ").strip()
        if not project_name:
            project_name = "generated_project"
        
        print(f"\n🚀 Génération en cours pour: {request}")
        print(f"📁 Projet: {project_name}")
        
        # Générer le code
        result = await agent.generate_code(request, project_name)
        
        if result['success']:
            print(f"\n✅ Génération réussie!")
            print(f"📁 Projet créé dans: {result['project_path']}")
            print(f"📄 Fichiers générés: {result['total_files']}")
            for file in result['files_generated']:
                print(f"   - {file['filename']} ({file['size']} octets)")
            
            # Afficher comment accéder aux fichiers
            print(f"\n💡 Pour voir les fichiers générés:")
            print(f"   Localement: ./agent_workspace/projects/{agent.agent_id}/{project_name}/")
            print(f"   Dans Docker: docker-compose -f docker-compose.dev.yml exec core ls -la {result['project_path']}")
        else:
            print(f"\n❌ Erreur: {result['error']}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Génération annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())