#!/usr/bin/env python3
"""
Test Swarm with Logging - Simple test to verify swarm functionality
"""

import sys
sys.path.append('/app')

import asyncio
from autonomous_swarm_with_logging import AutonomousSwarmWithLogging
import os
from datetime import datetime

async def test_swarm_logging():
    """Test the swarm with enhanced logging"""
    print("\n🐝 TESTING AUTONOMOUS SWARM WITH LOGGING")
    print("=" * 50)
    print(f"Start time: {datetime.now()}")
    print("\nLog files will be created:")
    print("- swarm_operations_*.log")
    print("- agent_messages_*.log")
    print("- llm_communications_*.log")
    print("- swarm_log_*.log")
    print("=" * 50)
    
    # Create small swarm for testing
    num_agents = 6  # Small number for testing
    print(f"\n📋 Creating swarm with {num_agents} agents...")
    
    swarm = AutonomousSwarmWithLogging(num_agents=num_agents)
    
    try:
        # Initialize swarm
        print("🚀 Initializing agents...")
        await swarm.initialize(num_agents)
        print(f"✅ Successfully initialized {len(swarm.agents)} agents")
        
        # Print agent details
        print("\n👥 Agent Details:")
        for agent in swarm.agents:
            print(f"   - {agent.name} ({agent.__class__.__name__}) - Role: {agent.role}")
        
        # Simple task
        task_desc = "Analyze system performance and create optimization plan"
        print(f"\n📋 Task: {task_desc}")
        
        # Decompose task
        print("\n🔍 Decomposing task...")
        task_graph = swarm.decompose_task(task_desc)
        print(f"✅ Created {len(task_graph.nodes())} subtasks")
        
        # Run swarm
        print("\n🏃 Running swarm execution...")
        await swarm.run_swarm(task_graph)
        
        # Get results
        print("\n📊 Aggregating results...")
        summary = swarm.aggregate_results(task_desc)
        print("\n📈 Execution Summary:")
        print(summary)
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await swarm.cleanup()
        
        print("\n✅ Test completed successfully!")
        
        # List created log files
        print("\n📁 Created log files:")
        log_files = [f for f in os.listdir('.') if f.endswith('.log')]
        for log_file in sorted(log_files):
            size = os.path.getsize(log_file)
            print(f"   - {log_file} ({size} bytes)")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Still try to cleanup
        try:
            await swarm.cleanup()
        except:
            pass

if __name__ == "__main__":
    # Set logging level
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_swarm_logging())