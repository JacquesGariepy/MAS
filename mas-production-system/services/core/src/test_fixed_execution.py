#!/usr/bin/env python3
"""Test the fixed task execution"""

import asyncio
import sys
import os
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator

async def test_execution():
    print("Testing fixed execution...")
    
    # Create config with desired number of agents
    from swarm_mas_unified import UnifiedSwarmConfig
    config = UnifiedSwarmConfig()
    config.max_agents = 5
    
    coordinator = UnifiedSwarmCoordinator(config=config)
    await coordinator.initialize()
    
    # Test the request
    result = await coordinator.process_request("create python sample lib")
    
    print(f"\nResult: {result.get('status')}")
    print(f"Success rate: {result.get('success_rate', 0):.1f}%")
    
    # Check created files
    workspace = "agent_workspace"
    if os.path.exists(workspace):
        files = []
        for root, dirs, filenames in os.walk(workspace):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                files.append(filepath)
                print(f"✅ Created: {filepath}")
        print(f"\nTotal files created: {len(files)}")
    else:
        print("No workspace directory found")

if __name__ == "__main__":
    asyncio.run(test_execution())