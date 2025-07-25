#!/usr/bin/env python3
"""
Demonstration of the unified swarm with actual task execution
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedSwarmCoordinator, UnifiedSwarmConfig, MessagePriority
import uuid

async def demo_with_tasks():
    print("\n" + "="*70)
    print("UNIFIED SWARM MAS - DEMO WITH ACTUAL TASKS")
    print("="*70 + "\n")
    
    # Create coordinator with fewer agents for demo
    config = UnifiedSwarmConfig(
        name="DemoSwarm",
        max_agents=10,
        agent_distribution={
            'architect': 1,
            'developer': 2,
            'tester': 1,
            'analyst': 1,
            'coordinator': 1
        }
    )
    
    coordinator = UnifiedSwarmCoordinator(config)
    
    try:
        # Initialize
        print("1. Initializing swarm...")
        await coordinator.initialize()
        print(f"✅ Swarm initialized with {len(coordinator.agents)} agents!")
        
        # Manually create and submit tasks to demonstrate the system
        print("\n2. Creating and submitting tasks...")
        
        tasks_to_submit = [
            {
                "description": "Design Python test framework structure",
                "type": "design",
                "priority": MessagePriority.HIGH
            },
            {
                "description": "Implement unit test for calculator function",
                "type": "development",
                "priority": MessagePriority.HIGH
            },
            {
                "description": "Create test fixtures and mocks",
                "type": "development",
                "priority": MessagePriority.MEDIUM
            },
            {
                "description": "Analyze test coverage requirements",
                "type": "analysis",
                "priority": MessagePriority.MEDIUM
            },
            {
                "description": "Validate test implementation",
                "type": "testing",
                "priority": MessagePriority.HIGH
            }
        ]
        
        task_ids = []
        for task_spec in tasks_to_submit:
            task_id = await coordinator.submit_task(
                description=task_spec["description"],
                priority=task_spec["priority"],
                metadata={"type": task_spec["type"]}
            )
            task_ids.append(task_id)
            print(f"  ✓ Submitted: {task_spec['description']}")
        
        print(f"\n✅ Submitted {len(task_ids)} tasks to the swarm")
        
        # Show task distribution
        print("\n3. Task Distribution:")
        for agent_id, agent in coordinator.agents.items():
            load = coordinator.agent_load.get(agent_id, 0)
            if load > 0:
                print(f"  - {agent.name} ({agent.role}): {load} task(s)")
        
        # Wait a moment for tasks to be assigned
        await asyncio.sleep(2)
        
        # Show metrics
        print("\n4. Swarm Metrics:")
        metrics = await coordinator.get_swarm_metrics()
        print(f"  - Total Agents: {metrics['total_agents']}")
        print(f"  - Active Agents: {metrics['active_agents']}")
        print(f"  - Tasks Created: {len(task_ids)}")
        print(f"  - Tasks In Queue: {coordinator.task_queue.qsize()}")
        print(f"  - Tasks In Progress: {metrics['tasks_in_progress']}")
        
        # Show how the system would process a request
        print("\n5. Processing a request (demonstration):")
        request = "Create Python unit tests for a calculator module"
        
        # Show the analysis phase
        print(f"\n  Phase 1: Analyzing '{request}'")
        print("  - Identified components:")
        print("    1. Design test structure")
        print("    2. Implement test cases") 
        print("    3. Add test fixtures")
        print("    4. Ensure coverage")
        print("    5. Validate tests")
        
        # Show task assignment
        print("\n  Phase 2: Task Assignment:")
        print("    - Design → Architect-1")
        print("    - Implementation → Developer-1, Developer-2")
        print("    - Testing → Tester-1")
        print("    - Analysis → Analyst-1")
        print("    - Coordination → Coordinator-1")
        
        print("\n✅ This demonstrates how the swarm would process requests!")
        print("   With a real LLM service, tasks would be automatically:")
        print("   - Analyzed and decomposed")
        print("   - Assigned to appropriate agents")
        print("   - Executed in parallel")
        print("   - Validated for quality")
        
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await coordinator.cleanup()
        print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_with_tasks())