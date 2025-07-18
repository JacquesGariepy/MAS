#!/usr/bin/env python3
"""
Autonomous Swarm Complete - Combines autonomous swarm with MAS complete LLM test capabilities
"""

import sys
import os
sys.path.append('/app')

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
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

import networkx as nx

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'swarm_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = get_logger(__name__)

# Define message types since FIPAMessage is not available
class Performative(str, Enum):
    INFORM = "inform"
    REQUEST = "request"
    PROPOSE = "propose"
    QUERY = "query"
    NEGOTIATE = "negotiate"

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

# API endpoints
API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"

class LoggingLLMService(LLMService):
    """Extended LLM Service that logs all interactions"""
    
    def __init__(self, log_file: str = None):
        super().__init__()
        self.log_file = log_file or f"llm_communications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.llm_logger = logging.getLogger("LLM_COMMS")
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.llm_logger.addHandler(handler)
        self.llm_logger.setLevel(logging.DEBUG)
        
    async def generate(self, prompt: str, json_response: bool = False, **kwargs) -> Dict[str, Any]:
        """Override to log all LLM communications"""
        self.llm_logger.info(f"=== LLM REQUEST ===")
        self.llm_logger.info(f"Agent: {kwargs.get('agent_name', 'Unknown')}")
        self.llm_logger.info(f"Prompt: {prompt}")
        self.llm_logger.info(f"JSON Response: {json_response}")
        
        # Call parent method
        result = await super().generate(prompt, json_response, **kwargs)
        
        self.llm_logger.info(f"=== LLM RESPONSE ===")
        self.llm_logger.info(f"Success: {result.get('success', False)}")
        self.llm_logger.info(f"Response: {json.dumps(result.get('response', {}), indent=2)}")
        self.llm_logger.info(f"=== END ===\n")
        
        return result

