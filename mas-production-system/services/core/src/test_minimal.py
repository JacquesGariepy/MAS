#!/usr/bin/env python3
"""
Minimal test for unified swarm
"""

import sys
sys.path.insert(0, '/app/src')

print("Importing modules...")
try:
    from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig
    print("✓ Import successful")
    
    print("\nCreating config...")
    config = UnifiedSwarmConfig()
    print(f"✓ Config created: {config.name}")
    
    print("\nCreating coordinator...")
    coordinator = UnifiedSwarmCoordinator(config)
    print(f"✓ Coordinator created: {coordinator.name}")
    
    print("\nChecking services...")
    print(f"✓ LLM Service: {coordinator.llm_service}")
    print(f"✓ Tool Service: {coordinator.tool_service}")
    print(f"✓ Embedding Service: {coordinator.embedding_service}")
    
    print("\nAvailable tools:")
    for tool_name, tool in coordinator.tools.items():
        print(f"  - {tool_name}: {tool}")
    
    print("\n✅ Basic initialization successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()