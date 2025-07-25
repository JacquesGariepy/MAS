#!/usr/bin/env python3
"""
Enhanced Production MAS Swarm System
Combines the power of swarm coordination with autonomous agent capabilities
Including task decomposition, 6-phase pipeline, and comprehensive reporting
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging
import json
import psutil
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import signal
from datetime import timedelta
import traceback
import unicodedata
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

# Import MAS components
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.tools.filesystem_tool import FileSystemTool
from src.tools.code_tool import CodeTool
from src.tools.git_tool import GitTool
from src.tools.web_search_tool import WebSearchTool
from src.tools.database_tool import DatabaseTool
from src.tools.http_tool import HTTPTool

# Import agents
from src.core.agents import CognitiveAgent, HybridAgent

# Import environment
from src.core.environment import (
    SoftwareEnvironment,
    TopologyType,
    VisibilityLevel,
    EnvironmentAdapter
)

# Define coordination enums locally
class CoordinationStrategy(Enum):
    CENTRALIZED = "centralized"
    DECENTRALIZED = "decentralized"
    HIERARCHICAL = "hierarchical"
    MARKET_BASED = "market_based"
    CONSENSUS = "consensus"
    EMERGENT = "emergent"

class MessagePriority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

from src.core.runtime import get_agent_runtime
from src.utils.logger import get_logger

# Configure enhanced logging
os.makedirs("/app/logs", exist_ok=True)
LOG_FILE = f"/app/logs/swarm_mas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', errors='replace'),
        logging.StreamHandler()
    ]
)
logger = get_logger("ENHANCED_PRODUCTION_SWARM")


# Task States (Enhanced)
class TaskState(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Agent States
class AgentState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"


# Helper functions from autonomous
def sanitize_unicode(text: str) -> str:
    """Sanitize Unicode text by removing surrogate characters and normalizing."""
    if not isinstance(text, str):
        return str(text)
    
    text = re.sub(r'[\ud800-\udfff]', '', text)
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
    
    return ''.join(cleaned)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely convert an object to a JSON string with proper encoding."""
    kwargs['ensure_ascii'] = False
    json_str = json.dumps(obj, **kwargs)
    return sanitize_unicode(json_str)


# Enhanced Swarm Configuration
@dataclass
class EnhancedSwarmConfig:
    """Enhanced production swarm configuration"""
    name: str = "EnhancedProductionSwarm"
    num_architects: int = 1
    num_analysts: int = 3
    num_developers: int = 5
    num_testers: int = 3
    num_devops: int = 2
    num_data_engineers: int = 2
    num_security: int = 1
    num_ml_engineers: int = 2
    
    # Performance settings
    max_agents: int = 20
    coordination_interval: float = 0.1
    monitoring_interval: float = 1.0
    checkpoint_interval: float = 60.0
    
    # Resource limits
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 8192
    
    # Task management
    max_task_queue: int = 1000
    task_timeout: float = 300.0
    max_retries: int = 3
    max_decomposition_depth: int = 3
    
    # Coordination
    enable_load_balancing: bool = True
    enable_auto_scaling: bool = True
    enable_fault_recovery: bool = True
    enable_task_decomposition: bool = True
    enable_validation: bool = True
    
    # Parallelism
    process_pool_size: int = 4
    thread_pool_size: int = 8


