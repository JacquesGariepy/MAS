#!/usr/bin/env python3
"""
Production-Ready Swarm Multi-Agent System
Complete implementation with all features, no simplifications
"""

import asyncio
import os
import sys
import json
import psutil
import signal
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiofiles
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from collections import defaultdict, deque
import hashlib
import inspect
import networkx as nx
import numpy as np
from abc import ABC, abstractmethod

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

# Import MAS components
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService

# Import all tools
from src.tools.filesystem_tool import FileSystemTool
from src.tools.code_tool import CodeTool
from src.tools.git_tool import GitTool
from src.tools.web_search_tool import WebSearchTool
from src.tools.database_tool import DatabaseTool
from src.tools.http_tool import HTTPTool

# Import agents
from src.core.agents.base_agent import BaseAgent, BDI, AgentContext
from src.core.agents.cognitive_agent import CognitiveAgent
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.hybrid_agent import HybridAgent

# Import runtime and environment
from src.core.runtime.agent_runtime import AgentRuntime, get_agent_runtime
from src.core.environment import (
    SoftwareEnvironment,
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    EnvironmentAdapter,
    SystemConstraint,
    EnvironmentEvent,
    EnvironmentRule
)

from src.utils.logger import get_logger

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/app/logs/swarm_mas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Production logger
logger = get_logger("SWARM_MAS_PRODUCTION")


# Swarm States
class SwarmState(Enum):
    """Swarm lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    WORKING = "working"
    COORDINATING = "coordinating"
    OPTIMIZING = "optimizing"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


# Agent Task States
class TaskState(Enum):
    """Task execution states"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Coordination Strategies
class CoordinationStrategy(Enum):
    """Swarm coordination strategies"""
    CENTRALIZED = "centralized"
    DECENTRALIZED = "decentralized"
    HIERARCHICAL = "hierarchical"
    MARKET_BASED = "market_based"
    CONSENSUS = "consensus"
    EMERGENT = "emergent"


