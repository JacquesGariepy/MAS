#!/usr/bin/env python3
"""
Autonomous Swarm Example - Demonstrates large-scale multi-agent coordination
with mixed agent types (reflexive, cognitive, hybrid) working on complex tasks.
Includes all features from mas_complete_llm_test.py
"""

import sys
import os
sys.path.append('/app')  # Docker container path

# Imports from the MAS project
from src.core.agents import AgentFactory, get_agent_runtime
from src.core.agents.reflexive_agent import ReflexiveAgent
from src.core.agents.cognitive_agent import CognitiveAgent
from src.core.agents.hybrid_agent import HybridAgent
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

from uuid import uuid4
import asyncio
import aiohttp
import random
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = get_logger(__name__)

import networkx as nx

# API endpoints for MAS integration
API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"

# Message types
class Performative(str, Enum):
    INFORM = "inform"
    REQUEST = "request"
    PROPOSE = "propose"
    QUERY = "query"

@dataclass
class SimpleMessage:
    sender: Any
    receiver: Any
    performative: str
    content: Dict[str, Any]
    conversation_id: str = ""
    
    def __post_init__(self):
        if not self.conversation_id:
            self.conversation_id = str(uuid4())

class AutonomousSwarm:
    """
    Large-scale autonomous swarm that can handle complex tasks with mixed agent types.
    Demonstrates task decomposition, parallel execution, and self-validation.
    """
    
    def __init__(self, num_agents: int = 10):
        self.agents = []
        self.results = []
        self.tasks = []
        self.llm_service = LLMService()
        self.factory = AgentFactory()
        self.runtime = get_agent_runtime()
        logger.info(f"Initializing autonomous swarm with {num_agents} agents")
        
    async def initialize(self, num_agents: int):
        """Initialize the swarm with mixed agent types"""
        await self._spawn_mixed_agents(num_agents)
        
    async def _spawn_mixed_agents(self, num_agents: int):
        """Spawn agents with mixed types and roles"""
        # Distribute agent types
        types = (["reflexive"] * (num_agents // 3) + 
                ["reactive"] * (num_agents // 3) +  # cognitive in our system
                ["hybrid"] * (num_agents - 2*(num_agents // 3)))
        random.shuffle(types)
        
        # Define roles cyclically
        roles = ["planner", "executor", "validator", "documenter"]
        
        for i, agent_type in enumerate(types):
            role = roles[i % len(roles)]
            
            # Create agent with appropriate configuration
            agent_config = {
                "agent_type": agent_type,
                "agent_id": uuid4(),
                "name": f"{role.capitalize()}-{agent_type}-{i}",
                "role": role,
                "capabilities": self._get_capabilities_for_role(role),
            }
            
            # Add reactive rules for reflexive and hybrid agents
            if agent_type in ["reflexive", "hybrid"]:
                agent_config["reactive_rules"] = {
                    "bug_detected": "fix_bug",
                    "refactor_needed": "refactor_code",
                    "test_failed": "debug_test"
                }
            
            # Add LLM service for cognitive and hybrid agents
            if agent_type in ["reactive", "hybrid"]:
                agent_config["llm_service"] = self.llm_service
            
            # Add initial beliefs and desires
            agent_config["initial_beliefs"] = {
                "swarm_size": num_agents,
                "role": role,
                "status": "ready"
            }
            agent_config["initial_desires"] = [
                f"complete_{role}_tasks",
                "collaborate_with_swarm"
            ]
            
            try:
                agent = self.factory.create_agent(**agent_config)
                await self.runtime.register_agent(agent)
                await self.runtime.start_agent(agent)
                self.agents.append(agent)
                logger.debug(f"Created agent: {agent.name}")
            except Exception as e:
                logger.error(f"Failed to create agent {i}: {e}")
                
        logger.info(f"Successfully spawned {len(self.agents)} agents")
    
    def _get_capabilities_for_role(self, role: str) -> List[str]:
        """Get capabilities based on agent role"""
        capabilities_map = {
            "planner": ["task_decomposition", "strategy_planning", "resource_allocation"],
            "executor": ["code_generation", "testing", "implementation"],
            "validator": ["code_review", "testing", "quality_assurance"],
            "documenter": ["documentation", "reporting", "analysis"]
        }
        return capabilities_map.get(role, ["general_processing"])
    
    def decompose_task(self, task_desc: str) -> nx.DiGraph:
        """Decompose a complex task into subtasks using a directed graph"""
        graph = nx.DiGraph()
        
        # Define phases based on task type
        if "compiler" in task_desc.lower():
            phases = ["lexer", "parser", "semantic_analysis", "optimizer", "codegen"]
        elif "refactor" in task_desc.lower():
            phases = ["analyze", "identify_issues", "refactor", "test", "document"]
        else:
            phases = ["planning", "implementation", "testing", "validation", "documentation"]
        
        # Create enough subtasks for all agents
        subtasks_per_phase = max(1, len(self.agents) // len(phases))
        
        node_id = 0
        for phase_idx, phase in enumerate(phases):
            for i in range(subtasks_per_phase):
                graph.add_node(node_id, 
                             sub_task=f"{phase}_{i}",
                             phase=phase,
                             status="pending",
                             assigned_agent=None)
                
                # Add dependencies within phases
                if i > 0:
                    graph.add_edge(node_id - 1, node_id)
                
                # Add dependencies between phases
                if phase_idx > 0 and i == 0:
                    # Connect to last node of previous phase
                    prev_phase_last = node_id - subtasks_per_phase
                    graph.add_edge(prev_phase_last, node_id)
                
                node_id += 1
        
        self.tasks = list(graph.nodes())
        logger.info(f"Decomposed task into {len(graph.nodes())} subtasks with {len(graph.edges())} dependencies")
        return graph
    
    async def execute_workflow(self, agent, sub_task: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step with an agent"""
        start_time = time.time()
        
        try:
            # Update agent beliefs with task info
            await agent.update_beliefs({
                "current_task": sub_task,
                "task_phase": task_data.get("phase", "unknown"),
                "task_dependencies": task_data.get("dependencies", [])
            })
            
            # Execute based on agent type
            if hasattr(agent, 'reactive_rules'):  # Reflexive or hybrid
                # Check if any reactive rule applies
                for trigger, action in agent.reactive_rules.items():
                    if trigger in sub_task.lower():
                        logger.debug(f"{agent.name} reacting to {trigger} with {action}")
                        break
            
            # For cognitive processing (cognitive and hybrid agents)
            if hasattr(agent, 'deliberate'):
                intentions = await agent.deliberate()
                for intention in intentions:
                    await agent.commit_to_intention(intention)
            
            # Simulate task execution
            result = {
                "sub_task": sub_task,
                "agent": agent.name,
                "agent_type": agent.__class__.__name__,
                "status": "completed",
                "duration": time.time() - start_time,
                "output": f"Processed {sub_task} successfully"
            }
            
            # Add specific outputs based on task type
            if "analyze" in sub_task:
                result["analysis"] = {"issues_found": random.randint(0, 5)}
            elif "test" in sub_task:
                result["test_results"] = {"passed": random.randint(80, 100), "total": 100}
            elif "document" in sub_task:
                result["documentation"] = {"pages_generated": random.randint(1, 10)}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            return {
                "sub_task": sub_task,
                "agent": agent.name,
                "status": "failed",
                "error": str(e)
            }
    
    async def self_play_validation(self):
        """Agents validate each other's work"""
        validation_rounds = 3
        
        for round_num in range(validation_rounds):
            logger.info(f"Starting validation round {round_num + 1}")
            
            # Get validators
            validators = [a for a in self.agents if "validator" in a.role]
            if not validators:
                validators = self.agents[:5]  # Use first 5 agents as validators
            
            # Validate random results
            for _ in range(min(10, len(self.results))):
                result = random.choice(self.results)
                validator = random.choice(validators)
                
                # Update validator's beliefs with result to validate
                await validator.update_beliefs({
                    "validating_result": result,
                    "validation_round": round_num
                })
                
                # Simulate validation
                if result.get("status") == "completed":
                    if random.random() > 0.9:  # 10% chance of finding issue
                        result["validation_feedback"] = {
                            "validator": validator.name,
                            "status": "needs_improvement",
                            "issues": ["performance", "documentation"]
                        }
                    else:
                        result["validation_feedback"] = {
                            "validator": validator.name,
                            "status": "approved"
                        }
    
    async def run_swarm(self, task_graph: nx.DiGraph):
        """Run the swarm on the task graph"""
        logger.info("Starting swarm execution")
        
        # Group tasks by phase for better parallelization
        phases = {}
        for node in task_graph.nodes():
            phase = task_graph.nodes[node].get('phase', 'default')
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(node)
        
        # Execute phases in order
        for phase, nodes in phases.items():
            logger.info(f"Executing phase: {phase} with {len(nodes)} tasks")
            
            # Assign agents to tasks
            tasks = []
            for i, node in enumerate(nodes):
                # Find suitable agent
                sub_task = task_graph.nodes[node]['sub_task']
                agent = self._find_suitable_agent(sub_task)
                
                # Create task
                task = self.execute_workflow(
                    agent, 
                    sub_task,
                    {"phase": phase, "node_id": node}
                )
                tasks.append(task)
            
            # Execute tasks in parallel
            phase_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for result in phase_results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                else:
                    self.results.append(result)
        
        # Run validation
        await self.self_play_validation()
        
        logger.info(f"Swarm execution completed with {len(self.results)} results")
    
    def _find_suitable_agent(self, sub_task: str) -> Any:
        """Find the most suitable agent for a task"""
        # Prioritize by role matching
        if "plan" in sub_task:
            candidates = [a for a in self.agents if "planner" in a.role]
        elif "test" in sub_task or "valid" in sub_task:
            candidates = [a for a in self.agents if "validator" in a.role]
        elif "document" in sub_task:
            candidates = [a for a in self.agents if "documenter" in a.role]
        else:
            candidates = [a for a in self.agents if "executor" in a.role]
        
        if not candidates:
            candidates = self.agents
        
        # Return random candidate to distribute load
        return random.choice(candidates)
    
    def aggregate_results(self, request: str) -> str:
        """Aggregate and format results"""
        summary = {
            "request": request,
            "total_tasks": len(self.results),
            "completed_tasks": len([r for r in self.results if r.get("status") == "completed"]),
            "failed_tasks": len([r for r in self.results if r.get("status") == "failed"]),
            "total_duration": sum(r.get("duration", 0) for r in self.results),
            "validation_results": {
                "approved": len([r for r in self.results if r.get("validation_feedback", {}).get("status") == "approved"]),
                "needs_improvement": len([r for r in self.results if r.get("validation_feedback", {}).get("status") == "needs_improvement"])
            }
        }
        
        # Generate documentation if requested
        if "document" in request.lower():
            doc_content = f"""# Autonomous Swarm Execution Report

## Summary
- **Request**: {request}
- **Total Agents**: {len(self.agents)}
- **Tasks Completed**: {summary['completed_tasks']}/{summary['total_tasks']}
- **Total Duration**: {summary['total_duration']:.2f} seconds

## Agent Distribution
- Reflexive Agents: {len([a for a in self.agents if isinstance(a, ReflexiveAgent)])}
- Cognitive Agents: {len([a for a in self.agents if isinstance(a, CognitiveAgent)])}
- Hybrid Agents: {len([a for a in self.agents if isinstance(a, HybridAgent)])}

## Results by Phase
"""
            
            # Group results by phase
            phase_results = {}
            for result in self.results:
                phase = result.get("sub_task", "").split("_")[0]
                if phase not in phase_results:
                    phase_results[phase] = []
                phase_results[phase].append(result)
            
            for phase, results in phase_results.items():
                doc_content += f"\n### {phase.capitalize()}\n"
                doc_content += f"- Tasks: {len(results)}\n"
                doc_content += f"- Success Rate: {len([r for r in results if r.get('status') == 'completed'])/len(results)*100:.1f}%\n"
            
            # Write documentation
            output_file = f"swarm_report_{int(time.time())}.md"
            with open(output_file, "w") as f:
                f.write(doc_content)
            logger.info(f"Documentation generated: {output_file}")
            
            summary["documentation"] = output_file
        
        return json.dumps(summary, indent=2)
    
    async def cleanup(self):
        """Clean up all agents"""
        logger.info("Cleaning up swarm...")
        
        for agent in self.agents:
            try:
                await self.runtime.stop_agent(agent.agent_id)
            except Exception as e:
                logger.error(f"Error stopping agent {agent.name}: {e}")
        
        logger.info("Swarm cleanup completed")


async def handle_extreme_request(request: str, num_agents: int = 100):
    """Handle complex requests with large agent swarms"""
    logger.info(f"Handling request: {request} with {num_agents} agents")
    
    swarm = AutonomousSwarm(num_agents)
    await swarm.initialize(num_agents)
    
    # Decompose task
    task_graph = swarm.decompose_task(request)
    
    # Run swarm
    await swarm.run_swarm(task_graph)
    
    # Aggregate results
    aggregated = swarm.aggregate_results(request)
    
    # Cleanup
    await swarm.cleanup()
    
    return aggregated


class MASAPIIntegration:
    """Integration with MAS API for complete testing"""
    
    def __init__(self):
        self.session = None
        self.users = {}
        self.agents = {}
        self.timestamp = int(time.time() * 1000) % 1000000
        
    async def setup(self):
        """Setup API session"""
        self.session = aiohttp.ClientSession()
        print("\n📡 API Integration Setup Complete")
        
    async def create_users_and_agents(self):
        """Create users and agents via API"""
        # Similar to mas_complete_llm_test.py
        users_data = {
            "alice": {"role": "Chef de Projet"},
            "bob": {"role": "Architecte"},
            "charlie": {"role": "Expert IA"}
        }
        
        for name, info in users_data.items():
            user_data = {
                "username": f"{name}_{self.timestamp}",
                "email": f"{name}_{self.timestamp}@mas.ai",
                "password": "password123"
            }
            
            try:
                # Register
                async with self.session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                    if resp.status in [200, 201]:
                        print(f"✅ User {name} created")
                        
                # Login
                login_form = aiohttp.FormData()
                login_form.add_field('username', user_data["username"])
                login_form.add_field('password', user_data["password"])
                
                async with self.session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
                    if resp.status == 200:
                        auth_resp = await resp.json()
                        self.users[name] = {
                            "token": auth_resp["access_token"],
                            "headers": {"Authorization": f"Bearer {auth_resp['access_token']}"}
                        }
            except Exception as e:
                print(f"❌ Error creating user {name}: {e}")
    
    async def cleanup(self):
        """Cleanup API session"""
        if self.session:
            await self.session.close()

# Example execution with multiple modes
async def run_complete_demo():
    """Run complete demo with all features"""
    print("\n🚀 AUTONOMOUS SWARM - COMPLETE DEMO")
    print("="*60)
    print("Select mode:")
    print("1. Local Swarm Only")
    print("2. API Integration Mode")
    print("3. Continuous Loop Mode")
    print("4. All Features Demo")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        # Local swarm mode
        print("\n=== LOCAL SWARM MODE ===")
        result = await handle_extreme_request("Create complete system with all components", 10)
        print("Result:", result)
        
    elif choice == "2":
        # API integration mode
        print("\n=== API INTEGRATION MODE ===")
        api = MASAPIIntegration()
        await api.setup()
        await api.create_users_and_agents()
        print("✅ API integration complete")
        await api.cleanup()
        
    elif choice == "3":
        # Continuous loop mode
        print("\n=== CONTINUOUS LOOP MODE ===")
        cycle = 0
        while True:
            try:
                cycle += 1
                print(f"\n🔄 Cycle #{cycle}")
                
                # Run swarm task
                swarm = AutonomousSwarm(num_agents=5)
                await swarm.initialize(5)
                
                task = f"Iteration {cycle}: Optimize system performance"
                task_graph = swarm.decompose_task(task)
                await swarm.run_swarm(task_graph)
                
                summary = swarm.aggregate_results(task)
                print(f"Cycle {cycle} complete:", summary)
                
                await swarm.cleanup()
                
                print("\n⏸️  Press Ctrl+C to stop, or wait 10s for next cycle...")
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                print("\n✋ Stopping continuous mode")
                break
                
    elif choice == "4":
        # All features demo
        print("\n=== ALL FEATURES DEMO ===")
        
        # 1. Create large swarm
        print("\n1️⃣ Creating Large Swarm...")
        swarm_result = await handle_extreme_request("Build complete e-commerce platform", 20)
        print("Swarm Result:", swarm_result)
        
        # 2. API Integration
        print("\n2️⃣ API Integration...")
        api = MASAPIIntegration()
        await api.setup()
        await api.create_users_and_agents()
        await api.cleanup()
        
        # 3. Demonstrate logging
        print("\n3️⃣ Check log files:")
        log_files = [f for f in os.listdir('.') if f.endswith('.log')]
        for log_file in log_files[:5]:
            print(f"   - {log_file}")
            
        print("\n✅ All features demonstrated!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the complete demo
    asyncio.run(run_complete_demo())