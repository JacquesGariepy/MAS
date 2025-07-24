"""
Environment module for Multi-Agent System
Provides software-based spatial representation, resource management, and dynamics
"""

from .software_environment import (
    SoftwareEnvironment,
    SoftwareLocation,
    SoftwareSpatialModel,
    TopologyType,
    SystemResource,
    ResourceManager,
    EnvironmentDynamics,
    EnvironmentEvent,
    EnvironmentRule,
    ConstraintType,
    SystemConstraint,
    ConstraintEngine,
    VisibilityLevel,
    ObservabilityFilter
)

try:
    from .integration import (
        EnvironmentAdapter,
        EnhancedAgentContext,
        integrate_mas_with_environment,
        enhance_agent_perception
    )
except ImportError:
    # Fallback to standalone version if dependencies are missing
    from .integration_standalone import (
        StandaloneEnvironmentAdapter as EnvironmentAdapter,
        integrate_mas_with_environment,
        enhance_agent_perception
    )
    # Create dummy for compatibility
    class EnhancedAgentContext:
        pass

__all__ = [
    # Main environment
    'SoftwareEnvironment',
    
    # Spatial representation
    'SoftwareLocation',
    'SoftwareSpatialModel', 
    'TopologyType',
    
    # Resource management
    'SystemResource',
    'ResourceManager',
    
    # Dynamics
    'EnvironmentDynamics',
    'EnvironmentEvent',
    'EnvironmentRule',
    
    # Constraints
    'ConstraintType',
    'SystemConstraint',
    'ConstraintEngine',
    
    # Observability
    'VisibilityLevel',
    'ObservabilityFilter',
    
    # Integration
    'EnvironmentAdapter',
    'EnhancedAgentContext',
    'integrate_mas_with_environment',
    'enhance_agent_perception'
]