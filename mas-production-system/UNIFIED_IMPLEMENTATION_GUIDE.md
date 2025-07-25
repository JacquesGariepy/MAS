# Unified MAS Implementation Guide

## Overview

This guide provides concrete implementation details for merging all MAS components into a unified system.

## 1. Unified Agent Factory

Create a central factory that can instantiate any agent type:

```python
# src/core/agents/unified_agent_factory.py

from typing import Dict, Any, Optional, Type
from uuid import UUID, uuid4

from src.core.agents.base_agent import BaseAgent
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.cognitive_agent_improved import ImprovedCognitiveAgent
from src.core.agents.hybrid_agent import HybridAgent
from src.agents.autonomous_integrated import AutonomousIntegratedAgent
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UnifiedAgentFactory:
    """Factory for creating any type of agent with unified configuration"""
    
    # Agent type registry
    AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
        'reflexive': ReflexiveAgent,
        'cognitive': ImprovedCognitiveAgent,
        'hybrid': HybridAgent,
        'autonomous': AutonomousIntegratedAgent,
    }
    
    # Default configurations per agent type
    DEFAULT_CONFIGS = {
        'reflexive': {
            'reactive_rules': {
                'help_request': {
                    'condition': {'type': 'message', 'performative': 'request'},
                    'action': {'type': 'respond', 'performative': 'inform'}
                }
            }
        },
        'cognitive': {
            'max_context_size': 2000,
            'max_history_items': 10,
            'json_retry_attempts': 3
        },
        'hybrid': {
            'cognitive_threshold': 0.7,
            'reactive_rules': {}
        },
        'autonomous': {
            'enable_environment': True,
            'resource_limits': {
                'cpu': 80.0,
                'memory': 4 * 1024 * 1024 * 1024
            }
        }
    }
    
    @classmethod
    def create_agent(
        cls,
        agent_type: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BaseAgent:
        """
        Create an agent of specified type with unified configuration
        
        Args:
            agent_type: Type of agent ('reflexive', 'cognitive', 'hybrid', 'autonomous')
            name: Agent name (auto-generated if not provided)
            role: Agent role
            capabilities: List of agent capabilities
            config: Additional configuration
            **kwargs: Additional arguments passed to agent constructor
            
        Returns:
            Configured agent instance
        """
        
        if agent_type not in cls.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Generate defaults
        agent_id = kwargs.pop('agent_id', uuid4())
        name = name or f"{agent_type.capitalize()}_Agent_{str(agent_id)[:8]}"
        role = role or f"{agent_type}_specialist"
        
        # Default capabilities based on agent type
        if not capabilities:
            capabilities = cls._get_default_capabilities(agent_type)
        
        # Merge configurations
        default_config = cls.DEFAULT_CONFIGS.get(agent_type, {})
        merged_config = {**default_config, **(config or {})}
        
        # Add LLM service for cognitive agents
        if agent_type in ['cognitive', 'hybrid', 'autonomous']:
            kwargs['llm_service'] = kwargs.get('llm_service') or LLMService()
        
        # Create agent instance
        agent_class = cls.AGENT_TYPES[agent_type]
        
        try:
            agent = agent_class(
                agent_id=agent_id,
                name=name,
                role=role,
                capabilities=capabilities,
                **merged_config,
                **kwargs
            )
            
            logger.info(f"Created {agent_type} agent: {name} ({agent_id})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent: {e}")
            raise
    
    @classmethod
    def _get_default_capabilities(cls, agent_type: str) -> List[str]:
        """Get default capabilities for agent type"""
        base_capabilities = ['communication', 'task_execution']
        
        type_capabilities = {
            'reflexive': ['rule_processing', 'fast_response'],
            'cognitive': ['reasoning', 'learning', 'planning'],
            'hybrid': ['adaptive_behavior', 'mode_switching'],
            'autonomous': ['team_coordination', 'resource_management', 'goal_setting']
        }
        
        return base_capabilities + type_capabilities.get(agent_type, [])
    
    @classmethod
    def create_team(
        cls,
        team_config: Dict[str, Any]
    ) -> Dict[str, BaseAgent]:
        """
        Create a team of agents based on configuration
        
        Args:
            team_config: Team configuration specifying agent types and counts
            
        Returns:
            Dictionary of agent_id -> agent instance
        """
        team = {}
        
        for agent_spec in team_config.get('agents', []):
            count = agent_spec.get('count', 1)
            agent_type = agent_spec['type']
            base_config = agent_spec.get('config', {})
            
            for i in range(count):
                agent = cls.create_agent(
                    agent_type=agent_type,
                    name=f"{agent_spec.get('name_prefix', agent_type)}_{i+1}",
                    role=agent_spec.get('role'),
                    capabilities=agent_spec.get('capabilities'),
                    config=base_config
                )
                team[str(agent.agent_id)] = agent
        
        logger.info(f"Created team with {len(team)} agents")
        return team
```

