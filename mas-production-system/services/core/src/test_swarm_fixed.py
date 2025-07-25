#!/usr/bin/env python3
"""Test script to verify the swarm_mas_unified fix"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarm_mas_unified import UnifiedSwarmCoordinator, SwarmConfig, CoordinationStrategy

async def test_swarm_initialization():
    """Test that swarm initializes without coordination_strategy error"""
    try:
        print("Testing swarm initialization...")
        
        # Create config
        config = SwarmConfig(
            min_agents=3,
            max_agents=5,
            enable_monitoring=True,
            coordination_strategy=CoordinationStrategy.HIERARCHICAL
        )
        
        # Create coordinator
        coordinator = UnifiedSwarmCoordinator(config)
        
        # Initialize
        await coordinator.initialize()
        
        print("✅ Swarm initialized successfully!")
        print(f"Coordination strategy type: {type(coordinator.coordination_strategy)}")
        print(f"Coordination strategy value: {coordinator.coordination_strategy}")
        
        # Test the logging that was failing
        await coordinator._log_initialization_summary()
        print("✅ Initialization summary logged successfully!")
        
        # Cleanup
        await coordinator.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_swarm_initialization())
    sys.exit(0 if success else 1)