#!/usr/bin/env python3
"""
Simplified demo of the Software Environment without agent runtime dependencies
"""

import asyncio
import sys
import os
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.environment.software_environment_standalone import (
    SoftwareEnvironment, 
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    SystemConstraint,
    ConstraintType
)

async def simple_demo():
    """Simple demonstration of software environment features"""
    
    print("\n" + "="*80)
    print("🌐 SIMPLE SOFTWARE ENVIRONMENT DEMONSTRATION")
    print("="*80)
    
    # 1. Create environment
    print("\n📦 Creating software environment...")
    env = SoftwareEnvironment(TopologyType.NETWORK_GRAPH)
    print(f"✓ Created environment with {env.spatial_model.topology.value} topology")
    
    # 2. Add entities (simulating agents)
    print("\n📍 Adding entities to spatial model...")
    
    # Add three entities at different locations
    locations = {
        "agent1": SoftwareLocation(
            host="server1",
            process_id=1234,
            namespace="app/services/auth",
            coordinates={'x': 0, 'y': 0}
        ),
        "agent2": SoftwareLocation(
            host="server1", 
            process_id=1234,
            namespace="app/services/api",
            coordinates={'x': 10, 'y': 10}
        ),
        "agent3": SoftwareLocation(
            host="server2",
            process_id=5678,
            namespace="app/services/db",
            coordinates={'x': 100, 'y': 100}
        )
    }
    
    for agent_id, location in locations.items():
        env.add_agent(agent_id, location)
        print(f"✓ Added {agent_id} at {location.namespace} on {location.host}")
    
    # 3. Test spatial relationships
    print("\n🗺️ Testing spatial relationships...")
    
    # Find neighbors
    neighbors = env.spatial_model.get_neighbors("agent1", radius=50.0)
    print(f"  - Neighbors of agent1 (radius 50): {neighbors}")
    
    # Check distances
    dist12 = locations["agent1"].distance_to(locations["agent2"])
    dist13 = locations["agent1"].distance_to(locations["agent3"])
    print(f"  - Distance agent1 → agent2: {dist12:.2f}")
    print(f"  - Distance agent1 → agent3: {dist13:.2f}")
    
    # 4. Resource management
    print("\n💾 Testing resource allocation...")
    
    # Request resources for each agent
    allocations = [
        ("agent1", {'cpu': 25, 'memory': 512*1024*1024}),  # 512MB
        ("agent2", {'cpu': 35, 'memory': 1024*1024*1024}), # 1GB
        ("agent3", {'cpu': 20, 'memory': 256*1024*1024})   # 256MB
    ]
    
    for agent_id, resources in allocations:
        success = env.resource_manager.request_resources(agent_id, resources)
        status = "✓" if success else "✗"
        print(f"  {status} {agent_id}: CPU={resources['cpu']}%, Memory={resources['memory']/1024/1024:.0f}MB")
    
    # Show resource usage
    usage = env.resource_manager.get_resource_usage()
    print(f"\n  System Usage:")
    print(f"    - CPU: {usage['cpu']['utilization']:.1f}% ({usage['cpu']['used']:.0f}% allocated)")
    print(f"    - Memory: {usage['memory']['used']/1024/1024/1024:.2f}GB allocated")
    
    # 5. Partial observability
    print("\n👁️ Testing partial observability...")
    
    # Set different visibility levels
    env.observability.set_visibility("agent1", VisibilityLevel.FULL)
    env.observability.set_visibility("agent2", VisibilityLevel.NAMESPACE)
    env.observability.set_visibility("agent3", VisibilityLevel.PROCESS)
    
    # Test what each agent can see
    for agent_id in ["agent1", "agent2", "agent3"]:
        perception = env.perceive(agent_id)
        visible_entities = perception.get('entities', {})
        visibility = env.observability.visibility_levels.get(agent_id, VisibilityLevel.NAMESPACE)
        print(f"  - {agent_id} ({visibility.value}): sees {len(visible_entities)} entities")
    
    # 6. Environmental dynamics
    print("\n🌊 Testing environmental dynamics...")
    
    # Update environment several times
    for i in range(3):
        await env.update(1.0)
        state = env.dynamics.state_variables
        print(f"  - Update {i+1}: Load={state['system_load']:.1f}%, Memory={state['memory_pressure']:.1f}%")
        await asyncio.sleep(0.5)
    
    # 7. System constraints
    print("\n🚫 Testing system constraints...")
    
    # Try to allocate excessive resources
    excessive_request = {'cpu': 85, 'memory': 100*1024*1024*1024}  # 85% CPU, 100GB
    success, result = await env.execute_action("agent2", {
        'type': 'allocate_resource',
        'resources': excessive_request
    })
    
    if not success:
        print(f"  ✓ Excessive allocation blocked:")
        for violation in result.get('violations', []):
            print(f"    - {violation}")
    else:
        print(f"  ✗ Warning: Excessive allocation was allowed!")
    
    # 8. Communication with visibility
    print("\n📡 Testing communication with visibility constraints...")
    
    # agent3 tries to communicate with agent1 (different hosts)
    comm_result, _ = await env.execute_action("agent3", {
        'type': 'communicate',
        'target': 'agent1',
        'message': {'content': 'Hello from agent3'}
    })
    
    # agent2 tries to communicate with agent1 (same namespace prefix)
    comm_result2, _ = await env.execute_action("agent2", {
        'type': 'communicate', 
        'target': 'agent1',
        'message': {'content': 'Hello from agent2'}
    })
    
    print(f"  - agent3 → agent1 (different hosts): {'✓' if comm_result else '✗'}")
    print(f"  - agent2 → agent1 (same namespace): {'✓' if comm_result2 else '✗'}")
    
    # 9. Show final state
    print("\n📊 Final Environment State:")
    state = env.global_state
    print(f"  - Active Entities: {len(state['entities'])}")
    print(f"  - Topology: {state['spatial_model']['topology']}")
    print(f"  - Events Logged: {len(env.event_log)}")
    print(f"  - Active Constraints: {len(env.constraint_engine.constraints)}")
    
    print("\n✅ Simple demo completed!")
    print("="*80)

if __name__ == "__main__":
    print("\n🚀 Starting Simple Software Environment Demo...")
    print("This demonstrates core environment features without agent dependencies")
    
    asyncio.run(simple_demo())