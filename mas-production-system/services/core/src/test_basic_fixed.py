#!/usr/bin/env python3
"""
Basic test of fixed swarm
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig
from datetime import datetime
import json

async def test_basic():
    print("\n=== BASIC SWARM TEST ===\n")
    
    # Use default config
    coordinator = UnifiedSwarmCoordinator()
    
    try:
        # Test JSON serialization
        print("1. Testing JSON serialization...")
        test_data = {
            "timestamp": datetime.now(),
            "name": "test",
            "value": 123
        }
        from swarm_mas_unified import safe_json_dumps
        json_str = safe_json_dumps(test_data)
        print(f"✓ JSON serialization works: {json_str[:50]}...")
        
        # Test VisibilityLevel comparison
        print("\n2. Testing VisibilityLevel comparison...")
        from swarm_mas_unified import VisibilityLevel
        assert VisibilityLevel.FULL >= VisibilityLevel.PARTIAL
        assert VisibilityLevel.PARTIAL > VisibilityLevel.NONE
        print("✓ VisibilityLevel comparisons work")
        
        # Test checkpoint methods exist
        print("\n3. Testing checkpoint methods...")
        assert hasattr(coordinator, '_load_checkpoint')
        assert hasattr(coordinator, '_save_checkpoint')
        print("✓ Checkpoint methods exist")
        
        print("\n✅ All basic tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic())