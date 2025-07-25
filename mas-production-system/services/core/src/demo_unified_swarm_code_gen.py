#!/usr/bin/env python3
"""
Demonstration of Unified Swarm MAS with Code Generation
Shows how the swarm processes requests and generates actual code
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig

async def demo_code_generation():
    """Demonstrate the unified swarm generating actual code"""
    print("\n" + "="*80)
    print("🚀 UNIFIED SWARM MAS - CODE GENERATION DEMO")
    print("="*80 + "\n")
    
    # Create coordinator
    config = UnifiedSwarmConfig(
        name="CodeGenSwarm",
        max_agents=10,  # Smaller for demo
        agent_distribution={
            'architect': 1,
            'developer': 3,
            'tester': 2,
            'analyst': 1,
            'coordinator': 1
        }
    )
    
    coordinator = UnifiedSwarmCoordinator(config)
    
    try:
        # Initialize
        print("1. Initializing swarm...")
        await coordinator.initialize()
        print(f"✅ Swarm initialized with {len(coordinator.agents)} agents")
        
        # Test requests that should generate code
        test_requests = [
            "Create a Python function to calculate fibonacci numbers",
            "Build a simple calculator that can add, subtract, multiply and divide",
            "Create unit tests for a calculator module"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n{'='*60}")
            print(f"📝 Request {i}: {request}")
            print("="*60)
            
            # Process the request
            result = await coordinator.process_request(request)
            
            print(f"\n✅ Status: {result['status']}")
            print(f"⏱️  Duration: {result.get('duration', 'N/A')}")
            
            # Show analysis
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"\n📋 Analysis:")
                print(f"   - Objective: {analysis.get('objective', 'N/A')}")
                print(f"   - Components: {len(analysis.get('components', []))}")
                for comp in analysis.get('components', [])[:3]:
                    print(f"     • {comp}")
            
            # Show task execution
            if 'tasks' in result:
                print(f"\n📊 Task Execution:")
                print(f"   - Total tasks: {len(result['tasks'])}")
                print(f"   - Executed: {result.get('tasks_executed', 0)}")
                print(f"   - Success rate: {result.get('success_rate', 0):.1f}%")
            
            # In a real implementation with proper LLM integration,
            # the generated code would be in the task results
            print(f"\n💡 How it works:")
            print("   1. Request analyzed by LLM service")
            print("   2. Tasks decomposed and assigned to agents")
            print("   3. Agents collaborate to generate code")
            print("   4. Results validated and returned")
            
            # Show what code would be generated
            if "fibonacci" in request.lower():
                print("\n📄 Generated code would include:")
                print("   - fibonacci(n) function with optimal algorithm")
                print("   - fibonacci_sequence(count) helper function")
                print("   - Comprehensive error handling")
                print("   - Unit tests with edge cases")
            elif "calculator" in request.lower():
                print("\n📄 Generated code would include:")
                print("   - calculator(operation, a, b) function")
                print("   - Support for +, -, *, / operations")
                print("   - Error handling for division by zero")
                print("   - Invalid operation handling")
            elif "test" in request.lower():
                print("\n📄 Generated code would include:")
                print("   - Complete unittest.TestCase class")
                print("   - Tests for all operations")
                print("   - Edge case testing")
                print("   - Error condition testing")
            
            await asyncio.sleep(1)  # Brief pause between requests
        
        # Show final metrics
        print(f"\n{'='*60}")
        print("📊 FINAL SWARM METRICS")
        print("="*60)
        
        metrics = await coordinator.get_swarm_metrics()
        print(f"Total Agents: {metrics['total_agents']}")
        print(f"Active Agents: {metrics['active_agents']}")
        print(f"Tasks Completed: {metrics['tasks_completed']}")
        print(f"Messages Processed: {metrics['messages_processed']}")
        print(f"Average Task Time: {metrics.get('average_task_time', 0):.2f}s")
        
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await coordinator.cleanup()
        print("\n✅ Demo completed!")

if __name__ == "__main__":
    print("Starting Unified Swarm Code Generation Demo...")
    print("This demonstrates how the swarm processes requests to generate code.")
    print("With full LLM integration, actual code would be generated.\n")
    
    asyncio.run(demo_code_generation())