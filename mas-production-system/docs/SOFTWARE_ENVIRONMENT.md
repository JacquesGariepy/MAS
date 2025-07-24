# Software Environment for Multi-Agent Systems

## Overview

This document describes the implementation of a complete software-based environment for Multi-Agent Systems (MAS) that addresses the missing environmental components identified in the system analysis. All concepts are adapted to the OS/software level without requiring physical agents.

## Key Components

### 1. Spatial Representation

Instead of physical space, we implement software spatial models:

- **Process Tree Topology**: Agents organized by OS process hierarchy
- **Network Graph**: Agents connected through network topology
- **Memory Map**: Virtual memory space representation
- **File System Hierarchy**: Directory/file structure as spatial model
- **Container Mesh**: Docker/Kubernetes pod topology
- **Cloud Regions**: Multi-region cloud infrastructure

```python
class SoftwareLocation:
    host: str                  # Hostname or IP
    process_id: Optional[int]  # Process ID
    container_id: Optional[str] # Container ID
    namespace: str             # Logical namespace
    coordinates: Dict[str, float] # Abstract coordinates
```

### 2. Resource Management

System resources are managed at the OS level:

- **CPU**: Percentage allocation per core
- **Memory**: RAM allocation and limits
- **Disk I/O**: Bandwidth allocation
- **Network**: Bandwidth limits and QoS
- **File Handles**: OS file descriptor limits
- **Threads**: Thread pool management

Resources support atomic allocation and release with agent-specific quotas.

### 3. Environmental Dynamics

The environment changes over time based on:

- **System Load**: CPU and memory pressure affect performance
- **Network Congestion**: Time-based patterns (business hours)
- **Resource Availability**: Dynamic based on system state
- **Event-Driven Changes**: System events trigger state changes

Rules can be added to create complex environmental behaviors:

```python
# Example: High CPU load triggers throttling
EnvironmentRule(
    'high_load_throttle',
    condition=lambda state: state['system_load'] > 80,
    effect=throttle_performance
)
```

### 4. System Constraints

Constraints enforce system-level rules:

- **Security Constraints**: Access control, namespace isolation
- **Performance Constraints**: CPU/memory thresholds
- **Resource Constraints**: Allocation limits
- **Network Constraints**: Bandwidth and connectivity rules
- **Scheduling Constraints**: Process priority and affinity

### 5. Partial Observability

Agents have limited visibility based on their type and location:

- **Full Visibility**: See entire system state
- **Namespace Visibility**: Only same namespace
- **Process Visibility**: Only same process tree
- **Network Visibility**: Only network-reachable entities
- **No Visibility**: Completely isolated

## Integration with Existing MAS

The `EnvironmentAdapter` class bridges the new environment with existing agents:

```python
# Register existing agent
await adapter.register_agent(agent, namespace="services")

# Execute actions through environment
success, result = await adapter.execute_agent_action(agent, {
    'type': 'allocate_resource',
    'resources': {'cpu': 25, 'memory': 100*1024*1024}
})

# Update agent perception
await adapter.update_agent_context(agent)
```

## Usage Example

```python
# Create software environment
env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)

# Add agent with location
location = SoftwareLocation(
    host="server1",
    process_id=12345,
    namespace="app/service",
    coordinates={'x': 10, 'y': 20}
)
env.add_agent("agent1", location)

# Set observability
env.observability.set_visibility("agent1", VisibilityLevel.NETWORK)

# Execute action with constraints
success, result = await env.execute_action("agent1", {
    'type': 'allocate_resource',
    'resources': {'cpu': 50, 'memory': 1024*1024*512}
})

# Get filtered perception
perception = env.perceive("agent1")
```

## Benefits

1. **Realistic Constraints**: Based on actual system resources
2. **Dynamic Environment**: Changes based on system state
3. **Scalable**: Works from single machine to distributed systems
4. **Observable**: Integrates with system monitoring
5. **Flexible**: Multiple topology types for different use cases

## Implementation Details

### Resource Monitoring

The system uses `psutil` to monitor actual system resources:
- Real-time CPU usage
- Memory availability
- Disk I/O statistics
- Network interface status

### Event System

Environmental events are queued and processed asynchronously:
- Performance throttling events
- Resource exhaustion warnings
- Agent communication events
- System state changes

### Constraint Checking

All agent actions are validated against constraints before execution:
1. Check resource availability
2. Verify security permissions
3. Validate performance impact
4. Ensure network policies

### Spatial Distances

Distance in software space is calculated based on:
- Same host: 0-10 units
- Different processes: 10-50 units
- Different hosts: 100-1000 units
- Network hops: Calculated from topology

## Future Enhancements

1. **Kubernetes Integration**: Native K8s resource management
2. **Cloud Provider APIs**: Direct integration with AWS/GCP/Azure
3. **Service Mesh**: Istio/Linkerd topology awareness
4. **Distributed Tracing**: OpenTelemetry integration
5. **Policy Engines**: OPA (Open Policy Agent) integration

## Conclusion

This software environment provides a complete implementation of spatial representation, resource management, environmental dynamics, system constraints, and partial observability - all adapted for software-based multi-agent systems. It bridges the gap between theoretical MAS concepts and practical software systems.