## 2. Unified Environment Manager

Integrate all environment types with a single interface:

```python
# src/core/environment/unified_environment.py

from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import asyncio

from src.core.environment.software_environment import (
    SoftwareEnvironment, TopologyType, VisibilityLevel
)
from src.core.agents.base_agent import BaseAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EnvironmentMode(Enum):
    """Environment operation modes"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    SWARM = "swarm"

@dataclass
class EnvironmentConfig:
    """Unified environment configuration"""
    mode: EnvironmentMode
    topology: TopologyType
    max_agents: int = 100
    enable_resource_management: bool = True
    enable_partial_observability: bool = True
    enable_dynamics: bool = True
    resource_limits: Dict[str, float] = None

class UnifiedEnvironment:
    """
    Unified environment that integrates all environment types
    Supports development, testing, production, and swarm modes
    """
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.environment = SoftwareEnvironment(
            topology=config.topology,
            enable_resource_management=config.enable_resource_management,
            enable_partial_observability=config.enable_partial_observability
        )
        
        # Mode-specific initialization
        self._init_mode_specific()
        
        # Running state
        self._running = False
        self._tasks = asyncio.Queue()
        
    def _init_mode_specific(self):
        """Initialize mode-specific features"""
        if self.config.mode == EnvironmentMode.PRODUCTION:
            # Production optimizations
            self.environment.resource_manager.set_strict_limits(True)
            self.environment.set_monitoring_level('detailed')
            
        elif self.config.mode == EnvironmentMode.SWARM:
            # Swarm-specific setup
            self.environment.enable_swarm_features()
            self.coordination_strategy = 'emergent'
            
        elif self.config.mode == EnvironmentMode.TESTING:
            # Testing features
            self.environment.enable_deterministic_mode()
            self.environment.set_time_acceleration(10.0)
    
    async def add_agent(self, agent: BaseAgent) -> bool:
        """Add an agent to the unified environment"""
        try:
            # Register with base environment
            location = await self.environment.register_agent(
                agent_id=str(agent.agent_id),
                agent_type=agent.agent_type,
                capabilities=agent.capabilities
            )
            
            # Store agent reference
            self.agents[str(agent.agent_id)] = agent
            
            # Set up agent's environment adapter
            agent.environment_adapter = self.environment.get_agent_adapter(
                str(agent.agent_id)
            )
            
            # Initialize agent in environment
            await agent.environment_adapter.initialize()
            
            logger.info(f"Added agent {agent.name} to environment at {location}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add agent: {e}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the environment"""
        if agent_id in self.agents:
            # Stop agent
            agent = self.agents[agent_id]
            await agent.stop()
            
            # Unregister from environment
            await self.environment.unregister_agent(agent_id)
            
            # Remove reference
            del self.agents[agent_id]
            
            logger.info(f"Removed agent {agent_id} from environment")
            return True
        return False
    
    async def broadcast_message(
        self,
        message: Dict[str, Any],
        sender_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None
    ):
        """Broadcast a message to agents"""
        if target_ids:
            # Targeted broadcast
            recipients = [self.agents[aid] for aid in target_ids if aid in self.agents]
        else:
            # Broadcast to all
            recipients = list(self.agents.values())
        
        # Apply visibility rules
        for agent in recipients:
            if self.environment.can_communicate(sender_id, str(agent.agent_id)):
                await agent.receive_message(message)
    
    async def assign_task(self, task: Dict[str, Any]) -> str:
        """Assign a task to the most suitable agent"""
        # Find best agent based on capabilities and load
        best_agent = None
        best_score = -1
        
        for agent in self.agents.values():
            score = await self._calculate_agent_suitability(agent, task)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            await best_agent.add_task(task)
            return str(best_agent.agent_id)
        
        # Queue task if no suitable agent
        await self._tasks.put(task)
        return ""
    
    async def _calculate_agent_suitability(
        self,
        agent: BaseAgent,
        task: Dict[str, Any]
    ) -> float:
        """Calculate how suitable an agent is for a task"""
        score = 0.0
        
        # Check capability match
        required_capabilities = task.get('required_capabilities', [])
        for cap in required_capabilities:
            if cap in agent.capabilities:
                score += 1.0
        
        # Check resource availability
        if self.config.enable_resource_management:
            resources = await self.environment.get_agent_resources(str(agent.agent_id))
            if resources['cpu']['available'] < 20:  # Less than 20% CPU available
                score *= 0.5
        
        # Check agent load
        agent_metrics = await agent.get_metrics()
        queue_size = agent_metrics.get('task_queue_size', 0)
        if queue_size > 5:
            score *= 0.7
        
        return score
    
    async def run(self):
        """Run the unified environment"""
        self._running = True
        logger.info(f"Starting unified environment in {self.config.mode} mode")
        
        # Start all agents
        agent_tasks = []
        for agent in self.agents.values():
            agent_tasks.append(asyncio.create_task(agent.run()))
        
        # Start environment dynamics
        if self.config.enable_dynamics:
            dynamics_task = asyncio.create_task(self.environment.run_dynamics())
        
        # Main environment loop
        try:
            while self._running:
                # Process queued tasks
                await self._process_queued_tasks()
                
                # Update environment state
                await self.environment.update()
                
                # Mode-specific operations
                await self._mode_specific_update()
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Environment error: {e}")
        finally:
            # Stop all agents
            for task in agent_tasks:
                task.cancel()
            
            if self.config.enable_dynamics:
                dynamics_task.cancel()
    
    async def _process_queued_tasks(self):
        """Process tasks waiting in queue"""
        while not self._tasks.empty():
            task = await self._tasks.get()
            assigned = await self.assign_task(task)
            if not assigned:
                # Re-queue if still can't assign
                await self._tasks.put(task)
                break
    
    async def _mode_specific_update(self):
        """Mode-specific update operations"""
        if self.config.mode == EnvironmentMode.SWARM:
            # Swarm coordination
            await self._update_swarm_coordination()
        elif self.config.mode == EnvironmentMode.PRODUCTION:
            # Production monitoring
            await self._check_production_health()
    
    async def _update_swarm_coordination(self):
        """Update swarm coordination state"""
        # Implement swarm-specific coordination logic
        pass
    
    async def _check_production_health(self):
        """Check production environment health"""
        # Implement health checks
        pass
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        return {
            'mode': self.config.mode.value,
            'topology': self.config.topology.value,
            'num_agents': len(self.agents),
            'agents': {
                aid: {
                    'name': agent.name,
                    'type': agent.agent_type,
                    'state': 'running' if agent._running else 'stopped'
                }
                for aid, agent in self.agents.items()
            },
            'environment_state': await self.environment.get_state(),
            'queued_tasks': self._tasks.qsize()
        }
```

## 3. Unified Tool Manager

Integrate all tools with a single management interface:

```python
# src/tools/unified_tool_manager.py

from typing import Dict, Any, List, Optional, Type
import asyncio
from abc import ABC

from src.tools.base_tool import BaseTool, ToolResult
from src.tools.code_tool import CodeTool
from src.tools.filesystem_tool import FileSystemTool
from src.tools.git_tool import GitTool
from src.tools.web_search_tool import WebSearchTool
from src.tools.database_tool import DatabaseTool
from src.tools.http_tool import HTTPTool
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UnifiedToolManager:
    """
    Unified manager for all tool types
    Provides centralized tool access, permission management, and execution tracking
    """
    
    # Tool registry
    TOOL_CLASSES: Dict[str, Type[BaseTool]] = {
        'code': CodeTool,
        'filesystem': FileSystemTool,
        'git': GitTool,
        'web_search': WebSearchTool,
        'database': DatabaseTool,
        'http': HTTPTool,
    }
    
    def __init__(self, workspace_root: str = "/app/agent_workspace"):
        self.workspace_root = workspace_root
        self.tools: Dict[str, Dict[str, BaseTool]] = {}  # agent_id -> tool_name -> tool
        self.permissions: Dict[str, Set[str]] = {}  # agent_id -> allowed_tools
        self.usage_stats: Dict[str, Dict[str, int]] = {}  # agent_id -> tool_name -> count
        
    def register_agent(self, agent_id: str, allowed_tools: List[str]):
        """Register an agent and initialize their tools"""
        if agent_id in self.tools:
            logger.warning(f"Agent {agent_id} already registered")
            return
        
        self.tools[agent_id] = {}
        self.permissions[agent_id] = set(allowed_tools)
        self.usage_stats[agent_id] = {}
        
        # Initialize allowed tools for agent
        for tool_name in allowed_tools:
            if tool_name in self.TOOL_CLASSES:
                tool_class = self.TOOL_CLASSES[tool_name]
                tool_instance = tool_class(
                    agent_id=agent_id,
                    workspace_root=f"{self.workspace_root}/{agent_id}"
                )
                self.tools[agent_id][tool_name] = tool_instance
                self.usage_stats[agent_id][tool_name] = 0
                
        logger.info(f"Registered agent {agent_id} with tools: {allowed_tools}")
    
    async def execute_tool(
        self,
        agent_id: str,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """Execute a tool on behalf of an agent"""
        
        # Permission check
        if agent_id not in self.permissions:
            return ToolResult(
                success=False,
                error=f"Agent {agent_id} not registered"
            )
        
        if tool_name not in self.permissions[agent_id]:
            return ToolResult(
                success=False,
                error=f"Agent {agent_id} not authorized to use {tool_name}"
            )
        
        # Get tool instance
        if tool_name not in self.tools[agent_id]:
            return ToolResult(
                success=False,
                error=f"Tool {tool_name} not initialized for agent {agent_id}"
            )
        
        tool = self.tools[agent_id][tool_name]
        
        # Execute with tracking
        try:
            result = await tool.execute(**kwargs)
            self.usage_stats[agent_id][tool_name] += 1
            
            logger.info(f"Agent {agent_id} executed {tool_name} successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def update_permissions(
        self,
        agent_id: str,
        allowed_tools: List[str]
    ):
        """Update tool permissions for an agent"""
        if agent_id not in self.permissions:
            logger.error(f"Agent {agent_id} not registered")
            return
        
        old_tools = self.permissions[agent_id]
        new_tools = set(allowed_tools)
        
        # Remove tools no longer allowed
        for tool_name in old_tools - new_tools:
            if tool_name in self.tools[agent_id]:
                del self.tools[agent_id][tool_name]
        
        # Add newly allowed tools
        for tool_name in new_tools - old_tools:
            if tool_name in self.TOOL_CLASSES:
                tool_class = self.TOOL_CLASSES[tool_name]
                tool_instance = tool_class(
                    agent_id=agent_id,
                    workspace_root=f"{self.workspace_root}/{agent_id}"
                )
                self.tools[agent_id][tool_name] = tool_instance
                self.usage_stats[agent_id][tool_name] = 0
        
        self.permissions[agent_id] = new_tools
        logger.info(f"Updated permissions for agent {agent_id}: {allowed_tools}")
    
    def get_usage_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tool usage statistics"""
        if agent_id:
            return self.usage_stats.get(agent_id, {})
        return self.usage_stats
    
    def get_available_tools(self, agent_id: str) -> List[str]:
        """Get list of available tools for an agent"""
        return list(self.permissions.get(agent_id, []))
```

## 4. Unified Orchestrator

Central orchestration for all components:

```python
# src/orchestration/unified_orchestrator.py

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from enum import Enum

from src.core.agents.unified_agent_factory import UnifiedAgentFactory
from src.core.environment.unified_environment import (
    UnifiedEnvironment, EnvironmentConfig, EnvironmentMode
)
from src.tools.unified_tool_manager import UnifiedToolManager
from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.core.runtime.agent_runtime import AgentRuntime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OrchestratorState(Enum):
    """Orchestrator states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"

class UnifiedOrchestrator:
    """
    Central orchestrator that manages all MAS components
    Provides high-level control over the entire system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = OrchestratorState.INITIALIZING
        
        # Core components
        self.environment: Optional[UnifiedEnvironment] = None
        self.tool_manager: Optional[UnifiedToolManager] = None
        self.llm_service: Optional[LLMService] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.runtime: Optional[AgentRuntime] = None
        
        # Agent tracking
        self.agents: Dict[str, Any] = {}
        self.teams: Dict[str, List[str]] = {}  # team_name -> agent_ids
        
        # Task management
        self.tasks: Dict[str, Any] = {}
        self.workflows: Dict[str, Any] = {}
        
        # Metrics
        self.metrics = {
            'start_time': None,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'agents_created': 0,
            'uptime': 0
        }
    
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing unified orchestrator...")
            
            # Initialize services
            self.llm_service = LLMService()
            self.embedding_service = EmbeddingService()
            
            # Initialize tool manager
            self.tool_manager = UnifiedToolManager(
                workspace_root=self.config.get('workspace_root', '/app/agent_workspace')
            )
            
            # Initialize environment
            env_config = EnvironmentConfig(
                mode=EnvironmentMode[self.config.get('environment_mode', 'PRODUCTION')],
                topology=self.config.get('topology', 'hierarchical'),
                max_agents=self.config.get('max_agents', 100),
                enable_resource_management=self.config.get('enable_resource_management', True)
            )
            self.environment = UnifiedEnvironment(env_config)
            
            # Initialize runtime
            self.runtime = AgentRuntime()
            
            self.state = OrchestratorState.READY
            self.metrics['start_time'] = datetime.utcnow()
            
            logger.info("Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.state = OrchestratorState.STOPPED
            raise
    
    async def create_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a new agent"""
        if self.state not in [OrchestratorState.READY, OrchestratorState.RUNNING]:
            raise RuntimeError(f"Cannot create agent in state {self.state}")
        
        # Create agent using factory
        agent = UnifiedAgentFactory.create_agent(
            agent_type=agent_type,
            name=name,
            llm_service=self.llm_service,
            **kwargs
        )
        
        agent_id = str(agent.agent_id)
        
        # Register with tool manager
        default_tools = self._get_default_tools_for_type(agent_type)
        self.tool_manager.register_agent(agent_id, default_tools)
        
        # Add to environment
        await self.environment.add_agent(agent)
        
        # Track agent
        self.agents[agent_id] = {
            'agent': agent,
            'type': agent_type,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        self.metrics['agents_created'] += 1
        
        logger.info(f"Created {agent_type} agent: {agent.name} ({agent_id})")
        return agent_id
    
    def _get_default_tools_for_type(self, agent_type: str) -> List[str]:
        """Get default tools for agent type"""
        tool_sets = {
            'reflexive': ['filesystem'],
            'cognitive': ['code', 'filesystem', 'web_search'],
            'hybrid': ['code', 'filesystem', 'git'],
            'autonomous': ['code', 'filesystem', 'git', 'web_search', 'database', 'http']
        }
        return tool_sets.get(agent_type, ['filesystem'])
    
    async def create_team(
        self,
        team_name: str,
        team_config: Dict[str, Any]
    ) -> List[str]:
        """Create a team of agents"""
        logger.info(f"Creating team: {team_name}")
        
        team = UnifiedAgentFactory.create_team(team_config)
        agent_ids = []
        
        for agent_id, agent in team.items():
            # Register and add each agent
            default_tools = self._get_default_tools_for_type(agent.agent_type)
            self.tool_manager.register_agent(agent_id, default_tools)
            await self.environment.add_agent(agent)
            
            self.agents[agent_id] = {
                'agent': agent,
                'type': agent.agent_type,
                'created_at': datetime.utcnow(),
                'status': 'active',
                'team': team_name
            }
            
            agent_ids.append(agent_id)
        
        self.teams[team_name] = agent_ids
        self.metrics['agents_created'] += len(agent_ids)
        
        logger.info(f"Created team {team_name} with {len(agent_ids)} agents")
        return agent_ids
    
    async def assign_task(
        self,
        task: Dict[str, Any],
        agent_id: Optional[str] = None,
        team_name: Optional[str] = None
    ) -> str:
        """Assign a task to an agent or team"""
        task_id = task.get('id', str(uuid4()))
        
        self.tasks[task_id] = {
            'task': task,
            'status': 'assigned',
            'created_at': datetime.utcnow(),
            'assigned_to': agent_id or team_name
        }
        
        if agent_id:
            # Direct assignment
            agent = self.agents[agent_id]['agent']
            await agent.add_task(task)
        elif team_name:
            # Team assignment - let environment decide
            await self.environment.assign_task(task)
        else:
            # Let environment choose best agent
            assigned_id = await self.environment.assign_task(task)
            self.tasks[task_id]['assigned_to'] = assigned_id
        
        return task_id
    
    async def run(self):
        """Run the orchestrator"""
        if self.state != OrchestratorState.READY:
            raise RuntimeError(f"Cannot run orchestrator in state {self.state}")
        
        self.state = OrchestratorState.RUNNING
        logger.info("Starting orchestrator...")
        
        # Start environment
        env_task = asyncio.create_task(self.environment.run())
        
        try:
            while self.state == OrchestratorState.RUNNING:
                # Update metrics
                self._update_metrics()
                
                # Process any pending operations
                await self._process_pending_operations()
                
                # Health checks
                await self._perform_health_checks()
                
                await asyncio.sleep(1.0)
                
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
        finally:
            env_task.cancel()
            await self._cleanup()
    
    def _update_metrics(self):
        """Update orchestrator metrics"""
        if self.metrics['start_time']:
            self.metrics['uptime'] = (
                datetime.utcnow() - self.metrics['start_time']
            ).total_seconds()
    
    async def _process_pending_operations(self):
        """Process any pending operations"""
        # Check task completions
        for task_id, task_info in self.tasks.items():
            if task_info['status'] == 'assigned':
                # Check if task is completed
                # This would interface with agents to get status
                pass
    
    async def _perform_health_checks(self):
        """Perform system health checks"""
        # Check agent health
        for agent_id, agent_info in self.agents.items():
            agent = agent_info['agent']
            if not agent._running and agent_info['status'] == 'active':
                logger.warning(f"Agent {agent_id} stopped unexpectedly")
                agent_info['status'] = 'failed'
    
    async def _cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up orchestrator resources...")
        
        # Stop all agents
        for agent_info in self.agents.values():
            await agent_info['agent'].stop()
        
        self.state = OrchestratorState.STOPPED
    
    async def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state"""
        return {
            'orchestrator': {
                'state': self.state.value,
                'metrics': self.metrics
            },
            'environment': await self.environment.get_state() if self.environment else {},
            'agents': {
                agent_id: {
                    'type': info['type'],
                    'status': info['status'],
                    'team': info.get('team'),
                    'created_at': info['created_at'].isoformat()
                }
                for agent_id, info in self.agents.items()
            },
            'teams': self.teams,
            'tasks': {
                task_id: {
                    'status': info['status'],
                    'assigned_to': info['assigned_to'],
                    'created_at': info['created_at'].isoformat()
                }
                for task_id, info in self.tasks.items()
            },
            'tool_usage': self.tool_manager.get_usage_stats() if self.tool_manager else {}
        }
```

