#!/usr/bin/env python3
"""
Fully Autonomous Agent – Corrected Version
Solves any request autonomously
Uses the MAS framework with cognitive agents, LLM, and full logging
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

# -----------------------------------------------------------------------------
# Full logging configuration
# -----------------------------------------------------------------------------
# Create the logs directory if it does not exist
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

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def sanitize_unicode(text: str) -> str:
    """Sanitize Unicode text by removing surrogate characters and normalizing.

    Args:
        text: The text to sanitize

    Returns:
        Sanitized text safe for UTF‑8 encoding
    """
    if not isinstance(text, str):
        return str(text)

    # Remove surrogate characters (U+D800 to U+DFFF) which are invalid in UTF‑8
    text = re.sub(r'[\ud800-\udfff]', '', text)

    # Normalize Unicode to NFC (Canonical Decomposition followed by Canonical Composition)
    text = unicodedata.normalize('NFC', text)

    cleaned: List[str] = []
    for char in text:
        try:
            char.encode('utf-8')
            cleaned.append(char)
        except UnicodeEncodeError:
            ascii_repr = unicodedata.normalize('NFKD', char).encode('ascii', 'ignore').decode('ascii')
            if ascii_repr:
                cleaned.append(ascii_repr)
            else:
                # Skip the character if it can't be represented
                pass
    
    return ''.join(cleaned)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely convert an object to a JSON string with proper encoding.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string with sanitized Unicode
    """
    kwargs['ensure_ascii'] = False  # Allow Unicode characters
    json_str = json.dumps(obj, **kwargs)
    return sanitize_unicode(json_str)

# -----------------------------------------------------------------------------
# Core data structures
# -----------------------------------------------------------------------------

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
    metadata: Dict[str, Any] = None
    result: Any = None
    error: str = None
    created_at: float = None
    completed_at: float = None

    def __post_init__(self):
        if self.subtasks is None:
            self.subtasks = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = time.time()

# -----------------------------------------------------------------------------
# LLM Service with extended logging
# -----------------------------------------------------------------------------

class AutonomousLLMService(LLMService):
    """Extended LLM service with full logging"""

    def __init__(self):
        super().__init__()
        self.llm_logger = logging.getLogger("LLM_SERVICE")

    async def analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze a request to understand its nature and complexity."""
        prompt = f"""Analyze the following request and determine its type, complexity, and how it should be tackled.

Request: {request}

Return a JSON object with:
{{
    "type": "technical|business|creative|research|other",
    "complexity": "simple|medium|complex|very_complex",
    "domains": ["list", "of", "domains"],
    "requires_code": true/false,
    "requires_research": true/false,
    "requires_creativity": true/false,
    "estimated_subtasks": number,
    "approach": "recommended approach"
}}"""

        self.llm_logger.info(f"Request analysis: {sanitize_unicode(request[:100])}…")
        result = await self.generate(prompt, json_response=True)
        self.llm_logger.info(f"Analysis result: {sanitize_unicode(str(result))}")
        return result.get('response', {})

    async def decompose_task(self, task: str, analysis: Dict[str, Any]) -> List[str]:
        """Break a task down into concrete, actionable subtasks."""
        prompt = f"""Decompose the following task into concrete, actionable subtasks.

Task: {task}
Analysis: {safe_json_dumps(analysis, indent=2)}

Create an ordered list of subtasks that together fully accomplish the main task. Each subtask must be:
- Specific and actionable
- Independent or with clear dependencies
- Performable by a specialised agent

