#!/usr/bin/env python3
"""
Run Autonomous Swarm - Interactive demonstration of swarm capabilities
"""

import sys
sys.path.append('/app')

import asyncio
from autonomous_swarm_demo import SimpleAutonomousSwarm
from autonomous_swarm_example import handle_extreme_request
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def interactive_swarm_demo():
    """Interactive swarm demonstration"""
    print("\n🐝 AUTONOMOUS SWARM SYSTEM")
    print("=" * 50)
    print("Multi-Agent Swarm with Mixed Agent Types")
    print("=" * 50)
    
    while True:
        print("\n📋 Select a demonstration:")
        print("1. Simple Swarm Demo (5 agents, quick tasks)")
        print("2. Large Swarm Demo (20+ agents, complex tasks)")
        print("3. Custom Task (you define the task)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await run_simple_demo()
        elif choice == "2":
            await run_large_demo()
        elif choice == "3":
            await run_custom_task()
        elif choice == "4":
            print("\n👋 Exiting swarm demonstration")
            break
        else:
            print("❌ Invalid choice, please try again")

async def run_simple_demo():
    """Run simple swarm demonstration"""
    print("\n🚀 Starting Simple Swarm Demo...")
    
    swarm = SimpleAutonomousSwarm(num_agents=5)
    await swarm.initialize()
    
    print("\n✅ Swarm initialized with 5 agents:")
    for agent in swarm.agents:
        print(f"   - {agent.name} ({type(agent).__name__}) - Role: {agent.role}")
    
    # Predefined tasks
    tasks = [
        "Analyze customer feedback and generate insights",
        "Build a recommendation system for e-commerce",
        "Create comprehensive project documentation"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📌 Task {i}/3: {task}")
        input("Press Enter to execute this task...")
        
        result = await swarm.execute_task(task)
        
        print(f"\n📊 Task Results:")
        print(f"   - Success Rate: {result['success_rate']:.1f}%")
        print(f"   - Duration: {result['total_duration']:.2f}s")
        print(f"   - Subtasks: {result['subtasks_completed']}/{result['total_subtasks']}")
        
        # Show detailed results
        print(f"\n📝 Subtask Details:")
        for r in result['results']:
            if r.get('status') == 'completed':
                print(f"   ✅ {r['subtask']} - {r['agent']} ({r['duration']:.2f}s)")
                # Show role-specific outputs
                if 'analysis' in r:
                    print(f"      └─ Insights found: {r['analysis']['insights']}")
                elif 'plan' in r:
                    print(f"      └─ Steps planned: {r['plan']['steps']}")
                elif 'implementation' in r:
                    print(f"      └─ Lines of code: {r['implementation']['lines_of_code']}")
    
    await swarm.cleanup()
    print("\n✅ Simple demo completed!")

async def run_large_demo():
    """Run large swarm demonstration"""
    print("\n🚀 Starting Large Swarm Demo...")
    
    # Check if networkx is available
    try:
        import networkx as nx
    except ImportError:
        print("\n❌ NetworkX is required for large swarm demo")
        print("   Install with: pip install networkx")
        return
    
    print("\n📋 Available complex tasks:")
    print("1. Create a complete compiler (lexer, parser, optimizer)")
    print("2. Refactor a large codebase with documentation")
    print("3. Build a distributed system with microservices")
    
    task_choice = input("\nSelect task (1-3): ").strip()
    
    tasks = {
        "1": "Create compiler with lexer, parser, semantic analysis, optimizer, and code generator",
        "2": "Refactor large codebase, identify code smells, optimize performance, create documentation",
        "3": "Build distributed system with microservices, message queue, load balancer, monitoring"
    }
    
    task = tasks.get(task_choice, tasks["1"])
    
    agent_count = input("\nNumber of agents (10-100, default 20): ").strip()
    try:
        agent_count = int(agent_count)
        agent_count = max(10, min(100, agent_count))
    except:
        agent_count = 20
    
    print(f"\n🐝 Deploying {agent_count} agents for task:")
    print(f"   '{task}'")
    input("\nPress Enter to start...")
    
    import json
    result_json = await handle_extreme_request(task, num_agents=agent_count)
    result = json.loads(result_json)
    
    print(f"\n📊 Swarm Execution Results:")
    print(f"   - Total Agents: {result.get('total_agents', agent_count)}")
    print(f"   - Tasks Completed: {result.get('completed_tasks')}/{result.get('total_tasks')}")
    print(f"   - Failed Tasks: {result.get('failed_tasks', 0)}")
    print(f"   - Success Rate: {result.get('success_rate', 0):.1f}%")
    print(f"   - Total Duration: {result.get('total_duration', 0):.2f}s")
    
    # Validation results
    val = result.get('validation_results', {})
    if val:
        print(f"\n🔍 Validation Results:")
        print(f"   - Approved: {val.get('approved', 0)}")
        print(f"   - Needs Improvement: {val.get('needs_improvement', 0)}")
    
    if 'documentation' in result:
        print(f"\n📄 Documentation generated: {result['documentation']}")
        view = input("View documentation? (y/n): ").strip().lower()
        if view == 'y':
            try:
                with open(result['documentation'], 'r') as f:
                    print("\n" + f.read())
            except:
                print("❌ Could not read documentation file")
    
    print("\n✅ Large swarm demo completed!")

async def run_custom_task():
    """Run custom task defined by user"""
    print("\n🎯 Custom Task Execution")
    
    task = input("\nDescribe your task: ").strip()
    if not task:
        print("❌ No task provided")
        return
    
    agent_count = input("Number of agents (5-50, default 10): ").strip()
    try:
        agent_count = int(agent_count)
        agent_count = max(5, min(50, agent_count))
    except:
        agent_count = 10
    
    print(f"\n🚀 Creating swarm with {agent_count} agents...")
    
    # Determine if task is complex enough for large swarm
    complex_keywords = ["build", "create", "develop", "implement", "design", "refactor"]
    is_complex = any(keyword in task.lower() for keyword in complex_keywords)
    
    if is_complex and agent_count > 15:
        # Use large swarm
        try:
            import networkx as nx
            print("Using large swarm with task graph...")
            import json
            result_json = await handle_extreme_request(task, num_agents=agent_count)
            result = json.loads(result_json)
            
            print(f"\n📊 Results:")
            print(f"   - Success Rate: {result.get('success_rate', 0):.1f}%")
            print(f"   - Tasks: {result.get('completed_tasks')}/{result.get('total_tasks')}")
            print(f"   - Duration: {result.get('total_duration', 0):.2f}s")
        except ImportError:
            print("NetworkX not available, falling back to simple swarm...")
            is_complex = False
    
    if not is_complex or agent_count <= 15:
        # Use simple swarm
        swarm = SimpleAutonomousSwarm(num_agents=agent_count)
        await swarm.initialize()
        
        print(f"\n📋 Executing: {task}")
        result = await swarm.execute_task(task)
        
        print(f"\n📊 Results:")
        print(f"   - Success Rate: {result['success_rate']:.1f}%")
        print(f"   - Subtasks: {result['subtasks_completed']}/{result['total_subtasks']}")
        print(f"   - Duration: {result['total_duration']:.2f}s")
        
        # Show agent contributions
        print(f"\n👥 Agent Contributions:")
        agent_work = {}
        for r in result['results']:
            agent = r.get('agent', 'Unknown')
            agent_work[agent] = agent_work.get(agent, 0) + 1
        
        for agent, count in sorted(agent_work.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {agent}: {count} subtasks")
        
        await swarm.cleanup()
    
    print("\n✅ Custom task completed!")

async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🐝 AUTONOMOUS SWARM SYSTEM - MAS PRODUCTION")
    print("="*60)
    print("\nThis demo showcases:")
    print("✓ Mixed agent types (Reflexive, Cognitive, Hybrid)")
    print("✓ Parallel task execution")
    print("✓ Self-validation and coordination")
    print("✓ Scalable from 5 to 100+ agents")
    print("✓ Real LLM integration when available")
    
    await interactive_swarm_demo()

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())