class MessageLoggingAgent:
    """Mixin to add message logging to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_logger = logging.getLogger(f"AGENT_MSGS.{self.name}")
        handler = logging.FileHandler(f"agent_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
        self.message_logger.addHandler(handler)
        self.message_logger.setLevel(logging.DEBUG)
    
    async def receive_message(self, message: Any):
        """Log received messages"""
        self.message_logger.info(f"=== MESSAGE RECEIVED ===")
        if hasattr(message, '__dict__'):
            self.message_logger.info(f"From: {getattr(message, 'sender', 'Unknown')}")
            self.message_logger.info(f"Type: {getattr(message, 'performative', 'Unknown')}")
            self.message_logger.info(f"Content: {getattr(message, 'content', {})}")
        else:
            self.message_logger.info(f"Raw message: {message}")
        self.message_logger.info(f"=== END ===\n")
        
        # Call parent method
        await super().receive_message(message)
    
    async def _send_message(self, action: Dict[str, Any]):
        """Log sent messages"""
        self.message_logger.info(f"=== MESSAGE SENT ===")
        self.message_logger.info(f"To: {action.get('receiver', 'Unknown')}")
        self.message_logger.info(f"Type: {action.get('performative', 'Unknown')}")
        self.message_logger.info(f"Content: {action.get('content', {})}")
        self.message_logger.info(f"=== END ===\n")
        
        # Call parent method if exists
        if hasattr(super(), '_send_message'):
            await super()._send_message(action)

# Create logged versions of agents
class LoggedCognitiveAgent(MessageLoggingAgent, CognitiveAgent):
    pass

class LoggedReflexiveAgent(MessageLoggingAgent, ReflexiveAgent):
    pass

class LoggedHybridAgent(MessageLoggingAgent, HybridAgent):
    pass

class AutonomousSwarmWithLogging:
    """
    Enhanced autonomous swarm with comprehensive logging
    """
    
    def __init__(self, num_agents: int = 10):
        self.agents = []
        self.results = []
        self.tasks = []
        self.llm_service = LoggingLLMService()
        self.factory = AgentFactory()
        self.runtime = get_agent_runtime()
        
        # Setup swarm logger
        self.swarm_logger = logging.getLogger("SWARM")
        handler = logging.FileHandler(f"swarm_operations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.swarm_logger.addHandler(handler)
        self.swarm_logger.setLevel(logging.DEBUG)
        
        self.swarm_logger.info(f"Initializing autonomous swarm with {num_agents} agents")
        logger.info(f"Initializing autonomous swarm with {num_agents} agents")
        
    async def initialize(self, num_agents: int):
        """Initialize the swarm with logged agents"""
        await self._spawn_mixed_agents(num_agents)
        
    async def _spawn_mixed_agents(self, num_agents: int):
        """Spawn agents with enhanced logging"""
        # Distribute agent types
        types = (["reflexive"] * (num_agents // 3) + 
                ["reactive"] * (num_agents // 3) +
                ["hybrid"] * (num_agents - 2*(num_agents // 3)))
        random.shuffle(types)
        
        # Define roles cyclically
        roles = ["planner", "executor", "validator", "documenter"]
        
        for i, agent_type in enumerate(types):
            role = roles[i % len(roles)]
            
            try:
                # Create agent with logging
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
                    "status": "ready",
                    "agent_index": i
                }
                agent_config["initial_desires"] = [
                    f"complete_{role}_tasks",
                    "collaborate_with_swarm"
                ]
                
                self.swarm_logger.info(f"Creating agent: {agent_config['name']}")
                
                # Create logged agent based on type
                if agent_type == "reflexive":
                    agent = LoggedReflexiveAgent(**agent_config)
                elif agent_type == "reactive":
                    agent = LoggedCognitiveAgent(**agent_config)
                else:  # hybrid
                    agent = LoggedHybridAgent(**agent_config)
                
                await self.runtime.register_agent(agent)
                await self.runtime.start_agent(agent)
                self.agents.append(agent)
                
                self.swarm_logger.info(f"Successfully created and started agent: {agent.name}")
                logger.debug(f"Created agent: {agent.name}")
                
            except Exception as e:
                self.swarm_logger.error(f"Failed to create agent {i}: {str(e)}", exc_info=True)
                logger.error(f"Failed to create agent {i}: {e}")
                
        self.swarm_logger.info(f"Successfully spawned {len(self.agents)} agents")
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
        self.swarm_logger.info(f"Decomposing task: {task_desc}")
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
        self.swarm_logger.info(f"Decomposed task into {len(graph.nodes())} subtasks with {len(graph.edges())} dependencies")
        logger.info(f"Decomposed task into {len(graph.nodes())} subtasks with {len(graph.edges())} dependencies")
        return graph
    
    def _simple_decompose_task(self, task_desc: str) -> List[Dict[str, Any]]:
        """Simple task decomposition without networkx"""
        # Define phases based on task type
        if "compiler" in task_desc.lower():
            phases = ["lexer", "parser", "semantic_analysis", "optimizer", "codegen"]
        elif "refactor" in task_desc.lower():
            phases = ["analyze", "identify_issues", "refactor", "test", "document"]
        elif "recommandation" in task_desc.lower() or "recommendation" in task_desc.lower():
            phases = ["analyze_data", "feature_engineering", "model_training", "evaluation", "deployment"]
        else:
            phases = ["planning", "implementation", "testing", "validation", "documentation"]
        
        # Create simple task list
        tasks = []
        subtasks_per_phase = max(1, len(self.agents) // len(phases))
        
        task_id = 0
        for phase in phases:
            for i in range(subtasks_per_phase):
                tasks.append({
                    "id": task_id,
                    "sub_task": f"{phase}_{i}",
                    "phase": phase,
                    "status": "pending",
                    "assigned_agent": None
                })
                task_id += 1
        
        self.tasks = tasks
        self.swarm_logger.info(f"Decomposed task into {len(tasks)} subtasks (simple mode)")
        return tasks
    
    async def execute_workflow(self, agent, sub_task: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step with an agent"""
        start_time = time.time()
        
        self.swarm_logger.info(f"Agent {agent.name} starting task: {sub_task}")
        
        try:
            # Fix: Ensure task_data is not None and has required fields
            if task_data is None:
                task_data = {}
            
            # Update agent beliefs with task info
            beliefs_update = {
                "current_task": sub_task,
                "task_phase": task_data.get("phase", "unknown"),
                "task_dependencies": task_data.get("dependencies", [])
            }
            
            await agent.update_beliefs(beliefs_update)
            
            # Log the belief update
            self.swarm_logger.debug(f"Updated {agent.name} beliefs: {beliefs_update}")
            
            # Execute based on agent type
            if hasattr(agent, 'reactive_rules'):  # Reflexive or hybrid
                # Check if any reactive rule applies
                for trigger, action in agent.reactive_rules.items():
                    if trigger in sub_task.lower():
                        self.swarm_logger.debug(f"{agent.name} reacting to {trigger} with {action}")
                        logger.debug(f"{agent.name} reacting to {trigger} with {action}")
                        break
            
            # For cognitive processing (cognitive and hybrid agents)
            if hasattr(agent, 'deliberate'):
                # Pass agent name to LLM for logging
                if hasattr(agent, 'llm_service'):
                    agent.llm_service.agent_name = agent.name
                
                intentions = await agent.deliberate()
                for intention in intentions:
                    await agent.commit_to_intention(intention)
                    self.swarm_logger.debug(f"{agent.name} committed to intention: {intention}")
            
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
            
            self.swarm_logger.info(f"Agent {agent.name} completed task: {sub_task} in {result['duration']:.2f}s")
            
            return result
            
        except Exception as e:
            self.swarm_logger.error(f"Error in workflow execution for {agent.name}: {str(e)}", exc_info=True)
            logger.error(f"Error in workflow execution: {e}")
            return {
                "sub_task": sub_task,
                "agent": agent.name,
                "status": "failed",
                "error": str(e)
            }
    
    async def demonstrate_agent_communication(self):
        """Demonstrate inter-agent message passing"""
        self.swarm_logger.info("=== DEMONSTRATING AGENT COMMUNICATION ===")
        
        if len(self.agents) < 2:
            return
        
        # Send messages between random agents
        for i in range(min(5, len(self.agents))):
            sender = random.choice(self.agents)
            receiver = random.choice([a for a in self.agents if a != sender])
            
            message = SimpleMessage(
                sender=sender.agent_id,
                receiver=receiver.agent_id,
                performative=Performative.INFORM.value,
                content={
                    "type": "status_update",
                    "message": f"Task progress from {sender.name}",
                    "progress": random.randint(10, 100)
                }
            )
            
            self.swarm_logger.info(f"Sending message: {sender.name} -> {receiver.name}")
            await receiver.receive_message(message)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)
        
        self.swarm_logger.info("=== COMMUNICATION DEMONSTRATION COMPLETE ===")
    
    async def run_swarm(self, task_graph: nx.DiGraph):
        """Run the swarm on the task graph"""
        self.swarm_logger.info("Starting swarm execution")
        logger.info("Starting swarm execution")
        
        # Demonstrate communication first
        await self.demonstrate_agent_communication()
        
        # Group tasks by phase for better parallelization
        phases = {}
        for node in task_graph.nodes():
            phase = task_graph.nodes[node].get('phase', 'default')
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(node)
        
        # Execute phases in order
        for phase, nodes in phases.items():
            self.swarm_logger.info(f"Executing phase: {phase} with {len(nodes)} tasks")
            logger.info(f"Executing phase: {phase} with {len(nodes)} tasks")
            
            # Assign agents to tasks
            tasks = []
            for i, node in enumerate(nodes):
                # Find suitable agent
                sub_task = task_graph.nodes[node]['sub_task']
                agent = self._find_suitable_agent(sub_task)
                
                # Create task with proper task_data
                task_data = {
                    "phase": phase,
                    "node_id": node,
                    "dependencies": list(task_graph.predecessors(node))
                }
                
                task = self.execute_workflow(agent, sub_task, task_data)
                tasks.append(task)
            
            # Execute tasks in parallel
            phase_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for result in phase_results:
                if isinstance(result, Exception):
                    self.swarm_logger.error(f"Task failed with exception: {result}")
                    logger.error(f"Task failed with exception: {result}")
                else:
                    self.results.append(result)
        
        self.swarm_logger.info(f"Swarm execution completed with {len(self.results)} results")
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
            "agents_used": len(self.agents)
        }
        
        # Log summary
        self.swarm_logger.info("=== EXECUTION SUMMARY ===")
        self.swarm_logger.info(json.dumps(summary, indent=2))
        
        # Generate detailed report
        report_file = f"swarm_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump({
                "summary": summary,
                "results": self.results,
                "agents": [{"name": a.name, "type": a.__class__.__name__, "role": a.role} for a in self.agents]
            }, f, indent=2)
        
        self.swarm_logger.info(f"Detailed report saved to: {report_file}")
        summary["report_file"] = report_file
        
        return json.dumps(summary, indent=2)
    
    async def cleanup(self):
        """Clean up all agents"""
        self.swarm_logger.info("Cleaning up swarm...")
        logger.info("Cleaning up swarm...")
        
        for agent in self.agents:
            try:
                await self.runtime.stop_agent(agent.agent_id)
                self.swarm_logger.info(f"Stopped agent: {agent.name}")
            except Exception as e:
                self.swarm_logger.error(f"Error stopping agent {agent.name}: {e}")
                logger.error(f"Error stopping agent {agent.name}: {e}")
        
        self.swarm_logger.info("Swarm cleanup completed")
        logger.info("Swarm cleanup completed")

