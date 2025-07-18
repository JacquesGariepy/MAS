#!/usr/bin/env python3
"""
Test Swarm Integration - Validates autonomous swarm functionality
with the MAS production system
"""

import sys
sys.path.append('/app')

import asyncio
import time
from uuid import uuid4

from src.core.agents import AgentFactory, get_agent_runtime
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.core.messages import FIPAMessage, Performative

# Import our swarm implementations
from autonomous_swarm_demo import SimpleAutonomousSwarm
from autonomous_swarm_example import AutonomousSwarm, handle_extreme_request

logger = get_logger(__name__)

async def test_simple_swarm():
    """Test the simple swarm demo with 5 agents"""
    print("\n" + "="*60)
    print("TEST 1: Simple Swarm Demo (5 agents)")
    print("="*60)
    
    try:
        swarm = SimpleAutonomousSwarm(num_agents=5)
        await swarm.initialize()
        
        # Test task execution
        task = "Build a web application with authentication"
        print(f"\n📋 Task: {task}")
        
        result = await swarm.execute_task(task)
        
        print(f"\n✅ Results:")
        print(f"   - Success Rate: {result['success_rate']:.1f}%")
        print(f"   - Total Duration: {result['total_duration']:.2f}s")
        print(f"   - Subtasks Completed: {result['subtasks_completed']}/{result['total_subtasks']}")
        
        # Clean up
        await swarm.cleanup()
        print("\n✅ Simple swarm test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Simple swarm test failed: {e}")
        logger.error(f"Simple swarm test error: {e}", exc_info=True)

async def test_large_swarm():
    """Test the large swarm with networkx integration"""
    print("\n" + "="*60)
    print("TEST 2: Large Swarm with Task Graph (20 agents)")
    print("="*60)
    
    try:
        # Test if networkx is available
        try:
            import networkx as nx
            print("✅ NetworkX available - running full swarm test")
        except ImportError:
            print("⚠️  NetworkX not available - skipping large swarm test")
            print("   Install with: pip install networkx")
            return
        
        # Create and test large swarm
        request = "Create a complete compiler with lexer, parser, and optimizer"
        print(f"\n📋 Request: {request}")
        
        result_json = await handle_extreme_request(request, num_agents=20)
        
        # Parse result
        import json
        result = json.loads(result_json)
        
        print(f"\n✅ Results:")
        print(f"   - Total Agents: {result.get('agents_used', 0)}")
        print(f"   - Tasks Completed: {result.get('completed_tasks', 0)}/{result.get('total_tasks', 0)}")
        print(f"   - Success Rate: {result.get('success_rate', 0):.1f}%")
        print(f"   - Total Duration: {result.get('total_duration', 0):.2f}s")
        
        if 'documentation' in result:
            print(f"   - Documentation: {result['documentation']}")
        
        print("\n✅ Large swarm test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Large swarm test failed: {e}")
        logger.error(f"Large swarm test error: {e}", exc_info=True)

async def test_swarm_communication():
    """Test inter-agent communication within swarm"""
    print("\n" + "="*60)
    print("TEST 3: Swarm Agent Communication")
    print("="*60)
    
    try:
        runtime = get_agent_runtime()
        factory = AgentFactory()
        llm = LLMService()
        
        # Create a mini swarm of 3 agents
        agents = []
        for i in range(3):
            agent_type = ["reflexive", "reactive", "hybrid"][i]
            agent = factory.create_agent(
                agent_type=agent_type,
                agent_id=uuid4(),
                name=f"SwarmAgent-{i}",
                role=["analyzer", "planner", "executor"][i],
                capabilities=["communication", "collaboration"],
                llm_service=llm if agent_type != "reflexive" else None,
                reactive_rules={"test": "respond"} if agent_type in ["reflexive", "hybrid"] else None
            )
            
            await runtime.register_agent(agent)
            await runtime.start_agent(agent)
            agents.append(agent)
            print(f"✅ Started {agent.name} ({agent_type})")
        
        # Test message passing
        print("\n📨 Testing message passing...")
        
        # Agent 0 sends to Agent 1
        message = FIPAMessage(
            sender=agents[0].agent_id,
            receiver=agents[1].agent_id,
            performative=Performative.INFORM,
            content={"text": "Swarm coordination test"},
            conversation_id=str(uuid4())
        )
        
        await agents[1].receive_message(message)
        print(f"   - {agents[0].name} → {agents[1].name}: Message sent")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check metrics
        print("\n📊 Agent Metrics:")
        for agent in agents:
            metrics = await agent.get_metrics()
            print(f"   - {agent.name}: Messages={metrics['messages_processed']}, Actions={metrics['actions_executed']}")
        
        # Clean up
        for agent in agents:
            await runtime.stop_agent(agent.agent_id)
        
        print("\n✅ Communication test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Communication test failed: {e}")
        logger.error(f"Communication test error: {e}", exc_info=True)

async def test_swarm_performance():
    """Test swarm performance and scalability"""
    print("\n" + "="*60)
    print("TEST 4: Swarm Performance & Scalability")
    print("="*60)
    
    agent_counts = [5, 10, 15]
    results = []
    
    for count in agent_counts:
        print(f"\n🚀 Testing with {count} agents...")
        
        start_time = time.time()
        
        try:
            swarm = SimpleAutonomousSwarm(num_agents=count)
            await swarm.initialize()
            
            # Execute a standard task
            task = "Analyze system performance and optimize"
            result = await swarm.execute_task(task)
            
            duration = time.time() - start_time
            
            results.append({
                "agents": count,
                "duration": duration,
                "success_rate": result['success_rate'],
                "subtasks": result['total_subtasks']
            })
            
            await swarm.cleanup()
            
            print(f"   ✅ Completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                "agents": count,
                "duration": 0,
                "success_rate": 0,
                "subtasks": 0
            })
    
    # Display performance summary
    print("\n📊 Performance Summary:")
    print("   Agents | Duration | Success Rate | Subtasks")
    print("   -------|----------|--------------|----------")
    for r in results:
        print(f"   {r['agents']:>6} | {r['duration']:>7.2f}s | {r['success_rate']:>11.1f}% | {r['subtasks']:>8}")
    
    print("\n✅ Performance test completed!")

async def main():
    """Run all swarm integration tests"""
    print("\n🐝 AUTONOMOUS SWARM INTEGRATION TESTS")
    print("=====================================")
    print("Testing autonomous swarm implementations with MAS production system")
    
    # Run tests
    await test_simple_swarm()
    await test_large_swarm()
    await test_swarm_communication()
    await test_swarm_performance()
    
    print("\n" + "="*60)
    print("🎉 ALL SWARM TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())