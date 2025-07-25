#!/usr/bin/env python3
"""
Test the fixed swarm with basic operations
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig

async def test_fixed_swarm():
    """Test basic swarm operations"""
    print("\n=== TESTING FIXED SWARM ===\n")
    
    # Create config with reduced memory
    config = UnifiedSwarmConfig(
        name="TestSwarm",
        max_agents=5,
        resource_limits={
            "cpu_cores": 4,
            "memory_mb": 4096,
            "disk_gb": 50
        },
        agent_defaults={
            "memory_mb": 128,
            "cpu_share": 0.2,
            "disk_mb": 50
        }
    )
    
    coordinator = UnifiedSwarmCoordinator(config)
    
    try:
        # Initialize
        print("1. Initializing swarm...")
        await coordinator.initialize()
        print("✓ Swarm initialized successfully!")
        
        # Create a simple agent
        print("\n2. Creating agent...")
        agent = await coordinator.create_agent(
            "test-developer",
            "developer", 
            capabilities=["coding", "testing"]
        )
        print(f"✓ Created agent: {agent['name']}")
        
        # Create a task
        print("\n3. Creating task...")
        task = await coordinator.create_task(
            "Write a hello world function in Python"
        )
        print(f"✓ Created task: {task['id']}")
        
        # Get metrics
        print("\n4. Getting metrics...")
        metrics = await coordinator.get_swarm_metrics()
        print(f"✓ Active agents: {metrics['active_agents']}")
        print(f"✓ Total agents: {metrics['total_agents']}")
        print(f"✓ Swarm state: {coordinator.state.value}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n5. Shutting down...")
        await coordinator.cleanup()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(test_fixed_swarm())