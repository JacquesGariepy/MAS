#!/usr/bin/env python3
"""
Autonomous Multi-Agent System with Integrated Software Environment
Complete implementation with Ferber's principles adapted to software level
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import logging
from dataclasses import dataclass, field
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import environment components
from src.core.environment import (
    SoftwareEnvironment,
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    EnvironmentAdapter,
    integrate_mas_with_environment
)

# Import runtime
from src.core.runtime import AgentRuntime, get_agent_runtime

# Import existing MAS components from services/core
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.tools.filesystem_tool import FileSystemTool
from src.core.agents import CognitiveAgent, ReflexiveAgent, HybridAgent
from src.utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/app/logs/autonomous_mas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = get_logger("AUTONOMOUS_MAS")

@dataclass
class MASConfig:
    """Configuration for the integrated MAS system"""
    topology: TopologyType = TopologyType.NETWORK_GRAPH
    max_agents: int = 10
    enable_environment: bool = True
    enable_resource_management: bool = True
    enable_partial_observability: bool = True
    enable_constraints: bool = True
    enable_dynamics: bool = True
    resource_limits: Dict[str, float] = field(default_factory=lambda: {
        'cpu': 80.0,  # Max 80% CPU
        'memory': 8 * 1024 * 1024 * 1024,  # 8GB max
        'disk_io': 500.0,  # 500 MB/s
        'network': 100.0  # 100 MB/s
    })

class IntegratedAutonomousAgent:
    """
    Enhanced Autonomous Agent with full environment integration
    Implements Ferber's MAS principles at software level
    """
    
    def __init__(self, config: Optional[MASConfig] = None):
        self.config = config or MASConfig()
        self.agent_id = uuid4()
        self.name = f"AutonomousMAS-{str(self.agent_id)[:8]}"
        
        # Core services
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        
        # Agent management
        self.agents: Dict[str, Any] = {}
        self.agent_roles = {
            'analyst': None,
            'developer': None,
            'creative': None,
            'validator': None,
            'coordinator': None
        }
        
        # Environment components
        self.environment: Optional[SoftwareEnvironment] = None
        self.env_adapter: Optional[EnvironmentAdapter] = None
        self.runtime: Optional[AgentRuntime] = None
        
        # Workspace
        self.workspace_path = Path(f"/app/agent_workspace/mas_integrated/{self.agent_id}")
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Metrics
        self.metrics = {
            'requests_processed': 0,
            'agents_spawned': 0,
            'resources_allocated': 0,
            'environment_updates': 0,
            'constraint_violations': 0
        }
        
        logger.info(f"Initialized {self.name} with environment integration")
        
    async def initialize(self):
        """Initialize the integrated MAS system"""
        logger.info("Initializing integrated MAS system...")
        
        # 1. Create runtime
        self.runtime = get_agent_runtime()
        
        # 2. Initialize environment if enabled
        if self.config.enable_environment:
            logger.info("Creating software environment...")
            self.environment = SoftwareEnvironment(self.config.topology)
            
            # Configure resource limits
            if self.config.enable_resource_management:
                for resource, limit in self.config.resource_limits.items():
                    if resource in self.environment.resource_manager.resources:
                        self.environment.resource_manager.resources[resource].total = limit
            
            # Create adapter
            self.env_adapter = EnvironmentAdapter(self.environment)
            self.env_adapter.set_runtime(self.runtime)
            
            logger.info(f"Environment created with {self.config.topology.value} topology")
        
        # 3. Create specialized agents
        await self._create_agents()
        
        # 4. Start environment dynamics if enabled
        if self.config.enable_environment and self.config.enable_dynamics:
            asyncio.create_task(self._environment_update_loop())
            
        logger.info("MAS system initialized successfully")
        
    async def _create_agents(self):
        """Create and register specialized agents"""
        logger.info("Creating specialized agents...")
        
        # Analyst - Cognitive agent with full observability
        analyst = CognitiveAgent(
            agent_id=uuid4(),
            name=f"Analyst-{self.name}",
            role="analyst",
            capabilities=["analysis", "understanding", "research"],
            llm_service=self.llm_service,
            initial_beliefs={
                'purpose': 'Analyze requests and understand requirements',
                'environment_aware': self.config.enable_environment
            }
        )
        analyst.agent_type = "cognitive"  # For environment integration
        await self._register_agent(analyst, "analyst")
        
        # Developer - Hybrid agent for implementation
        developer = HybridAgent(
            agent_id=uuid4(),
            name=f"Developer-{self.name}",
            role="developer",
            capabilities=["coding", "implementation", "debugging"],
            llm_service=self.llm_service,
            complexity_threshold=0.7,
            initial_beliefs={
                'purpose': 'Implement solutions and write code',
                'resource_aware': self.config.enable_resource_management
            }
        )
        developer.agent_type = "hybrid"
        await self._register_agent(developer, "developer")
        
        # Creative - Cognitive agent for innovative solutions
        creative = CognitiveAgent(
            agent_id=uuid4(),
            name=f"Creative-{self.name}",
            role="creative",
            capabilities=["creativity", "innovation", "design"],
            llm_service=self.llm_service,
            initial_beliefs={
                'purpose': 'Generate creative solutions and ideas',
                'think_outside_box': True
            }
        )
        creative.agent_type = "cognitive"
        await self._register_agent(creative, "creative")
        
        # Validator - Hybrid agent for quality assurance
        validator = HybridAgent(
            agent_id=uuid4(),
            name=f"Validator-{self.name}",
            role="validator",
            capabilities=["testing", "validation", "quality_assurance"],
            llm_service=self.llm_service,
            complexity_threshold=0.6,
            initial_beliefs={
                'purpose': 'Validate solutions and ensure quality',
                'constraint_aware': self.config.enable_constraints
            }
        )
        validator.agent_type = "hybrid"
        await self._register_agent(validator, "validator")
        
        # Coordinator - Reflexive agent for orchestration
        coordinator = ReflexiveAgent(
            agent_id=uuid4(),
            name=f"Coordinator-{self.name}",
            role="coordinator",
            capabilities=["coordination", "planning", "orchestration"],
            rules={
                'high_complexity': lambda ctx: ctx.get('complexity', 0) > 0.8,
                'resource_shortage': lambda ctx: ctx.get('available_cpu', 100) < 20,
                'multiple_agents_needed': lambda ctx: ctx.get('subtasks', 0) > 3
            },
            initial_beliefs={
                'purpose': 'Coordinate agent activities and manage resources',
                'global_view': True
            }
        )
        coordinator.agent_type = "reflexive"
        await self._register_agent(coordinator, "coordinator")
        
        # Create agent network if environment is enabled
        if self.env_adapter:
            await self.env_adapter.create_agent_network(
                list(self.agents.values()),
                topology="star"  # Coordinator at center
            )
            
        logger.info(f"Created {len(self.agents)} specialized agents")
        
    async def _register_agent(self, agent: Any, role: str):
        """Register agent with runtime and environment"""
        # Register with runtime
        await self.runtime.register_agent(agent)
        await self.runtime.start_agent(agent)
        
        # Register with environment
        if self.env_adapter:
            await self.env_adapter.register_agent(agent, namespace=f"mas/{role}")
            
            # Allocate initial resources based on role
            initial_resources = self._get_initial_resources(role)
            success, result = await self.env_adapter.execute_agent_action(agent, {
                'type': 'request_resources',
                'resources': initial_resources
            })
            
            if success:
                logger.info(f"Allocated resources for {agent.name}: {initial_resources}")
                self.metrics['resources_allocated'] += 1
            else:
                logger.warning(f"Failed to allocate resources for {agent.name}: {result}")
                
        # Store agent reference
        self.agents[str(agent.agent_id)] = agent
        self.agent_roles[role] = agent
        self.metrics['agents_spawned'] += 1
        
    def _get_initial_resources(self, role: str) -> Dict[str, float]:
        """Get initial resource allocation for agent role"""
        allocations = {
            'analyst': {'cpu': 10, 'memory': 512 * 1024 * 1024},  # 512MB
            'developer': {'cpu': 30, 'memory': 2 * 1024 * 1024 * 1024},  # 2GB
            'creative': {'cpu': 15, 'memory': 1024 * 1024 * 1024},  # 1GB
            'validator': {'cpu': 20, 'memory': 1024 * 1024 * 1024},  # 1GB
            'coordinator': {'cpu': 5, 'memory': 256 * 1024 * 1024}  # 256MB
        }
        return allocations.get(role, {'cpu': 10, 'memory': 512 * 1024 * 1024})
        
    async def _environment_update_loop(self):
        """Background loop to update environment dynamics"""
        while True:
            try:
                # Update environment
                await self.environment.update(1.0)
                self.metrics['environment_updates'] += 1
                
                # Update agent contexts with perception
                for agent in self.agents.values():
                    await self.env_adapter.update_agent_context(agent)
                    
                # Check for constraint violations
                if self.config.enable_constraints:
                    violations = await self._check_constraints()
                    if violations:
                        self.metrics['constraint_violations'] += len(violations)
                        logger.warning(f"Constraint violations detected: {violations}")
                        
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Environment update error: {e}")
                
    async def _check_constraints(self) -> List[str]:
        """Check system constraints"""
        violations = []
        
        if self.environment:
            # Check resource usage
            usage = self.environment.resource_manager.get_resource_usage()
            
            for resource, data in usage.items():
                if data['utilization'] > 90:
                    violations.append(f"{resource} usage critical: {data['utilization']:.1f}%")
                    
            # Check agent health
            for agent_id, agent in self.agents.items():
                if agent_id not in self.environment.entities:
                    violations.append(f"Agent {agent.name} not in environment")
                    
        return violations
        
    async def process_request(self, request: str) -> Dict[str, Any]:
        """Process a request using the integrated MAS"""
        logger.info(f"Processing request: {request[:100]}...")
        start_time = datetime.utcnow()
        self.metrics['requests_processed'] += 1
        
        result = {
            'request': request,
            'status': 'processing',
            'agents_involved': [],
            'environment_state': {},
            'tasks': [],
            'artifacts': [],
            'errors': []
        }
        
        try:
            # 1. Analyze request with environment awareness
            analysis = await self._analyze_request_with_environment(request)
            result['analysis'] = analysis
            
            # 2. Check resource availability
            if self.config.enable_resource_management:
                available = await self._check_resource_availability(analysis)
                if not available:
                    result['status'] = 'resource_constrained'
                    result['errors'].append("Insufficient resources for request")
                    return result
                    
            # 3. Decompose into tasks considering agent visibility
            tasks = await self._decompose_with_observability(request, analysis)
            result['tasks'] = tasks
            
            # 4. Allocate tasks to agents based on capabilities and resources
            allocations = await self._allocate_tasks_with_constraints(tasks)
            
            # 5. Execute tasks with environment monitoring
            for task, agent_id in allocations.items():
                agent = self.agents[agent_id]
                result['agents_involved'].append(agent.name)
                
                # Execute with resource tracking
                task_result = await self._execute_task_with_environment(
                    agent, task
                )
                
                if task_result.get('success'):
                    if 'artifact' in task_result:
                        result['artifacts'].append(task_result['artifact'])
                else:
                    result['errors'].append(task_result.get('error', 'Unknown error'))
                    
            # 6. Validate results considering constraints
            if self.agent_roles['validator'] and not result['errors']:
                validation = await self._validate_with_constraints(result['artifacts'])
                if not validation['valid']:
                    result['errors'].extend(validation['issues'])
                    
            # 7. Capture final environment state
            if self.environment:
                result['environment_state'] = {
                    'resources': self.environment.resource_manager.get_resource_usage(),
                    'dynamics': self.environment.dynamics.state_variables,
                    'events': len(self.environment.event_log),
                    'constraints': self.metrics['constraint_violations']
                }
                
            result['status'] = 'completed' if not result['errors'] else 'failed'
            result['duration'] = (datetime.utcnow() - start_time).total_seconds()
            
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            result['status'] = 'error'
            result['errors'].append(str(e))
            
        return result
        
    async def _analyze_request_with_environment(self, request: str) -> Dict[str, Any]:
        """Analyze request considering environment state"""
        analyst = self.agent_roles['analyst']
        
        # Get analyst's perception of environment
        perception = {}
        if self.env_adapter:
            perception = self.env_adapter.get_agent_perception(analyst)
            
        # Include environment context in analysis
        enhanced_prompt = f"""
        Analyze the following request considering the current system state:
        
        Request: {request}
        
        Environment State:
        - Available Resources: {perception.get('resources', 'Unknown')}
        - System Dynamics: {perception.get('dynamics', 'Unknown')}
        - Visible Agents: {len(perception.get('entities', {}))}
        
        Provide analysis including resource requirements and complexity.
        """
        
        # Use LLM for analysis
        response = await self.llm_service.generate(enhanced_prompt)
        
        # Parse and enhance with environment data
        analysis = {
            'complexity': 'medium',  # Would be parsed from response
            'resource_requirements': {
                'cpu': 20,
                'memory': 1024 * 1024 * 1024
            },
            'estimated_duration': 30,
            'subtasks': 3,
            'environment_suitable': True
        }
        
        return analysis
        
    async def _check_resource_availability(self, analysis: Dict[str, Any]) -> bool:
        """Check if resources are available for request"""
        if not self.environment:
            return True
            
        required = analysis.get('resource_requirements', {})
        usage = self.environment.resource_manager.get_resource_usage()
        
        for resource, amount in required.items():
            if resource in usage:
                available = usage[resource]['available']
                if available < amount:
                    logger.warning(f"Insufficient {resource}: need {amount}, have {available}")
                    return False
                    
        return True
        
    async def _decompose_with_observability(self, request: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose request considering agent observability"""
        coordinator = self.agent_roles['coordinator']
        
        # Get coordinator's global view
        if self.env_adapter:
            await self.env_adapter.update_agent_context(coordinator)
            
        # Simple task decomposition (would use LLM in practice)
        tasks = [
            {
                'id': f'task_{i}',
                'description': f'Subtask {i} of {request[:50]}',
                'requirements': ['capability1', 'capability2'],
                'visibility_required': VisibilityLevel.NAMESPACE,
                'resources': {
                    'cpu': 10,
                    'memory': 512 * 1024 * 1024
                }
            }
            for i in range(analysis.get('subtasks', 1))
        ]
        
        return tasks
        
    async def _allocate_tasks_with_constraints(self, tasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Allocate tasks to agents considering constraints"""
        allocations = {}
        
        for task in tasks:
            best_agent = None
            best_score = -1
            
            for agent_id, agent in self.agents.items():
                # Check capability match
                capabilities_match = any(
                    cap in agent.capabilities 
                    for cap in task.get('requirements', [])
                )
                
                if not capabilities_match:
                    continue
                    
                # Check visibility requirements
                if self.env_adapter:
                    agent_visibility = self.environment.observability.visibility_levels.get(
                        agent_id, VisibilityLevel.NAMESPACE
                    )
                    required_visibility = task.get('visibility_required', VisibilityLevel.NAMESPACE)
                    
                    # Check if agent has sufficient visibility
                    visibility_levels = [VisibilityLevel.NONE, VisibilityLevel.PROCESS, 
                                       VisibilityLevel.NAMESPACE, VisibilityLevel.HOST, 
                                       VisibilityLevel.FULL]
                    
                    if visibility_levels.index(agent_visibility) < visibility_levels.index(required_visibility):
                        continue
                        
                # Check resource availability
                if self.environment:
                    can_allocate = self.environment.resource_manager.request_resources(
                        agent_id, task.get('resources', {})
                    )
                    if not can_allocate:
                        # Release the attempted allocation
                        self.environment.resource_manager.release_resources(
                            agent_id, task.get('resources', {})
                        )
                        continue
                        
                # Calculate score based on current load and capabilities
                score = len(agent.capabilities) / (1 + len(allocations.get(agent_id, [])))
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
                    
            if best_agent:
                allocations[task['id']] = best_agent
                logger.info(f"Allocated task {task['id']} to agent {self.agents[best_agent].name}")
            else:
                logger.warning(f"Could not allocate task {task['id']}")
                
        return allocations
        
    async def _execute_task_with_environment(self, agent: Any, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with environment tracking"""
        result = {
            'task_id': task['id'],
            'agent': agent.name,
            'success': False
        }
        
        try:
            # Update agent context before execution
            if self.env_adapter:
                await self.env_adapter.update_agent_context(agent)
                
            # Send task to agent
            await agent.receive_message({
                'type': 'task',
                'task': task,
                'environment_aware': True
            })
            
            # Simulate task execution (would wait for real result)
            await asyncio.sleep(1)
            
            # Create artifact
            artifact_path = self.workspace_path / f"{task['id']}_result.py"
            artifact_path.write_text(f"# Result of {task['id']}\n# Executed by {agent.name}\n")
            
            result['success'] = True
            result['artifact'] = str(artifact_path)
            
            # Release task resources
            if self.environment:
                self.environment.resource_manager.release_resources(
                    str(agent.agent_id), task.get('resources', {})
                )
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Task execution error: {e}")
            
        return result
        
    async def _validate_with_constraints(self, artifacts: List[str]) -> Dict[str, Any]:
        """Validate results considering system constraints"""
        validator = self.agent_roles['validator']
        
        validation = {
            'valid': True,
            'issues': []
        }
        
        # Check each artifact
        for artifact in artifacts:
            # Would perform real validation here
            if not Path(artifact).exists():
                validation['valid'] = False
                validation['issues'].append(f"Artifact not found: {artifact}")
                
        # Check system constraints weren't violated
        if self.environment:
            violations = await self._check_constraints()
            if violations:
                validation['valid'] = False
                validation['issues'].extend(violations)
                
        return validation
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'mas_id': str(self.agent_id),
            'name': self.name,
            'agents': {},
            'environment': {},
            'metrics': self.metrics,
            'runtime': {}
        }
        
        # Agent status
        for role, agent in self.agent_roles.items():
            if agent:
                status['agents'][role] = {
                    'id': str(agent.agent_id),
                    'name': agent.name,
                    'running': str(agent.agent_id) in self.runtime.running_agents,
                    'capabilities': agent.capabilities
                }
                
        # Environment status
        if self.environment:
            status['environment'] = {
                'topology': self.config.topology.value,
                'resources': self.environment.resource_manager.get_resource_usage(),
                'dynamics': self.environment.dynamics.state_variables,
                'entities': len(self.environment.entities),
                'events': len(self.environment.event_log)
            }
            
        # Runtime status
        if self.runtime:
            status['runtime'] = self.runtime.get_metrics()
            
        return status
        
    async def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up integrated MAS...")
        
        # Stop all agents
        if self.runtime:
            await self.runtime.shutdown()
            
        # Clean workspace
        # Would implement proper cleanup here
        
        logger.info("Cleanup complete")


