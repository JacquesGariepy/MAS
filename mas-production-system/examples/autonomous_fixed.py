#!/usr/bin/env python3
"""
Agent Autonome Complet - Version corrigée
Résout n'importe quelle requête de manière autonome
Utilise le framework MAS avec agents cognitifs, LLM et logging complet
"""

import sys
import os
sys.path.append('/app')

from src.core.agents import AgentFactory, get_agent_runtime
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.cognitive_agent import CognitiveAgent
from src.core.agents.hybrid_agent import HybridAgent
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.utils.logger import get_logger

from uuid import uuid4
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import traceback
import unicodedata
import re

# Configuration du logging complet
# Créer le dossier logs s'il n'existe pas
os.makedirs("/app/logs", exist_ok=True)
LOG_FILE = f"/app/logs/autonomous_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', errors='replace'),
        logging.StreamHandler()
    ]
)

logger = get_logger(__name__)

def sanitize_unicode(text: str) -> str:
    """Sanitize Unicode text by removing surrogate characters and normalizing.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text safe for UTF-8 encoding
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove surrogate characters (U+D800 to U+DFFF)
    # These are invalid in UTF-8 and cause encoding errors
    text = re.sub(r'[\ud800-\udfff]', '', text)
    
    # Normalize Unicode to NFC (Canonical Decomposition, followed by Canonical Composition)
    text = unicodedata.normalize('NFC', text)
    
    # Replace any remaining problematic characters with their closest ASCII equivalent
    # or remove them if no equivalent exists
    cleaned = []
    for char in text:
        try:
            # Try to encode the character to UTF-8
            char.encode('utf-8')
            cleaned.append(char)
        except UnicodeEncodeError:
            # Try to get an ASCII representation
            ascii_repr = unicodedata.normalize('NFKD', char).encode('ascii', 'ignore').decode('ascii')
            if ascii_repr:
                cleaned.append(ascii_repr)
            else:
                # Skip the character if it can't be represented
                pass
    
    return ''.join(cleaned)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely convert object to JSON string with proper encoding.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with sanitized Unicode
    """
    # Ensure ensure_ascii is False to allow Unicode characters
    kwargs['ensure_ascii'] = False
    
    # Convert to JSON
    json_str = json.dumps(obj, **kwargs)
    
    # Sanitize the result
    return sanitize_unicode(json_str)

class TaskStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    subtasks: List['Task'] = None
    assigned_agent: Any = None
    result: Any = None
    error: str = None
    created_at: float = None
    completed_at: float = None
    
    def __post_init__(self):
        if self.subtasks is None:
            self.subtasks = []
        if self.created_at is None:
            self.created_at = time.time()

class AutonomousLLMService(LLMService):
    """Service LLM étendu avec logging complet"""
    
    def __init__(self):
        super().__init__()
        self.llm_logger = logging.getLogger("LLM_SERVICE")
        
    async def analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyser une requête pour comprendre sa nature et complexité"""
        prompt = f"""Analyser cette requête et déterminer sa nature, complexité et approche de résolution.

Requête: {request}

Répondre en JSON avec:
{{
    "type": "technique|business|créatif|recherche|autre",
    "complexity": "simple|moyenne|complexe|très_complexe",
    "domains": ["liste", "des", "domaines"],
    "requires_code": true/false,
    "requires_research": true/false,
    "requires_creativity": true/false,
    "estimated_subtasks": nombre,
    "approach": "description de l'approche recommandée"
}}"""
        
        self.llm_logger.info(f"Analyse de requête: {sanitize_unicode(request[:100])}...")
        result = await self.generate(prompt, json_response=True)
        self.llm_logger.info(f"Résultat analyse: {sanitize_unicode(str(result))}")
        return result.get('response', {})
    
    async def decompose_task(self, task: str, analysis: Dict[str, Any]) -> List[str]:
        """Décomposer une tâche en sous-tâches"""
        prompt = f"""Décomposer cette tâche en sous-tâches concrètes et actionnables.

Tâche: {task}
Analyse: {safe_json_dumps(analysis, indent=2)}

Créer une liste ordonnée de sous-tâches qui couvrent complètement la tâche principale.
Chaque sous-tâche doit être:
- Spécifique et actionnable
- Indépendante ou avec dépendances claires
- Réalisable par un agent spécialisé