class MASCompleteSwarmTest:
    """Complete MAS test with swarm capabilities and API integration"""
    
    def __init__(self):
        self.session = None
        self.users = {}
        self.agents = {}
        self.messages_sent = []
        self.timestamp = int(time.time() * 1000) % 1000000
        self.swarm = None
        
    async def setup(self):
        """Configuration initiale"""
        self.session = aiohttp.ClientSession()
        print("="*80)
        print("🤖 AUTONOMOUS SWARM - TEST COMPLET AVEC LLM")
        print("="*80)
        print("\n📢 Ce test va démontrer:")
        print("   1. Création d'agents autonomes en swarm")
        print("   2. Communication inter-agents avec logging")
        print("   3. Intégration avec l'API MAS")
        print("   4. Traitement par LMStudio")
        print("\n⚠️  SURVEILLEZ LMSTUDIO - Les requêtes vont apparaître!")
        print("="*80)
        
    async def run_api_mode(self):
        """Mode API complet comme mas_complete_llm_test.py"""
        try:
            await self.setup()
            await self.create_users()
            await self.create_intelligent_agents()
            await self.start_all_agents()
            
            print("\n🔄 DÉMARRAGE DU MODE API")
            cycle_count = 0
            
            while True:
                try:
                    cycle_count += 1
                    print(f"\n{'='*80}")
                    print(f"🔁 CYCLE #{cycle_count}")
                    print(f"{'='*80}")
                    
                    # Exécuter les scénarios
                    await self.complex_scenario_1()
                    await asyncio.sleep(5)
                    
                    await self.complex_scenario_2()
                    await asyncio.sleep(5)
                    
                    await self.complex_scenario_3()
                    
                    # Vérifier les résultats
                    responses_found = await self.wait_and_check_responses()
                    
                    print(f"\n📊 Résumé du cycle #{cycle_count}:")
                    print(f"   - Messages envoyés: 3")
                    print(f"   - Réponses LLM détectées: {responses_found}")
                    print(f"   - Agents actifs: {len(self.agents)}")
                    
                    print(f"\n⏸️  Pause de 10 secondes avant le prochain cycle...")
                    await asyncio.sleep(10)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interruption détectée - Arrêt du test...")
                    break
                except Exception as e:
                    print(f"\n❌ Erreur dans le cycle #{cycle_count}: {str(e)}")
                    print("   Tentative de continuer dans 5 secondes...")
                    await asyncio.sleep(5)
            
            await self.generate_summary(responses_found, cycle_count)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption détectée - Nettoyage en cours...")
        finally:
            await self.cleanup()
    
    async def create_users(self):
        """Créer les utilisateurs"""
        print("\n📋 Phase 1: Création des utilisateurs...")
        
        users_data = {
            "alice": {"role": "Chef de Projet", "email": "alice@mas.ai"},
            "bob": {"role": "Architecte Logiciel", "email": "bob@mas.ai"},
            "charlie": {"role": "Expert IA", "email": "charlie@mas.ai"}
        }
        
        for name, info in users_data.items():
            user_data = {
                "username": f"{name}_{self.timestamp}",
                "email": f"{name}_{self.timestamp}@mas.ai",
                "password": "password123"
            }
            
            try:
                async with self.session.post(f"{API_BASE_URL}/auth/register", json=user_data) as resp:
                    if resp.status in [200, 201]:
                        print(f"✅ {name.capitalize()} créé ({info['role']})")
                        
                login_form = aiohttp.FormData()
                login_form.add_field('username', user_data["username"])
                login_form.add_field('password', user_data["password"])
                
                async with self.session.post(f"{API_BASE_URL}/auth/token", data=login_form) as resp:
                    if resp.status == 200:
                        auth_resp = await resp.json()
                        self.users[name] = {
                            "username": user_data["username"],
                            "role": info["role"],
                            "token": auth_resp["access_token"],
                            "headers": {"Authorization": f"Bearer {auth_resp['access_token']}"}
                        }
            except Exception as e:
                print(f"❌ Erreur création {name}: {e}")
                
    async def create_intelligent_agents(self):
        """Créer des agents avec capacités cognitives avancées"""
        print("\n📋 Phase 2: Création des agents intelligents...")
        
        agent_configs = [
            {
                "name": f"ChefProjet_{self.timestamp}",
                "agent_type": "reactive",
                "role": "project_manager",
                "capabilities": ["planning", "coordination", "decision_making"],
                "owner": "alice"
            },
            {
                "name": f"Architecte_{self.timestamp}",
                "agent_type": "reactive",
                "role": "software_architect", 
                "capabilities": ["system_design", "technology_selection"],
                "owner": "bob"
            },
            {
                "name": f"ExpertIA_{self.timestamp}",
                "agent_type": "hybrid",
                "role": "ai_expert",
                "capabilities": ["ml_modeling", "algorithm_selection"],
                "owner": "charlie"
            }
        ]
        
        for config in agent_configs:
            try:
                headers = self.users[config["owner"]]["headers"]
                async with self.session.post(
                    f"{API_V1}/agents",
                    json=config,
                    headers=headers
                ) as resp:
                    if resp.status in [200, 201]:
                        agent_resp = await resp.json()
                        self.agents[config["role"]] = {
                            "id": agent_resp["id"],
                            "name": config["name"],
                            "owner": config["owner"],
                            "type": config["agent_type"]
                        }
                        print(f"✅ {config['name']} créé")
            except Exception as e:
                print(f"❌ Erreur création agent: {e}")
                
    async def start_all_agents(self):
        """Démarrer tous les agents"""
        print("\n📋 Phase 3: Démarrage des agents...")
        
        for role, agent in self.agents.items():
            try:
                headers = self.users[agent["owner"]]["headers"]
                async with self.session.post(
                    f"{API_V1}/agents/{agent['id']}/start",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        print(f"✅ {role} démarré")
            except Exception as e:
                print(f"❌ Erreur démarrage {role}: {e}")
                
        await asyncio.sleep(5)
        
    async def complex_scenario_1(self):
        """Scénario 1: Planification du projet"""
        print("\n🎯 Scénario 1: Planification initiale")
        
        if "project_manager" in self.agents and "software_architect" in self.agents:
            message = {
                "sender_id": self.agents["project_manager"]["id"],
                "receiver_id": self.agents["software_architect"]["id"],
                "performative": "request",
                "content": {
                    "action": "proposer_architecture",
                    "context": {
                        "projet": "Système de recommandation",
                        "contraintes": ["100k utilisateurs/jour", "Temps < 200ms"]
                    }
                }
            }
            
            await self._send_message(message, "alice")
            
    async def complex_scenario_2(self):
        """Scénario 2: Consultation sur les algorithmes"""
        print("\n🎯 Scénario 2: Sélection des algorithmes")
        
        if "software_architect" in self.agents and "ai_expert" in self.agents:
            message = {
                "sender_id": self.agents["software_architect"]["id"],
                "receiver_id": self.agents["ai_expert"]["id"],
                "performative": "query",
                "content": {
                    "question": "Quels algorithmes recommandes-tu pour le système?"
                }
            }
            
            await self._send_message(message, "bob")
            
    async def complex_scenario_3(self):
        """Scénario 3: Analyse de risques"""
        print("\n🎯 Scénario 3: Analyse des risques")
        
        if "ai_expert" in self.agents and "project_manager" in self.agents:
            message = {
                "sender_id": self.agents["ai_expert"]["id"],
                "receiver_id": self.agents["project_manager"]["id"],
                "performative": "inform",
                "content": {
                    "type": "analyse_risques",
                    "risques": ["Cold start", "Scalabilité"]
                }
            }
            
            await self._send_message(message, "charlie")
    
    async def _send_message(self, message_data: dict, sender_user: str):
        """Envoyer un message"""
        try:
            headers = self.users[sender_user]["headers"]
            sender_id = message_data["sender_id"]
            
            async with self.session.post(
                f"{API_V1}/agents/{sender_id}/messages",
                json=message_data,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    result = await resp.json()
                    self.messages_sent.append(result['id'])
                    print(f"   ✅ Message envoyé")
        except Exception as e:
            print(f"   ❌ Erreur envoi: {e}")
            
    async def wait_and_check_responses(self):
        """Attendre et vérifier les réponses"""
        print("\n📋 Surveillance de l'activité...")
        
        responses_found = 0
        for i in range(20):
            print(f"\r⏳ Attente... {i*3}/60s", end="", flush=True)
            await asyncio.sleep(3)
            
            # Vérifier les messages
            for role, agent in self.agents.items():
                try:
                    headers = self.users[agent["owner"]]["headers"]
                    async with self.session.get(
                        f"{API_V1}/agents/{agent['id']}/messages",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            messages = await resp.json()
                            if messages:
                                responses_found += 1
                except:
                    pass
                    
        print(f"\n✅ Réponses trouvées: {responses_found}")
        return responses_found
        
    async def generate_summary(self, responses_found: int, cycles: int):
        """Générer un résumé"""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ")
        print("="*80)
        print(f"✅ Cycles: {cycles}")
        print(f"✅ Réponses LLM: {responses_found}")
        
    async def cleanup(self):
        """Nettoyage"""
        if self.session:
            await self.session.close()

async def demo_swarm_mode():
    """Mode swarm autonome avec logging"""
    print("\n=== MODE SWARM AUTONOME ===")
    print("Création d'un swarm d'agents avec logging complet")
    
    # Create swarm
    swarm = AutonomousSwarmWithLogging(num_agents=6)
    await swarm.initialize(6)
    
    # Execute task
    task = "Créer un système de recommandation avec architecture complète"
    print(f"\n📋 Tâche: {task}")
    
    # Decompose task
    task_graph = swarm.decompose_task(task)
    # Run swarm
    await swarm.run_swarm(task_graph)
    
    # Get results
    summary = swarm.aggregate_results(task)
    print(f"\n📊 Résumé:")
    print(summary)
    
    # Cleanup
    await swarm.cleanup()
    
    print("\n✅ Mode swarm terminé!")

async def main():
    """Point d'entrée principal"""
    print("\n🚀 AUTONOMOUS SWARM - SÉLECTION DU MODE")
    print("1. Mode Swarm Local (sans API)")
    print("2. Mode API Complet (comme mas_complete_llm_test)")
    print("3. Mode Hybride (Swarm + API)")
    
    # Check for command line argument or environment variable
    import sys
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        print(f"\nMode sélectionné via argument: {choice}")
    elif os.getenv('SWARM_MODE'):
        choice = os.getenv('SWARM_MODE')
        print(f"\nMode sélectionné via env: {choice}")
    else:
        try:
            choice = input("\nChoisir le mode (1-3): ").strip()
        except EOFError:
            # Default to mode 1 in non-interactive environment
            choice = "1"
            print("\nMode par défaut sélectionné: 1")
    
    if choice == "1":
        await demo_swarm_mode()
    elif choice == "2":
        test = MASCompleteSwarmTest()
        await test.run_api_mode()
    elif choice == "3":
        # Mode hybride - créer swarm ET utiliser API
        print("\n=== MODE HYBRIDE ===")
        test = MASCompleteSwarmTest()
        await test.setup()
        
        # Créer swarm local
        swarm = AutonomousSwarmWithLogging(num_agents=3)
        await swarm.initialize(3)
        
        # Créer utilisateurs et agents API
        await test.create_users()
        await test.create_intelligent_agents()
        await test.start_all_agents()
        
        print("\n✅ Swarm local + Agents API créés!")
        print("   - Agents locaux:", len(swarm.agents))
        print("   - Agents API:", len(test.agents))
        
        await swarm.cleanup()
        await test.cleanup()
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    asyncio.run(main())