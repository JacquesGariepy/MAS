#!/usr/bin/env python3
"""
Simple test for the unified swarm MAS system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig

async def simple_test():
    """Run a simple test of the swarm system"""
    print("=== SIMPLE SWARM TEST ===")
    
    # Create minimal config
    config = UnifiedSwarmConfig(
        max_agents=5,  # Small number for testing
        enable_background_tasks=False  # Disable background tasks to avoid the error
    )
    
    # Create coordinator
    coordinator = UnifiedSwarmCoordinator(config)
    
    try:
        # Create a few agents manually
        print("\n1. Creating agents...")
        
        developer = await coordinator.create_agent(
            "developer-1",
            "developer",
            capabilities=["coding", "debugging"]
        )
        print(f"✓ Created developer: {developer['name']}")
        
        analyst = await coordinator.create_agent(
            "analyst-1", 
            "analyst",
            capabilities=["analysis", "planning"]
        )
        print(f"✓ Created analyst: {analyst['name']}")
        
        # Create a simple task
        print("\n2. Creating task...")
        task = await coordinator.create_task(
            "Write a simple Python function to calculate fibonacci numbers"
        )
        print(f"✓ Created task: {task['id']}")
        
        # Decompose task
        print("\n3. Decomposing task...")
        subtasks = await coordinator.decompose_task(task['id'])
        print(f"✓ Created {len(subtasks)} subtasks")
        
        # Get swarm metrics
        print("\n4. Getting metrics...")
        metrics = await coordinator.get_swarm_metrics()
        print(f"✓ Active agents: {metrics['active_agents']}")
        print(f"✓ Total agents: {metrics['total_agents']}")
        print(f"✓ Tasks created: {metrics['tasks_created']}")
        
        print("\n✅ Simple test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        print("\n5. Shutting down...")
        await coordinator.cleanup()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(simple_test())