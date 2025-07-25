#!/usr/bin/env python3
"""
SIMPLE DEMO OF UNIFIED SWARM MAS
================================
A working demonstration without the complex environment system
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("SWARM_DEMO")

class SimpleAgent:
    """Simplified agent for demonstration"""
    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.id = str(uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.active = True
        logger.info(f"Created agent: {name} ({role})")
        
    async def process_task(self, task: str) -> str:
        """Process a task"""
        logger.info(f"{self.name} processing: {task}")
        await asyncio.sleep(1)  # Simulate work
        return f"{self.name} completed: {task}"

class SimpleSwarmCoordinator:
    """Simplified swarm coordinator"""
    def __init__(self, name: str = "SimpleSwarm"):
        self.name = name
        self.agents = {}
        self.tasks = []
        logger.info(f"Initialized {name} coordinator")
        
    def create_agent(self, name: str, role: str, capabilities: List[str]) -> SimpleAgent:
        """Create a new agent"""
        agent = SimpleAgent(name, role, capabilities)
        self.agents[agent.id] = agent
        return agent
        
    async def submit_task(self, description: str) -> Dict[str, Any]:
        """Submit a task to the swarm"""
        task = {
            "id": str(uuid4()),
            "description": description,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        self.tasks.append(task)
        logger.info(f"Task submitted: {description}")
        
        # Simple task assignment - find capable agent
        for agent in self.agents.values():
            if agent.active:
                task["assigned_to"] = agent.name
                task["status"] = "assigned"
                
                # Process task
                result = await agent.process_task(description)
                task["result"] = result
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
                break
                
        return task
        
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status"""
        return {
            "name": self.name,
            "agents": len(self.agents),
            "active_agents": sum(1 for a in self.agents.values() if a.active),
            "total_tasks": len(self.tasks),
            "completed_tasks": sum(1 for t in self.tasks if t.get("status") == "completed")
        }

async def demo():
    """Run a simple demonstration"""
    print("\n" + "="*60)
    print("UNIFIED SWARM MAS - SIMPLE DEMONSTRATION")
    print("="*60 + "\n")
    
    # Create coordinator
    swarm = SimpleSwarmCoordinator("DemoSwarm")
    
    # Create agents
    print("Creating agents...")
    agents = [
        swarm.create_agent("Architect-1", "architect", ["design", "planning"]),
        swarm.create_agent("Developer-1", "developer", ["coding", "testing"]),
        swarm.create_agent("Developer-2", "developer", ["coding", "debugging"]),
        swarm.create_agent("Analyst-1", "analyst", ["analysis", "optimization"]),
        swarm.create_agent("Tester-1", "tester", ["testing", "validation"])
    ]
    
    print(f"\n✓ Created {len(agents)} agents\n")
    
    # Submit tasks
    print("Submitting tasks...")
    tasks = [
        "Design REST API architecture",
        "Implement user authentication",
        "Create database schema",
        "Write unit tests",
        "Optimize performance"
    ]
    
    results = []
    for task_desc in tasks:
        result = await swarm.submit_task(task_desc)
        results.append(result)
        print(f"✓ {result['result']}")
        
    # Show status
    print("\n" + "-"*60)
    print("SWARM STATUS:")
    print("-"*60)
    status = swarm.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
        
    print("\n" + "-"*60)
    print("TASK RESULTS:")
    print("-"*60)
    for task in results:
        print(f"\nTask: {task['description']}")
        print(f"Status: {task['status']}")
        print(f"Assigned to: {task.get('assigned_to', 'N/A')}")
        print(f"Result: {task.get('result', 'N/A')}")
        
    print("\n✅ Demonstration complete!\n")

if __name__ == "__main__":
    asyncio.run(demo())