Return JSON:
{{
    "subtasks": [
        {{
            "id": "1",
            "description": "clear description",
            "type": "research|code|analysis|creative|validation",
            "dependencies": ["IDs of prerequisite tasks"],
            "estimated_time": "in minutes"
        }}
    ]
}}"""
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {}).get('subtasks', [])

    async def solve_subtask(self, subtask: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Solve a specific subtask."""
        prompt = f"""Solve the following subtask in a complete and detailed manner.

Subtask: {subtask['description']}
Type: {subtask.get('type', 'general')}
Context: {context}

IMPORTANT – PROJECT STRUCTURE:
All files must follow the standard Python project structure:
- src/ : main source code
  - src/core/ : core business logic
  - src/models/ : data models
  - src/services/ : services & integrations
  - src/utils/ : utilities & helpers
- tests/ : unit & integration tests
  - tests/unit/ : unit tests
  - tests/integration/ : integration tests
- docs/ : documentation
- config/ : configuration files
- scripts/ : utility scripts

When creating files:
- DO NOT create directories specific to the task
- ONLY use paths relative to the project root
- Place each file in the appropriate directory according to its purpose

Provide a complete solution with:
- Detailed steps
- Code if required
- Clear explanations
- Validation steps

Return JSON:
{{
    "solution": "detailed description",
    "code": "code if applicable",
    "steps": ["step 1", "step 2", …],
    "validation": "how to verify correctness",
    "output": "concrete output",
    "files_to_create": [
        {{
            "path": "relative/path/file.py",
            "content": "full file content",
            "description": "file description"
        }}
    ]
}}

Correct path examples:
- "main.py" for a main file
- "calculator.py" for a simple module
- "test_calculator.py" for a unit test
- "api_service.py" for a service
- "user_model.py" for a data model
- "README.md" for documentation"""
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})

    async def validate_solution(self, task: str, solution: Any) -> Dict[str, Any]:
        """Validate a proposed solution."""
        prompt = f"""Validate the following solution for the given task.

Task: {task}
Proposed solution: {safe_json_dumps(solution, indent=2) if isinstance(solution, dict) else sanitize_unicode(str(solution))}

Assess:
1. Completeness of the solution
2. Technical quality
3. Areas for improvement
4. Overall score (0–100)

Return JSON:
{{
    "is_valid": true/false,
    "score": 85,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1"],
    "improvements": ["suggested improvement"],
    "final_verdict": "accepted|needs_revision|rejected"
}}"""
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})

# -----------------------------------------------------------------------------
# Main autonomous agent class
# -----------------------------------------------------------------------------