# Enhanced Swarm Task
@dataclass
class EnhancedSwarmTask:
    """Enhanced production task with decomposition support"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    task_type: str = "general"
    priority: MessagePriority = MessagePriority.MEDIUM
    data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0
    
    # Enhanced fields
    subtasks: List['EnhancedSwarmTask'] = field(default_factory=list)
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_score: Optional[float] = None
    analysis: Optional[Dict[str, Any]] = None


# Enhanced LLM Service
class EnhancedLLMService(LLMService):
    """Extended LLM service with autonomous capabilities"""
    
    def __init__(self):
        super().__init__()
        self.llm_logger = logging.getLogger("ENHANCED_LLM_SERVICE")
    
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
    "approach": "recommended approach",
    "agent_types_needed": ["architect", "developer", "analyst", etc.]
}}"""

        self.llm_logger.info(f"Request analysis: {sanitize_unicode(request[:100])}…")
        result = await self.generate(prompt, json_response=True)
        self.llm_logger.info(f"Analysis result: {sanitize_unicode(str(result))}")
        return result.get('response', {})
    
    async def decompose_task(self, task: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break a task down into concrete, actionable subtasks."""
        prompt = f"""Decompose the following task into concrete, actionable subtasks.

Task: {task}
Analysis: {safe_json_dumps(analysis, indent=2)}

Create an ordered list of subtasks that together fully accomplish the main task. Each subtask must be:
- Specific and actionable
- Independent or with clear dependencies
- Performable by a specialized agent

Return JSON:
{{
    "subtasks": [
        {{
            "id": "1",
            "description": "clear description",
            "type": "research|code|analysis|creative|validation|deployment",
            "dependencies": ["IDs of prerequisite tasks"],
            "estimated_time": "in minutes",
            "required_agent_type": "architect|developer|analyst|tester|devops|etc"
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
}}"""
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


# Enhanced Production Swarm Coordinator
class EnhancedProductionSwarmCoordinator:
    """Enhanced production-ready swarm coordinator with autonomous capabilities"""
    
    def __init__(self, config: Optional[EnhancedSwarmConfig] = None):
        self.config = config or EnhancedSwarmConfig()
        self.id = uuid4()
        self.name = f"{self.config.name}-{str(self.id)[:8]}"
        
        # Services
        self.llm_service = EnhancedLLMService()
        self.tool_service = ToolService()
        self.runtime = get_agent_runtime()
        
        # Environment
        self.environment = SoftwareEnvironment(TopologyType.PROCESS_TREE)
        self.adapter = EnvironmentAdapter(self.environment)
        
        # Agents
        self.agents: Dict[str, Any] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Tasks
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_task_queue)
        self.task_registry: Dict[str, EnhancedSwarmTask] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        # Coordination
        self.coordination_strategy = CoordinationStrategy.HIERARCHICAL
        self.broadcast_channel: asyncio.Queue = asyncio.Queue()
        
        # Process and thread pools
        self.process_pool: Optional[ProcessPoolExecutor] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        
        # State management
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.state_lock = asyncio.Lock()
        self.checkpoint_path = Path(f"/app/swarm_state/{self.name}")
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        # Project management
        self.current_project_path: Optional[str] = None
        self.project_structure: Optional[Dict[str, Any]] = None
        self.filesystem_tool = None
        
        # Performance tracking
        self.metrics = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_decomposed': 0,
            'tasks_validated': 0,
            'agents_created': 0,
            'messages_sent': 0,
            'coordination_cycles': 0,
            'load_balance_events': 0,
            'auto_scale_events': 0,
            'recovery_events': 0,
            'total_runtime': 0.0,
            'average_task_time': 0.0,
            'average_validation_score': 0.0
        }
        
        self.start_time = datetime.utcnow()
        
        logger.info(f"Initialized {self.name} - Enhanced Production Swarm System")
    
    async def initialize(self):
        """Initialize the enhanced production swarm"""
        logger.info(f"Initializing enhanced swarm with up to {self.config.max_agents} agents...")
        
        try:
            # Initialize filesystem tool
            self.filesystem_tool = self.tool_service.registry.get_tool("filesystem")
            if self.filesystem_tool:
                logger.info("FileSystemTool successfully loaded")
            else:
                logger.warning("FileSystemTool not available")
            
            # Create process and thread pools
            self.process_pool = ProcessPoolExecutor(max_workers=self.config.process_pool_size)
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.thread_pool_size)
            
            # Create all agent types
            await self._create_agents()
            
            # Start background tasks
            self.running = True
            await self._start_background_tasks()
            
            # Load previous state if exists
            await self._load_checkpoint()
            
            logger.info(f"✅ Enhanced swarm initialized with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize swarm: {e}")
            raise
    
    async def _create_agents(self):
        """Create all agent types"""
        # Agent configurations
        agent_configs = []
        
        # Architects
        for i in range(self.config.num_architects):
            agent_configs.append({
                'name': f'Architect-{i+1}',
                'type': CognitiveAgent,
                'role': 'architect',
                'capabilities': ['design', 'architecture', 'planning', 'system_design', 'task_decomposition'],
                'tools': [FileSystemTool, CodeTool],
                'visibility': VisibilityLevel.FULL
            })
        
        # Analysts
        for i in range(self.config.num_analysts):
            agent_configs.append({
                'name': f'Analyst-{i+1}',
                'type': CognitiveAgent,
                'role': 'analyst',
                'capabilities': ['analysis', 'research', 'requirements', 'documentation', 'validation'],
                'tools': [WebSearchTool, FileSystemTool, DatabaseTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # Developers
        for i in range(self.config.num_developers):
            agent_configs.append({
                'name': f'Developer-{i+1}',
                'type': HybridAgent,
                'role': 'developer',
                'capabilities': ['coding', 'implementation', 'debugging', 'optimization', 'solution_development'],
                'tools': [CodeTool, GitTool, FileSystemTool, DatabaseTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # Testers
        for i in range(self.config.num_testers):
            agent_configs.append({
                'name': f'Tester-{i+1}',
                'type': HybridAgent,
                'role': 'tester',
                'capabilities': ['testing', 'validation', 'quality_assurance', 'automation', 'solution_validation'],
                'tools': [CodeTool, FileSystemTool, HTTPTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # DevOps Engineers
        for i in range(self.config.num_devops):
            agent_configs.append({
                'name': f'DevOps-{i+1}',
                'type': HybridAgent,
                'role': 'devops',
                'capabilities': ['deployment', 'automation', 'monitoring', 'infrastructure'],
                'tools': [GitTool, HTTPTool, FileSystemTool, CodeTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # Data Engineers
        for i in range(self.config.num_data_engineers):
            agent_configs.append({
                'name': f'DataEngineer-{i+1}',
                'type': HybridAgent,
                'role': 'data_engineer',
                'capabilities': ['data_processing', 'etl', 'analytics', 'pipelines'],
                'tools': [DatabaseTool, CodeTool, FileSystemTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # Security Engineers
        for i in range(self.config.num_security):
            agent_configs.append({
                'name': f'Security-{i+1}',
                'type': CognitiveAgent,
                'role': 'security',
                'capabilities': ['security_analysis', 'vulnerability_assessment', 'compliance'],
                'tools': [CodeTool, FileSystemTool, WebSearchTool],
                'visibility': VisibilityLevel.FULL
            })
        
        # ML Engineers
        for i in range(self.config.num_ml_engineers):
            agent_configs.append({
                'name': f'MLEngineer-{i+1}',
                'type': HybridAgent,
                'role': 'ml_engineer',
                'capabilities': ['machine_learning', 'model_training', 'data_science'],
                'tools': [CodeTool, DatabaseTool, FileSystemTool],
                'visibility': VisibilityLevel.NAMESPACE
            })
        
        # Coordinator (Enhanced with autonomous capabilities)
        agent_configs.append({
            'name': 'SwarmCoordinator',
            'type': CognitiveAgent,
            'role': 'coordinator',
            'capabilities': ['coordination', 'orchestration', 'monitoring', 'optimization', 'planning', 'reporting'],
            'tools': [FileSystemTool],
            'visibility': VisibilityLevel.FULL
        })
        
        # Create agents in parallel
        tasks = []
        for config in agent_configs:
            tasks.append(self._create_agent(config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful creations
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"Created {success_count}/{len(agent_configs)} agents successfully")
    
    async def _create_agent(self, config: Dict[str, Any]) -> Optional[Any]:
        """Create and configure a single agent"""
        try:
            # Create agent instance
            agent_class = config['type']
            
            agent = agent_class(
                agent_id=uuid4(),
                name=f"{config['name']}-{self.name}",
                role=config['role'],
                capabilities=config['capabilities'],
                llm_service=self.llm_service
            )
            
            # Load tools
            for tool_class in config['tools']:
                if tool_class.__name__ == 'FileSystemTool':
                    tool = tool_class()
                else:
                    # Our custom tools
                    workspace = self.checkpoint_path / "workspaces" / str(agent.agent_id)
                    workspace.mkdir(parents=True, exist_ok=True)
                    tool = tool_class(
                        agent_id=str(agent.agent_id),
                        workspace_root=str(workspace)
                    )
                agent.tools[tool.name] = tool
            
            # Register with runtime
            await self.runtime.register_agent(agent)
            await self.runtime.start_agent(agent)
            
            # Register with environment
            namespace = f"swarm/{config['role']}/{config['name']}"
            await self.adapter.register_agent(agent, namespace=namespace)
            
            # Set visibility
            self.environment.observability.set_visibility(
                str(agent.agent_id),
                config['visibility']
            )
            
            # Allocate resources
            resources = {
                'cpu': 15 if 'architect' in config['role'] or 'coordinator' in config['role'] else 10,
                'memory': 1024 * 1024 * 1024  # 1GB
            }
            
            success = self.environment.resource_manager.request_resources(
                str(agent.agent_id),
                resources
            )
            
            if success:
                # Store agent
                self.agents[str(agent.agent_id)] = agent
                self.agent_states[str(agent.agent_id)] = AgentState.IDLE
                self.agent_metrics[str(agent.agent_id)] = {
                    'tasks_completed': 0,
                    'tasks_failed': 0,
                    'avg_task_time': 0.0,
                    'avg_validation_score': 0.0,
                    'last_active': datetime.utcnow()
                }
                
                self.metrics['agents_created'] += 1
                logger.info(f"✅ Created {config['name']} agent with {len(config['tools'])} tools")
                return agent
            else:
                logger.error(f"Failed to allocate resources for {config['name']}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to create {config['name']}: {e}")
            return None
    
    async def _start_background_tasks(self):
        """Start all background tasks"""
        tasks = [
            self._environment_update_loop(),
            self._task_scheduler_loop(),
            self._coordination_loop(),
            self._monitoring_loop(),
            self._checkpoint_loop(),
            self._optimization_loop()
        ]
        
        for task in tasks:
            asyncio.create_task(task)
    
    async def _environment_update_loop(self):
        """Update environment state periodically"""
        while self.running:
            try:
                await self.environment.update(1.0)
                
                # Update agent contexts
                for agent in self.agents.values():
                    await self.adapter.update_agent_context(agent)
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Environment update error: {e}")
    
    async def _task_scheduler_loop(self):
        """Enhanced task scheduling loop with decomposition support"""
        while self.running:
            try:
                # Get next task
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Check if task needs decomposition
                if self.config.enable_task_decomposition and not task.subtasks and task.parent_task_id is None:
                    await self._decompose_task(task)
                    continue
                
                # Find best agent
                agent_id = await self._select_agent_for_task(task)
                
                if agent_id:
                    # Assign task
                    task.assigned_agent = agent_id
                    task.state = TaskState.ASSIGNED
                    task.started_at = datetime.utcnow()
                    
                    self.task_assignments[task.id] = agent_id
                    self.agent_states[agent_id] = AgentState.BUSY
                    
                    # Send to agent
                    agent = self.agents[agent_id]
                    await self.runtime.send_message(
                        'coordinator',
                        agent_id,
                        {
                            'type': 'task_assignment',
                            'task': task.__dict__,
                            'priority': task.priority.value
                        }
                    )
                    
                    # Process task in background
                    asyncio.create_task(self._process_task(task, agent))
                    
                else:
                    # No available agent, requeue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.5)
                    
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
    
    async def _decompose_task(self, task: EnhancedSwarmTask):
        """Decompose a task into subtasks using the 6-phase pipeline"""
        try:
            logger.info(f"Phase 1: Analyzing task {task.name}")
            task.state = TaskState.ANALYZING
            
            # 1. Analyze the task
            analysis = await self.llm_service.analyze_request(task.description)
            task.analysis = analysis
            logger.info(f"Analysis completed: {safe_json_dumps(analysis, indent=2)}")
            
            # 2. Decompose into subtasks
            logger.info(f"Phase 2: Planning - Decomposing task {task.name}")
            task.state = TaskState.PLANNING
            
            subtasks_data = await self.llm_service.decompose_task(task.description, analysis)
            
            if subtasks_data:
                self.metrics['tasks_decomposed'] += 1
                
                # Create subtasks
                for st_data in subtasks_data:
                    subtask = EnhancedSwarmTask(
                        id=st_data.get('id', str(uuid4())),
                        name=f"{task.name}-subtask-{st_data.get('id', '')}",
                        description=st_data.get('description', ''),
                        task_type=st_data.get('type', 'general'),
                        priority=task.priority,
                        parent_task_id=task.id,
                        metadata=st_data,
                        dependencies=[f"{task.id}-{dep}" for dep in st_data.get('dependencies', [])]
                    )
                    
                    task.subtasks.append(subtask)
                    self.task_registry[subtask.id] = subtask
                    
                    # Queue subtask
                    await self.task_queue.put(subtask)
                
                logger.info(f"Created {len(task.subtasks)} subtasks for {task.name}")
            else:
                # No subtasks needed, queue the task directly
                await self.task_queue.put(task)
                
        except Exception as e:
            logger.error(f"Task decomposition error: {e}")
            task.state = TaskState.FAILED
            task.error = str(e)
    
    async def _coordination_loop(self):
        """Handle inter-agent coordination"""
        while self.running:
            try:
                await asyncio.sleep(self.config.coordination_interval)
                
                # Process broadcast messages
                try:
                    message = await asyncio.wait_for(
                        self.broadcast_channel.get(),
                        timeout=0.1
                    )
                    await self._handle_broadcast(message)
                except asyncio.TimeoutError:
                    pass
                
                # Check load balancing needs
                if self.config.enable_load_balancing:
                    await self._check_load_balance()
                
                # Update coordination metrics
                self.metrics['coordination_cycles'] += 1
                
            except Exception as e:
                logger.error(f"Coordination error: {e}")
    
    async def _monitoring_loop(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                await asyncio.sleep(self.config.monitoring_interval)
                
                # Collect metrics
                system_metrics = {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'active_agents': sum(1 for s in self.agent_states.values() if s != AgentState.OFFLINE),
                    'busy_agents': sum(1 for s in self.agent_states.values() if s == AgentState.BUSY),
                    'queue_size': self.task_queue.qsize(),
                    'tasks_in_progress': sum(1 for t in self.task_registry.values() if t.state == TaskState.IN_PROGRESS)
                }
                
                # Check system health
                if system_metrics['cpu_percent'] > self.config.max_cpu_percent:
                    logger.warning(f"High CPU usage: {system_metrics['cpu_percent']}%")
                    if self.config.enable_auto_scaling:
                        await self._scale_down()
                
                # Log metrics periodically
                if self.metrics['coordination_cycles'] % 60 == 0:
                    logger.info(f"System metrics: {system_metrics}")
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    async def _checkpoint_loop(self):
        """Periodically save swarm state"""
        while self.running:
            try:
                await asyncio.sleep(self.config.checkpoint_interval)
                await self._save_checkpoint()
                
            except Exception as e:
                logger.error(f"Checkpoint error: {e}")
    
    async def _optimization_loop(self):
        """Continuous optimization loop"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Auto-scale if enabled
                if self.config.enable_auto_scaling:
                    await self._auto_scale()
                
                # Optimize agent allocation
                await self._optimize_agent_allocation()
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
            except Exception as e:
                logger.error(f"Optimization error: {e}")
    
    async def _select_agent_for_task(self, task: EnhancedSwarmTask) -> Optional[str]:
        """Select best agent for task using multi-criteria selection"""
        best_agent = None
        best_score = -1
        
        # Check if task specifies required agent type
        required_type = task.metadata.get('required_agent_type')
        
        for agent_id, agent in self.agents.items():
            # Skip offline/overloaded agents
            if self.agent_states[agent_id] in [AgentState.OFFLINE, AgentState.OVERLOADED]:
                continue
            
            # Calculate suitability score
            score = 0
            
            # Check required agent type
            if required_type and agent.role == required_type:
                score += 20
            
            # Check capabilities match
            task_keywords = task.task_type.lower().split('_')
            for keyword in task_keywords:
                if any(keyword in cap for cap in agent.capabilities):
                    score += 10
            
            # Consider agent state
            if self.agent_states[agent_id] == AgentState.IDLE:
                score += 5
            
            # Consider agent performance
            metrics = self.agent_metrics[agent_id]
            if metrics['tasks_completed'] > 0:
                success_rate = 1 - (metrics['tasks_failed'] / metrics['tasks_completed'])
                score += success_rate * 5
                
                # Consider validation scores
                if metrics['avg_validation_score'] > 0:
                    score += (metrics['avg_validation_score'] / 100) * 5
            
            # Consider workload
            agent_workload = sum(1 for t in self.task_registry.values() 
                               if t.assigned_agent == agent_id and t.state == TaskState.IN_PROGRESS)
            score -= agent_workload * 2
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        return best_agent
    
    async def _process_task(self, task: EnhancedSwarmTask, agent: Any):
        """Process a task with an agent (enhanced with validation)"""
        try:
            task.state = TaskState.IN_PROGRESS
            
            # Initialize project structure if this is a root task
            if task.parent_task_id is None and self.current_project_path is None:
                await self._initialize_project_structure(task)
            
            # Build context from dependencies
            context = await self._build_context(task)
            
            # Execute task based on type
            if task.task_type == 'analysis':
                result = await self._execute_analysis_task(task, agent, context)
            elif task.task_type == 'development' or task.task_type == 'code':
                result = await self._execute_development_task(task, agent, context)
            elif task.task_type == 'testing' or task.task_type == 'validation':
                result = await self._execute_testing_task(task, agent, context)
            elif task.task_type == 'deployment':
                result = await self._execute_deployment_task(task, agent, context)
            else:
                # General task execution with LLM
                result = await self._execute_general_task(task, agent, context)
            
            # Validate result if enabled
            if self.config.enable_validation and result:
                task.state = TaskState.VALIDATING
                validation = await self.llm_service.validate_solution(task.description, result)
                task.validation_score = validation.get('score', 0)
                
                if validation.get('is_valid', False):
                    task.state = TaskState.COMPLETED
                    task.completed_at = datetime.utcnow()
                    task.result = result
                    
                    # Update metrics
                    self.metrics['tasks_completed'] += 1
                    self.metrics['tasks_validated'] += 1
                    agent_metrics = self.agent_metrics[str(agent.agent_id)]
                    agent_metrics['tasks_completed'] += 1
                    
                    # Update validation score average
                    if agent_metrics['avg_validation_score'] == 0:
                        agent_metrics['avg_validation_score'] = task.validation_score
                    else:
                        agent_metrics['avg_validation_score'] = (
                            agent_metrics['avg_validation_score'] * 0.9 + 
                            task.validation_score * 0.1
                        )
                    
                    logger.info(f"✅ Task {task.name} completed by {agent.name} (Score: {task.validation_score})")
                else:
                    # Validation failed, retry if possible
                    task.state = TaskState.FAILED
                    task.error = f"Validation failed: {validation.get('final_verdict', 'rejected')}"
                    task.retries += 1
                    
                    if task.retries < self.config.max_retries:
                        logger.warning(f"Task {task.name} validation failed, retrying...")
                        await self.task_queue.put(task)
                    else:
                        self.metrics['tasks_failed'] += 1
                        agent_metrics = self.agent_metrics[str(agent.agent_id)]
                        agent_metrics['tasks_failed'] += 1
            else:
                # No validation or no result
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                
                self.metrics['tasks_completed'] += 1
                agent_metrics = self.agent_metrics[str(agent.agent_id)]
                agent_metrics['tasks_completed'] += 1
            
            # Update agent state
            self.agent_states[str(agent.agent_id)] = AgentState.IDLE
            
            # Check if parent task is complete
            if task.parent_task_id:
                await self._check_parent_task_completion(task.parent_task_id)
            
        except Exception as e:
            # Handle task failure
            task.state = TaskState.FAILED
            task.error = str(e)
            task.retries += 1
            
            self.metrics['tasks_failed'] += 1
            agent_metrics = self.agent_metrics[str(agent.agent_id)]
            agent_metrics['tasks_failed'] += 1
            
            logger.error(f"Task {task.name} failed: {e}")
            logger.error(traceback.format_exc())
            
            # Retry if possible
            if task.retries < self.config.max_retries:
                await self.task_queue.put(task)
    
    async def _initialize_project_structure(self, main_task: EnhancedSwarmTask):
        """Initialize the main project structure for this request"""
        if not self.filesystem_tool:
            return
        
        project_name = f"project_{main_task.id[:8]}"
        try:
            project_result = await self.filesystem_tool.execute(
                action="create_directory",
                agent_id=str(self.id),
                project_name=project_name
            )
            if project_result.success:
                self.current_project_path = project_result.data['project_path']
                logger.info(f"Main project created: {self.current_project_path}")
                
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
                    "data": {},
                    "requirements.txt": "",
                    "setup.py": "",
                    "README.md": f"# {project_name}\n\nAutomatically generated project for: {main_task.description}\n",
                    ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n.DS_Store\n"
                }
                await self._create_project_structure(self.current_project_path, self.project_structure)
        except Exception as e:
            logger.error(f"Error during project structure initialization: {e}")
    
    async def _create_project_structure(self, base_path: str, structure: Dict, parent_path: str = ""):
        """Recursively create the project structure"""
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
                        agent_id=str(self.id)
                    )
                    if file_result.success:
                        logger.debug(f"File created: {path}")
                except Exception as e:
                    logger.error(f"File creation error {path}: {e}")
    
    async def _build_context(self, task: EnhancedSwarmTask) -> str:
        """Build context from task dependencies"""
        context_parts = []
        
        # Add parent task context
        if task.parent_task_id and task.parent_task_id in self.task_registry:
            parent = self.task_registry[task.parent_task_id]
            context_parts.append(f"Parent task: {parent.description}")
            if parent.analysis:
                context_parts.append(f"Analysis: {safe_json_dumps(parent.analysis, indent=2)}")
        
        # Add dependency results
        for dep_id in task.dependencies:
            if dep_id in self.task_registry:
                dep_task = self.task_registry[dep_id]
                if dep_task.state == TaskState.COMPLETED and dep_task.result:
                    context_parts.append(f"Dependency {dep_id} result: {safe_json_dumps(dep_task.result, indent=2)}")
        
        # Add project structure info
        if self.current_project_path:
            context_parts.append(f"Project path: {self.current_project_path}")
            context_parts.append("Follow the standard project structure for all file creation")
        
        return "\n\n".join(context_parts) if context_parts else "No context available"
    
    async def _execute_general_task(self, task: EnhancedSwarmTask, agent: Any, context: str) -> Any:
        """Execute a general task using LLM"""
        # Update agent beliefs
        await agent.update_beliefs({
            "current_task": task.description,
            "task_type": task.task_type,
            "context": context,
            "project_path": self.current_project_path
        })
        
        # Use LLM to solve the task
        subtask_data = {
            'description': task.description,
            'type': task.task_type
        }
        result = await self.llm_service.solve_subtask(subtask_data, context)
        
        # Handle file creation if needed
        if result and self.filesystem_tool and result.get('files_to_create'):
            try:
                created_files = []
                for file_info in result['files_to_create']:
                    file_path = self._determine_file_location(file_info)
                    full_path = os.path.join(self.current_project_path, file_path) if self.current_project_path else file_path
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    file_result = await self.filesystem_tool.execute(
                        action="write",
                        file_path=full_path,
                        content=sanitize_unicode(file_info['content']),
                        agent_id=str(agent.agent_id)
                    )
                    
                    if file_result.success:
                        created_files.append({
                            'path': file_path,
                            'full_path': file_result.data['file_path'],
                            'size': file_result.data['size']
                        })
                        logger.info(f"File created: {file_path}")
                    else:
                        logger.error(f"File creation error {file_path}: {file_result.error}")
                
                result['created_files'] = created_files
            except Exception as e:
                logger.error(f"Error during file creation: {e}")
        
        return result
    
    async def _execute_analysis_task(self, task: EnhancedSwarmTask, agent: Any, context: str) -> Any:
        """Execute analysis task"""
        # Use web search tool for research
        if 'WebSearchTool' in agent.tools:
            search_tool = agent.tools['WebSearchTool']
            results = await search_tool.execute(
                action='search',
                query=task.data.get('query', task.description),
                limit=5
            )
            
            # Analyze results
            analysis = await agent.analyze(results.data)
            
            # Save analysis
            if 'filesystem' in agent.tools:
                fs_tool = agent.tools['filesystem']
                await fs_tool.execute(
                    action='write',
                    file_path=f"analysis_{task.id}.md",
                    content=analysis
                )
            
            return {"analysis": analysis, "sources": results.data}
        
        # Fallback to general execution
        return await self._execute_general_task(task, agent, context)
    
    async def _execute_development_task(self, task: EnhancedSwarmTask, agent: Any, context: str) -> Any:
        """Execute development task"""
        # Use code tool for implementation
        if 'CodeTool' in agent.tools:
            code_tool = agent.tools['CodeTool']
            
            # Generate code
            result = await code_tool.execute(
                action='generate',
                language=task.data.get('language', 'python'),
                requirements=task.data.get('requirements', {'description': task.description})
            )
            
            # Version control
            if 'GitTool' in agent.tools and result.success:
                git_tool = agent.tools['GitTool']
                await git_tool.execute(
                    action='commit',
                    message=f"Implement {task.name}",
                    files=[result.data['file_path']]
                )
            
            return result.data
        
        # Fallback to general execution
        return await self._execute_general_task(task, agent, context)
    
    async def _execute_testing_task(self, task: EnhancedSwarmTask, agent: Any, context: str) -> Any:
        """Execute testing task"""
        # Use code tool for testing
        if 'CodeTool' in agent.tools:
            code_tool = agent.tools['CodeTool']
            
            # Run tests
            result = await code_tool.execute(
                action='test',
                test_path=task.data.get('test_path', 'tests/'),
                coverage=True
            )
            
            return result.data
        
        # Fallback to general execution
        return await self._execute_general_task(task, agent, context)
    
    async def _execute_deployment_task(self, task: EnhancedSwarmTask, agent: Any, context: str) -> Any:
        """Execute deployment task"""
        # Use HTTP tool for deployment
        if 'HTTPTool' in agent.tools:
            http_tool = agent.tools['HTTPTool']
            
            # Deploy application
            result = await http_tool.execute(
                method='POST',
                url=task.data.get('deploy_url', ''),
                data=task.data.get('deploy_config', {})
            )
            
            return result.data
        
        # Fallback to general execution
        return await self._execute_general_task(task, agent, context)
    
    def _determine_file_location(self, file_info: Dict[str, Any]) -> str:
        """Determine the correct location for a file within the project"""
        file_path = file_info['path']
        lower_path = file_path.lower()
        
        # Test files
        if 'test' in lower_path:
            if 'unit' in lower_path:
                return f"tests/unit/{os.path.basename(file_path)}"
            if 'integration' in lower_path:
                return f"tests/integration/{os.path.basename(file_path)}"
            return f"tests/{os.path.basename(file_path)}"
        
        # Python source files
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
        
        # Documentation
        if file_path.endswith('.md'):
            return f"docs/{os.path.basename(file_path)}"
        
        # Configuration files
        if file_path.endswith(('.json', '.yaml', '.yml', '.ini', '.conf')):
            return f"config/{os.path.basename(file_path)}"
        
        # Scripts
        if file_path.endswith('.sh') or 'script' in lower_path:
            return f"scripts/{os.path.basename(file_path)}"
        
        # Data files
        if file_path.endswith(('.csv', '.txt', '.dat')):
            return f"data/{os.path.basename(file_path)}"
        
        # Default to root
        return os.path.basename(file_path)
    
    async def _check_parent_task_completion(self, parent_task_id: str):
        """Check if all subtasks of a parent task are complete"""
        if parent_task_id not in self.task_registry:
            return
        
        parent_task = self.task_registry[parent_task_id]
        
        # Check if all subtasks are complete
        all_complete = all(
            st.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]
            for st in parent_task.subtasks
        )
        
        if all_complete and parent_task.state == TaskState.PLANNING:
            # Aggregate results
            parent_task.state = TaskState.COMPLETED
            parent_task.completed_at = datetime.utcnow()
            
            # Calculate aggregate metrics
            success_count = sum(1 for st in parent_task.subtasks if st.state == TaskState.COMPLETED)
            total_count = len(parent_task.subtasks)
            
            # Aggregate validation scores
            validation_scores = [st.validation_score for st in parent_task.subtasks if st.validation_score is not None]
            avg_validation_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
            
            parent_task.result = {
                "subtasks_total": total_count,
                "subtasks_completed": success_count,
                "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
                "average_validation_score": avg_validation_score,
                "subtask_results": [
                    {
                        "id": st.id,
                        "description": st.description,
                        "state": st.state.value,
                        "validation_score": st.validation_score,
                        "result": st.result
                    }
                    for st in parent_task.subtasks
                ]
            }
            
            logger.info(f"Parent task {parent_task.name} completed with {success_count}/{total_count} successful subtasks")
            
            # Generate report if this is a root task
            if parent_task.parent_task_id is None:
                await self._generate_report(parent_task)
    
    async def _generate_report(self, task: EnhancedSwarmTask):
        """Generate a comprehensive execution report"""
        report_file = self.checkpoint_path / f"report_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            task_desc = sanitize_unicode(task.description)
            duration = (task.completed_at - task.created_at).total_seconds() if task.completed_at else 0
            
            report = f"""# Enhanced Production Swarm Execution Report

## Request
{task_desc}

## Metadata
- **ID**: {task.id}
- **Status**: {task.state.value}
- **Duration**: {duration:.2f} seconds
- **Priority**: {task.priority.value}

## Initial Analysis
"""
            
            if task.analysis:
                analysis = task.analysis
                report += f"""- **Type**: {analysis.get('type', 'N/A')}
- **Complexity**: {analysis.get('complexity', 'N/A')}
- **Domains**: {', '.join(analysis.get('domains', []))}
- **Approach**: {analysis.get('approach', 'N/A')}
- **Agent Types Needed**: {', '.join(analysis.get('agent_types_needed', []))}
"""
            
            # Subtask execution details
            if task.subtasks:
                report += f"\n## Subtask Execution ({len(task.subtasks)} subtasks)\n\n"
                
                for i, subtask in enumerate(task.subtasks):
                    agent_name = 'N/A'
                    if subtask.assigned_agent and subtask.assigned_agent in self.agents:
                        agent_name = self.agents[subtask.assigned_agent].name
                    
                    report += f"""### Subtask {i + 1}: {sanitize_unicode(subtask.description)}
- **Status**: {subtask.state.value}
- **Type**: {subtask.task_type}
- **Agent**: {agent_name}
- **Validation Score**: {subtask.validation_score if subtask.validation_score else 'N/A'}/100

"""
                    
                    if subtask.result:
                        if isinstance(subtask.result, dict):
                            if subtask.result.get('solution'):
                                report += f"**Solution**:\n{sanitize_unicode(subtask.result['solution'])}\n\n"
                            
                            if subtask.result.get('code'):
                                report += f"**Generated Code**:\n```python\n{sanitize_unicode(subtask.result['code'])}\n```\n\n"
                            
                            if subtask.result.get('created_files'):
                                report += "**Created Files**:\n"
                                for file in subtask.result['created_files']:
                                    report += f"- `{file['path']}` ({file['size']} bytes)\n"
                                report += "\n"
            
            # Summary statistics
            if task.result and isinstance(task.result, dict):
                report += f"""## Summary
- **Total Subtasks**: {task.result.get('subtasks_total', 0)}
- **Completed Successfully**: {task.result.get('subtasks_completed', 0)}
- **Success Rate**: {task.result.get('success_rate', 0):.1f}%
- **Average Validation Score**: {task.result.get('average_validation_score', 0):.1f}/100
"""
            
            # Project information
            if self.current_project_path:
                report += f"\n## Project Location\n`{self.current_project_path}`\n"
            
            # System metrics
            report += f"""\n## System Metrics
- **Total Agents**: {len(self.agents)}
- **Tasks Created**: {self.metrics['tasks_created']}
- **Tasks Completed**: {self.metrics['tasks_completed']}
- **Tasks Failed**: {self.metrics['tasks_failed']}
- **Tasks Decomposed**: {self.metrics['tasks_decomposed']}
- **Tasks Validated**: {self.metrics['tasks_validated']}
- **Coordination Cycles**: {self.metrics['coordination_cycles']}

Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Write report
            report = sanitize_unicode(report)
            with open(report_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(report)
            
            logger.info(f"Report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error during report generation: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def _handle_broadcast(self, message: Dict[str, Any]):
        """Handle broadcast messages"""
        msg_type = message.get('type')
        
        if msg_type == 'emergency_stop':
            await self.emergency_stop()
        elif msg_type == 'resource_update':
            await self._update_resource_allocations(message.get('resources', {}))
        elif msg_type == 'coordination':
            # Coordinate specific agents
            target_agents = message.get('agents', [])
            for agent_id in target_agents:
                if agent_id in self.agents:
                    await self.runtime.send_message(
                        'coordinator',
                        agent_id,
                        message
                    )
        
        self.metrics['messages_sent'] += len(self.agents)
    
    async def _check_load_balance(self):
        """Check and perform load balancing if needed"""
        # Count tasks per agent
        agent_loads = {}
        for task in self.task_registry.values():
            if task.state == TaskState.IN_PROGRESS and task.assigned_agent:
                agent_loads[task.assigned_agent] = agent_loads.get(task.assigned_agent, 0) + 1
        
        # Find overloaded agents
        avg_load = sum(agent_loads.values()) / len(self.agents) if self.agents else 0
        
        for agent_id, load in agent_loads.items():
            if load > avg_load * 1.5:
                self.agent_states[agent_id] = AgentState.OVERLOADED
                logger.warning(f"Agent {agent_id} is overloaded with {load} tasks")
                
                # TODO: Redistribute tasks
                self.metrics['load_balance_events'] += 1
    
    async def _auto_scale(self):
        """Auto-scale agents based on load"""
        queue_size = self.task_queue.qsize()
        active_agents = sum(1 for s in self.agent_states.values() if s != AgentState.OFFLINE)
        
        # Scale up if needed
        if queue_size > active_agents * 5 and len(self.agents) < self.config.max_agents:
            # Create additional developer
            config = {
                'name': f'Developer-Auto-{len(self.agents)}',
                'type': HybridAgent,
                'role': 'developer',
                'capabilities': ['coding', 'implementation', 'solution_development'],
                'tools': [CodeTool, FileSystemTool],
                'visibility': VisibilityLevel.NAMESPACE
            }
            
            agent = await self._create_agent(config)
            if agent:
                self.metrics['auto_scale_events'] += 1
                logger.info(f"Auto-scaled: Added new developer agent")
    
    async def _scale_down(self):
        """Scale down agents if system is overloaded"""
        # Find idle agents
        idle_agents = [aid for aid, state in self.agent_states.items() if state == AgentState.IDLE]
        
        if idle_agents and len(self.agents) > 5:  # Keep minimum 5 agents
            # Remove an idle agent
            agent_id = idle_agents[0]
            agent = self.agents[agent_id]
            
            await agent.stop()
            del self.agents[agent_id]
            del self.agent_states[agent_id]
            
            logger.info(f"Scaled down: Removed idle agent {agent.name}")
    
    async def _optimize_agent_allocation(self):
        """Optimize agent task allocation"""
        # Analyze agent performance
        for agent_id, metrics in self.agent_metrics.items():
            if metrics['tasks_completed'] > 10:
                metrics['avg_task_time']
                success_rate = 1 - (metrics['tasks_failed'] / metrics['tasks_completed'])
                
                # Adjust agent capabilities based on performance
                if success_rate < 0.5:
                    logger.warning(f"Agent {agent_id} has low success rate: {success_rate:.2%}")
    
    async def _cleanup_completed_tasks(self):
        """Clean up old completed tasks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        tasks_to_remove = []
        for task_id, task in self.task_registry.items():
            if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                if task.completed_at and task.completed_at < cutoff_time:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.task_registry[task_id]
            if task_id in self.task_assignments:
                del self.task_assignments[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    async def _save_checkpoint(self):
        """Save swarm state to disk"""
        try:
            state = {
                'swarm_id': str(self.id),
                'name': self.name,
                'metrics': self.metrics,
                'agent_states': {k: v.value for k, v in self.agent_states.items()},
                'agent_metrics': self.agent_metrics,
                'task_registry': {k: v.__dict__ for k, v in self.task_registry.items()},
                'current_project_path': self.current_project_path,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            checkpoint_file = self.checkpoint_path / f"checkpoint_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(checkpoint_file, 'w') as f:
                json.dump(state, f, default=str, indent=2)
            
            logger.info(f"Checkpoint saved to {checkpoint_file}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    async def _load_checkpoint(self):
        """Load previous swarm state"""
        try:
            # Find latest checkpoint
            checkpoints = list(self.checkpoint_path.glob("checkpoint_*.json"))
            if not checkpoints:
                return
            
            latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
            
            with open(latest, 'r') as f:
                state = json.load(f)
            
            # Restore metrics
            self.metrics.update(state.get('metrics', {}))
            
            # Restore project path
            if 'current_project_path' in state:
                self.current_project_path = state['current_project_path']
            
            logger.info(f"Loaded checkpoint from {latest}")
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
    
    async def _update_resource_allocations(self, resources: Dict[str, Any]):
        """Update resource allocations for agents"""
        for agent_id, allocation in resources.items():
            if agent_id in self.agents:
                success = self.environment.resource_manager.update_resources(
                    agent_id,
                    allocation
                )
                if success:
                    logger.info(f"Updated resources for agent {agent_id}")
    
    # Public API methods
    
    async def process_request(self, request: str, priority: MessagePriority = MessagePriority.MEDIUM) -> str:
        """Process a complex request autonomously"""
        main_task = EnhancedSwarmTask(
            name=f"Request-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            description=request,
            task_type="complex",
            priority=priority
        )
        
        self.task_registry[main_task.id] = main_task
        await self.task_queue.put(main_task)
        
        self.metrics['tasks_created'] += 1
        logger.info(f"Processing request: {request}")
        
        return main_task.id
    
    async def submit_task(self, name: str, task_type: str, data: Dict[str, Any],
                         priority: MessagePriority = MessagePriority.MEDIUM,
                         dependencies: List[str] = None) -> str:
        """Submit a task to the swarm"""
        task = EnhancedSwarmTask(
            name=name,
            description=data.get('description', name),
            task_type=task_type,
            data=data,
            priority=priority,
            dependencies=dependencies or []
        )
        
        self.task_registry[task.id] = task
        await self.task_queue.put(task)
        
        self.metrics['tasks_created'] += 1
        logger.info(f"Task {name} submitted with ID {task.id}")
        
        return task.id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.task_registry:
            task = self.task_registry[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'state': task.state.value,
                'assigned_agent': task.assigned_agent,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'validation_score': task.validation_score,
                'error': task.error,
                'retries': task.retries,
                'subtasks': len(task.subtasks),
                'result': task.result
            }
        return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get swarm status"""
        return {
            'swarm_id': str(self.id),
            'name': self.name,
            'running': self.running,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds(),
            'agents': {
                'total': len(self.agents),
                'active': sum(1 for s in self.agent_states.values() if s != AgentState.OFFLINE),
                'busy': sum(1 for s in self.agent_states.values() if s == AgentState.BUSY),
                'idle': sum(1 for s in self.agent_states.values() if s == AgentState.IDLE)
            },
            'tasks': {
                'total': self.metrics['tasks_created'],
                'completed': self.metrics['tasks_completed'],
                'failed': self.metrics['tasks_failed'],
                'decomposed': self.metrics['tasks_decomposed'],
                'validated': self.metrics['tasks_validated'],
                'in_queue': self.task_queue.qsize(),
                'in_progress': sum(1 for t in self.task_registry.values() if t.state == TaskState.IN_PROGRESS)
            },
            'performance': {
                'coordination_cycles': self.metrics['coordination_cycles'],
                'messages_sent': self.metrics['messages_sent'],
                'load_balance_events': self.metrics['load_balance_events'],
                'auto_scale_events': self.metrics['auto_scale_events'],
                'average_validation_score': self.metrics['average_validation_score']
            },
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent
            },
            'project_path': self.current_project_path
        }
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all agents"""
        await self.broadcast_channel.put(message)
    
    async def emergency_stop(self):
        """Emergency stop all operations"""
        logger.warning("EMERGENCY STOP initiated!")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Save final checkpoint
        await self._save_checkpoint()
        
        logger.info("Emergency stop completed")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        
        self.running = False
        
        # Wait for tasks to complete
        timeout = 30
        start = datetime.utcnow()
        
        while self.task_queue.qsize() > 0 and (datetime.utcnow() - start).total_seconds() < timeout:
            await asyncio.sleep(1)
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Close pools
        if self.process_pool:
            self.process_pool.shutdown(wait=True)
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        # Save final state
        await self._save_checkpoint()
        
        # Clear resources
        self.environment.entities.clear()
        
        logger.info("Shutdown complete")


# Example usage and demonstration
async def demonstrate_enhanced_production_swarm():
    """Demonstrate the enhanced production swarm capabilities"""
    print("\n" + "="*80)
    print("🚀 ENHANCED PRODUCTION MAS SWARM SYSTEM")
    print("With autonomous task decomposition and validation")
    print("="*80 + "\n")
    
    # Create swarm with custom configuration
    config = EnhancedSwarmConfig(
        name="EnhancedDemoSwarm",
        num_developers=4,
        num_testers=2,
        num_analysts=2,
        max_agents=15,
        enable_task_decomposition=True,
        enable_validation=True
    )
    
    swarm = EnhancedProductionSwarmCoordinator(config)
    
    # Initialize
    await swarm.initialize()
    
    print("\n📋 Processing complex autonomous request...")
    
    # Submit a complex request that will be decomposed
    request_id = await swarm.process_request(
        "Build a complete REST API for a task management system with user authentication, " +
        "database persistence, comprehensive tests, and deployment configuration",
        priority=MessagePriority.HIGH
    )
    
    print(f"✅ Request submitted with ID: {request_id}")
    
    # Monitor progress
    print("\n📊 Monitoring swarm progress...")
    
    for i in range(10):
        await asyncio.sleep(3)
        
        status = await swarm.get_status()
        print(f"\nCycle {i+1}:")
        print(f"  - Active agents: {status['agents']['active']}/{status['agents']['total']}")
        print(f"  - Tasks in progress: {status['tasks']['in_progress']}")
        print(f"  - Tasks completed: {status['tasks']['completed']}")
        print(f"  - Tasks validated: {status['tasks']['validated']}")
        print(f"  - Queue size: {status['tasks']['in_queue']}")
        
        # Check main task status
        task_status = await swarm.get_task_status(request_id)
        if task_status:
            print(f"  - Main task state: {task_status['state']}")
            print(f"  - Subtasks created: {task_status['subtasks']}")
            if task_status['validation_score']:
                print(f"  - Validation score: {task_status['validation_score']}/100")
    
    # Final status
    final_status = await swarm.get_status()
    
    print("\n" + "="*60)
    print("📊 FINAL SWARM STATUS")
    print("="*60)
    print(f"Uptime: {final_status['uptime']:.1f} seconds")
    print(f"Total agents: {final_status['agents']['total']}")
    print(f"Tasks created: {final_status['tasks']['total']}")
    print(f"Tasks completed: {final_status['tasks']['completed']}")
    print(f"Tasks failed: {final_status['tasks']['failed']}")
    print(f"Tasks decomposed: {final_status['tasks']['decomposed']}")
    print(f"Tasks validated: {final_status['tasks']['validated']}")
    print(f"Coordination cycles: {final_status['performance']['coordination_cycles']}")
    print(f"Messages sent: {final_status['performance']['messages_sent']}")
    
    if final_status['project_path']:
        print(f"\n📁 Project created at: {final_status['project_path']}")
    
    print("="*60)
    
    # Graceful shutdown
    await swarm.shutdown()


# Emergency signal handler
def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n⚠️ Shutdown signal received!")
    # Set global shutdown flag
    asyncio.create_task(emergency_shutdown())


async def emergency_shutdown():
    """Emergency shutdown all swarms"""
    # TODO: Track all active swarms and shut them down


# Interactive mode
async def interactive_mode():
    """Interactive mode for processing requests"""
    print("\n" + "="*80)
    print("🤖 ENHANCED PRODUCTION SWARM - INTERACTIVE MODE")
    print("="*80)
    print("\nThis swarm can autonomously solve any complex request.")
    print("It decomposes tasks, coordinates agents, validates results, and generates reports.")
    print(f"\nAll logs are saved to: {LOG_FILE}")
    print("="*80)
    
    # Create swarm
    config = EnhancedSwarmConfig(
        name="InteractiveSwarm",
        enable_task_decomposition=True,
        enable_validation=True
    )
    
    swarm = EnhancedProductionSwarmCoordinator(config)
    await swarm.initialize()
    
    try:
        while True:
            print("\n" + "-"*60)
            request = input("📝 Enter your request (or 'quit' to exit):\n> ").strip()
            
            if request.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Stopping swarm...")
                break
            
            if request.lower() == 'status':
                status = await swarm.get_status()
                print(f"\nSwarm Status:")
                print(f"  Agents: {status['agents']['active']}/{status['agents']['total']} active")
                print(f"  Tasks: {status['tasks']['completed']} completed, {status['tasks']['in_progress']} in progress")
                continue
            
            if not request:
                print("❌ Empty request, please try again.")
                continue
            
            print("\n🚀 Processing request...")
            print("(Check logs for detailed execution)")
            
            # Process request
            task_id = await swarm.process_request(request)
            print(f"\n✅ Request submitted with task ID: {task_id}")
            print("Monitoring progress...")
            
            # Monitor until complete
            while True:
                await asyncio.sleep(2)
                task_status = await swarm.get_task_status(task_id)
                
                if task_status:
                    print(f"\r⏳ Status: {task_status['state']} | Subtasks: {task_status['subtasks']}", end='', flush=True)
                    
                    if task_status['state'] in ['completed', 'failed']:
                        print()
                        break
            
            # Show results
            if task_status['state'] == 'completed':
                print(f"\n✅ Request completed successfully!")
                if task_status['validation_score']:
                    print(f"Validation score: {task_status['validation_score']}/100")
                if swarm.current_project_path:
                    print(f"📁 Files created in: {swarm.current_project_path}")
                print("\n📄 A detailed report has been generated")
            else:
                print(f"\n❌ Request failed: {task_status.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption detected...")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        await swarm.shutdown()
        print("\n✅ Swarm stopped cleanly")
        print(f"📁 Logs available at: {LOG_FILE}")


# Main entry point
async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        # Run demonstration
        await demonstrate_enhanced_production_swarm()
    else:
        # Run interactive mode
        print("\n📌 Sample requests you can try:")
        print("- Create a simple calculator with unit tests")
        print("- Build a task management web app with React and FastAPI")
        print("- Analyze AI market trends and create an investment strategy report")
        print("- Develop a machine learning pipeline for customer churn prediction")
        print("- Create a microservices architecture for an e-commerce platform")
        print("- Build a real-time chat application with WebSocket support")
        
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())