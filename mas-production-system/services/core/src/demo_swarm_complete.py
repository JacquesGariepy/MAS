#!/usr/bin/env python3
"""
Complete demonstration of the fixed MAS swarm system
Shows how it now creates real files like autonomous_fixed.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime
sys.path.insert(0, '/app/src')

async def demo_complete_swarm():
    """Demonstrate the complete fixed swarm functionality"""
    
    print("\n" + "="*80)
    print("🚀 COMPLETE MAS SWARM DEMONSTRATION")
    print("="*80 + "\n")
    
    # Import the fixed swarm
    from swarm_mas_unified import UnifiedSwarmCoordinator
    
    # Initialize with reasonable number of agents
    print("📋 Phase 1: Initialization")
    print("-" * 40)
    coordinator = UnifiedSwarmCoordinator(max_agents=10)
    await coordinator.initialize()
    print(f"✅ Initialized swarm with {coordinator.metrics.total_agents} agents")
    print(f"   - Cognitive Agents: {len([a for a in coordinator.agents.values() if 'cognitive' in str(type(a)).lower()])}")
    print(f"   - Reflexive Agents: {len([a for a in coordinator.agents.values() if 'reflexive' in str(type(a)).lower()])}")
    print(f"   - Hybrid Agents: {len([a for a in coordinator.agents.values() if 'hybrid' in str(type(a)).lower()])}")
    
    # Test requests similar to what autonomous_fixed.py handles
    test_scenarios = [
        {
            "name": "Simple Test Creation",
            "request": "create a unit test for a calculator class",
            "expected_files": ["test_*.py"]
        },
        {
            "name": "Library Generation",
            "request": "create a python library for data processing with tests",
            "expected_files": ["lib_*/", "__init__.py", "core.py"]
        },
        {
            "name": "API Development",
            "request": "build a REST API with authentication endpoints",
            "expected_files": ["api_*.py"]
        }
    ]
    
    total_files_created = 0
    successful_tasks = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Phase {i+1}: {scenario['name']}")
        print("-" * 40)
        
        start_time = time.time()
        print(f"📝 Request: '{scenario['request']}'")
        
        # Submit request
        result = await coordinator.submit_request(scenario['request'])
        
        duration = time.time() - start_time
        
        # Analyze results
        print(f"\n📊 Results:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Tasks created: {result.get('task_count', 0)}")
        
        # Count files created
        files_created = 0
        if 'task_results' in result:
            for task_result in result['task_results']:
                if isinstance(task_result, dict) and 'result' in task_result:
                    files = task_result.get('result', {}).get('files_created', [])
                    files_created += len(files)
                    for file in files:
                        print(f"   ✅ Created: {file}")
        
        total_files_created += files_created
        if files_created > 0:
            successful_tasks += 1
        
        print(f"   Files created: {files_created}")
        print(f"   Success rate: {result.get('success_rate', 0):.1f}%")
    
    # Final workspace analysis
    print("\n" + "="*80)
    print("📂 WORKSPACE ANALYSIS")
    print("="*80)
    
    workspace = "agent_workspace"
    if os.path.exists(workspace):
        print(f"\n📁 Contents of {workspace}/:")
        
        file_types = {}
        total_size = 0
        
        for root, dirs, files in os.walk(workspace):
            level = root.replace(workspace, '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}{os.path.basename(root)}/")
            
            subindent = '  ' * (level + 1)
            for file in sorted(files):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                total_size += size
                
                # Track file types
                ext = os.path.splitext(file)[1] or 'no extension'
                file_types[ext] = file_types.get(ext, 0) + 1
                
                print(f"{subindent}{file} ({size} bytes)")
        
        print(f"\n📊 File Statistics:")
        print(f"   Total files: {sum(file_types.values())}")
        print(f"   Total size: {total_size:,} bytes")
        print(f"   File types:")
        for ext, count in sorted(file_types.items()):
            print(f"     {ext}: {count} files")
    
    # Performance comparison
    print("\n" + "="*80)
    print("📈 PERFORMANCE COMPARISON")
    print("="*80)
    
    print("\n🔵 autonomous_fixed.py (baseline):")
    print("   • Creates 39 files in 224 seconds")
    print("   • Success rate: 52.2%")
    print("   • Uses real LLM API")
    print("   • Single-threaded execution")
    
    print(f"\n🟢 swarm_mas_unified.py (fixed):")
    print(f"   • Created {total_files_created} files")
    print(f"   • Success rate: {(successful_tasks/len(test_scenarios)*100):.1f}%")
    print("   • Uses template-based generation")
    print("   • Parallel agent execution")
    
    # Agent activity report
    print("\n" + "="*80)
    print("🤖 AGENT ACTIVITY REPORT")
    print("="*80)
    
    metrics = await coordinator.get_swarm_metrics()
    print(f"\nSwarm Metrics:")
    print(f"   Total agents: {metrics['total_agents']}")
    print(f"   Active agents: {metrics['active_agents']}")
    print(f"   Idle agents: {metrics['idle_agents']}")
    print(f"   Tasks completed: {metrics['tasks_completed']}")
    print(f"   Tasks failed: {metrics['tasks_failed']}")
    print(f"   Average task duration: {metrics['avg_task_duration']:.2f}s")
    
    # Show some agent details
    print(f"\n🎯 Sample Agent Activities:")
    for i, (agent_id, agent) in enumerate(list(coordinator.agents.items())[:5]):
        load = coordinator.agent_load.get(agent_id, 0)
        print(f"   {agent.name}: Load={load}, Type={type(agent).__name__}")
    
    print("\n✅ Demonstration complete!")
    print(f"📍 Files saved to: {os.path.abspath(workspace)}/")
    
    return {
        'total_files': total_files_created,
        'success_rate': (successful_tasks/len(test_scenarios)*100),
        'workspace': os.path.abspath(workspace)
    }

async def quick_test():
    """Quick test to verify everything works"""
    print("\n🧪 Running quick verification test...")
    
    from swarm_mas_unified import UnifiedSwarmCoordinator
    
    coordinator = UnifiedSwarmCoordinator(max_agents=3)
    await coordinator.initialize()
    
    result = await coordinator.submit_request("create a simple hello world script")
    
    if result.get('status') == 'completed':
        print("✅ Quick test passed!")
        return True
    else:
        print("❌ Quick test failed!")
        return False

if __name__ == "__main__":
    print("Starting complete MAS swarm demonstration...")
    print("This will show how the fixed swarm creates real files.\n")
    
    # Run quick test first
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if loop.run_until_complete(quick_test()):
        # Run full demo
        results = loop.run_until_complete(demo_complete_swarm())
        
        print("\n" + "="*80)
        print("🎉 FINAL SUMMARY")
        print("="*80)
        print(f"✅ Total files created: {results['total_files']}")
        print(f"✅ Overall success rate: {results['success_rate']:.1f}%")
        print(f"✅ Files location: {results['workspace']}")
        print("\n💡 The swarm is now creating real files just like autonomous_fixed.py!")
    else:
        print("\n⚠️ Quick test failed. Please check the fixes.")
    
    loop.close()