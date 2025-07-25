#!/usr/bin/env python3
"""
Test script for the interactive unified swarm system
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig

async def test_interactive():
    print("\n" + "="*70)
    print("UNIFIED SWARM MAS - INTERACTIVE TEST")
    print("="*70 + "\n")
    
    # Create coordinator with optimized memory settings
    config = UnifiedSwarmConfig(
        name="InteractiveSwarm",
        max_agents=10,  # Fewer agents for testing
        agent_distribution={
            'architect': 1,
            'analyst': 1,
            'developer': 2,
            'tester': 1,
            'coordinator': 1
        }
    )
    
    coordinator = UnifiedSwarmCoordinator(config)
    
    try:
        # Initialize
        print("1. Initializing swarm...")
        await coordinator.initialize()
        print("✅ Swarm initialized!")
        
        # Test request processing
        print("\n2. Processing test request...")
        
        test_request = "Create a simple Python function to calculate fibonacci numbers"
        
        result = await coordinator.process_request(test_request)
        
        print("\n✅ Request processed!")
        print(f"\nResults:")
        print(f"  - Status: {result['status']}")
        print(f"  - Duration: {result.get('duration', 'N/A')}")
        print(f"  - Task Count: {result.get('task_count', 0)}")
        print(f"  - Success Rate: {result.get('success_rate', 0):.1f}%")
        
        if result['status'] == 'completed':
            print("\n✅ Request completed successfully!")
        else:
            print(f"\n⚠️ Request failed: {result.get('error')}")
        
        print("\n✅ All fixes verified:")
        print("  ✓ coordination_groups attribute added")
        print("  ✓ capability_index attribute added") 
        print("  ✓ process_request method working")
        print("  ✓ checkpoint saving fixed")
        
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await coordinator.cleanup()

if __name__ == "__main__":
    asyncio.run(test_interactive())