Répondre en JSON:
{{
    "subtasks": [
        {{
            "id": "1",
            "description": "description claire",
            "type": "research|code|analysis|creative|validation",
            "dependencies": ["ids des tâches prérequises"],
            "estimated_time": "en minutes"
        }}
    ]
}}"""
        
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {}).get('subtasks', [])
    
    async def solve_subtask(self, subtask: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Résoudre une sous-tâche spécifique"""
        prompt = f"""Résoudre cette sous-tâche de manière complète et détaillée.

Sous-tâche: {subtask['description']}
Type: {subtask.get('type', 'general')}
Contexte: {context}

Fournir une solution complète avec:
- Étapes détaillées
- Code si nécessaire
- Explications claires
- Validation de la solution

Répondre en JSON:
{{
    "solution": "description détaillée",
    "code": "code si applicable",
    "steps": ["étape 1", "étape 2", ...],
    "validation": "comment vérifier que c'est correct",
    "output": "résultat concret",
    "files_to_create": [
        {{
            "path": "chemin/relatif/fichier.py",
            "content": "contenu complet du fichier",
            "description": "description du fichier"
        }}
    ]
}}"""
        
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})
    
    async def validate_solution(self, task: str, solution: Any) -> Dict[str, Any]:
        """Valider une solution"""
        prompt = f"""Valider cette solution pour la tâche donnée.

Tâche: {task}
Solution proposée: {safe_json_dumps(solution, indent=2) if isinstance(solution, dict) else sanitize_unicode(str(solution))}

Évaluer:
1. Complétude de la solution
2. Qualité technique
3. Points à améliorer
4. Score global (0-100)

Répondre en JSON:
{{
    "is_valid": true/false,
    "score": 85,
    "strengths": ["point fort 1", "point fort 2"],
    "weaknesses": ["point faible 1"],
    "improvements": ["amélioration suggérée"],
    "final_verdict": "accepté|à revoir|rejeté"
}}"""
        
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})

