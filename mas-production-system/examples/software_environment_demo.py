#!/usr/bin/env python3
"""
Demo showing integration of the new Software Environment with existing MAS
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services', 'core'))

from src.agents.agent_factory import AgentFactory
from src.agents.agent_runtime import get_agent_runtime
from src.core.environment import (
    SoftwareEnvironment, 
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    integrate_mas_with_environment
)
from src.services.llm_service import LLMService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demonstrate_software_environment():
    """Demonstrate the new software environment capabilities"""
    
    print("\n" + "="*80)
    print("🌐 SOFTWARE ENVIRONMENT DEMONSTRATION")
    print("="*80)
    
    # 1. Create agent runtime
    runtime = get_agent_runtime()
    factory = AgentFactory()
    llm_service = LLMService()
    
    # 2. Create different types of agents
    print("\n📦 Creating agents...")
    
    # Cognitive agent with full visibility
    cognitive_agent = factory.create_agent(
        agent_type="cognitive",
        name="SystemMonitor",
        role="monitor",
        capabilities=["system_analysis", "resource_monitoring"],
        llm_service=llm_service,
        initial_beliefs={
            "purpose": "Monitor system resources and agent activities",
            "visibility": "full"
        }
    )
    await runtime.register_agent(cognitive_agent)
    await runtime.start_agent(cognitive_agent)
    print(f"✓ Created {cognitive_agent.name} (Cognitive - Full Visibility)")
    
    # Hybrid agent with network visibility
    hybrid_agent = factory.create_agent(
        agent_type="hybrid",
        name="TaskExecutor",
        role="executor",
        capabilities=["task_execution", "resource_allocation"],
        llm_service=llm_service,
        initial_beliefs={
            "purpose": "Execute tasks with resource constraints",
            "visibility": "network"
        }
    )
    await runtime.register_agent(hybrid_agent)
    await runtime.start_agent(hybrid_agent)
    print(f"✓ Created {hybrid_agent.name} (Hybrid - Network Visibility)")
    
    # Reflexive agent with namespace visibility
    reflexive_agent = factory.create_agent(
        agent_type="reflexive",
        name="DataProcessor",
        role="processor",
        capabilities=["data_processing", "response"],
        llm_service=llm_service,
        reactive_rules={
            "high_load": lambda ctx: ctx.get("cpu_usage", 0) > 80,
            "low_memory": lambda ctx: ctx.get("memory_available", 0) < 100*1024*1024
        },
        initial_beliefs={
            "purpose": "Process data with reactive responses",
            "visibility": "namespace"
        }
    )
    await runtime.register_agent(reflexive_agent)
    await runtime.start_agent(reflexive_agent)
    print(f"✓ Created {reflexive_agent.name} (Reflexive - Namespace Visibility)")
    
    # 3. Integrate with software environment
    print("\n🔧 Integrating with software environment...")
    adapter = await integrate_mas_with_environment(runtime)
    env = adapter.environment
    
    # 4. Demonstrate spatial representation
    print("\n📍 Spatial Representation:")
    for agent_id, location in env.spatial_model.entities.items():
        agent = runtime.get_agent(agent_id)
        if agent:
            print(f"  - {agent.name}: {location.namespace} @ {location.host}")
    
    # 5. Demonstrate resource allocation
    print("\n💾 Resource Allocation:")
    
    # Cognitive agent requests moderate resources
    success1, result1 = await adapter.execute_agent_action(cognitive_agent, {
        'type': 'request_resources',
        'resources': {'cpu': 20, 'memory': 512*1024*1024}  # 512MB
    })
    print(f"  - {cognitive_agent.name}: CPU=20%, Memory=512MB - {'✓' if success1 else '✗'}")
    
    # Hybrid agent requests more resources
    success2, result2 = await adapter.execute_agent_action(hybrid_agent, {
        'type': 'request_resources', 
        'resources': {'cpu': 40, 'memory': 1024*1024*1024}  # 1GB
    })
    print(f"  - {hybrid_agent.name}: CPU=40%, Memory=1GB - {'✓' if success2 else '✗'}")
    
    # Reflexive agent requests minimal resources
    success3, result3 = await adapter.execute_agent_action(reflexive_agent, {
        'type': 'request_resources',
        'resources': {'cpu': 10, 'memory': 256*1024*1024}  # 256MB
    })
    print(f"  - {reflexive_agent.name}: CPU=10%, Memory=256MB - {'✓' if success3 else '✗'}")
    
    # Show resource usage
    usage = env.resource_manager.get_resource_usage()
    print(f"\n  System Resource Usage:")
    print(f"    - CPU: {usage['cpu']['utilization']:.1f}% used")
    print(f"    - Memory: {usage['memory']['used']/1024/1024/1024:.2f}GB used")
    
    # 6. Demonstrate partial observability
    print("\n👁️ Partial Observability Test:")
    
    # Each agent perceives the environment differently
    cognitive_perception = env.perceive(str(cognitive_agent.agent_id))
    hybrid_perception = env.perceive(str(hybrid_agent.agent_id))
    reflexive_perception = env.perceive(str(reflexive_agent.agent_id))
    
    print(f"  - {cognitive_agent.name} sees: {len(cognitive_perception.get('entities', {}))} entities (Full)")
    print(f"  - {hybrid_agent.name} sees: {len(hybrid_perception.get('entities', {}))} entities (Network)")
    print(f"  - {reflexive_agent.name} sees: {len(reflexive_perception.get('entities', {}))} entities (Namespace)")
    
    # 7. Demonstrate communication with visibility constraints
    print("\n📡 Communication Test:")
    
    # Cognitive agent can communicate with everyone
    comm1, _ = await adapter.execute_agent_action(cognitive_agent, {
        'type': 'send_message',
        'target': reflexive_agent.agent_id,
        'message': {'content': 'Status request', 'type': 'query'}
    })
    print(f"  - {cognitive_agent.name} → {reflexive_agent.name}: {'✓' if comm1 else '✗'}")
    
    # Reflexive agent may not see hybrid agent (different namespace)
    comm2, _ = await adapter.execute_agent_action(reflexive_agent, {
        'type': 'send_message',
        'target': hybrid_agent.agent_id,
        'message': {'content': 'Hello', 'type': 'inform'}
    })
    print(f"  - {reflexive_agent.name} → {hybrid_agent.name}: {'✓' if comm2 else '✗'} (limited visibility)")
    
    # 8. Demonstrate environmental dynamics
    print("\n🌊 Environmental Dynamics:")
    
    # Let environment run for a few seconds
    for i in range(5):
        await env.update(1.0)
        await asyncio.sleep(1)
        
        # Update agent contexts
        for agent in runtime.list_agents():
            await adapter.update_agent_context(agent)
    
    # Check dynamic state
    dynamics = env.dynamics.state_variables
    print(f"  - System Load: {dynamics['system_load']:.1f}%")
    print(f"  - Memory Pressure: {dynamics['memory_pressure']:.1f}%")
    print(f"  - Network Congestion: {dynamics['network_congestion']:.1f}%")
    
    # 9. Test system constraints
    print("\n🚫 System Constraints Test:")
    
    # Try to allocate excessive resources (should fail)
    excessive, result = await adapter.execute_agent_action(hybrid_agent, {
        'type': 'request_resources',
        'resources': {'cpu': 80, 'memory': 100*1024*1024*1024}  # 100GB
    })
    print(f"  - Excessive allocation attempt: {'✓' if excessive else '✗ (Blocked by constraints)'}")
    if not excessive and 'violations' in result:
        for violation in result['violations']:
            print(f"    - {violation}")
    
    # 10. Show final state
    print("\n📊 Final Environment State:")
    state = env.global_state
    print(f"  - Active Agents: {len(state['entities'])}")
    print(f"  - Events Logged: {len(env.event_log)}")
    print(f"  - Active Rules: {len(env.dynamics.rules)}")
    print(f"  - Active Constraints: {len(env.constraint_engine.constraints)}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await runtime.shutdown()
    
    print("\n✅ Demo completed successfully!")
    print("="*80)

async def main():
    """Main entry point"""
    try:
        await demonstrate_software_environment()
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    print("\n🚀 Starting Software Environment Demo...")
    print("This demonstrates the new environment features:")
    print("  - Spatial representation (process/network topology)")
    print("  - Resource management (CPU, memory allocation)")
    print("  - Environmental dynamics (load, congestion)")
    print("  - System constraints (resource limits)")
    print("  - Partial observability (visibility levels)")
    
    asyncio.run(main())