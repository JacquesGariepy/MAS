"""
Software-based Environment for Multi-Agent Systems
Implements spatial representation, resource management, dynamics, constraints, and partial observability
All concepts adapted to OS/software level without physical agents
"""

import asyncio
import os
import psutil
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict
import networkx as nx
import logging

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Spatial Representation for Software Environment
# -----------------------------------------------------------------------------

class TopologyType(Enum):
    """Different spatial topologies for software agents"""
    PROCESS_TREE = "process_tree"      # OS process hierarchy
    NETWORK_GRAPH = "network_graph"    # Network topology
    MEMORY_MAP = "memory_map"          # Virtual memory space
    FILE_SYSTEM = "file_system"        # File system hierarchy
    CONTAINER_MESH = "container_mesh"  # Docker/K8s topology
    CLOUD_REGIONS = "cloud_regions"    # Cloud infrastructure

@dataclass
class SoftwareLocation:
    """Location in software space"""
    host: str                  # Hostname or IP
    process_id: Optional[int]  # Process ID
    container_id: Optional[str] # Container ID
    namespace: str             # Logical namespace
    coordinates: Dict[str, float] = field(default_factory=dict)  # Abstract coordinates
    
    def distance_to(self, other: 'SoftwareLocation') -> float:
        """Calculate distance in software space"""
        if self.host != other.host:
            return 1000.0  # Different hosts are far
        if self.process_id and other.process_id:
            # Same host, different processes
            return 10.0 if self.process_id != other.process_id else 0.0
        # Use abstract coordinates if available
        if self.coordinates and other.coordinates:
            return np.linalg.norm(
                np.array(list(self.coordinates.values())) - 
                np.array(list(other.coordinates.values()))
            )
        return 50.0  # Default distance

class SoftwareSpatialModel:
    """Spatial model for software environment"""
    
    def __init__(self, topology: TopologyType = TopologyType.NETWORK_GRAPH):
        self.topology = topology
        self.graph = nx.DiGraph()  # Directed graph for relationships
        self.entities: Dict[str, SoftwareLocation] = {}
        self.regions: Dict[str, Set[str]] = defaultdict(set)
        
    def add_entity(self, entity_id: str, location: SoftwareLocation):
        """Add entity to spatial model"""
        self.entities[entity_id] = location
        self.graph.add_node(entity_id, location=location)
        self.regions[location.namespace].add(entity_id)
        
    def move_entity(self, entity_id: str, new_location: SoftwareLocation):
        """Move entity in software space (e.g., process migration)"""
        if entity_id in self.entities:
            old_location = self.entities[entity_id]
            self.regions[old_location.namespace].discard(entity_id)
            self.entities[entity_id] = new_location
            self.regions[new_location.namespace].add(entity_id)
            self.graph.nodes[entity_id]['location'] = new_location
            
    def get_neighbors(self, entity_id: str, radius: float) -> List[str]:
        """Get entities within radius in software space"""
        if entity_id not in self.entities:
            return []
            
        location = self.entities[entity_id]
        neighbors = []
        
        for other_id, other_location in self.entities.items():
            if other_id != entity_id:
                distance = location.distance_to(other_location)
                if distance <= radius:
                    neighbors.append(other_id)
                    
        return neighbors
        
    def add_connection(self, from_id: str, to_id: str, connection_type: str = "network"):
        """Add connection between entities (network, IPC, etc.)"""
        self.graph.add_edge(from_id, to_id, type=connection_type)

# -----------------------------------------------------------------------------
# Resource Management at OS Level
# -----------------------------------------------------------------------------

@dataclass
class SystemResource:
    """System resource representation"""
    resource_type: str  # cpu, memory, disk, network, file_handle, thread
    total: float
    available: float
    allocated: Dict[str, float] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def allocate(self, agent_id: str, amount: float) -> bool:
        """Allocate resource to agent"""
        if amount <= self.available:
            self.allocated[agent_id] = self.allocated.get(agent_id, 0) + amount
            self.available -= amount
            return True
        return False
        
    def release(self, agent_id: str, amount: float):
        """Release resource from agent"""
        if agent_id in self.allocated:
            release_amount = min(amount, self.allocated[agent_id])
            self.allocated[agent_id] -= release_amount
            self.available += release_amount
            if self.allocated[agent_id] <= 0:
                del self.allocated[agent_id]