class AutonomousAgent:
    """Fully autonomous main agent."""

    def __init__(self):
        self.agent_id = uuid4()
        self.name = f"AutonomousAgent-{self.agent_id}"
        self.llm_service = AutonomousLLMService()
        self.factory = AgentFactory()
        self.runtime = get_agent_runtime()
        self.tool_service = ToolService()
        self.filesystem_tool = None  # Will be initialised in initialise()
        self.sub_agents = []
        self.tasks: List[Task] = []
        self.results: Dict[str, Any] = {}
        self.initialised = False  # To check whether init has been run
        self.current_project_path: Optional[str] = None  # Main project path
        self.project_structure: Optional[Dict[str, Any]] = None  # Project structure to maintain
        self.max_depth = 2  # Maximum decomposition depth

        # Main logger
        self.logger = logging.getLogger("AUTONOMOUS_AGENT")
        self.logger.info(f"Initialising {self.name}")

    async def initialise(self):
        """Initialise the agent and its resources."""
        if self.initialised:
            self.logger.info("Agent already initialised")
            return

        self.logger.info("Initialising resources…")

        # Retrieve FileSystemTool
        try:
            self.filesystem_tool = self.tool_service.registry.get_tool("filesystem")
            if self.filesystem_tool:
                self.logger.info("FileSystemTool successfully loaded")
            else:
                self.logger.warning("FileSystemTool not available")
        except Exception as e:
            self.logger.error(f"FileSystemTool loading error: {e}")

        # Create baseline agents
        await self._create_base_agents()

        self.initialised = True
        self.logger.info("Autonomous agent ready")

    async def _create_base_agents(self):
        """Create the base agents for different task types."""
        agent_configs = [
            {
                "name": "Analyst",
                "type": "cognitive",
                "role": "analyst",
                "capabilities": ["analysis", "research", "data_processing"]
            },
            {
                "name": "Developer",
                "type": "hybrid",
                "role": "developer",
                "capabilities": ["coding", "debugging", "optimization"]
            },
            {
                "name": "Creative",
                "type": "cognitive",
                "role": "creative",
                "capabilities": ["writing", "design", "ideation"]
            },
            {
                "name": "Validator",
                "type": "hybrid",
                "role": "validator",
                "capabilities": ["testing", "quality_assurance", "verification"]
            },
            {
                "name": "Coordinator",
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

                # Add reactive rules for hybrid agents
                if config["type"] == "hybrid":
                    agent_data["reactive_rules"] = {
                        "urgent_task": "prioritize_execution",
                        "error_detected": "debug_and_fix",
                        "validation_needed": "run_validation"
                    }

                # Instantiate according to type
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

                self.logger.info(f"Agent created: {agent.name} ({config['role']})")

            except Exception as e:
                self.logger.error(f"Agent creation error {config['name']}: {str(e)}")
                self.logger.error(traceback.format_exc())

    # ---------------------------------------------------------------------
    # Task decomposition helpers
    # ---------------------------------------------------------------------

    async def _recursive_decompose_task(self, task: Task, analysis: Dict[str, Any], depth: int = 1) -> None:
        """Recursively decompose a task into subtasks."""
        if depth > self.max_depth:
            return

        subtasks_data = await self.llm_service.decompose_task(task.description, analysis)
        if not subtasks_data:
            return

        for st_data in subtasks_data:
            subtask = Task(
                id=st_data.get('id', str(uuid4())),
                description=st_data.get('description', ''),
                status=TaskStatus.PENDING,
                metadata=st_data
            )
            task.subtasks.append(subtask)

            sub_analysis = await self.llm_service.analyze_request(subtask.description)
            await self._recursive_decompose_task(subtask, sub_analysis, depth + 1)

    def _collect_leaf_tasks(self, task: Task) -> List[Task]:
        """Collect all tasks without subtasks recursively."""
        if not task.subtasks:
            return [task]

        leaves: List[Task] = []
        for st in task.subtasks:
            leaves.extend(self._collect_leaf_tasks(st))
        return leaves

    # ---------------------------------------------------------------------
    # Main request processing pipeline
    # ---------------------------------------------------------------------

    async def process_request(self, request: str) -> Dict[str, Any]:
        """Process a user request autonomously."""
        if not self.initialised:
            await self.initialise()

        self.logger.info("=" * 80)
        self.logger.info(f"NEW REQUEST: {request}")
        self.logger.info("=" * 80)

        main_task = Task(
            id=str(uuid4()),
            description=request,
            status=TaskStatus.ANALYZING
        )
        self.tasks.append(main_task)

        await self._initialize_project_structure(main_task)

        try:
            # 1. Analyse the request
            self.logger.info("Phase 1: Request analysis")
            analysis = await self.llm_service.analyze_request(request)
            self.logger.info(f"Analysis completed: {safe_json_dumps(analysis, indent=2)}")

            # 2. Decompose into subtasks
            main_task.status = TaskStatus.PLANNING
            self.logger.info("Phase 2: Task decomposition")
            await self._recursive_decompose_task(main_task, analysis, depth=1)
            leaf_tasks = self._collect_leaf_tasks(main_task)
            self.logger.info(f"Subtasks created: {len(leaf_tasks)}")

            # 3. Execute subtasks
            main_task.status = TaskStatus.EXECUTING
            self.logger.info("Phase 3: Executing subtasks")
            results = await self._execute_subtasks(leaf_tasks)

            # 4. Validate results
            main_task.status = TaskStatus.VALIDATING
            self.logger.info("Phase 4: Validating results")
            validation_results = []
            for i, result in enumerate(results):
                validation = await self.llm_service.validate_solution(leaf_tasks[i].description, result)
                validation_results.append(validation)
                self.logger.info(f"Subtask validation {i + 1}: {validation.get('final_verdict', 'unknown')}")

            # 5. Aggregate results
            main_task.status = TaskStatus.COMPLETED
            main_task.completed_at = time.time()
            duration = main_task.completed_at - main_task.created_at

            success_count = sum(1 for v in validation_results if v.get('is_valid', False))
            success_rate = (success_count / len(validation_results) * 100) if validation_results else 0

            final_result = {
                "request": request,
                "status": "completed",
                "duration": f"{duration:.2f} seconds",
                "analysis": analysis,
                "subtasks_count": len(leaf_tasks),
                "subtasks_results": results,
                "validations": validation_results,
                "success_rate": success_rate
            }
            main_task.result = final_result

            await self._generate_report(main_task, final_result)
            self.logger.info("=" * 80)
            self.logger.info("REQUEST SUCCESSFULLY COMPLETED")
            self.logger.info(f"Total duration: {duration:.2f}s")
            self.logger.info(f"Success rate: {final_result['success_rate']:.1f}%")
            self.logger.info("=" * 80)
            return final_result

        except Exception as e:
            main_task.status = TaskStatus.FAILED
            main_task.error = str(e)
            self.logger.error(f"Error during processing: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "request": request,
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    # ---------------------------------------------------------------------
    # Subtask execution helpers
    # ---------------------------------------------------------------------

    async def _execute_subtasks(self, subtasks: List[Task]) -> List[Any]:
        """Execute subtasks considering their dependencies."""
        results: List[Any] = []
        completed: set = set()

        if not self.sub_agents:
            self.logger.error("No agents available to execute tasks!")
            await self._create_base_agents()

        while len(completed) < len(subtasks):
            executable = []
            for i, task in enumerate(subtasks):
                if i in completed:
                    continue
                deps = task.metadata.get('dependencies', [])
                if all(int(d) - 1 in completed for d in deps if isinstance(d, str) and d.isdigit()):
                    executable.append((i, task))

            if not executable:
                self.logger.error("Dependency deadlock detected!")
                break

            batch_tasks = []
            for idx, task in executable:
                agent_info = self._find_suitable_agent(task.metadata.get('type', 'general'))
                if not agent_info:
                    self.logger.error(f"No agent found for task {task.description}")
                    task.status = TaskStatus.FAILED
                    task.error = "No agent available"
                    results.append({"error": "No agent available"})
                    completed.add(idx)
                    continue

                task.assigned_agent = agent_info
                task.status = TaskStatus.EXECUTING
                context = self._build_context(task.metadata.get('dependencies', []), results)
                batch_tasks.append(self._execute_single_task(task, agent_info, context))

            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                j = 0
                for (idx, task) in executable:
                    if task.status == TaskStatus.FAILED:
                        completed.add(idx)
                        continue

                    result = batch_results[j]
                    j += 1

                    if isinstance(result, Exception):
                        self.logger.error(f"Subtask error {idx + 1}: {str(result)}")
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                        results.append({"error": str(result)})
                    else:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        results.append(result)
                        self.logger.info(f"Subtask {idx + 1} completed")
                    completed.add(idx)
        return results

    # ---------------------------------------------------------------------
    # Project initialisation helpers
    # ---------------------------------------------------------------------

    async def _initialize_project_structure(self, main_task: Task):
        """Initialise the main project structure for this request."""
        if not self.filesystem_tool:
            return

        project_name = f"project_{main_task.id[:8]}"
        try:
            project_result = await self.filesystem_tool.execute(
                action="create_directory",
                agent_id=str(self.agent_id),
                project_name=project_name
            )
            if project_result.success:
                self.current_project_path = project_result.data['project_path']
                self.logger.info(f"Main project created: {self.current_project_path}")

                self.project_structure = {
                    "src": {
                        "__init__.py": "",
                        "core": {"__init__.py": ""},
                        "utils": {"__init__.py": ""},
                        "services": {"__init__.py": ""},
                        "models": {"__init__.py": ""}
                    },
                    "tests": {
                        "__init__.py": "",
                        "unit": {"__init__.py": ""},
                        "integration": {"__init__.py": ""}
                    },
                    "docs": {},
                    "config": {},
                    "scripts": {},
                    "requirements.txt": "",
                    "setup.py": "",
                    "README.md": f"# {project_name}\n\nAutomatically generated project for: {main_task.description}\n",
                    ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n.DS_Store\n"
                }
                await self._create_project_structure(self.current_project_path, self.project_structure)
        except Exception as e:
            self.logger.error(f"Error during project structure initialisation: {e}")

    async def _create_project_structure(self, base_path: str, structure: Dict, parent_path: str = ""):
        """Recursively create the project structure."""
        for name, content in structure.items():
            path = os.path.join(parent_path, name) if parent_path else name
            full_path = os.path.join(base_path, path)

            if isinstance(content, dict):
                os.makedirs(full_path, exist_ok=True)
                await self._create_project_structure(base_path, content, path)
            else:
                try:
                    file_result = await self.filesystem_tool.execute(
                        action="write",
                        file_path=full_path,
                        content=content,
                        agent_id=str(self.agent_id)
                    )
                    if file_result.success:
                        self.logger.debug(f"File created: {path}")
                except Exception as e:
                    self.logger.error(f"File creation error {path}: {e}")

    # ---------------------------------------------------------------------
    # File location helper
    # ---------------------------------------------------------------------

    def _determine_file_location(self, file_info: Dict[str, Any]) -> str:
        """Determine the correct location for a file within the project."""
        file_path = file_info['path']
        lower_path = file_path.lower()

        if 'test' in lower_path:
            if 'unit' in lower_path:
                return f"tests/unit/{os.path.basename(file_path)}"
            if 'integration' in lower_path:
                return f"tests/integration/{os.path.basename(file_path)}"
            return f"tests/{os.path.basename(file_path)}"

        if file_path.endswith('.py'):
            if 'model' in lower_path:
                return f"src/models/{os.path.basename(file_path)}"
            if 'service' in lower_path:
                return f"src/services/{os.path.basename(file_path)}"
            if 'util' in lower_path or 'helper' in lower_path:
                return f"src/utils/{os.path.basename(file_path)}"
            if 'core' in lower_path or 'main' in lower_path:
                return f"src/core/{os.path.basename(file_path)}"
            return f"src/{os.path.basename(file_path)}"

        if file_path.endswith('.md'):
            return f"docs/{os.path.basename(file_path)}"

        if file_path.endswith(('.json', '.yaml', '.yml', '.ini', '.conf')):
            return f"config/{os.path.basename(file_path)}"

        if file_path.endswith('.sh') or 'script' in lower_path:
            return f"scripts/{os.path.basename(file_path)}"

        return os.path.basename(file_path)

    # ---------------------------------------------------------------------
    # Individual subtask execution
    # ---------------------------------------------------------------------

    async def _execute_single_task(self, task: Task, agent: Any, context: str) -> Dict[str, Any]:
        """Execute a single subtask with an assigned agent."""
        self.logger.info(f"Executing: {task.description}")
        self.logger.info(f"Assigned agent: {agent['agent'].name}")

        await agent['agent'].update_beliefs({
            "current_task": task.description,
            "task_type": task.metadata.get('type', 'general'),
            "context": context,
            "project_structure_rules": {
                "message": "FOLLOW THE PROJECT STRUCTURE",
                "src_for_code": True,
                "tests_for_tests": True,
                "no_task_specific_dirs": True,
                "use_relative_paths": True
            }
        })

        if hasattr(agent['agent'], 'llm_service'):
            subtask_data = {
                'description': task.description,
                'type': task.metadata.get('type', 'general')
            }
            result = await self.llm_service.solve_subtask(subtask_data, context)
        else:
            result = {
                "solution": f"Task {task.description} processed",
                "output": "Simulated result"
            }

        if result and self.filesystem_tool and result.get('files_to_create'):
            try:
                if not self.current_project_path:
                    self.logger.error("No main project initialised")
                    return result

                result['project_path'] = self.current_project_path
                self.logger.info(f"Using main project: {self.current_project_path}")

                created_files = []
                for file_info in result['files_to_create']:
                    structured_path = self._determine_file_location(file_info)
                    full_path = os.path.join(self.current_project_path, structured_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    file_result = await self.filesystem_tool.execute(
                        action="write",
                        file_path=full_path,
                        content=sanitize_unicode(file_info['content']),
                        agent_id=str(self.agent_id)
                    )
                    if file_result.success:
                        created_files.append({
                            'path': structured_path,
                            'full_path': file_result.data['file_path'],
                            'size': file_result.data['size']
                        })
                        self.logger.info(f"File created within structure: {structured_path}")
                        await agent['agent'].update_beliefs({
                            f"file_created_{os.path.basename(structured_path)}": structured_path
                        })
                    else:
                        self.logger.error(f"File creation error {structured_path}: {file_result.error}")

                result['created_files'] = created_files
                await self._share_project_structure_with_agents()
            except Exception as e:
                self.logger.error(f"Error during file creation: {e}")
        return result

    async def _share_project_structure_with_agents(self):
        """Share the project structure with all agents."""
        project_info = {
            "project_path": self.current_project_path,
            "structure": self.project_structure,
            "message": "All files must be created in this structure"
        }
        for agent_info in self.sub_agents:
            try:
                await agent_info['agent'].update_beliefs({
                    "project_structure": project_info,
                    "working_directory": self.current_project_path
                })
                self.logger.debug(f"Structure shared with {agent_info['agent'].name}")
            except Exception as e:
                self.logger.error(f"Error sharing structure with {agent_info['agent'].name}: {e}")

    # ---------------------------------------------------------------------
    # Agent lookup helpers
    # ---------------------------------------------------------------------

    def _find_suitable_agent(self, task_type: str) -> Optional[Dict[str, Any]]:
        """Find the most suitable agent for a task type."""
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
        for agent_info in self.sub_agents:
            if agent_info['role'] == preferred_role:
                return agent_info
        for agent_info in self.sub_agents:
            if agent_info['role'] == "coordinator":
                return agent_info
        return self.sub_agents[0] if self.sub_agents else None

    # ---------------------------------------------------------------------
    # Context builder
    # ---------------------------------------------------------------------

    def _build_context(self, dependencies: List[str], results: List[Any]) -> str:
        """Build context string from dependency results."""
        context_parts = []
        for dep in dependencies:
            if dep.isdigit():
                idx = int(dep) - 1
                if 0 <= idx < len(results):
                    context_parts.append(f"Task result {dep}: {safe_json_dumps(results[idx], indent=2)}")
        return "\n".join(context_parts) if context_parts else "No dependency context"

    # ---------------------------------------------------------------------
    # Report generation
    # ---------------------------------------------------------------------

    async def _generate_report(self, task: Task, result: Dict[str, Any]):
        """Generate a detailed execution report with proper encoding handling."""
        report_file = f"/app/logs/report_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        try:
            task_desc = sanitize_unicode(task.description)
            duration = sanitize_unicode(result.get('duration', 'N/A'))
            success_rate = result.get('success_rate', 0)
            analysis = result.get('analysis', {})
            analysis_type = sanitize_unicode(analysis.get('type', 'N/A'))
            complexity = sanitize_unicode(analysis.get('complexity', 'N/A'))
            domains = [sanitize_unicode(d) for d in analysis.get('domains', [])]
            approach = sanitize_unicode(analysis.get('approach', 'N/A'))

            report = f"""# Autonomous Execution Report

## Request
{task_desc}

## Metadata
- **ID**: {task.id}
- **Status**: {task.status.value}
- **Duration**: {duration}
- **Success rate**: {success_rate:.1f}%

## Initial Analysis
- **Type**: {analysis_type}
- **Complexity**: {complexity}
- **Domains**: {', '.join(domains)}
- **Approach**: {approach}

## Subtask Execution

"""
            leaf_tasks = self._collect_leaf_tasks(task)
            for i, (subtask, st_result, validation) in enumerate(zip(leaf_tasks, result['subtasks_results'], result['validations'])):
                subtask_desc = sanitize_unicode(subtask.description)
                agent_name = sanitize_unicode(subtask.assigned_agent['agent'].name) if subtask.assigned_agent else 'N/A'
                verdict = sanitize_unicode(validation.get('final_verdict', 'N/A'))
                solution = sanitize_unicode(st_result.get('solution', 'N/A'))

                report += f"""### Subtask {i + 1}: {subtask_desc}
- **Status**: {subtask.status.value}
- **Agent**: {agent_name}
- **Validation**: {verdict} (Score: {validation.get('score', 0)}/100)

**Solution**:
{solution}

"""
                if st_result.get('code'):
                    code = sanitize_unicode(st_result['code'])
                    report += f"""**Generated code**:
```python
{code}
```

"""
                if st_result.get('created_files'):
                    report += "**Created files**:\n"
                    for file in st_result['created_files']:
                        file_path = sanitize_unicode(file['path'])
                        report += f"- `{file_path}` ({file['size']} bytes)\n"
                    report += "\n"
                if st_result.get('project_path'):
                    project_path = sanitize_unicode(st_result['project_path'])
                    report += f"**Project located at**: `{project_path}`\n\n"

            report += f"""## Summary
- All subtasks executed
- {sum(1 for v in result['validations'] if v.get('is_valid', False))} successful validations out of {len(result['validations'])}
- Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            report = sanitize_unicode(report)
            with open(report_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(report)
            self.logger.info(f"Report generated: {report_file}")
        except Exception as e:
            self.logger.error(f"Error during report generation: {str(e)}")
            self.logger.error(traceback.format_exc())
            try:
                error_report = f"""# Error Report

An error occurred while generating the full report.

Error: {sanitize_unicode(str(e))}

Please check the logs for details.
"""
                with open(report_file, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(error_report)
                self.logger.info(f"Minimal error report generated: {report_file}")
            except Exception:
                self.logger.error("Unable to generate even a minimal report")

    # ---------------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------------

    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up resources…")
        for agent_info in self.sub_agents:
            try:
                await self.runtime.stop_agent(agent_info['agent'].agent_id)
                self.logger.info(f"Agent {agent_info['agent'].name} stopped")
            except Exception as e:
                self.logger.error(f"Error stopping agent: {e}")
        self.logger.info("Cleanup complete")

# -----------------------------------------------------------------------------
# Entry‑point
# -----------------------------------------------------------------------------

async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("🤖 FULLY AUTONOMOUS AGENT – REQUEST RESOLUTION")
    print("=" * 80)
    print("\nThis agent can autonomously solve any request.")
    print("It decomposes, plans, executes, and validates automatically.")
    print(f"\nAll logs are saved to: {LOG_FILE}")
    print("=" * 80)

    agent = AutonomousAgent()
    await agent.initialise()
    try:
        while True:
            print("\n" + "-" * 60)
            request = input("📝 Enter your request (or 'quit' to exit):\n> ").strip()
            if request.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Stopping agent…")
                break
            if not request:
                print("❌ Empty request, please try again.")
                continue
            print("\n🚀 Processing…")
            print("(See logs for detailed execution)")
            result = await agent.process_request(request)
            print("\n" + "=" * 60)
            print("✅ RESULT")
            print("=" * 60)
            print(f"Status: {result['status']}")
            print(f"Duration: {result.get('duration', 'N/A')}")
            if result['status'] == 'completed':
                print(f"Subtasks executed: {result.get('subtasks_count', 0)}")
                print(f"Success rate: {result.get('success_rate', 0):.1f}%")
                print("\n📄 A detailed report has been generated")
                total_files = sum(len(st_result.get('created_files', [])) for st_result in result.get('subtasks_results', []))
                if total_files:
                    print(f"\n📁 {total_files} file(s) created in agent_workspace")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            print("\n💡 Check the log files for all details")
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption detected…")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        await agent.cleanup()
        print("\n✅ Agent stopped cleanly")
        print(f"📁 Logs available at: {LOG_FILE}")


if __name__ == "__main__":
    # Sample requests the agent can handle
    print("\n📌 Sample requests:")
    print("- Create a simple unit test in Python for a function that adds two numbers")
    print("- Build a task management web app with React and FastAPI")
    print("- Analyse AI market trends and propose an investment strategy")
    print("- Write a blog article on DevOps best practices")
    print("- Develop a recommendation algorithm for an e‑commerce platform")
    print("- Create a cloud migration plan for a company")
    asyncio.run(main())