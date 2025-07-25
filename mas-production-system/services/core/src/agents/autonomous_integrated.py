"""
Enhanced Autonomous Agent with Full Environment Integration
Extends the existing autonomous agent with Ferber's MAS principles
"""

import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.agents.cognitive_agent import CognitiveAgent
from src.agents.reflexive_agent import ReflexiveAgent
from src.agents.hybrid_agent import HybridAgent
from src.tools import FileSystemTool
from src.utils.logger import get_logger

# Import environment if available
try:
    from src.core.environment import (
        SoftwareEnvironment,
        TopologyType,
        VisibilityLevel,
        EnvironmentAdapter
    )
    HAS_ENVIRONMENT = True
except ImportError:
    HAS_ENVIRONMENT = False
    logger = get_logger(__name__)
    logger.warning("Environment module not available, running with minimal environment")

class AutonomousIntegratedAgent(BaseAgent):
    """
    Autonomous agent with full environment integration
    Manages a team of specialized agents with resource management,
    partial observability, and constraint handling
    """
    
    def __init__(
        self,
        agent_id: UUID,
        name: str = "AutonomousIntegrated",
        enable_environment: bool = True,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="autonomous_coordinator",
            capabilities=[
                "orchestration",
                "analysis", 
                "implementation",
                "validation",
                "resource_management",
                "environment_aware"
            ],
            **kwargs
        )
        
        self.agent_type = "cognitive"  # For environment integration
        self.enable_environment = enable_environment and HAS_ENVIRONMENT
        
        # Environment components
        self.environment: Optional[Any] = None
        self.env_adapter: Optional[Any] = None
        
        # Team agents
        self.team_agents: Dict[str, BaseAgent] = {}
        self.agent_locations: Dict[str, Any] = {}
        
        # Resource tracking
        self.resource_allocations: Dict[str, Dict[str, float]] = {}
        self.resource_limits = {
            'cpu': 80.0,  # Max 80% total CPU
            'memory': 4 * 1024 * 1024 * 1024,  # 4GB total
            'disk_io': 100.0,
            'network': 50.0
        }
        
        # Workspace
        self.workspace_path = Path(f"/app/agent_workspace/integrated/{agent_id}")
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Load FileSystemTool
        self.fs_tool = FileSystemTool(
            agent_id=str(agent_id),
            workspace_root=str(self.workspace_path)
        )
        self.tools['filesystem'] = self.fs_tool
        
        self.logger = get_logger(f"{self.__class__.__name__}-{agent_id}")
        
    async def initialize_environment(self):
        """Initialize the software environment"""
        if not self.enable_environment:
            self.logger.info("Environment disabled, using minimal setup")
            return
            
        try:
            # Create software environment
            self.environment = SoftwareEnvironment(TopologyType.HIERARCHICAL)
            
            # Configure resource limits
            for resource, limit in self.resource_limits.items():
                if hasattr(self.environment.resource_manager.resources.get(resource, None), 'total'):
                    self.environment.resource_manager.resources[resource].total = limit
                    
            # Create adapter
            self.env_adapter = EnvironmentAdapter(self.environment)
            
            # Register self in environment
            await self.env_adapter.register_agent(self, namespace="autonomous")
            
            # Set full visibility for coordinator
            self.environment.observability.set_visibility(
                str(self.agent_id), VisibilityLevel.FULL
            )
            
            self.logger.info("Software environment initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize environment: {e}")
            self.enable_environment = False
            
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced perception with environment integration"""
        perception = await super().perceive(environment)
        
        if self.enable_environment and self.env_adapter:
            # Get environment perception
            env_perception = self.env_adapter.get_agent_perception(self)
            
            # Merge with base perception
            perception.update({
                'environment_state': {
                    'resources': env_perception.get('resources', {}),
                    'nearby_agents': env_perception.get('entities', {}),
                    'dynamics': env_perception.get('dynamics', {}),
                    'events': env_perception.get('events', [])
                },
                'team_status': {
                    agent_name: {
                        'active': agent._running,
                        'location': self.agent_locations.get(str(agent.agent_id)),
                        'resources': self.resource_allocations.get(str(agent.agent_id), {})
                    }
                    for agent_name, agent in self.team_agents.items()
                }
            })
            
        return perception
        
    async def deliberate(self) -> List[str]:
        """Deliberate with environment awareness"""
        intentions = []
        
        # Check resource availability
        if self.enable_environment and self.environment:
            usage = self.environment.resource_manager.get_resource_usage()
            
            # High CPU usage - optimize
            if usage['cpu']['utilization'] > 70:
                intentions.append("optimize_resource_usage")
                
            # Low memory - cleanup
            if usage['memory']['available'] < 500 * 1024 * 1024:  # Less than 500MB
                intentions.append("cleanup_memory")
                
        # Check team health
        for agent_name, agent in self.team_agents.items():
            if not agent._running:
                intentions.append(f"restart_agent_{agent_name}")
                
        # Process pending tasks
        if self.context.current_task:
            intentions.append("process_current_task")
            
        return intentions
        
    async def act(self) -> List[Dict[str, Any]]:
        """Execute actions with environment constraints"""
        actions = []
        
        for intention in self.bdi.intentions:
            if intention == "optimize_resource_usage":
                actions.append({
                    'type': 'tool_call',
                    'tool': 'resource_optimizer',
                    'params': {'target': 'cpu'}
                })
                
            elif intention == "cleanup_memory":
                actions.append({
                    'type': 'cleanup',
                    'target': 'memory'
                })
                
            elif intention.startswith("restart_agent_"):
                agent_name = intention.replace("restart_agent_", "")
                actions.append({
                    'type': 'restart_agent',
                    'agent': agent_name
                })
                
            elif intention == "process_current_task":
                actions.append({
                    'type': 'process_task',
                    'task': self.context.current_task
                })
                
        return actions
        
    async def create_team(self):
        """Create specialized team agents with environment integration"""
        self.logger.info("Creating specialized team...")
        
        # Initialize environment first
        await self.initialize_environment()
        
        # Create team agents
        team_config = [
            {
                'name': 'analyst',
                'class': CognitiveAgent,
                'capabilities': ['analysis', 'research', 'understanding'],
                'agent_type': 'cognitive',
                'resources': {'cpu': 15, 'memory': 512 * 1024 * 1024}
            },
            {
                'name': 'developer', 
                'class': HybridAgent,
                'capabilities': ['coding', 'implementation', 'debugging'],
                'agent_type': 'hybrid',
                'resources': {'cpu': 30, 'memory': 1024 * 1024 * 1024}
            },
            {
                'name': 'validator',
                'class': HybridAgent,
                'capabilities': ['testing', 'validation', 'quality_assurance'],
                'agent_type': 'hybrid',
                'resources': {'cpu': 20, 'memory': 512 * 1024 * 1024}
            },
            {
                'name': 'coordinator',
                'class': ReflexiveAgent,
                'capabilities': ['coordination', 'planning', 'monitoring'],
                'agent_type': 'reflexive',
                'resources': {'cpu': 10, 'memory': 256 * 1024 * 1024}
            }
        ]
        
        for config in team_config:
            agent = await self._create_team_agent(config)
            if agent:
                self.team_agents[config['name']] = agent
                
        # Create network topology if environment enabled
        if self.enable_environment and self.env_adapter:
            agents = [self] + list(self.team_agents.values())
            await self.env_adapter.create_agent_network(agents, topology="star")
            
        self.logger.info(f"Created team with {len(self.team_agents)} agents")
        
    async def _create_team_agent(self, config: Dict[str, Any]) -> Optional[BaseAgent]:
        """Create and register a team agent"""
        try:
            # Create agent instance
            agent_class = config['class']
            agent = agent_class(
                agent_id=uuid4(),
                name=f"{config['name']}-{self.name}",
                role=config['name'],
                capabilities=config['capabilities'],
                llm_service=self.llm_service
            )
            
            # Set agent type for environment
            agent.agent_type = config['agent_type']
            
            # Start agent
            asyncio.create_task(agent.run())
            
            # Register with environment
            if self.enable_environment and self.env_adapter:
                await self.env_adapter.register_agent(
                    agent, 
                    namespace=f"team/{config['name']}"
                )
                
                # Set visibility based on type
                visibility_map = {
                    'cognitive': VisibilityLevel.NAMESPACE,
                    'hybrid': VisibilityLevel.PROCESS,
                    'reflexive': VisibilityLevel.PROCESS
                }
                
                self.environment.observability.set_visibility(
                    str(agent.agent_id),
                    visibility_map.get(config['agent_type'], VisibilityLevel.PROCESS)
                )
                
                # Allocate resources
                success, result = await self.env_adapter.execute_agent_action(agent, {
                    'type': 'request_resources',
                    'resources': config['resources']
                })
                
                if success:
                    self.resource_allocations[str(agent.agent_id)] = config['resources']
                    self.logger.info(f"Allocated resources for {agent.name}")
                else:
                    self.logger.warning(f"Failed to allocate resources for {agent.name}: {result}")
                    
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent {config['name']}: {e}")
            return None
            
    async def handle_message(self, message: Any):
        """Handle messages with environment awareness"""
        msg_type = message.get('type')
        
        if msg_type == 'task':
            # Check resource availability before accepting
            if self.enable_environment and not await self._check_resources_for_task(message['task']):
                await self._send_response(message, {
                    'status': 'rejected',
                    'reason': 'insufficient_resources'
                })
                return
                
            # Process task
            await self.add_task(message['task'])
            
        elif msg_type == 'environment_update':
            # Handle environment changes
            await self._handle_environment_update(message)
            
        else:
            await super().handle_message(message)
            
    async def handle_task(self, task: Any):
        """Handle task with environment orchestration"""
        self.logger.info(f"Processing task with environment awareness: {task}")
        
        try:
            # Update beliefs with task
            await self.update_beliefs({'current_task': task})
            
            # Decompose task
            subtasks = await self._decompose_task(task)
            
            # Allocate subtasks to team agents
            allocations = await self._allocate_subtasks_with_environment(subtasks)
            
            # Execute with monitoring
            results = await self._execute_with_monitoring(allocations)
            
            # Validate results
            validation = await self._validate_results(results)
            
            # Store results
            await self._store_results(task, results, validation)
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            await self.update_beliefs({'last_error': str(e)})
            
    async def _check_resources_for_task(self, task: Dict[str, Any]) -> bool:
        """Check if resources are available for task"""
        if not self.environment:
            return True
            
        required = task.get('resources', {'cpu': 20, 'memory': 512 * 1024 * 1024})
        usage = self.environment.resource_manager.get_resource_usage()
        
        for resource, amount in required.items():
            if resource in usage:
                if usage[resource]['available'] < amount:
                    return False
                    
        return True
        
    async def _decompose_task(self, task: Any) -> List[Dict[str, Any]]:
        """Decompose task into subtasks"""
        # Use LLM to decompose (simplified here)
        subtasks = [
            {
                'id': f'subtask_{i}',
                'type': 'analyze' if i == 0 else 'implement' if i == 1 else 'validate',
                'description': f'Part {i+1} of task',
                'requirements': ['capability1'],
                'resources': {'cpu': 10, 'memory': 256 * 1024 * 1024}
            }
            for i in range(3)
        ]
        
        return subtasks
        
    async def _allocate_subtasks_with_environment(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Allocate subtasks considering environment constraints"""
        allocations = {}
        
        for subtask in subtasks:
            # Find best agent based on capabilities and visibility
            best_agent = None
            best_score = -1
            
            for name, agent in self.team_agents.items():
                # Check capabilities
                if not any(cap in agent.capabilities for cap in subtask.get('requirements', [])):
                    continue
                    
                # Check visibility if needed
                if self.enable_environment:
                    perception = self.env_adapter.get_agent_perception(agent)
                    visible_agents = len(perception.get('entities', {}))
                    
                    # Prefer agents with better visibility for coordination tasks
                    visibility_score = visible_agents / len(self.team_agents)
                else:
                    visibility_score = 1.0
                    
                # Check resource availability
                if self.enable_environment:
                    can_allocate = await self._try_allocate_resources(
                        agent, subtask.get('resources', {})
                    )
                    if not can_allocate:
                        continue
                        
                # Calculate score
                capability_score = len([c for c in agent.capabilities if c in subtask.get('requirements', [])])
                score = capability_score * visibility_score
                
                if score > best_score:
                    best_score = score
                    best_agent = name
                    
            if best_agent:
                allocations[subtask['id']] = best_agent
                self.logger.info(f"Allocated {subtask['id']} to {best_agent}")
                
        return allocations
        
    async def _try_allocate_resources(self, agent: BaseAgent, resources: Dict[str, float]) -> bool:
        """Try to allocate resources for agent"""
        if not self.environment:
            return True
            
        success = self.environment.resource_manager.request_resources(
            str(agent.agent_id), resources
        )
        
        if not success:
            # Try to free up resources
            await self._optimize_resources()
            # Retry
            success = self.environment.resource_manager.request_resources(
                str(agent.agent_id), resources
            )
            
        return success
        
    async def _optimize_resources(self):
        """Optimize resource usage across agents"""
        if not self.environment:
            return
            
        self.logger.info("Optimizing resource allocations...")
        
        # Find underutilized allocations
        for agent_id, allocation in self.resource_allocations.items():
            # Release and re-request smaller amounts
            self.environment.resource_manager.release_resources(agent_id, allocation)
            
            # Request 80% of original
            reduced = {k: v * 0.8 for k, v in allocation.items()}
            if self.environment.resource_manager.request_resources(agent_id, reduced):
                self.resource_allocations[agent_id] = reduced
                
    async def _execute_with_monitoring(self, allocations: Dict[str, str]) -> Dict[str, Any]:
        """Execute tasks with environment monitoring"""
        results = {}
        
        for subtask_id, agent_name in allocations.items():
            agent = self.team_agents[agent_name]
            
            # Update agent context if environment enabled
            if self.enable_environment and self.env_adapter:
                await self.env_adapter.update_agent_context(agent)
                
            # Send subtask to agent
            await agent.receive_message({
                'type': 'subtask',
                'id': subtask_id,
                'from': str(self.agent_id)
            })
            
            # Monitor execution (simplified)
            await asyncio.sleep(1)
            
            # Collect result
            results[subtask_id] = {
                'agent': agent_name,
                'status': 'completed',
                'artifact': f"{subtask_id}_result.txt"
            }
            
            # Release resources if environment enabled
            if self.enable_environment and str(agent.agent_id) in self.resource_allocations:
                resources = self.resource_allocations[str(agent.agent_id)]
                self.environment.resource_manager.release_resources(
                    str(agent.agent_id), resources
                )
                
        return results
        
    async def _validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate results with constraint checking"""
        validation = {
            'valid': True,
            'issues': []
        }
        
        # Check completeness
        for subtask_id, result in results.items():
            if result['status'] != 'completed':
                validation['valid'] = False
                validation['issues'].append(f"{subtask_id} not completed")
                
        # Check environment constraints if enabled
        if self.enable_environment and self.environment:
            # Check for constraint violations
            for constraint in self.environment.constraint_engine.constraints:
                # Simplified constraint checking
                if constraint.name == "cpu_limit":
                    usage = self.environment.resource_manager.get_resource_usage()
                    if usage['cpu']['utilization'] > 90:
                        validation['issues'].append("CPU usage exceeded safe limits during execution")
                        
        return validation
        
    async def _store_results(self, task: Any, results: Dict[str, Any], validation: Dict[str, Any]):
        """Store task results"""
        # Create result summary
        summary = {
            'task': str(task),
            'timestamp': datetime.utcnow().isoformat(),
            'results': results,
            'validation': validation,
            'environment_state': {}
        }
        
        # Add environment state if enabled
        if self.enable_environment and self.environment:
            summary['environment_state'] = {
                'resources': self.environment.resource_manager.get_resource_usage(),
                'dynamics': self.environment.dynamics.state_variables,
                'events': len(self.environment.event_log)
            }
            
        # Store to workspace
        result_file = self.workspace_path / f"task_result_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        result_file.write_text(json.dumps(summary, indent=2, default=str))
        
        # Update beliefs
        await self.update_beliefs({
            'last_task_result': summary,
            'task_success': validation['valid']
        })
        
    async def _handle_environment_update(self, message: Dict[str, Any]):
        """Handle environment state updates"""
        update_type = message.get('update_type')
        
        if update_type == 'resource_alert':
            # Handle resource shortage
            await self._optimize_resources()
            
        elif update_type == 'constraint_violation':
            # Handle constraint violations
            violations = message.get('violations', [])
            self.logger.warning(f"Constraint violations: {violations}")
            
            # Take corrective action
            for violation in violations:
                if 'cpu' in violation.lower():
                    await self._reduce_cpu_usage()
                elif 'memory' in violation.lower():
                    await self._free_memory()
                    
    async def _reduce_cpu_usage(self):
        """Reduce CPU usage across team"""
        self.logger.info("Reducing CPU usage...")
        
        # Pause non-critical agents
        for name, agent in self.team_agents.items():
            if name not in ['coordinator', 'validator']:
                # Send throttle message
                await agent.receive_message({
                    'type': 'throttle',
                    'level': 0.5
                })
                
    async def _free_memory(self):
        """Free up memory"""
        self.logger.info("Freeing memory...")
        
        # Clear caches and temporary data
        # Would implement actual memory cleanup here
        
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status including environment"""
        status = {
            'agent_id': str(self.agent_id),
            'name': self.name,
            'running': self._running,
            'team_agents': {
                name: {
                    'id': str(agent.agent_id),
                    'running': agent._running,
                    'capabilities': agent.capabilities
                }
                for name, agent in self.team_agents.items()
            },
            'metrics': self.metrics
        }
        
        # Add environment status if enabled
        if self.enable_environment and self.environment:
            status['environment'] = {
                'enabled': True,
                'resources': self.environment.resource_manager.get_resource_usage(),
                'entities': len(self.environment.entities),
                'events': len(self.environment.event_log),
                'dynamics': self.environment.dynamics.state_variables
            }
        else:
            status['environment'] = {'enabled': False}
            
        return status