class ResourceManager:
    """Manages system resources for agents"""
    
    def __init__(self):
        self.resources: Dict[str, SystemResource] = {}
        self._initialize_system_resources()
        
    def _initialize_system_resources(self):
        """Initialize with actual system resources"""
        # CPU resources
        cpu_count = psutil.cpu_count()
        self.resources['cpu'] = SystemResource(
            resource_type='cpu',
            total=cpu_count * 100,  # Percentage per core
            available=cpu_count * 100,
            properties={'cores': cpu_count, 'frequency': psutil.cpu_freq()}
        )
        
        # Memory resources
        memory = psutil.virtual_memory()
        self.resources['memory'] = SystemResource(
            resource_type='memory',
            total=memory.total,
            available=memory.available,
            properties={'swap': psutil.swap_memory()}
        )
        
        # Disk I/O bandwidth (simplified)
        self.resources['disk_io'] = SystemResource(
            resource_type='disk_io',
            total=1000.0,  # MB/s theoretical max
            available=1000.0,
            properties={'partitions': psutil.disk_partitions()}
        )
        
        # Network bandwidth (simplified)
        self.resources['network'] = SystemResource(
            resource_type='network',
            total=1000.0,  # Mbps theoretical max
            available=1000.0,
            properties={'interfaces': psutil.net_if_addrs()}
        )
        
        # File handles
        self.resources['file_handles'] = SystemResource(
            resource_type='file_handles',
            total=65536,  # Typical Linux limit
            available=65536
        )
        
        # Thread pool
        self.resources['threads'] = SystemResource(
            resource_type='threads',
            total=1000,  # Max threads
            available=1000
        )
        
    def request_resources(self, agent_id: str, requirements: Dict[str, float]) -> bool:
        """Request multiple resources atomically"""
        # Check availability first
        for resource_type, amount in requirements.items():
            if resource_type not in self.resources:
                return False
            if self.resources[resource_type].available < amount:
                return False
                
        # Allocate all resources
        for resource_type, amount in requirements.items():
            self.resources[resource_type].allocate(agent_id, amount)
            
        return True
        
    def release_resources(self, agent_id: str, resources: Dict[str, float]):
        """Release resources back to pool"""
        for resource_type, amount in resources.items():
            if resource_type in self.resources:
                self.resources[resource_type].release(agent_id, amount)
                
    def get_resource_usage(self) -> Dict[str, Dict[str, float]]:
        """Get current resource usage statistics"""
        usage = {}
        for name, resource in self.resources.items():
            usage[name] = {
                'total': resource.total,
                'available': resource.available,
                'used': resource.total - resource.available,
                'utilization': (resource.total - resource.available) / resource.total * 100
            }
        return usage

# -----------------------------------------------------------------------------
# Environmental Dynamics
# -----------------------------------------------------------------------------

