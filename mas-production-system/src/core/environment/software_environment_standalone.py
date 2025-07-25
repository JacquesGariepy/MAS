"""
Standalone Software Environment for MAS (no external dependencies)
This version works without psutil, networkx, or numpy
"""

import time
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import random
import math

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Spatial Representation
# -----------------------------------------------------------------------------

class TopologyType(Enum):
    """Different spatial topologies for software agents"""
    PROCESS_TREE = "process_tree"
    NETWORK_GRAPH = "network_graph"
    MEMORY_MAP = "memory_map"
    FILE_SYSTEM = "file_system"

@dataclass
class SoftwareLocation:
    """Location in software space"""
    host: str
    process_id: Optional[int] = None
    namespace: str = "default"
    coordinates: Dict[str, float] = field(default_factory=dict)
    
    def distance_to(self, other: 'SoftwareLocation') -> float:
        """Calculate distance in software space"""
        if self.host != other.host:
            return 1000.0  # Different hosts
        if self.process_id and other.process_id:
            if self.process_id != other.process_id:
                return 100.0  # Different processes
        if self.namespace != other.namespace:
            # Calculate namespace distance
            ns1_parts = self.namespace.split('/')
            ns2_parts = other.namespace.split('/')
            common_prefix = 0
            for p1, p2 in zip(ns1_parts, ns2_parts):
                if p1 == p2:
                    common_prefix += 1
                else:
                    break
            return 10.0 * (len(ns1_parts) + len(ns2_parts) - 2 * common_prefix)
        
        # Same location or use coordinates
        if self.coordinates and other.coordinates:
            # Euclidean distance
            dist = 0.0
            for key in set(self.coordinates.keys()) | set(other.coordinates.keys()):
                v1 = self.coordinates.get(key, 0)
                v2 = other.coordinates.get(key, 0)
                dist += (v1 - v2) ** 2
            return math.sqrt(dist)
        return 0.0

class SimpleSpatialModel:
    """Simple spatial model without networkx"""
    
    def __init__(self, topology: TopologyType):
        self.topology = topology
        self.entities: Dict[str, SoftwareLocation] = {}
        self.connections: Dict[str, Set[str]] = defaultdict(set)
        
    def add_entity(self, entity_id: str, location: SoftwareLocation):
        """Add entity at location"""
        self.entities[entity_id] = location
        
    def remove_entity(self, entity_id: str):
        """Remove entity"""
        if entity_id in self.entities:
            del self.entities[entity_id]
            # Remove connections
            for neighbors in self.connections.values():
                neighbors.discard(entity_id)
            if entity_id in self.connections:
                del self.connections[entity_id]
                
    def get_neighbors(self, entity_id: str, radius: float) -> List[str]:
        """Get neighbors within radius"""
        if entity_id not in self.entities:
            return []
            
        location = self.entities[entity_id]
        neighbors = []
        
        for other_id, other_loc in self.entities.items():
            if other_id != entity_id:
                dist = location.distance_to(other_loc)
                if dist <= radius:
                    neighbors.append(other_id)
                    
        return neighbors
        
    def add_connection(self, entity1: str, entity2: str, connection_type: str = "default"):
        """Add connection between entities"""
        self.connections[entity1].add(entity2)
        self.connections[entity2].add(entity1)

# -----------------------------------------------------------------------------
# Resource Management
# -----------------------------------------------------------------------------

@dataclass
class SystemResource:
    """System resource representation"""
    total: float
    used: float
    allocated: float
    
    @property
    def available(self) -> float:
        return self.total - self.used
        
    @property
    def utilization(self) -> float:
        return (self.used / self.total * 100) if self.total > 0 else 0