## 5. Example Usage

Here's how to use the unified system:

```python
# examples/unified_system_demo.py

import asyncio
from src.orchestration.unified_orchestrator import UnifiedOrchestrator

async def main():
    # Configure the system
    config = {
        'environment_mode': 'PRODUCTION',
        'topology': 'hierarchical',
        'max_agents': 50,
        'enable_resource_management': True,
        'workspace_root': '/app/agent_workspace'
    }
    
    # Create orchestrator
    orchestrator = UnifiedOrchestrator(config)
    await orchestrator.initialize()
    
    # Create a mixed team
    team_config = {
        'agents': [
            {
                'type': 'cognitive',
                'count': 2,
                'name_prefix': 'Analyst',
                'role': 'data_analyst',
                'capabilities': ['analysis', 'reporting']
            },
            {
                'type': 'hybrid',
                'count': 3,
                'name_prefix': 'Developer',
                'role': 'software_developer',
                'capabilities': ['coding', 'testing', 'debugging']
            },
            {
                'type': 'reflexive',
                'count': 2,
                'name_prefix': 'Monitor',
                'role': 'system_monitor',
                'capabilities': ['monitoring', 'alerting']
            },
            {
                'type': 'autonomous',
                'count': 1,
                'name_prefix': 'Coordinator',
                'role': 'team_lead',
                'capabilities': ['coordination', 'planning', 'resource_management']
            }
        ]
    }
    
    # Create the team
    team_ids = await orchestrator.create_team('Development Team', team_config)
    print(f"Created team with {len(team_ids)} agents")
    
    # Assign a complex task
    task = {
        'name': 'Build REST API',
        'description': 'Design and implement a REST API for user management',
        'required_capabilities': ['analysis', 'coding', 'testing'],
        'priority': 'high',
        'subtasks': [
            'Design API schema',
            'Implement endpoints',
            'Write unit tests',
            'Document API'
        ]
    }
    
    task_id = await orchestrator.assign_task(task, team_name='Development Team')
    print(f"Assigned task: {task_id}")
    
    # Run the system
    orchestrator_task = asyncio.create_task(orchestrator.run())
    
    # Monitor for 60 seconds
    await asyncio.sleep(60)
    
    # Get system state
    state = await orchestrator.get_system_state()
    print(f"System state: {state}")
    
    # Cleanup
    orchestrator_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
```

This implementation guide provides a concrete path to unifying all MAS components into a single, cohesive system that maintains the strengths of each component while providing centralized management and coordination.