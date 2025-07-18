#!/usr/bin/env python3
"""
Autonomous Swarm Demo - A simpler demonstration of swarm capabilities
that can run with fewer agents and doesn't require networkx
"""

import sys
sys.path.append('/app')

from src.core.agents import AgentFactory, get_agent_runtime
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from uuid import uuid4
import asyncio
import random
import json
import time
from typing import List, Dict, Any

logger = get_logger(__name__)

class SimpleAutonomousSwarm:
    """Simplified autonomous swarm for demonstration"""
    
    def __init__(self, num_agents: int = 5):
        self.agents = []
        self.results = []
        self.llm_service = LLMService()
        self.factory = AgentFactory()
        self.runtime = get_agent_runtime()
        self.num_agents = num_agents
        
    async def initialize(self):
        """Initialize the swarm"""
        logger.info(f"Initializing swarm with {self.num_agents} agents")
        
        # Create a mix of agent types
        agent_configs = [
            {
                "type": "reflexive",
                "role": "analyzer",
                "rules": {"error": "analyze_error", "performance": "optimize"}
            },
            {
                "type": "reactive",  # cognitive
                "role": "planner",
                "capabilities": ["planning", "strategy"]
            },
            {
                "type": "hybrid",
                "role": "executor",
                "rules": {"bug": "fix_bug"},
                "capabilities": ["implementation", "testing"]
            },
            {
                "type": "reflexive",
                "role": "validator",
                "rules": {"test": "validate_test", "quality": "check_quality"}
            },
            {
                "type": "reactive",
                "role": "documenter",
                "capabilities": ["documentation", "reporting"]
            }
        ]
        
        for i in range(self.num_agents):
            config = agent_configs[i % len(agent_configs)]
            
            agent_params = {
                "agent_type": config["type"],
                "agent_id": uuid4(),
                "name": f"{config['role'].capitalize()}-{i}",
                "role": config["role"],
                "capabilities": config.get("capabilities", ["general"]),
                "initial_beliefs": {
                    "swarm_id": "demo_swarm",
                    "agent_index": i
                },
                "initial_desires": ["complete_tasks", "collaborate"]
            }
            
            # Add reactive rules for reflexive/hybrid
            if "rules" in config:
                agent_params["reactive_rules"] = config["rules"]
            
            # Add LLM for cognitive/hybrid
            if config["type"] in ["reactive", "hybrid"]:
                agent_params["llm_service"] = self.llm_service
            
            try:
                agent = self.factory.create_agent(**agent_params)
                await self.runtime.register_agent(agent)
                await self.runtime.start_agent(agent)
                self.agents.append(agent)
                logger.info(f"Created agent: {agent.name}")
            except Exception as e:
                logger.error(f"Failed to create agent: {e}")
    
    async def execute_task(self, task: str):
        """Execute a task across the swarm"""
        logger.info(f"Executing task: {task}")
        
        # Simple task decomposition
        subtasks = self._decompose_task(task)
        
        # Assign subtasks to agents
        tasks = []
        for i, subtask in enumerate(subtasks):
            agent = self.agents[i % len(self.agents)]
            task_coroutine = self._agent_work(agent, subtask)
            tasks.append(task_coroutine)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
                self.results.append({
                    "subtask": subtasks[i],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                self.results.append(result)
        
        # Validation phase
        await self._validate_results()
        
        return self._aggregate_results(task)
    
    def _decompose_task(self, task: str) -> List[str]:
        """Simple task decomposition"""
        if "analyze" in task.lower():
            return ["analyze_requirements", "identify_patterns", "generate_report"]
        elif "build" in task.lower():
            return ["design_architecture", "implement_core", "add_features", "test_system"]
        else:
            return ["plan_task", "execute_task", "validate_task"]
    
    async def _agent_work(self, agent, subtask: str) -> Dict[str, Any]:
        """Simulate agent working on a subtask"""
        start_time = time.time()
        
        # Update agent beliefs
        await agent.update_beliefs({"current_subtask": subtask})
        
        # Simulate work
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Generate result
        result = {
            "subtask": subtask,
            "agent": agent.name,
            "agent_type": type(agent).__name__,
            "role": agent.role,
            "status": "completed",
            "duration": time.time() - start_time,
            "output": f"{agent.name} completed {subtask}"
        }
        
        # Add role-specific outputs
        if "analyzer" in agent.role:
            result["analysis"] = {"insights": random.randint(1, 5)}
        elif "planner" in agent.role:
            result["plan"] = {"steps": random.randint(3, 7)}
        elif "executor" in agent.role:
            result["implementation"] = {"lines_of_code": random.randint(50, 200)}
        
        return result
    
    async def _validate_results(self):
        """Simple validation phase"""
        validators = [a for a in self.agents if "validator" in a.role]
        if not validators:
            validators = [self.agents[0]]  # Use first agent as validator
        
        for result in self.results:
            if result.get("status") == "completed":
                validator = random.choice(validators)
                # Simulate validation
                result["validated"] = True
                result["validator"] = validator.name
    
    def _aggregate_results(self, task: str) -> Dict[str, Any]:
        """Aggregate results into summary"""
        summary = {
            "task": task,
            "timestamp": time.time(),
            "agents_used": len(self.agents),
            "subtasks_completed": len([r for r in self.results if r.get("status") == "completed"]),
            "total_subtasks": len(self.results),
            "total_duration": sum(r.get("duration", 0) for r in self.results),
            "results": self.results
        }
        
        # Calculate success rate
        if self.results:
            summary["success_rate"] = summary["subtasks_completed"] / summary["total_subtasks"] * 100
        else:
            summary["success_rate"] = 0
        
        return summary
    
    async def cleanup(self):
        """Clean up agents"""
        logger.info("Cleaning up swarm...")
        for agent in self.agents:
            try:
                await self.runtime.stop_agent(agent.agent_id)
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")


async def demo_swarm():
    """Run a simple swarm demonstration"""
    print("\n=== Autonomous Swarm Demo ===\n")
    
    # Create small swarm
    swarm = SimpleAutonomousSwarm(num_agents=5)
    await swarm.initialize()
    
    # Execute tasks
    tasks = [
        "Analyze system performance and identify bottlenecks",
        "Build a recommendation engine",
        "Create documentation for the project"
    ]
    
    for task in tasks:
        print(f"\n📋 Executing: {task}")
        result = await swarm.execute_task(task)
        
        print(f"\n📊 Results:")
        print(f"   - Subtasks: {result['total_subtasks']}")
        print(f"   - Completed: {result['subtasks_completed']}")
        print(f"   - Success Rate: {result['success_rate']:.1f}%")
        print(f"   - Duration: {result['total_duration']:.2f}s")
        
        # Show agent contributions
        print(f"\n👥 Agent Contributions:")
        agent_work = {}
        for r in result['results']:
            agent = r.get('agent', 'Unknown')
            if agent not in agent_work:
                agent_work[agent] = 0
            agent_work[agent] += 1
        
        for agent, count in agent_work.items():
            print(f"   - {agent}: {count} subtasks")
    
    # Cleanup
    await swarm.cleanup()
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_swarm())