class SimpleResourceManager:
    """Simple resource manager without psutil"""
    
    def __init__(self):
        # Simulated resources
        self.resources = {
            'cpu': SystemResource(total=100.0, used=20.0, allocated=0.0),
            'memory': SystemResource(total=16*1024*1024*1024, used=4*1024*1024*1024, allocated=0.0),
            'disk_io': SystemResource(total=1000.0, used=100.0, allocated=0.0),
            'network': SystemResource(total=1000.0, used=50.0, allocated=0.0)
        }
        self.allocations: Dict[str, Dict[str, float]] = defaultdict(dict)
        
    def request_resources(self, agent_id: str, requested: Dict[str, float]) -> bool:
        """Request resource allocation"""
        # Check availability
        for resource_type, amount in requested.items():
            if resource_type in self.resources:
                resource = self.resources[resource_type]
                if resource.available - resource.allocated < amount:
                    return False
                    
        # Allocate resources
        for resource_type, amount in requested.items():
            if resource_type in self.resources:
                self.resources[resource_type].allocated += amount
                self.allocations[agent_id][resource_type] = amount
                
        return True
        
    def release_resources(self, agent_id: str, resources: Dict[str, float]):
        """Release allocated resources"""
        if agent_id in self.allocations:
            for resource_type, amount in resources.items():
                if resource_type in self.allocations[agent_id]:
                    actual_amount = min(amount, self.allocations[agent_id][resource_type])
                    self.resources[resource_type].allocated -= actual_amount
                    self.allocations[agent_id][resource_type] -= actual_amount
                    if self.allocations[agent_id][resource_type] <= 0:
                        del self.allocations[agent_id][resource_type]
                        
    def get_resource_usage(self) -> Dict[str, Dict[str, float]]:
        """Get current resource usage"""
        usage = {}
        for name, resource in self.resources.items():
            usage[name] = {
                'total': resource.total,
                'used': resource.used + resource.allocated,
                'allocated': resource.allocated,
                'available': resource.available - resource.allocated,
                'utilization': (resource.used + resource.allocated) / resource.total * 100
            }
        return usage

# -----------------------------------------------------------------------------
# Environmental Dynamics
# -----------------------------------------------------------------------------

@dataclass
class EnvironmentEvent:
    """Environmental event"""
    timestamp: float
    event_type: str
    source: Optional[str]
    data: Dict[str, Any]

@dataclass
class EnvironmentRule:
    """Rule for environmental dynamics"""
    name: str
    condition: str  # Will be evaluated as simple expression
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)

class EnvironmentDynamics:
    """Manages environmental changes over time"""
    
    def __init__(self):
        self.state_variables = {
            'system_load': 20.0,
            'memory_pressure': 30.0,
            'network_congestion': 10.0,
            'disk_activity': 15.0,
            'time_of_day': 12.0  # 0-24 hours
        }
        self.rules: List[EnvironmentRule] = []
        self.event_queue = deque()
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """Setup default environmental rules"""
        self.rules.extend([
            EnvironmentRule(
                name="load_fluctuation",
                condition="random() < 0.3",
                action="fluctuate_load",
                parameters={'variance': 5.0}
            ),
            EnvironmentRule(
                name="memory_gc",
                condition="memory_pressure > 70",
                action="trigger_gc",
                parameters={'reduction': 20.0}
            )
        ])
        
    async def update(self, delta_time: float):
        """Update environmental state"""
        # Update time
        self.state_variables['time_of_day'] = (
            self.state_variables['time_of_day'] + delta_time / 3600
        ) % 24
        
        # Natural fluctuations
        for var in ['system_load', 'memory_pressure', 'network_congestion']:
            change = random.gauss(0, 2)  # Random walk
            self.state_variables[var] = max(0, min(100, 
                self.state_variables[var] + change
            ))
            
        # Apply rules
        for rule in self.rules:
            if self._evaluate_condition(rule.condition):
                await self._execute_action(rule.action, rule.parameters)
                
    def _evaluate_condition(self, condition: str) -> bool:
        """Simple condition evaluation"""
        # Very basic - just check for simple comparisons
        if "random()" in condition:
            return eval(condition.replace("random()", str(random.random())))
        for var, value in self.state_variables.items():
            condition = condition.replace(var, str(value))
        try:
            return eval(condition)
        except:
            return False
            
    async def _execute_action(self, action: str, params: Dict[str, Any]):
        """Execute environmental action"""
        if action == "fluctuate_load":
            variance = params.get('variance', 5.0)
            self.state_variables['system_load'] += random.gauss(0, variance)
        elif action == "trigger_gc":
            reduction = params.get('reduction', 20.0)
            self.state_variables['memory_pressure'] = max(0,
                self.state_variables['memory_pressure'] - reduction
            )