class EnvironmentEvent:
    """Events that occur in the software environment"""
    def __init__(self, event_type: str, source: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.source = source
        self.data = data
        self.timestamp = time.time()

class EnvironmentDynamics:
    """Manages dynamic changes in software environment"""
    
    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.rules: List[EnvironmentRule] = []
        self.state_variables: Dict[str, Any] = {}
        self._initialize_dynamics()
        
    def _initialize_dynamics(self):
        """Initialize environmental dynamics"""
        # System load dynamics
        self.state_variables['system_load'] = psutil.cpu_percent(interval=0.1)
        self.state_variables['memory_pressure'] = psutil.virtual_memory().percent
        self.state_variables['network_congestion'] = 0.0
        self.state_variables['disk_queue_depth'] = 0
        
        # Time-based dynamics
        self.state_variables['time_of_day'] = time.localtime().tm_hour
        self.state_variables['day_of_week'] = time.localtime().tm_wday
        
    async def update(self, delta_time: float):
        """Update environmental state"""
        # Update system metrics
        self.state_variables['system_load'] = psutil.cpu_percent(interval=0.1)
        self.state_variables['memory_pressure'] = psutil.virtual_memory().percent
        
        # Simulate network congestion based on time
        hour = time.localtime().tm_hour
        if 9 <= hour <= 17:  # Business hours
            self.state_variables['network_congestion'] = min(80, 
                self.state_variables['network_congestion'] + delta_time * 0.1)
        else:
            self.state_variables['network_congestion'] = max(10,
                self.state_variables['network_congestion'] - delta_time * 0.2)
                
        # Apply rules
        await self._apply_rules()
        
    async def _apply_rules(self):
        """Apply environmental rules"""
        for rule in self.rules:
            if await rule.check_condition(self.state_variables):
                await rule.apply_effect(self)
                
    async def add_event(self, event: EnvironmentEvent):
        """Add event to environment"""
        await self.event_queue.put(event)
        
    def add_rule(self, rule: 'EnvironmentRule'):
        """Add dynamic rule"""
        self.rules.append(rule)

# -----------------------------------------------------------------------------
# System Constraints and Rules
# -----------------------------------------------------------------------------

class ConstraintType(Enum):
    """Types of system constraints"""
    SECURITY = "security"          # Access control
    PERFORMANCE = "performance"    # Performance limits
    RESOURCE = "resource"          # Resource limits
    NETWORK = "network"           # Network policies
    SCHEDULING = "scheduling"      # Scheduling constraints

class SystemConstraint:
    """System-level constraint"""
    def __init__(self, constraint_type: ConstraintType, condition: callable, 
                 message: str = "Constraint violation"):
        self.constraint_type = constraint_type
        self.condition = condition
        self.message = message
        
    def check(self, action: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if action violates constraint"""
        if not self.condition(action, context):
            return False, self.message
        return True, ""

class EnvironmentRule:
    """Environmental rule with condition and effect"""
    def __init__(self, name: str, condition: callable, effect: callable):
        self.name = name
        self.condition = condition
        self.effect = effect
        
    async def check_condition(self, state: Dict[str, Any]) -> bool:
        """Check if rule condition is met"""
        return self.condition(state)
        
    async def apply_effect(self, dynamics: EnvironmentDynamics):
        """Apply rule effect"""
        await self.effect(dynamics)

class ConstraintEngine:
    """Manages and enforces system constraints"""
    
    def __init__(self):
        self.constraints: List[SystemConstraint] = []
        self._initialize_default_constraints()
        
    def _initialize_default_constraints(self):
        """Initialize default system constraints"""
        # CPU usage constraint
        self.constraints.append(SystemConstraint(
            ConstraintType.RESOURCE,
            lambda action, ctx: ctx.get('cpu_usage', 0) + action.get('cpu_required', 0) <= 90,
            "CPU usage would exceed 90% threshold"
        ))
        
        # Memory constraint
        self.constraints.append(SystemConstraint(
            ConstraintType.RESOURCE,
            lambda action, ctx: ctx.get('memory_available', 0) >= action.get('memory_required', 0),
            "Insufficient memory available"
        ))
        
        # Network bandwidth constraint
        self.constraints.append(SystemConstraint(
            ConstraintType.NETWORK,
            lambda action, ctx: action.get('bandwidth_required', 0) <= ctx.get('bandwidth_available', 100),
            "Network bandwidth limit exceeded"
        ))
        
        # Security constraint - process isolation
        self.constraints.append(SystemConstraint(
            ConstraintType.SECURITY,
            lambda action, ctx: action.get('target_namespace') in ctx.get('allowed_namespaces', []),
            "Access denied to target namespace"
        ))
        
    def check_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if action violates any constraints"""
        violations = []
        for constraint in self.constraints:
            valid, message = constraint.check(action, context)
            if not valid:
                violations.append(f"{constraint.constraint_type.value}: {message}")
        return len(violations) == 0, violations

# -----------------------------------------------------------------------------
# Partial Observability Implementation
# -----------------------------------------------------------------------------

class VisibilityLevel(Enum):
    """Visibility levels for partial observability"""
    FULL = "full"              # Complete visibility
    NAMESPACE = "namespace"    # Same namespace only
    PROCESS = "process"        # Same process tree
    NETWORK = "network"        # Network-reachable only
    NONE = "none"             # No visibility

class ObservabilityFilter:
    """Implements partial observability for agents"""
    
    def __init__(self, spatial_model: SoftwareSpatialModel):
        self.spatial_model = spatial_model
        self.visibility_rules: Dict[str, VisibilityLevel] = {}
        self.sensor_ranges: Dict[str, float] = {}
        
    def set_visibility(self, agent_id: str, level: VisibilityLevel, range: float = 100.0):
        """Set visibility level for agent"""
        self.visibility_rules[agent_id] = level
        self.sensor_ranges[agent_id] = range
        
    def filter_perception(self, observer_id: str, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Filter environment state based on observability rules"""
        if observer_id not in self.visibility_rules:
            return {}  # No visibility by default
            
        visibility = self.visibility_rules[observer_id]
        filtered_state = {'timestamp': environment_state.get('timestamp', time.time())}
        
        # Get observer location
        observer_location = self.spatial_model.entities.get(observer_id)
        if not observer_location:
            return filtered_state
            
        # Filter entities based on visibility level
        visible_entities = self._get_visible_entities(observer_id, observer_location, visibility)
        
        # Filter environment state
        if 'entities' in environment_state:
            filtered_state['entities'] = {
                eid: data for eid, data in environment_state['entities'].items()
                if eid in visible_entities
            }
            
        # Filter resources based on visibility
        if 'resources' in environment_state:
            if visibility in [VisibilityLevel.FULL, VisibilityLevel.NAMESPACE]:
                filtered_state['resources'] = environment_state['resources']
            else:
                # Limited resource visibility
                filtered_state['resources'] = {
                    'cpu': {'utilization': psutil.cpu_percent()},
                    'memory': {'percent': psutil.virtual_memory().percent}
                }
                
        # Filter events based on visibility
        if 'events' in environment_state:
            filtered_state['events'] = [
                event for event in environment_state['events']
                if self._can_observe_event(observer_id, event, visibility)
            ]
            
        return filtered_state
        
    def _get_visible_entities(self, observer_id: str, observer_location: SoftwareLocation, 
                            visibility: VisibilityLevel) -> Set[str]:
        """Get set of visible entities based on visibility level"""
        visible = {observer_id}  # Always see self
        
        if visibility == VisibilityLevel.FULL:
            # See all entities
            visible.update(self.spatial_model.entities.keys())
            
        elif visibility == VisibilityLevel.NAMESPACE:
            # See entities in same namespace
            visible.update(self.spatial_model.regions[observer_location.namespace])
            
        elif visibility == VisibilityLevel.PROCESS:
            # See entities in same process tree
            for eid, location in self.spatial_model.entities.items():
                if (location.host == observer_location.host and 
                    location.process_id == observer_location.process_id):
                    visible.add(eid)
                    
        elif visibility == VisibilityLevel.NETWORK:
            # See network-connected entities
            if observer_id in self.spatial_model.graph:
                # Direct connections
                visible.update(self.spatial_model.graph.neighbors(observer_id))
                # Within sensor range
                neighbors = self.spatial_model.get_neighbors(
                    observer_id, self.sensor_ranges.get(observer_id, 100.0)
                )
                visible.update(neighbors)
                
        return visible
        
    def _can_observe_event(self, observer_id: str, event: EnvironmentEvent, 
                          visibility: VisibilityLevel) -> bool:
        """Check if observer can see event"""
        if visibility == VisibilityLevel.FULL:
            return True
            
        # Check if event source is visible
        visible_entities = self._get_visible_entities(
            observer_id, 
            self.spatial_model.entities[observer_id],
            visibility
        )
        return event.source in visible_entities

# -----------------------------------------------------------------------------
# Complete Software Environment
# -----------------------------------------------------------------------------

class SoftwareEnvironment:
    """Complete software-based environment for MAS"""
    
    def __init__(self, topology: TopologyType = TopologyType.NETWORK_GRAPH):
        # Core components
        self.spatial_model = SoftwareSpatialModel(topology)
        self.resource_manager = ResourceManager()
        self.dynamics = EnvironmentDynamics()
        self.constraint_engine = ConstraintEngine()
        self.observability = ObservabilityFilter(self.spatial_model)
        
        # Environment state
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.global_state: Dict[str, Any] = {}
        self.event_log: List[EnvironmentEvent] = []
        
        # Initialize environment
        self._initialize_environment()
        
    def _initialize_environment(self):
        """Initialize environment with default state"""
        self.global_state = {
            'timestamp': time.time(),
            'entities': self.entities,
            'resources': self.resource_manager.get_resource_usage(),
            'dynamics': self.dynamics.state_variables,
            'events': []
        }
        
        # Add default rules
        self._add_default_rules()
        
    def _add_default_rules(self):
        """Add default environmental rules"""
        # High load throttling rule
        async def high_load_effect(dynamics):
            event = EnvironmentEvent(
                'performance_throttle',
                'system',
                {'reason': 'high_cpu_load', 'throttle_factor': 0.5}
            )
            await dynamics.add_event(event)
            
        self.dynamics.add_rule(EnvironmentRule(
            'high_load_throttle',
            lambda state: state.get('system_load', 0) > 80,
            high_load_effect
        ))
        
        # Memory pressure rule
        async def memory_pressure_effect(dynamics):
            event = EnvironmentEvent(
                'memory_pressure',
                'system',
                {'action': 'gc_triggered', 'pressure': dynamics.state_variables['memory_pressure']}
            )
            await dynamics.add_event(event)
            
        self.dynamics.add_rule(EnvironmentRule(
            'memory_gc_trigger',
            lambda state: state.get('memory_pressure', 0) > 85,
            memory_pressure_effect
        ))
        
    def add_agent(self, agent_id: str, location: SoftwareLocation, 
                  properties: Dict[str, Any] = None):
        """Add agent to environment"""
        self.spatial_model.add_entity(agent_id, location)
        self.entities[agent_id] = {
            'id': agent_id,
            'location': location,
            'properties': properties or {},
            'resources': {},
            'created_at': time.time()
        }
        
        # Set default observability
        self.observability.set_visibility(agent_id, VisibilityLevel.NAMESPACE)
        
    def remove_agent(self, agent_id: str):
        """Remove agent from environment"""
        if agent_id in self.entities:
            # Release all resources
            if 'resources' in self.entities[agent_id]:
                self.resource_manager.release_resources(
                    agent_id, self.entities[agent_id]['resources']
                )
            del self.entities[agent_id]
            # Remove from spatial model
            if agent_id in self.spatial_model.entities:
                del self.spatial_model.entities[agent_id]
                
    async def execute_action(self, agent_id: str, action: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute agent action with constraint checking"""
        # Build context for constraint checking
        context = {
            'agent_id': agent_id,
            'cpu_usage': psutil.cpu_percent(),
            'memory_available': psutil.virtual_memory().available,
            'bandwidth_available': 100 - self.dynamics.state_variables.get('network_congestion', 0),
            'allowed_namespaces': [self.entities[agent_id]['location'].namespace]
        }
        
        # Check constraints
        valid, violations = self.constraint_engine.check_action(action, context)
        if not valid:
            return False, {'error': 'Constraint violations', 'violations': violations}
            
        # Execute action based on type
        action_type = action.get('type')
        
        if action_type == 'move':
            # Process migration
            new_location = action['target_location']
            self.spatial_model.move_entity(agent_id, new_location)
            self.entities[agent_id]['location'] = new_location
            
        elif action_type == 'allocate_resource':
            # Resource allocation
            resources = action['resources']
            success = self.resource_manager.request_resources(agent_id, resources)
            if success:
                self.entities[agent_id]['resources'].update(resources)
            return success, {'allocated': resources if success else {}}
            
        elif action_type == 'communicate':
            # Inter-agent communication
            target_id = action['target']
            message = action['message']
            # Check if target is visible
            visible = target_id in self.observability._get_visible_entities(
                agent_id,
                self.entities[agent_id]['location'],
                self.observability.visibility_rules.get(agent_id, VisibilityLevel.NONE)
            )
            if visible:
                event = EnvironmentEvent('message', agent_id, {
                    'target': target_id,
                    'message': message
                })
                await self.dynamics.add_event(event)
                return True, {'sent': True}
            return False, {'error': 'Target not visible'}
            
        elif action_type == 'spawn_process':
            # Create new process/agent
            child_location = SoftwareLocation(
                host=self.entities[agent_id]['location'].host,
                process_id=os.getpid(),  # Would be new PID in real implementation
                container_id=self.entities[agent_id]['location'].container_id,
                namespace=f"{self.entities[agent_id]['location'].namespace}/child"
            )
            child_id = action['child_id']
            self.add_agent(child_id, child_location, {'parent': agent_id})
            self.spatial_model.add_connection(agent_id, child_id, 'parent-child')
            return True, {'child_id': child_id}
            
        return True, {'executed': action_type}
        
    def perceive(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's perception of environment"""
        # Update global state
        self.global_state.update({
            'timestamp': time.time(),
            'entities': self.entities,
            'resources': self.resource_manager.get_resource_usage(),
            'dynamics': self.dynamics.state_variables,
            'events': self.event_log[-100:]  # Last 100 events
        })
        
        # Apply observability filter
        return self.observability.filter_perception(agent_id, self.global_state)
        
    async def update(self, delta_time: float):
        """Update environment state"""
        # Update dynamics
        await self.dynamics.update(delta_time)
        
        # Process events
        while not self.dynamics.event_queue.empty():
            event = await self.dynamics.event_queue.get()
            self.event_log.append(event)
            
            # Event may trigger constraint changes
            if event.event_type == 'performance_throttle':
                # Temporarily tighten resource constraints
                pass
                
        # Update resource availability based on system state
        self.resource_manager.resources['cpu'].available = (
            self.resource_manager.resources['cpu'].total * 
            (100 - psutil.cpu_percent()) / 100
        )
        
        self.resource_manager.resources['memory'].available = (
            psutil.virtual_memory().available
        )

# -----------------------------------------------------------------------------
# Example Usage and Testing
# -----------------------------------------------------------------------------

async def test_software_environment():
    """Test the software environment implementation"""
    # Create environment
    env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
    
    # Add agents in different locations
    agent1_location = SoftwareLocation(
        host="localhost",
        process_id=os.getpid(),
        container_id=None,
        namespace="app/service1",
        coordinates={'x': 0, 'y': 0}
    )
    
    agent2_location = SoftwareLocation(
        host="localhost", 
        process_id=os.getpid() + 1,
        container_id=None,
        namespace="app/service2",
        coordinates={'x': 10, 'y': 10}
    )
    
    env.add_agent("agent1", agent1_location)
    env.add_agent("agent2", agent2_location)
    
    # Set different visibility levels
    env.observability.set_visibility("agent1", VisibilityLevel.FULL)
    env.observability.set_visibility("agent2", VisibilityLevel.NAMESPACE)
    
    # Test resource allocation
    success, result = await env.execute_action("agent1", {
        'type': 'allocate_resource',
        'resources': {'cpu': 25, 'memory': 1024*1024*100}  # 100MB
    })
    print(f"Resource allocation: {success}, {result}")
    
    # Test perception with partial observability
    agent1_view = env.perceive("agent1")
    agent2_view = env.perceive("agent2")
    
    print(f"Agent1 sees {len(agent1_view.get('entities', {}))} entities")
    print(f"Agent2 sees {len(agent2_view.get('entities', {}))} entities")
    
    # Test communication
    success, result = await env.execute_action("agent1", {
        'type': 'communicate',
        'target': 'agent2',
        'message': {'content': 'Hello from agent1'}
    })
    print(f"Communication: {success}, {result}")
    
    # Update environment
    await env.update(1.0)
    
    # Check dynamic state
    print(f"System load: {env.dynamics.state_variables['system_load']:.1f}%")
    print(f"Network congestion: {env.dynamics.state_variables['network_congestion']:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_software_environment())