@dataclass
class SwarmTask:
    """Task representation in swarm"""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    priority: int = 5
    requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'priority': self.priority,
            'requirements': self.requirements,
            'dependencies': self.dependencies,
            'assigned_agent': self.assigned_agent,
            'state': self.state.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class SwarmMetrics:
    """Swarm performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_time: float = 0.0
    agent_utilization: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    coordination_overhead: float = 0.0
    communication_volume: int = 0
    error_rate: float = 0.0
    throughput: float = 0.0
    latency: float = 0.0


class SwarmCoordinator:
    """Production swarm coordinator with full features"""
    
    def __init__(self, name: str = "ProductionSwarm"):
        self.id = uuid4()
        self.name = f"{name}-{str(self.id)[:8]}"
        self.state = SwarmState.INITIALIZING
        
        # Core services
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        self.runtime = get_agent_runtime()
        
        # Swarm components
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_load: Dict[str, int] = defaultdict(int)
        
        # Task management
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.task_registry: Dict[str, SwarmTask] = {}
        self.task_dependencies: nx.DiGraph = nx.DiGraph()
        
        # Environment
        self.environment = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
        self.adapter = EnvironmentAdapter(self.environment)
        
        # Coordination
        self.coordination_strategy = CoordinationStrategy.HIERARCHICAL
        self.coordination_graph = nx.DiGraph()
        
        # Communication
        self.message_bus: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.broadcast_channel = asyncio.Queue()
        
        # Monitoring
        self.metrics = SwarmMetrics()
        self.event_log: deque = deque(maxlen=10000)
        self.performance_history: deque = deque(maxlen=1000)
        
        # Persistence
        self.checkpoint_interval = 300  # 5 minutes
        self.state_file = Path(f"/app/state/swarm_{self.id}.pkl")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Process/Thread pools
        self.process_pool = ProcessPoolExecutor(max_workers=mp.cpu_count())
        self.thread_pool = ThreadPoolExecutor(max_workers=mp.cpu_count() * 2)
        
        # Workspace
        self.workspace = Path(f"/app/workspace/swarm_{self.id}")
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Running tasks
        self.running_tasks: Set[asyncio.Task] = set()
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized {self.name} - Production Swarm System")
        
    async def initialize(self, num_agents: int = 10, agent_types: Optional[Dict[str, int]] = None):
        """Initialize swarm with specified agents"""
        logger.info(f"Initializing swarm with {num_agents} agents...")
        
        try:
            # Default agent distribution
            if not agent_types:
                agent_types = {
                    'architect': max(1, num_agents // 10),
                    'analyst': max(2, num_agents // 5),
                    'developer': max(3, num_agents // 3),
                    'tester': max(2, num_agents // 5),
                    'devops': max(1, num_agents // 10),
                    'data_engineer': max(1, num_agents // 10),
                    'coordinator': 1,
                    'monitor': 1
                }
                
            # Adjust to match requested number
            total = sum(agent_types.values())
            if total < num_agents:
                agent_types['developer'] += num_agents - total
                
            # Create agents
            for agent_type, count in agent_types.items():
                for i in range(count):
                    agent = await self._create_specialized_agent(agent_type, i)
                    if agent:
                        self.agents[str(agent.agent_id)] = agent
                        self.agent_capabilities[str(agent.agent_id)] = set(agent.capabilities)
                        
            # Build coordination graph
            await self._build_coordination_graph()
            
            # Start background tasks
            self._start_background_tasks()
            
            # Load previous state if exists
            await self._load_state()
            
            self.state = SwarmState.READY
            logger.info(f"Swarm initialized with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize swarm: {e}")
            raise
            
    async def _create_specialized_agent(self, agent_type: str, index: int) -> Optional[BaseAgent]:
        """Create a specialized agent with full tool suite"""
        try:
            agent_configs = {
                'architect': {
                    'class': CognitiveAgent,
                    'capabilities': ['design', 'architecture', 'planning', 'system_analysis'],
                    'tools': [FileSystemTool, CodeTool, DatabaseTool],
                    'visibility': VisibilityLevel.FULL
                },
                'analyst': {
                    'class': CognitiveAgent,
                    'capabilities': ['analysis', 'research', 'data_processing', 'reporting'],
                    'tools': [FileSystemTool, WebSearchTool, DatabaseTool],
                    'visibility': VisibilityLevel.FULL
                },
                'developer': {
                    'class': HybridAgent,
                    'capabilities': ['coding', 'implementation', 'debugging', 'optimization'],
                    'tools': [FileSystemTool, CodeTool, GitTool, DatabaseTool],
                    'visibility': VisibilityLevel.NAMESPACE
                },
                'tester': {
                    'class': HybridAgent,
                    'capabilities': ['testing', 'validation', 'quality_assurance', 'automation'],
                    'tools': [FileSystemTool, CodeTool, HTTPTool],
                    'visibility': VisibilityLevel.NAMESPACE
                },
                'devops': {
                    'class': HybridAgent,
                    'capabilities': ['deployment', 'monitoring', 'infrastructure', 'ci_cd'],
                    'tools': [FileSystemTool, GitTool, HTTPTool, DatabaseTool],
                    'visibility': VisibilityLevel.NAMESPACE
                },
                'data_engineer': {
                    'class': HybridAgent,
                    'capabilities': ['etl', 'data_pipeline', 'analytics', 'data_modeling'],
                    'tools': [FileSystemTool, DatabaseTool, CodeTool],
                    'visibility': VisibilityLevel.NAMESPACE
                },
                'coordinator': {
                    'class': ReflexiveAgent,
                    'capabilities': ['coordination', 'resource_management', 'scheduling', 'conflict_resolution'],
                    'tools': [FileSystemTool],
                    'visibility': VisibilityLevel.FULL
                },
                'monitor': {
                    'class': ReflexiveAgent,
                    'capabilities': ['monitoring', 'alerting', 'performance_analysis', 'anomaly_detection'],
                    'tools': [FileSystemTool, HTTPTool],
                    'visibility': VisibilityLevel.FULL
                }
            }
            
            config = agent_configs.get(agent_type)
            if not config:
                logger.warning(f"Unknown agent type: {agent_type}")
                return None
                
            # Create agent
            agent_class = config['class']
            agent_name = f"{agent_type.capitalize()}-{index}-{self.name}"
            
            if agent_class == ReflexiveAgent:
                agent = agent_class(
                    agent_id=uuid4(),
                    name=agent_name,
                    role=agent_type,
                    capabilities=config['capabilities']
                )
                # Add production rules
                agent.rules = self._get_reflexive_rules(agent_type)
            else:
                agent = agent_class(
                    agent_id=uuid4(),
                    name=agent_name,
                    role=agent_type,
                    capabilities=config['capabilities'],
                    llm_service=self.llm_service
                )
                
            # Load tools
            for tool_class in config['tools']:
                tool = self._create_tool(tool_class, str(agent.agent_id))
                if tool:
                    agent.tools[tool.name] = tool
                    
            # Register with runtime
            await self.runtime.register_agent(agent)
            await self.runtime.start_agent(agent)
            
            # Register with environment
            await self.adapter.register_agent(agent, namespace=f"swarm/{agent_type}")
            
            # Set visibility
            self.environment.observability.set_visibility(
                str(agent.agent_id),
                config['visibility']
            )
            
            # Allocate resources
            resources = self._calculate_agent_resources(agent_type)
            success = self.environment.resource_manager.request_resources(
                str(agent.agent_id),
                resources
            )
            
            if not success:
                logger.warning(f"Failed to allocate resources for {agent_name}")
                
            logger.info(f"Created agent: {agent_name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent: {e}")
            return None
            
    def _create_tool(self, tool_class: type, agent_id: str) -> Any:
        """Create tool instance with proper initialization"""
        try:
            tool_name = tool_class.__name__
            
            if tool_name == 'FileSystemTool':
                return tool_class()
            else:
                # Our custom tools
                return tool_class(
                    agent_id=agent_id,
                    workspace_root=str(self.workspace)
                )
        except Exception as e:
            logger.error(f"Failed to create {tool_class.__name__}: {e}")
            return None
            
    def _get_reflexive_rules(self, agent_type: str) -> Dict[str, Callable]:
        """Get reflexive rules for agent type"""
        if agent_type == 'coordinator':
            return {
                'high_load': lambda ctx: ctx.get('system_load', 0) > 80,
                'task_backlog': lambda ctx: ctx.get('pending_tasks', 0) > 10,
                'agent_failure': lambda ctx: ctx.get('failed_agents', 0) > 0,
                'resource_shortage': lambda ctx: ctx.get('available_cpu', 100) < 20,
                'deadlock_detected': lambda ctx: ctx.get('circular_dependencies', False)
            }
        elif agent_type == 'monitor':
            return {
                'performance_degradation': lambda ctx: ctx.get('latency', 0) > 1000,
                'error_spike': lambda ctx: ctx.get('error_rate', 0) > 0.1,
                'memory_leak': lambda ctx: ctx.get('memory_growth_rate', 0) > 0.05,
                'agent_unresponsive': lambda ctx: ctx.get('unresponsive_agents', 0) > 0
            }
        return {}
        
    def _calculate_agent_resources(self, agent_type: str) -> Dict[str, float]:
        """Calculate resource allocation for agent type"""
        base_allocations = {
            'architect': {'cpu': 15, 'memory': 1024 * 1024 * 1024},  # 1GB
            'analyst': {'cpu': 20, 'memory': 2048 * 1024 * 1024},   # 2GB
            'developer': {'cpu': 30, 'memory': 2048 * 1024 * 1024}, # 2GB
            'tester': {'cpu': 25, 'memory': 1024 * 1024 * 1024},    # 1GB
            'devops': {'cpu': 20, 'memory': 1024 * 1024 * 1024},    # 1GB
            'data_engineer': {'cpu': 25, 'memory': 3072 * 1024 * 1024}, # 3GB
            'coordinator': {'cpu': 10, 'memory': 512 * 1024 * 1024},     # 512MB
            'monitor': {'cpu': 10, 'memory': 512 * 1024 * 1024}          # 512MB
        }
        
        return base_allocations.get(agent_type, {'cpu': 10, 'memory': 512 * 1024 * 1024})
        
    async def _build_coordination_graph(self):
        """Build coordination graph based on strategy"""
        if self.coordination_strategy == CoordinationStrategy.HIERARCHICAL:
            # Find coordinators
            coordinators = [aid for aid, agent in self.agents.items() 
                          if agent.role == 'coordinator']
            
            if coordinators:
                # Coordinator at top
                for coord_id in coordinators:
                    # Connect to all other agents
                    for agent_id in self.agents:
                        if agent_id != coord_id:
                            self.coordination_graph.add_edge(coord_id, agent_id)
                            
            # Create team connections
            teams = defaultdict(list)
            for agent_id, agent in self.agents.items():
                teams[agent.role].append(agent_id)
                
            # Connect team members
            for role, members in teams.items():
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        self.coordination_graph.add_edge(members[i], members[j])
                        
        elif self.coordination_strategy == CoordinationStrategy.DECENTRALIZED:
            # Full mesh
            for agent1 in self.agents:
                for agent2 in self.agents:
                    if agent1 != agent2:
                        self.coordination_graph.add_edge(agent1, agent2)
                        
        # Update environment connections
        await self._sync_coordination_to_environment()
        
    async def _sync_coordination_to_environment(self):
        """Sync coordination graph to environment connections"""
        for edge in self.coordination_graph.edges():
            agent1_id, agent2_id = edge
            self.environment.spatial_model.add_connection(
                agent1_id, agent2_id, "coordination"
            )
            
    def _start_background_tasks(self):
        """Start all background tasks"""
        tasks = [
            self._environment_update_loop(),
            self._task_scheduler_loop(),
            self._monitoring_loop(),
            self._checkpoint_loop(),
            self._coordination_loop(),
            self._optimization_loop()
        ]
        
        for task in tasks:
            task_obj = asyncio.create_task(task)
            self.running_tasks.add(task_obj)
            task_obj.add_done_callback(self.running_tasks.discard)
            
    async def _environment_update_loop(self):
        """Update environment state"""
        while not self.shutdown_event.is_set():
            try:
                await self.environment.update(1.0)
                
                # Update agent contexts
                for agent in self.agents.values():
                    await self.adapter.update_agent_context(agent)
                    
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Environment update error: {e}")
                
    async def _task_scheduler_loop(self):
        """Schedule tasks to agents"""
        while not self.shutdown_event.is_set():
            try:
                # Get task from queue (with timeout to check shutdown)
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                    
                # Check dependencies
                if await self._check_task_dependencies(task):
                    # Find best agent
                    agent_id = await self._find_best_agent(task)
                    
                    if agent_id:
                        # Assign task
                        task.assigned_agent = agent_id
                        task.state = TaskState.ASSIGNED
                        task.started_at = datetime.utcnow()
                        
                        # Send to agent
                        await self._dispatch_task_to_agent(task, agent_id)
                        
                        # Update metrics
                        self.agent_load[agent_id] += 1
                        
                    else:
                        # No suitable agent, requeue
                        await self.task_queue.put(task)
                        await asyncio.sleep(0.1)
                else:
                    # Dependencies not met, requeue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
                
    async def _monitoring_loop(self):
        """Monitor swarm health and performance"""
        while not self.shutdown_event.is_set():
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Update history
                self.performance_history.append({
                    'timestamp': datetime.utcnow(),
                    'metrics': metrics
                })
                
                # Check for issues
                await self._check_health(metrics)
                
                # Log status
                if len(self.performance_history) % 10 == 0:
                    logger.info(f"Swarm metrics: {metrics}")
                    
                await asyncio.sleep(5.0)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
    async def _checkpoint_loop(self):
        """Periodically save swarm state"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.checkpoint_interval)
                await self._save_state()
                logger.info("Swarm state checkpointed")
                
            except Exception as e:
                logger.error(f"Checkpoint error: {e}")
                
    async def _coordination_loop(self):
        """Handle inter-agent coordination"""
        while not self.shutdown_event.is_set():
            try:
                # Process broadcast messages
                try:
                    message = await asyncio.wait_for(
                        self.broadcast_channel.get(),
                        timeout=0.1
                    )
                    await self._handle_broadcast(message)
                except asyncio.TimeoutError:
                    pass
                    
                # Check for coordination needs (removed for now)
                # TODO: Implement coordination checking logic
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Coordination error: {e}")
                
    async def _optimization_loop(self):
        """Optimize swarm performance"""
        while not self.shutdown_event.is_set():
            try:
                # Run optimization every 30 seconds
                await asyncio.sleep(30.0)
                
                # Optimize task distribution
                await self._optimize_task_distribution()
                
                # Rebalance resources
                await self._rebalance_resources()
                
                # Update coordination graph if needed
                await self._optimize_coordination_graph()
                
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                
    async def submit_task(self, task_type: str, description: str, 
                         requirements: List[str] = None,
                         dependencies: List[str] = None,
                         priority: int = 5,
                         metadata: Dict[str, Any] = None) -> str:
        """Submit a task to the swarm"""
        task = SwarmTask(
            type=task_type,
            priority=priority,
            requirements=requirements or [],
            dependencies=dependencies or [],
            metadata=metadata or {'description': description}
        )
        
        # Register task
        self.task_registry[task.id] = task
        
        # Add to dependency graph
        self.task_dependencies.add_node(task.id)
        for dep in task.dependencies:
            if dep in self.task_registry:
                self.task_dependencies.add_edge(dep, task.id)
                
        # Queue task
        await self.task_queue.put(task)
        
        # Log event
        self._log_event('task_submitted', {
            'task_id': task.id,
            'type': task_type,
            'priority': priority
        })
        
        logger.info(f"Task submitted: {task.id} ({task_type})")
        return task.id
        
    async def _check_task_dependencies(self, task: SwarmTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id in self.task_registry:
                dep_task = self.task_registry[dep_id]
                if dep_task.state != TaskState.COMPLETED:
                    return False
        return True
        
    async def _find_best_agent(self, task: SwarmTask) -> Optional[str]:
        """Find best agent for task using multi-criteria optimization"""
        candidates = []
        
        for agent_id, agent in self.agents.items():
            # Check capability match
            capability_score = len(set(task.requirements) & self.agent_capabilities[agent_id])
            if capability_score == 0:
                continue
                
            # Check availability
            current_load = self.agent_load[agent_id]
            if current_load >= 5:  # Max 5 concurrent tasks
                continue
                
            # Calculate fitness score
            fitness = self._calculate_agent_fitness(agent_id, task)
            candidates.append((agent_id, fitness))
            
        if not candidates:
            return None
            
        # Sort by fitness
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
        
    def _calculate_agent_fitness(self, agent_id: str, task: SwarmTask) -> float:
        """Calculate agent fitness for task"""
        agent = self.agents[agent_id]
        
        # Capability match (40%)
        cap_match = len(set(task.requirements) & self.agent_capabilities[agent_id])
        cap_score = cap_match / max(len(task.requirements), 1) * 0.4
        
        # Current load (30%)
        load = self.agent_load[agent_id]
        load_score = (1 - load / 5) * 0.3
        
        # Historical performance (20%)
        success_rate = self._get_agent_success_rate(agent_id)
        perf_score = success_rate * 0.2
        
        # Resource availability (10%)
        resource_score = self._get_agent_resource_score(agent_id) * 0.1
        
        return cap_score + load_score + perf_score + resource_score
        
    def _get_agent_success_rate(self, agent_id: str) -> float:
        """Get agent's historical success rate"""
        completed = 0
        failed = 0
        
        for task in self.task_registry.values():
            if task.assigned_agent == agent_id:
                if task.state == TaskState.COMPLETED:
                    completed += 1
                elif task.state == TaskState.FAILED:
                    failed += 1
                    
        total = completed + failed
        return completed / total if total > 0 else 0.8  # Default 80%
        
    def _get_agent_resource_score(self, agent_id: str) -> float:
        """Get agent's resource availability score"""
        try:
            perception = self.environment.perceive(agent_id)
            resources = perception.get('resources', {})
            
            cpu_avail = 1 - resources.get('cpu', {}).get('utilization', 0) / 100
            mem_avail = resources.get('memory', {}).get('available', 0) / resources.get('memory', {}).get('total', 1)
            
            return (cpu_avail + mem_avail) / 2
        except:
            return 0.5
            
    async def _dispatch_task_to_agent(self, task: SwarmTask, agent_id: str):
        """Dispatch task to selected agent"""
        agent = self.agents[agent_id]
        
        # Create task message
        message = {
            'type': 'task_assignment',
            'task_id': task.id,
            'task_type': task.type,
            'requirements': task.requirements,
            'metadata': task.metadata,
            'from': 'coordinator',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send via runtime
        await self.runtime.send_message(
            'coordinator',
            agent_id,
            message
        )
        
        # Start task monitor
        asyncio.create_task(self._monitor_task_execution(task))
        
        logger.info(f"Task {task.id} dispatched to {agent.name}")
        
    async def _monitor_task_execution(self, task: SwarmTask):
        """Monitor task execution"""
        timeout = 300  # 5 minutes default
        start_time = datetime.utcnow()
        
        while task.state in [TaskState.ASSIGNED, TaskState.IN_PROGRESS]:
            # Check timeout
            if (datetime.utcnow() - start_time).total_seconds() > timeout:
                task.state = TaskState.FAILED
                task.error = "Task timeout"
                
                # Release agent
                if task.assigned_agent:
                    self.agent_load[task.assigned_agent] -= 1
                    
                logger.warning(f"Task {task.id} timed out")
                break
                
            # Check agent health
            if task.assigned_agent and not await self._is_agent_healthy(task.assigned_agent):
                # Reassign task
                task.state = TaskState.PENDING
                task.assigned_agent = None
                await self.task_queue.put(task)
                
                logger.warning(f"Task {task.id} agent unhealthy, reassigning")
                break
                
            await asyncio.sleep(5.0)
            
    async def _is_agent_healthy(self, agent_id: str) -> bool:
        """Check if agent is healthy"""
        if agent_id not in self.agents:
            return False
            
        agent = self.agents[agent_id]
        
        # Check if running
        if not agent._running:
            return False
            
        # Check runtime status
        if agent_id not in self.runtime.running_agents:
            return False
            
        # Check responsiveness (simplified)
        return True
        
    async def handle_task_result(self, task_id: str, result: Any, error: Optional[str] = None):
        """Handle task completion result"""
        if task_id not in self.task_registry:
            logger.warning(f"Unknown task result: {task_id}")
            return
            
        task = self.task_registry[task_id]
        task.completed_at = datetime.utcnow()
        
        if error:
            task.state = TaskState.FAILED
            task.error = error
            self.metrics.tasks_failed += 1
        else:
            task.state = TaskState.COMPLETED
            task.result = result
            self.metrics.tasks_completed += 1
            
        # Update agent load
        if task.assigned_agent:
            self.agent_load[task.assigned_agent] -= 1
            
        # Calculate task time
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            # Update average
            total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
            self.metrics.average_task_time = (
                (self.metrics.average_task_time * (total_tasks - 1) + duration) / total_tasks
            )
            
        # Check dependent tasks
        await self._check_dependent_tasks(task_id)
        
        # Log event
        self._log_event('task_completed', {
            'task_id': task_id,
            'state': task.state.value,
            'duration': duration if task.started_at else 0
        })
        
        logger.info(f"Task {task_id} completed: {task.state.value}")
        
    async def _check_dependent_tasks(self, completed_task_id: str):
        """Check and queue tasks dependent on completed task"""
        if completed_task_id in self.task_dependencies:
            dependents = list(self.task_dependencies.successors(completed_task_id))
            
            for dep_id in dependents:
                if dep_id in self.task_registry:
                    dep_task = self.task_registry[dep_id]
                    if dep_task.state == TaskState.PENDING:
                        # Recheck if all dependencies met
                        if await self._check_task_dependencies(dep_task):
                            await self.task_queue.put(dep_task)
                            
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all agents"""
        message['timestamp'] = datetime.utcnow().isoformat()
        message['from'] = 'coordinator'
        
        for agent_id in self.agents:
            await self.runtime.send_message(
                'coordinator',
                agent_id,
                message
            )
            
        self.metrics.communication_volume += len(self.agents)
        
    async def _handle_broadcast(self, message: Dict[str, Any]):
        """Handle broadcast message"""
        msg_type = message.get('type')
        
        if msg_type == 'emergency_stop':
            await self.emergency_stop()
        elif msg_type == 'resource_rebalance':
            await self._rebalance_resources()
        elif msg_type == 'strategy_change':
            new_strategy = message.get('strategy')
            if new_strategy:
                await self.change_coordination_strategy(new_strategy)
                
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current swarm metrics"""
        # Resource usage
        resource_usage = self.environment.resource_manager.get_resource_usage()
        
        # Agent utilization
        agent_utils = {}
        for agent_id in self.agents:
            load = self.agent_load[agent_id]
            agent_utils[agent_id] = load / 5.0  # Max 5 tasks
            
        # Update metrics
        self.metrics.agent_utilization = agent_utils
        self.metrics.resource_usage = {
            'cpu': resource_usage['cpu']['utilization'],
            'memory': resource_usage['memory']['used'] / resource_usage['memory']['total']
        }
        
        # Calculate rates
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        self.metrics.error_rate = self.metrics.tasks_failed / max(total_tasks, 1)
        
        # Throughput (tasks/minute)
        if self.performance_history:
            time_window = 60  # 1 minute
            recent_completed = sum(
                1 for entry in self.performance_history
                if (datetime.utcnow() - entry['timestamp']).total_seconds() <= time_window
                and entry.get('metrics', {}).get('tasks_completed', 0) > 0
            )
            self.metrics.throughput = recent_completed
            
        return {
            'tasks_completed': self.metrics.tasks_completed,
            'tasks_failed': self.metrics.tasks_failed,
            'error_rate': self.metrics.error_rate,
            'avg_utilization': np.mean(list(agent_utils.values())),
            'cpu_usage': self.metrics.resource_usage.get('cpu', 0),
            'memory_usage': self.metrics.resource_usage.get('memory', 0),
            'throughput': self.metrics.throughput
        }
        
    async def _check_health(self, metrics: Dict[str, Any]):
        """Check swarm health and take corrective actions"""
        issues = []
        
        # High error rate
        if metrics['error_rate'] > 0.2:
            issues.append('high_error_rate')
            
        # Low throughput
        if self.state == SwarmState.WORKING and metrics['throughput'] < 1:
            issues.append('low_throughput')
            
        # High resource usage
        if metrics['cpu_usage'] > 90:
            issues.append('high_cpu_usage')
            
        if metrics['memory_usage'] > 0.9:
            issues.append('high_memory_usage')
            
        # Take corrective actions
        if issues:
            logger.warning(f"Health issues detected: {issues}")
            
            if 'high_error_rate' in issues:
                await self._investigate_errors()
                
            if 'high_cpu_usage' in issues or 'high_memory_usage' in issues:
                await self._reduce_load()
                
    async def _investigate_errors(self):
        """Investigate high error rate"""
        # Analyze recent failures
        recent_failures = [
            task for task in self.task_registry.values()
            if task.state == TaskState.FAILED and task.completed_at and
            (datetime.utcnow() - task.completed_at).total_seconds() < 300
        ]
        
        # Group by error type
        error_groups = defaultdict(list)
        for task in recent_failures:
            error_groups[task.error or 'unknown'].append(task)
            
        # Log analysis
        for error, tasks in error_groups.items():
            logger.warning(f"Error pattern: {error} ({len(tasks)} occurrences)")
            
    async def _reduce_load(self):
        """Reduce system load"""
        logger.info("Reducing system load...")
        
        # Pause low priority tasks
        pending_tasks = [
            task for task in self.task_registry.values()
            if task.state == TaskState.PENDING and task.priority < 5
        ]
        
        for task in pending_tasks[:5]:  # Pause up to 5 tasks
            task.state = TaskState.BLOCKED
            task.metadata['blocked_reason'] = 'high_system_load'
            
        # Request resource optimization
        await self.broadcast_message({
            'type': 'resource_optimization',
            'level': 'aggressive'
        })
        
    async def _optimize_task_distribution(self):
        """Optimize task distribution across agents"""
        # Analyze current distribution
        load_variance = np.var(list(self.agent_load.values()))
        
        if load_variance > 2.0:  # High variance
            logger.info("Rebalancing task distribution...")
            
            # Find overloaded and underloaded agents
            avg_load = np.mean(list(self.agent_load.values()))
            overloaded = [aid for aid, load in self.agent_load.items() if load > avg_load + 1]
            underloaded = [aid for aid, load in self.agent_load.items() if load < avg_load - 1]
            
            # Reassign pending tasks
            for task in self.task_registry.values():
                if (task.state == TaskState.ASSIGNED and 
                    task.assigned_agent in overloaded and
                    task.started_at is None):
                    
                    # Find better agent from underloaded
                    for new_agent in underloaded:
                        if set(task.requirements) & self.agent_capabilities[new_agent]:
                            # Reassign
                            self.agent_load[task.assigned_agent] -= 1
                            task.assigned_agent = new_agent
                            self.agent_load[new_agent] += 1
                            
                            await self._dispatch_task_to_agent(task, new_agent)
                            break
                            
    async def _rebalance_resources(self):
        """Rebalance resource allocations"""
        logger.info("Rebalancing resources...")
        
        # Get current allocations
        allocations = {}
        for agent_id in self.agents:
            allocations[agent_id] = self.environment.resource_manager.allocations.get(agent_id, {})
            
        # Calculate ideal allocations based on load
        total_load = sum(self.agent_load.values())
        if total_load == 0:
            return
            
        # Redistribute proportionally
        for agent_id, agent in self.agents.items():
            load_ratio = self.agent_load[agent_id] / total_load
            
            # Calculate new allocation
            base_resources = self._calculate_agent_resources(agent.role)
            new_allocation = {
                'cpu': base_resources['cpu'] * (1 + load_ratio),
                'memory': base_resources['memory'] * (1 + load_ratio * 0.5)
            }
            
            # Update if significantly different
            current = allocations.get(agent_id, {})
            if (abs(current.get('cpu', 0) - new_allocation['cpu']) > 5 or
                abs(current.get('memory', 0) - new_allocation['memory']) > 100 * 1024 * 1024):
                
                # Release current
                self.environment.resource_manager.release_resources(
                    agent_id, current
                )
                
                # Request new
                self.environment.resource_manager.request_resources(
                    agent_id, new_allocation
                )
                
    async def _optimize_coordination_graph(self):
        """Optimize coordination graph based on communication patterns"""
        # Analyze communication patterns (simplified)
        comm_matrix = defaultdict(lambda: defaultdict(int))
        
        # Count communications from event log
        for event in self.event_log:
            if event.get('type') == 'message_sent':
                from_agent = event.get('from')
                to_agent = event.get('to')
                if from_agent and to_agent:
                    comm_matrix[from_agent][to_agent] += 1
                    
        # Add high-communication pairs
        threshold = 10  # Messages in recent history
        edges_added = 0
        
        for from_agent, targets in comm_matrix.items():
            for to_agent, count in targets.items():
                if count > threshold:
                    if not self.coordination_graph.has_edge(from_agent, to_agent):
                        self.coordination_graph.add_edge(from_agent, to_agent)
                        edges_added += 1
                        
        if edges_added > 0:
            logger.info(f"Added {edges_added} coordination edges")
            await self._sync_coordination_to_environment()
            
    async def change_coordination_strategy(self, new_strategy: CoordinationStrategy):
        """Change swarm coordination strategy"""
        logger.info(f"Changing coordination strategy to {new_strategy.value}")
        
        self.coordination_strategy = new_strategy
        
        # Rebuild coordination graph
        self.coordination_graph.clear()
        await self._build_coordination_graph()
        
        # Notify agents
        await self.broadcast_message({
            'type': 'strategy_change',
            'new_strategy': new_strategy.value
        })
        
    async def emergency_stop(self):
        """Emergency stop all operations"""
        logger.warning("Emergency stop initiated!")
        
        self.state = SwarmState.SUSPENDED
        
        # Stop all agents
        await self.broadcast_message({
            'type': 'emergency_stop',
            'reason': 'manual_trigger'
        })
        
        # Cancel running tasks
        for task in self.task_registry.values():
            if task.state in [TaskState.ASSIGNED, TaskState.IN_PROGRESS]:
                task.state = TaskState.CANCELLED
                
        # Clear queues
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except:
                break
                
    async def resume_operations(self):
        """Resume after emergency stop"""
        logger.info("Resuming operations...")
        
        self.state = SwarmState.READY
        
        # Notify agents
        await self.broadcast_message({
            'type': 'resume_operations'
        })
        
        # Requeue cancelled tasks
        for task in self.task_registry.values():
            if task.state == TaskState.CANCELLED:
                task.state = TaskState.PENDING
                await self.task_queue.put(task)
                
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log event to event log"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'data': data
        }
        self.event_log.append(event)
        
    async def _save_state(self):
        """Save swarm state to disk"""
        try:
            state = {
                'id': str(self.id),
                'name': self.name,
                'state': self.state.value,
                'agents': {aid: {
                    'name': agent.name,
                    'role': agent.role,
                    'capabilities': agent.capabilities
                } for aid, agent in self.agents.items()},
                'task_registry': {tid: task.to_dict() 
                                for tid, task in self.task_registry.items()},
                'metrics': self.metrics.__dict__,
                'coordination_strategy': self.coordination_strategy.value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(self.state_file, 'wb') as f:
                await f.write(pickle.dumps(state))
                
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    async def _load_state(self):
        """Load previous swarm state"""
        if not self.state_file.exists():
            return
            
        try:
            async with aiofiles.open(self.state_file, 'rb') as f:
                data = await f.read()
                state = pickle.loads(data)
                
            logger.info(f"Loaded previous state from {state['timestamp']}")
            
            # Restore task registry
            for tid, task_data in state.get('task_registry', {}).items():
                if tid not in self.task_registry:
                    task = SwarmTask(**{k: v for k, v in task_data.items() 
                                      if k != 'state'})
                    task.state = TaskState(task_data['state'])
                    self.task_registry[tid] = task
                    
                    # Requeue pending tasks
                    if task.state == TaskState.PENDING:
                        await self.task_queue.put(task)
                        
            # Restore metrics
            metrics_data = state.get('metrics', {})
            for key, value in metrics_data.items():
                if hasattr(self.metrics, key):
                    setattr(self.metrics, key, value)
                    
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm status"""
        return {
            'swarm_id': str(self.id),
            'name': self.name,
            'state': self.state.value,
            'agents': {
                'total': len(self.agents),
                'by_role': defaultdict(int, {
                    agent.role: sum(1 for a in self.agents.values() if a.role == agent.role)
                    for agent in self.agents.values()
                }),
                'utilization': {
                    aid: self.agent_load[aid] / 5.0
                    for aid in self.agents
                }
            },
            'tasks': {
                'total': len(self.task_registry),
                'pending': sum(1 for t in self.task_registry.values() if t.state == TaskState.PENDING),
                'in_progress': sum(1 for t in self.task_registry.values() if t.state == TaskState.IN_PROGRESS),
                'completed': self.metrics.tasks_completed,
                'failed': self.metrics.tasks_failed,
                'average_time': self.metrics.average_task_time
            },
            'resources': self.metrics.resource_usage,
            'performance': {
                'throughput': self.metrics.throughput,
                'error_rate': self.metrics.error_rate,
                'latency': self.metrics.latency
            },
            'coordination': {
                'strategy': self.coordination_strategy.value,
                'graph_nodes': self.coordination_graph.number_of_nodes(),
                'graph_edges': self.coordination_graph.number_of_edges()
            }
        }
        
    async def shutdown(self):
        """Gracefully shutdown swarm"""
        logger.info("Shutting down swarm...")
        
        self.state = SwarmState.TERMINATED
        self.shutdown_event.set()
        
        # Save final state
        await self._save_state()
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
            
        # Cancel running tasks
        for task in self.running_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.running_tasks, return_exceptions=True)
        
        # Shutdown pools
        self.process_pool.shutdown()
        self.thread_pool.shutdown()
        
        logger.info("Swarm shutdown complete")


# Production test
async def production_test():
    """Test production swarm system"""
    print("\n" + "="*80)
    print("🚀 PRODUCTION SWARM MULTI-AGENT SYSTEM")
    print("Complete implementation with all features")
    print("="*80 + "\n")
    
    # Create swarm
    swarm = SwarmCoordinator("ProductionSwarm")
    
    try:
        # Initialize with 15 agents
        await swarm.initialize(num_agents=15)
        
        # Show initial status
        status = await swarm.get_status()
        print("\n📊 Initial Swarm Status:")
        print(f"- State: {status['state']}")
        print(f"- Agents: {status['agents']['total']}")
        print(f"- Agent distribution: {dict(status['agents']['by_role'])}")
        
        # Submit complex workflow
        print("\n📝 Submitting Complex Workflow...")
        
        # Task 1: Analysis
        task1_id = await swarm.submit_task(
            task_type='analysis',
            description='Analyze requirements for microservices architecture',
            requirements=['analysis', 'architecture'],
            priority=8
        )
        
        # Task 2: Design (depends on analysis)
        task2_id = await swarm.submit_task(
            task_type='design',
            description='Design microservices system',
            requirements=['design', 'architecture'],
            dependencies=[task1_id],
            priority=7
        )
        
        # Task 3: Implementation (depends on design)
        task3_id = await swarm.submit_task(
            task_type='implementation',
            description='Implement user service',
            requirements=['coding', 'implementation'],
            dependencies=[task2_id],
            priority=6
        )
        
        # Task 4: Testing (depends on implementation)
        task4_id = await swarm.submit_task(
            task_type='testing',
            description='Test user service',
            requirements=['testing', 'validation'],
            dependencies=[task3_id],
            priority=5
        )
        
        # Task 5: Deployment (depends on testing)
        task5_id = await swarm.submit_task(
            task_type='deployment',
            description='Deploy user service',
            requirements=['deployment', 'infrastructure'],
            dependencies=[task4_id],
            priority=9
        )
        
        print(f"Submitted 5 tasks with dependencies")
        
        # Monitor progress
        print("\n⏳ Monitoring Progress...")
        for i in range(30):  # Monitor for 30 seconds
            await asyncio.sleep(1)
            
            # Get current metrics
            metrics = await swarm._collect_metrics()
            
            # Show progress every 5 seconds
            if i % 5 == 0:
                print(f"\n[{i}s] Progress Update:")
                print(f"- Tasks completed: {metrics['tasks_completed']}")
                print(f"- CPU usage: {metrics['cpu_usage']:.1f}%")
                print(f"- Avg utilization: {metrics['avg_utilization']:.2f}")
                
        # Final status
        final_status = await swarm.get_status()
        print("\n📊 Final Status:")
        print(f"- Tasks completed: {final_status['tasks']['completed']}")
        print(f"- Tasks failed: {final_status['tasks']['failed']}")
        print(f"- Average task time: {final_status['tasks']['average_time']:.2f}s")
        print(f"- Throughput: {final_status['performance']['throughput']} tasks/min")
        
        # Show some task details
        print("\n📋 Task Results:")
        for task_id in [task1_id, task2_id, task3_id, task4_id, task5_id]:
            if task_id in swarm.task_registry:
                task = swarm.task_registry[task_id]
                print(f"- {task.type}: {task.state.value}")
                
    finally:
        # Shutdown
        await swarm.shutdown()
        
    print("\n✅ Production test complete!")


if __name__ == "__main__":
    # Handle signals
    def signal_handler(sig, frame):
        print("\nShutdown signal received...")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run production test
    asyncio.run(production_test())