# -----------------------------------------------------------------------------
# System Constraints
# -----------------------------------------------------------------------------

class ConstraintType(Enum):
    """Types of system constraints"""
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_POLICY = "security_policy"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    NETWORK_ISOLATION = "network_isolation"

@dataclass
class SystemConstraint:
    """System-level constraint"""
    name: str
    constraint_type: ConstraintType
    condition: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
class ConstraintEngine:
    """Enforces system constraints"""
    
    def __init__(self):
        self.constraints: List[SystemConstraint] = []
        self._setup_default_constraints()
        
    def _setup_default_constraints(self):
        """Setup default system constraints"""
        self.constraints.extend([
            SystemConstraint(
                name="cpu_limit",
                constraint_type=ConstraintType.RESOURCE_LIMIT,
                condition="cpu_request > 90",
                parameters={'max_cpu': 90}
            ),
            SystemConstraint(
                name="memory_limit",
                constraint_type=ConstraintType.RESOURCE_LIMIT,
                condition="memory_request > total_memory * 0.8",
                parameters={'max_memory_ratio': 0.8}
            )
        ])
        
    async def check_constraints(self, action: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if action violates constraints"""
        violations = []
        
        for constraint in self.constraints:
            if constraint.constraint_type == ConstraintType.RESOURCE_LIMIT:
                if action.get('type') == 'allocate_resource':
                    resources = action.get('resources', {})
                    if 'cpu' in resources and resources['cpu'] > 90:
                        violations.append(f"CPU allocation exceeds limit (90%)")
                    if 'memory' in resources:
                        # Simplified check
                        if resources['memory'] > 10 * 1024 * 1024 * 1024:  # 10GB
                            violations.append(f"Memory allocation exceeds limit")
                            
        return len(violations) == 0, violations

# -----------------------------------------------------------------------------
# Partial Observability
# -----------------------------------------------------------------------------

class VisibilityLevel(Enum):
    """Agent visibility levels"""
    FULL = "full"              # See everything
    NAMESPACE = "namespace"    # See same namespace
    PROCESS = "process"        # See same process
    HOST = "host"            # See same host
    NONE = "none"            # See nothing

class ObservabilityFilter:
    """Manages partial observability"""
    
    def __init__(self, spatial_model: SimpleSpatialModel):
        self.spatial_model = spatial_model
        self.visibility_levels: Dict[str, VisibilityLevel] = {}
        
    def set_visibility(self, agent_id: str, level: VisibilityLevel):
        """Set agent visibility level"""
        self.visibility_levels[agent_id] = level
        
    def filter_perception(self, observer_id: str, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Filter perception based on visibility"""
        visibility = self.visibility_levels.get(observer_id, VisibilityLevel.NAMESPACE)
        
        if visibility == VisibilityLevel.FULL:
            return perception
            
        filtered = perception.copy()
        observer_loc = self.spatial_model.entities.get(observer_id)
        
        if not observer_loc:
            return {'entities': {}, 'resources': {}, 'events': []}
            
        # Filter entities
        visible_entities = {}
        for entity_id, entity_data in perception.get('entities', {}).items():
            if entity_id == observer_id:
                visible_entities[entity_id] = entity_data
                continue
                
            other_loc = self.spatial_model.entities.get(entity_id)
            if not other_loc:
                continue
                
            # Check visibility based on level
            if visibility == VisibilityLevel.HOST:
                if observer_loc.host == other_loc.host:
                    visible_entities[entity_id] = entity_data
            elif visibility == VisibilityLevel.PROCESS:
                if (observer_loc.host == other_loc.host and 
                    observer_loc.process_id == other_loc.process_id):
                    visible_entities[entity_id] = entity_data
            elif visibility == VisibilityLevel.NAMESPACE:
                if (observer_loc.host == other_loc.host and
                    observer_loc.namespace.split('/')[0] == other_loc.namespace.split('/')[0]):
                    visible_entities[entity_id] = entity_data
                    
        filtered['entities'] = visible_entities
        return filtered

# -----------------------------------------------------------------------------
# Main Software Environment
# -----------------------------------------------------------------------------

class SoftwareEnvironment:
    """Software-based environment for multi-agent systems"""
    
    def __init__(self, topology: TopologyType = TopologyType.NETWORK_GRAPH):
        self.topology = topology
        self.spatial_model = SimpleSpatialModel(topology)
        self.resource_manager = SimpleResourceManager()
        self.dynamics = EnvironmentDynamics()
        self.constraint_engine = ConstraintEngine()
        self.observability = ObservabilityFilter(self.spatial_model)
        
        # Global state tracking
        self.entities: Dict[str, Any] = {}
        self.event_log: List[EnvironmentEvent] = []
        self.time_step = 0
        
        logger.info(f"Software environment initialized with {topology.value} topology")
        
    def add_agent(self, agent_id: str, location: SoftwareLocation):
        """Add agent to environment"""
        self.spatial_model.add_entity(agent_id, location)
        self.entities[agent_id] = {
            'location': location,
            'resources': {},
            'state': 'active',
            'created_at': time.time()
        }
        
    def remove_agent(self, agent_id: str):
        """Remove agent from environment"""
        if agent_id in self.entities:
            # Release resources
            if agent_id in self.resource_manager.allocations:
                resources = self.resource_manager.allocations[agent_id].copy()
                self.resource_manager.release_resources(agent_id, resources)
                
            # Remove from spatial model
            self.spatial_model.remove_entity(agent_id)
            
            # Remove from entities
            del self.entities[agent_id]
            
    def perceive(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's perception of environment"""
        perception = {
            'entities': self.entities.copy(),
            'resources': self.resource_manager.get_resource_usage(),
            'dynamics': self.dynamics.state_variables.copy(),
            'events': list(self.event_log[-10:])  # Last 10 events
        }
        
        # Apply observability filter
        return self.observability.filter_perception(agent_id, perception)
        
    async def execute_action(self, agent_id: str, action: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Execute agent action in environment"""
        action_type = action.get('type')
        
        # Check constraints
        passed, violations = await self.constraint_engine.check_constraints(
            action, {'agent_id': agent_id, 'environment': self}
        )
        
        if not passed:
            return False, {'error': 'Constraint violations', 'violations': violations}
            
        # Execute action based on type
        if action_type == 'allocate_resource':
            resources = action.get('resources', {})
            success = self.resource_manager.request_resources(agent_id, resources)
            return success, {'allocated': resources if success else {}}
            
        elif action_type == 'release_resource':
            resources = action.get('resources', {})
            self.resource_manager.release_resources(agent_id, resources)
            return True, {'released': resources}
            
        elif action_type == 'move':
            new_location = action.get('location')
            if new_location and agent_id in self.entities:
                self.spatial_model.entities[agent_id] = new_location
                self.entities[agent_id]['location'] = new_location
                return True, {'new_location': new_location}
                
        elif action_type == 'communicate':
            target = action.get('target')
            message = action.get('message')
            
            # Check if target is visible
            perception = self.perceive(agent_id)
            if target not in perception.get('entities', {}):
                return False, {'error': f'Target {target} not visible'}
                
            # Log communication event
            event = EnvironmentEvent(
                timestamp=time.time(),
                event_type='communication',
                source=agent_id,
                data={'target': target, 'message': message}
            )
            self.event_log.append(event)
            return True, {'delivered': True}
            
        else:
            return False, {'error': f'Unknown action type: {action_type}'}
            
    async def update(self, delta_time: float):
        """Update environment state"""
        self.time_step += 1
        
        # Update dynamics
        await self.dynamics.update(delta_time)
        
        # Process environmental events
        while self.dynamics.event_queue:
            event = self.dynamics.event_queue.popleft()
            self.event_log.append(event)
            
        # Simulate resource usage changes
        for resource in self.resource_manager.resources.values():
            # Random fluctuation in base usage
            change = random.gauss(0, 1)
            resource.used = max(0, min(resource.total * 0.8, 
                resource.used + change
            ))
            
    @property
    def global_state(self) -> Dict[str, Any]:
        """Get complete environment state"""
        return {
            'topology': self.topology.value,
            'entities': self.entities,
            'spatial_model': {
                'topology': self.spatial_model.topology.value,
                'entity_count': len(self.spatial_model.entities)
            },
            'resources': self.resource_manager.get_resource_usage(),
            'dynamics': self.dynamics.state_variables,
            'time_step': self.time_step
        }