class AutonomousAgent:
    """Agent principal complètement autonome"""
    
    def __init__(self):
        self.agent_id = uuid4()
        self.name = f"AutonomousAgent-{self.agent_id}"
        self.llm_service = AutonomousLLMService()
        self.factory = AgentFactory()
        self.runtime = get_agent_runtime()
        self.tool_service = ToolService()
        self.filesystem_tool = None  # Sera initialisé dans initialize()
        self.sub_agents = []
        self.tasks = []
        self.results = {}
        self.initialized = False  # Flag pour vérifier l'initialisation
        
        # Logger principal
        self.logger = logging.getLogger("AUTONOMOUS_AGENT")
        self.logger.info(f"Initialisation de {self.name}")
        
    async def initialize(self):
        """Initialiser l'agent et ses ressources"""
        if self.initialized:
            self.logger.info("Agent déjà initialisé")
            return
            
        self.logger.info("Initialisation des ressources...")
        
        # Obtenir FileSystemTool
        try:
            self.filesystem_tool = self.tool_service.registry.get_tool("filesystem")
            if self.filesystem_tool:
                self.logger.info("FileSystemTool chargé avec succès")
            else:
                self.logger.warning("FileSystemTool non disponible")
        except Exception as e:
            self.logger.error(f"Erreur chargement FileSystemTool: {e}")
        
        # Créer les agents de base
        await self._create_base_agents()
        
        self.initialized = True
        self.logger.info("Agent autonome prêt")
        
    async def _create_base_agents(self):
        """Créer les agents de base pour différents types de tâches"""
        agent_configs = [
            {
                "name": "Analyste",
                "type": "cognitive",
                "role": "analyst",
                "capabilities": ["analysis", "research", "data_processing"]
            },
            {
                "name": "Développeur",
                "type": "hybrid",
                "role": "developer",
                "capabilities": ["coding", "debugging", "optimization"]
            },
            {
                "name": "Créatif",
                "type": "cognitive",
                "role": "creative",
                "capabilities": ["writing", "design", "ideation"]
            },
            {
                "name": "Validateur",
                "type": "hybrid",
                "role": "validator",
                "capabilities": ["testing", "quality_assurance", "verification"]
            },
            {
                "name": "Coordinateur",
                "type": "cognitive",
                "role": "coordinator",
                "capabilities": ["planning", "coordination", "reporting"]
            }
        ]
        
        for config in agent_configs:
            try:
                agent_data = {
                    "agent_type": config["type"],
                    "agent_id": uuid4(),
                    "name": f"{config['name']}-{self.agent_id}",
                    "role": config["role"],
                    "capabilities": config["capabilities"],
                    "llm_service": self.llm_service,
                    "initial_beliefs": {
                        "parent_agent": self.name,
                        "role": config["role"],
                        "status": "ready"
                    },
                    "initial_desires": [
                        f"complete_{config['role']}_tasks",
                        "collaborate_efficiently"
                    ]
                }
                
                # Ajouter des règles réactives pour les agents hybrid
                if config["type"] == "hybrid":
                    agent_data["reactive_rules"] = {
                        "urgent_task": "prioritize_execution",
                        "error_detected": "debug_and_fix",
                        "validation_needed": "run_validation"
                    }
                
                # Créer l'agent selon son type
                if config["type"] == "cognitive":
                    agent = CognitiveAgent(**agent_data)
                else:  # hybrid
                    agent = HybridAgent(**agent_data)
                
                await self.runtime.register_agent(agent)
                await self.runtime.start_agent(agent)
                
                self.sub_agents.append({
                    "agent": agent,
                    "role": config["role"],
                    "capabilities": config["capabilities"]
                })
                
                self.logger.info(f"Agent créé: {agent.name} ({config['role']})")
                
            except Exception as e:
                self.logger.error(f"Erreur création agent {config['name']}: {str(e)}")
                self.logger.error(traceback.format_exc())
    
    async def process_request(self, request: str) -> Dict[str, Any]:
        """Traiter une requête de manière complètement autonome"""
        # S'assurer que l'agent est initialisé
        if not self.initialized:
            await self.initialize()
            
        self.logger.info("="*80)
        self.logger.info(f"NOUVELLE REQUÊTE: {request}")
        self.logger.info("="*80)
        
        start_time = time.time()
        main_task = Task(
            id=str(uuid4()),
            description=request,
            status=TaskStatus.ANALYZING
        )
        self.tasks.append(main_task)
        
        try:
            # 1. Analyser la requête
            self.logger.info("Phase 1: Analyse de la requête")
            analysis = await self.llm_service.analyze_request(request)
            self.logger.info(f"Analyse complétée: {safe_json_dumps(analysis, indent=2)}")
            
            # 2. Décomposer en sous-tâches
            main_task.status = TaskStatus.PLANNING
            self.logger.info("Phase 2: Décomposition en sous-tâches")
            subtasks_data = await self.llm_service.decompose_task(request, analysis)
            
            # Créer les objets Task pour chaque sous-tâche
            for st_data in subtasks_data:
                subtask = Task(
                    id=st_data['id'],
                    description=st_data['description'],
                    status=TaskStatus.PENDING
                )
                main_task.subtasks.append(subtask)
            
            self.logger.info(f"Sous-tâches créées: {len(main_task.subtasks)}")
            
            # 3. Exécuter les sous-tâches
            main_task.status = TaskStatus.EXECUTING
            self.logger.info("Phase 3: Exécution des sous-tâches")
            
            # Grouper par dépendances et exécuter
            results = await self._execute_subtasks(main_task.subtasks, subtasks_data)
            
            # 4. Valider les résultats
            main_task.status = TaskStatus.VALIDATING
            self.logger.info("Phase 4: Validation des résultats")
            
            validation_results = []
            for i, result in enumerate(results):
                validation = await self.llm_service.validate_solution(
                    main_task.subtasks[i].description,
                    result
                )
                validation_results.append(validation)
                self.logger.info(f"Validation sous-tâche {i+1}: {validation.get('final_verdict', 'unknown')}")
            
            # 5. Agréger les résultats
            main_task.status = TaskStatus.COMPLETED
            main_task.completed_at = time.time()
            duration = main_task.completed_at - main_task.created_at
            
            final_result = {
                "request": request,
                "status": "completed",
                "duration": f"{duration:.2f} seconds",
                "analysis": analysis,
                "subtasks_count": len(main_task.subtasks),
                "subtasks_results": results,
                "validations": validation_results,
                "success_rate": (sum(1 for v in validation_results if v.get('is_valid', False)) / len(validation_results) * 100) if validation_results else 0
            }
            
            main_task.result = final_result
            
            # Générer un rapport complet
            await self._generate_report(main_task, final_result)
            
            self.logger.info("="*80)
            self.logger.info("REQUÊTE COMPLÉTÉE AVEC SUCCÈS")
            self.logger.info(f"Durée totale: {duration:.2f}s")
            self.logger.info(f"Taux de succès: {final_result['success_rate']:.1f}%")
            self.logger.info("="*80)
            
            return final_result
            
        except Exception as e:
            main_task.status = TaskStatus.FAILED
            main_task.error = str(e)
            self.logger.error(f"Erreur lors du traitement: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            return {
                "request": request,
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _execute_subtasks(self, subtasks: List[Task], subtasks_data: List[Dict]) -> List[Any]:
        """Exécuter les sous-tâches en parallèle ou séquentiellement selon les dépendances"""
        results = []
        completed = set()
        
        # Vérifier que nous avons des agents
        if not self.sub_agents:
            self.logger.error("Aucun agent disponible pour exécuter les tâches!")
            await self._create_base_agents()
            
        while len(completed) < len(subtasks):
            # Trouver les tâches exécutables (sans dépendances non satisfaites)
            executable = []
            for i, (task, data) in enumerate(zip(subtasks, subtasks_data)):
                if i not in completed:
                    deps = data.get('dependencies', [])
                    if all(int(d) - 1 in completed for d in deps if d.isdigit()):
                        executable.append((i, task, data))
            
            if not executable:
                self.logger.error("Deadlock détecté dans les dépendances!")
                break
            
            # Exécuter les tâches en parallèle
            batch_tasks = []
            for idx, task, data in executable:
                # Assigner à l'agent approprié
                agent_info = self._find_suitable_agent(data.get('type', 'general'))
                if not agent_info:
                    self.logger.error(f"Aucun agent trouvé pour la tâche {task.description}")
                    task.status = TaskStatus.FAILED
                    task.error = "Aucun agent disponible"
                    results.append({"error": "Aucun agent disponible"})
                    completed.add(idx)
                    continue
                    
                task.assigned_agent = agent_info
                task.status = TaskStatus.EXECUTING
                
                # Créer le contexte avec les résultats des dépendances
                context = self._build_context(data.get('dependencies', []), results)
                
                # Exécuter
                batch_tasks.append(self._execute_single_task(task, data, agent_info, context))
            
            # Attendre la complétion du batch
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Traiter les résultats
                j = 0
                for (idx, task, data) in executable:
                    if task.status == TaskStatus.FAILED:
                        continue
                        
                    result = batch_results[j]
                    j += 1
                    
                    if isinstance(result, Exception):
                        self.logger.error(f"Erreur sous-tâche {idx+1}: {str(result)}")
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                        results.append({"error": str(result)})
                    else:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        results.append(result)
                        self.logger.info(f"Sous-tâche {idx+1} complétée")
                    
                    completed.add(idx)
        
        return results
    
    async def _execute_single_task(self, task: Task, data: Dict, agent: Any, context: str) -> Dict[str, Any]:
        """Exécuter une seule sous-tâche avec un agent"""
        self.logger.info(f"Exécution de: {task.description}")
        self.logger.info(f"Agent assigné: {agent['agent'].name}")
        
        # Mettre à jour les croyances de l'agent
        await agent['agent'].update_beliefs({
            "current_task": task.description,
            "task_type": data.get('type', 'general'),
            "context": context
        })
        
        # Pour les agents cognitifs/hybrid, utiliser le LLM
        if hasattr(agent['agent'], 'llm_service'):
            # Créer le format attendu par solve_subtask
            subtask_data = {
                'description': task.description,
                'type': data.get('type', 'general')
            }
            result = await self.llm_service.solve_subtask(subtask_data, context)
        else:
            # Pour les agents reflexive, simulation simple
            result = {
                "solution": f"Tâche {task.description} traitée",
                "output": "Résultat simulé"
            }
        
        # Si des fichiers doivent être créés
        if result and self.filesystem_tool and result.get('files_to_create'):
            try:
                # Créer un projet pour cette tâche si nécessaire
                project_name = f"task_{task.id[:8]}"
                project_result = await self.filesystem_tool.execute(
                    action="create_directory",
                    agent_id=str(self.agent_id),
                    project_name=project_name
                )
                
                if project_result.success:
                    result['project_path'] = project_result.data['project_path']
                    self.logger.info(f"Projet créé: {project_result.data['project_path']}")
                    
                    # Créer chaque fichier
                    created_files = []
                    for file_info in result['files_to_create']:
                        file_path = f"projects/{self.agent_id}/{project_name}/{file_info['path']}"
                        
                        file_result = await self.filesystem_tool.execute(
                            action="write",
                            file_path=file_path,
                            content=sanitize_unicode(file_info['content']),
                            agent_id=str(self.agent_id)
                        )
                        
                        if file_result.success:
                            created_files.append({
                                'path': file_result.data['file_path'],
                                'size': file_result.data['size']
                            })
                            self.logger.info(f"Fichier créé: {file_info['path']}")
                        else:
                            self.logger.error(f"Erreur création fichier {file_info['path']}: {file_result.error}")
                    
                    result['created_files'] = created_files
                    
            except Exception as e:
                self.logger.error(f"Erreur lors de la création des fichiers: {e}")
        
        return result
    
    def _find_suitable_agent(self, task_type: str) -> Optional[Dict[str, Any]]:
        """Trouver l'agent le plus adapté pour un type de tâche"""
        type_mapping = {
            "research": "analyst",
            "analysis": "analyst",
            "code": "developer",
            "coding": "developer",
            "creative": "creative",
            "writing": "creative",
            "validation": "validator",
            "testing": "validator"
        }
        
        preferred_role = type_mapping.get(task_type, "coordinator")
        
        # Chercher un agent avec le rôle préféré
        for agent_info in self.sub_agents:
            if agent_info['role'] == preferred_role:
                return agent_info
        
        # Sinon prendre le coordinateur par défaut
        for agent_info in self.sub_agents:
            if agent_info['role'] == "coordinator":
                return agent_info
        
        # En dernier recours, prendre le premier disponible
        return self.sub_agents[0] if self.sub_agents else None
    
    def _build_context(self, dependencies: List[str], results: List[Any]) -> str:
        """Construire le contexte à partir des résultats des dépendances"""
        context_parts = []
        for dep in dependencies:
            if dep.isdigit():
                idx = int(dep) - 1
                if 0 <= idx < len(results):
                    context_parts.append(f"Résultat tâche {dep}: {safe_json_dumps(results[idx], indent=2)}")
        
        return "\n".join(context_parts) if context_parts else "Aucun contexte de dépendance"
    
    async def _generate_report(self, task: Task, result: Dict[str, Any]):
        """Générer un rapport détaillé avec gestion appropriée de l'encodage"""
        report_file = f"/app/logs/rapport_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            # Sanitize all string values in the result
            task_desc = sanitize_unicode(task.description)
            duration = sanitize_unicode(result.get('duration', 'N/A'))
            success_rate = result.get('success_rate', 0)
            
            # Safely extract analysis data
            analysis = result.get('analysis', {})
            analysis_type = sanitize_unicode(analysis.get('type', 'N/A'))
            complexity = sanitize_unicode(analysis.get('complexity', 'N/A'))
            domains = [sanitize_unicode(d) for d in analysis.get('domains', [])]
            approach = sanitize_unicode(analysis.get('approach', 'N/A'))
            
            report = f"""# Rapport d'Exécution Autonome

## Requête
{task_desc}

## Métadonnées
- **ID**: {task.id}
- **Statut**: {task.status.value}
- **Durée**: {duration}
- **Taux de succès**: {success_rate:.1f}%

## Analyse Initiale
- **Type**: {analysis_type}
- **Complexité**: {complexity}
- **Domaines**: {', '.join(domains)}
- **Approche**: {approach}

## Exécution des Sous-tâches

"""
            
            for i, (subtask, st_result, validation) in enumerate(zip(task.subtasks, 
                                                                     result['subtasks_results'], 
                                                                     result['validations'])):
                # Sanitize subtask data
                subtask_desc = sanitize_unicode(subtask.description)
                agent_name = sanitize_unicode(subtask.assigned_agent['agent'].name) if subtask.assigned_agent else 'N/A'
                verdict = sanitize_unicode(validation.get('final_verdict', 'N/A'))
                solution = sanitize_unicode(st_result.get('solution', 'N/A'))
                
                report += f"""### Sous-tâche {i+1}: {subtask_desc}
- **Statut**: {subtask.status.value}
- **Agent**: {agent_name}
- **Validation**: {verdict} (Score: {validation.get('score', 0)}/100)

**Solution**:
{solution}

"""
                
                if st_result.get('code'):
                    code = sanitize_unicode(st_result['code'])
                    report += f"""**Code généré**:
```python
{code}
```

"""
                
                if st_result.get('created_files'):
                    report += f"""**Fichiers créés**:
"""
                    for file in st_result['created_files']:
                        file_path = sanitize_unicode(file['path'])
                        report += f"- `{file_path}` ({file['size']} octets)\n"
                    report += "\n"
                
                if st_result.get('project_path'):
                    project_path = sanitize_unicode(st_result['project_path'])
                    report += f"""**Projet créé dans**: `{project_path}`

"""
        
            report += f"""## Résumé
- Toutes les sous-tâches ont été exécutées
- {sum(1 for v in result['validations'] if v.get('is_valid', False))} validations réussies sur {len(result['validations'])}
- Rapport généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
            # Final sanitization of the entire report
            report = sanitize_unicode(report)
            
            # Write with error handling
            with open(report_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(report)
            
            self.logger.info(f"Rapport généré: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Try to write a minimal error report
            try:
                error_report = f"""# Rapport d'Erreur

Une erreur s'est produite lors de la génération du rapport complet.

Erreur: {sanitize_unicode(str(e))}

Veuillez consulter les logs pour plus de détails.
"""
                with open(report_file, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(error_report)
                self.logger.info(f"Rapport d'erreur minimal généré: {report_file}")
            except:
                self.logger.error("Impossible de générer même un rapport minimal")
    
    async def cleanup(self):
        """Nettoyer les ressources"""
        self.logger.info("Nettoyage des ressources...")
        
        for agent_info in self.sub_agents:
            try:
                await self.runtime.stop_agent(agent_info['agent'].agent_id)
                self.logger.info(f"Agent {agent_info['agent'].name} arrêté")
            except Exception as e:
                self.logger.error(f"Erreur arrêt agent: {e}")
        
        self.logger.info("Nettoyage terminé")


async def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("🤖 AGENT AUTONOME COMPLET - RÉSOLUTION DE REQUÊTES")
    print("="*80)
    print("\nCet agent peut résoudre n'importe quelle requête de manière autonome.")
    print("Il décompose, planifie, exécute et valide automatiquement.")
    print(f"\nTous les logs sont enregistrés dans: {LOG_FILE}")
    print("="*80)
    
    # Créer l'agent autonome
    agent = AutonomousAgent()
    await agent.initialize()
    
    try:
        while True:
            print("\n" + "-"*60)
            request = input("📝 Entrez votre requête (ou 'quit' pour terminer):\n> ").strip()
            
            if request.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Arrêt de l'agent...")
                break
            
            if not request:
                print("❌ Requête vide, veuillez réessayer.")
                continue
            
            print("\n🚀 Traitement en cours...")
            print("(Consultez les logs pour le détail de l'exécution)")
            
            # Traiter la requête
            result = await agent.process_request(request)
            
            # Afficher le résumé
            print("\n" + "="*60)
            print("✅ RÉSULTAT")
            print("="*60)
            print(f"Statut: {result['status']}")
            print(f"Durée: {result.get('duration', 'N/A')}")
            
            if result['status'] == 'completed':
                print(f"Sous-tâches exécutées: {result.get('subtasks_count', 0)}")
                print(f"Taux de succès: {result.get('success_rate', 0):.1f}%")
                print("\n📄 Un rapport détaillé a été généré")
                
                # Afficher les fichiers créés
                total_files = 0
                for st_result in result.get('subtasks_results', []):
                    if st_result.get('created_files'):
                        total_files += len(st_result['created_files'])
                        
                if total_files > 0:
                    print(f"\n📁 {total_files} fichier(s) créé(s) dans agent_workspace")
            else:
                print(f"Erreur: {result.get('error', 'Erreur inconnue')}")
            
            print("\n💡 Consultez les fichiers de log pour tous les détails")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption détectée...")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {str(e)}")
        logger.error(f"Erreur fatale: {str(e)}", exc_info=True)
    finally:
        await agent.cleanup()
        print("\n✅ Agent arrêté proprement")
        print(f"📁 Logs disponibles dans: {LOG_FILE}")


if __name__ == "__main__":
    # Exemples de requêtes que l'agent peut traiter:
    print("\n📌 Exemples de requêtes:")
    print("- Créer un test unitaire simple en Python pour une fonction qui additionne deux nombres")
    print("- Créer une application web de gestion de tâches avec React et FastAPI")
    print("- Analyser les tendances du marché de l'IA et proposer une stratégie d'investissement")
    print("- Écrire un article de blog sur les meilleures pratiques DevOps")
    print("- Développer un algorithme de recommandation pour un e-commerce")
    print("- Créer un plan de migration cloud pour une entreprise")
    
    asyncio.run(main())