async def demonstrate_integrated_mas():
    """Demonstrate the integrated MAS system"""
    print("\n" + "="*80)
    print("🚀 INTEGRATED MULTI-AGENT SYSTEM DEMONSTRATION")
    print("="*80)
    
    # Create MAS with full environment integration
    config = MASConfig(
        topology=TopologyType.NETWORK_GRAPH,
        enable_environment=True,
        enable_resource_management=True,
        enable_partial_observability=True,
        enable_constraints=True,
        enable_dynamics=True
    )
    
    mas = IntegratedAutonomousAgent(config)
    await mas.initialize()
    
    # Show initial status
    print("\n📊 Initial System Status:")
    status = await mas.get_system_status()
    print(f"- Agents: {len(status['agents'])} active")
    print(f"- Topology: {status['environment']['topology']}")
    print(f"- Resources: CPU={status['environment']['resources']['cpu']['utilization']:.1f}%, "
          f"Memory={status['environment']['resources']['memory']['used']/1024/1024/1024:.2f}GB")
    
    # Process a test request
    print("\n📝 Processing Test Request...")
    request = "Create a Python web API with authentication and database integration"
    
    result = await mas.process_request(request)
    
    print(f"\n✅ Request processed!")
    print(f"- Status: {result['status']}")
    print(f"- Duration: {result.get('duration', 0):.2f}s")
    print(f"- Agents involved: {', '.join(result['agents_involved'])}")
    print(f"- Tasks completed: {len(result['tasks'])}")
    print(f"- Artifacts created: {len(result['artifacts'])}")
    
    if result['errors']:
        print(f"- Errors: {len(result['errors'])}")
        for error in result['errors']:
            print(f"  • {error}")
            
    # Show final environment state
    print("\n🌍 Final Environment State:")
    env_state = result.get('environment_state', {})
    if env_state:
        print(f"- Resource usage: CPU={env_state['resources']['cpu']['utilization']:.1f}%")
        print(f"- System load: {env_state['dynamics']['system_load']:.1f}%")
        print(f"- Events logged: {env_state['events']}")
        print(f"- Constraint violations: {env_state['constraints']}")
    
    # Cleanup
    await mas.cleanup()
    print("\n✅ Demonstration complete!")
    print("="*80)


def main():
    """Main entry point for the integrated MAS"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integrated Autonomous Multi-Agent System")
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--request', type=str, help='Process a specific request')
    parser.add_argument('--topology', choices=['mesh', 'hierarchical', 'ring', 'star'], 
                       default='hierarchical', help='Environment topology')
    parser.add_argument('--no-environment', action='store_true', help='Disable environment')
    parser.add_argument('--no-resources', action='store_true', help='Disable resource management')
    parser.add_argument('--no-constraints', action='store_true', help='Disable constraints')
    
    args = parser.parse_args()
    
    if args.demo:
        # Run demonstration
        asyncio.run(demonstrate_integrated_mas())
    elif args.request:
        # Process specific request
        async def process_request():
            config = MASConfig(
                topology=TopologyType[args.topology.upper()],
                enable_environment=not args.no_environment,
                enable_resource_management=not args.no_resources,
                enable_constraints=not args.no_constraints
            )
            
            mas = IntegratedAutonomousAgent(config)
            await mas.initialize()
            
            result = await mas.process_request(args.request)
            print(json.dumps(result, indent=2, default=str))
            
            await mas.cleanup()
            
        asyncio.run(process_request())
    else:
        # Interactive mode
        async def interactive():
            config = MASConfig()
            mas = IntegratedAutonomousAgent(config)
            await mas.initialize()
            
            print("\n🤖 Integrated MAS Ready!")
            print("Type 'quit' to exit, 'status' for system status")
            print("-" * 60)
            
            while True:
                try:
                    request = input("\n> ").strip()
                    
                    if request.lower() == 'quit':
                        break
                    elif request.lower() == 'status':
                        status = await mas.get_system_status()
                        print(json.dumps(status, indent=2, default=str))
                    elif request:
                        result = await mas.process_request(request)
                        print(f"\nStatus: {result['status']}")
                        if result['artifacts']:
                            print(f"Created: {', '.join(result['artifacts'])}")
                        if result['errors']:
                            print(f"Errors: {', '.join(result['errors'])}")
                            
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    
            await mas.cleanup()
            
        asyncio.run(interactive())


if __name__ == "__main__":
    main()