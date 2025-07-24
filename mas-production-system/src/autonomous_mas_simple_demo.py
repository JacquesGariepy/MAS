#!/usr/bin/env python3
"""
Simple MAS Demo with FileSystemTool only
Demonstrating core Ferber's principles
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

# Import MAS components
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.tools.filesystem_tool import FileSystemTool

# Import agents
from src.core.agents import CognitiveAgent, ReflexiveAgent, HybridAgent

# Import environment
from src.core.environment import (
    SoftwareEnvironment,
    SoftwareLocation,
    TopologyType,
    VisibilityLevel,
    EnvironmentAdapter
)

from src.core.runtime import get_agent_runtime
from src.utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger("MAS_SIMPLE_DEMO")


class SimpleMASDemo:
    """Simple Multi-Agent System demonstrating core principles"""
    
    def __init__(self):
        self.id = uuid4()
        self.name = f"SimpleMAS-{str(self.id)[:8]}"
        
        # Services
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        self.runtime = get_agent_runtime()
        
        # Agents
        self.agents = {}
        
        # Environment
        self.environment = SoftwareEnvironment(TopologyType.PROCESS_TREE)
        self.adapter = EnvironmentAdapter(self.environment)
        
        # Metrics
        self.metrics = {
            'agents_created': 0,
            'tasks_processed': 0,
            'messages_sent': 0,
            'resources_allocated': 0
        }
        
    async def initialize(self):
        """Initialize the MAS system"""
        logger.info(f"🚀 Initializing {self.name}...")
        
        # Create specialized agents
        await self._create_agents()
        
        # Start environment dynamics
        asyncio.create_task(self._environment_loop())
        
        logger.info("✅ System initialized successfully!")
        
    async def _create_agents(self):
        """Create specialized agents"""
        agent_configs = [
            {
                'name': 'Analyst',
                'type': CognitiveAgent,
                'role': 'analyst',
                'capabilities': ['analysis', 'research', 'understanding'],
                'visibility': VisibilityLevel.FULL
            },
            {
                'name': 'Developer',
                'type': HybridAgent,
                'role': 'developer',
                'capabilities': ['coding', 'implementation', 'debugging'],
                'visibility': VisibilityLevel.NAMESPACE
            },
            {
                'name': 'Tester',
                'type': HybridAgent,
                'role': 'tester',
                'capabilities': ['testing', 'validation', 'quality'],
                'visibility': VisibilityLevel.NAMESPACE
            },
            {
                'name': 'Coordinator',
                'type': ReflexiveAgent,
                'role': 'coordinator',
                'capabilities': ['coordination', 'orchestration', 'monitoring'],
                'visibility': VisibilityLevel.PROCESS
            }
        ]
        
        for config in agent_configs:
            agent = await self._create_agent(config)
            if agent:
                self.agents[config['role']] = agent
                
        # Create agent network (star topology with coordinator at center)
        await self.adapter.create_agent_network(
            list(self.agents.values()),
            topology="star"
        )
        
        logger.info(f"✅ Created {len(self.agents)} specialized agents")
        
    async def _create_agent(self, config: Dict[str, Any]):
        """Create and configure an agent"""
        try:
            # Create agent
            agent_class = config['type']
            
            if agent_class == ReflexiveAgent:
                agent = agent_class(
                    agent_id=uuid4(),
                    name=f"{config['name']}-{self.name}",
                    role=config['role'],
                    capabilities=config['capabilities']
                )
                # Add rules after creation
                agent.rules = {
                    'high_load': lambda ctx: ctx.get('cpu_usage', 0) > 80,
                    'task_complete': lambda ctx: ctx.get('task_status') == 'completed',
                    'error_detected': lambda ctx: ctx.get('error_count', 0) > 0
                }
            else:
                agent = agent_class(
                    agent_id=uuid4(),
                    name=f"{config['name']}-{self.name}",
                    role=config['role'],
                    capabilities=config['capabilities'],
                    llm_service=self.llm_service
                )
            
            # Add FileSystemTool to all agents
            fs_tool = FileSystemTool()
            agent.tools['filesystem'] = fs_tool
            
            # Register with runtime
            await self.runtime.register_agent(agent)
            await self.runtime.start_agent(agent)
            
            # Register with environment
            await self.adapter.register_agent(agent, namespace=f"mas/{config['role']}")
            
            # Set visibility
            self.environment.observability.set_visibility(
                str(agent.agent_id), 
                config['visibility']
            )
            
            # Allocate resources
            resources = {
                'cpu': 10 if config['role'] == 'developer' else 5,
                'memory': 512 * 1024 * 1024  # 512MB
            }
            
            success = self.environment.resource_manager.request_resources(
                str(agent.agent_id), 
                resources
            )
            
            if success:
                self.metrics['resources_allocated'] += 1
                logger.info(f"✅ Allocated resources for {config['name']}")
                
            self.metrics['agents_created'] += 1
            logger.info(f"✅ Created {config['name']} agent")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create {config['name']}: {e}")
            return None
            
    async def _environment_loop(self):
        """Update environment periodically"""
        while True:
            try:
                await self.environment.update(1.0)
                
                # Update agent contexts
                for agent in self.agents.values():
                    await self.adapter.update_agent_context(agent)
                    
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Environment update error: {e}")
                
    async def demonstrate_principles(self):
        """Demonstrate Ferber's MAS principles"""
        logger.info("\n" + "="*60)
        logger.info("🎯 DEMONSTRATING FERBER'S MAS PRINCIPLES")
        logger.info("="*60 + "\n")
        
        # 1. AGENTS - Autonomous entities
        logger.info("1️⃣ AGENTS - Autonomous Entities")
        for role, agent in self.agents.items():
            logger.info(f"  - {agent.name}: {agent.capabilities}")
            
        # 2. ENVIRONMENT - Software space
        logger.info("\n2️⃣ ENVIRONMENT - Software Space")
        env_state = self.environment.global_state
        logger.info(f"  - Topology: Process Tree")
        logger.info(f"  - Resources: CPU={env_state['resources']['cpu']['utilization']:.1f}%, "
                   f"Memory={env_state['resources']['memory']['used']/1024/1024:.1f}MB")
        logger.info(f"  - Entities: {len(self.environment.entities)}")
        
        # 3. INTERACTIONS - Agent communication
        logger.info("\n3️⃣ INTERACTIONS - Agent Communication")
        
        # Analyst sends analysis request
        analyst = self.agents['analyst']
        developer = self.agents['developer']
        
        await self.runtime.send_message(
            str(analyst.agent_id),
            str(developer.agent_id),
            {
                'type': 'analysis_result',
                'content': 'Requirements analyzed: Need REST API with authentication',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        self.metrics['messages_sent'] += 1
        logger.info("  ✅ Analyst → Developer: Analysis results sent")
        
        # Developer to Tester
        tester = self.agents['tester']
        await self.runtime.send_message(
            str(developer.agent_id),
            str(tester.agent_id),
            {
                'type': 'code_ready',
                'content': 'Implementation complete, ready for testing',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        self.metrics['messages_sent'] += 1
        logger.info("  ✅ Developer → Tester: Code ready notification")
        
        # 4. ORGANIZATION - Hierarchical structure
        logger.info("\n4️⃣ ORGANIZATION - Hierarchical Structure")
        coordinator = self.agents['coordinator']
        
        # Coordinator broadcasts to all
        for role, agent in self.agents.items():
            if role != 'coordinator':
                await self.runtime.send_message(
                    str(coordinator.agent_id),
                    str(agent.agent_id),
                    {
                        'type': 'coordination',
                        'content': 'Begin collaborative task',
                        'priority': 'high'
                    }
                )
                self.metrics['messages_sent'] += 1
                
        logger.info("  ✅ Coordinator broadcasted to all agents")
        
        # 5. EMERGENCE - Collective behavior
        logger.info("\n5️⃣ EMERGENCE - Collective Behavior")
        
        # Simulate emergent task completion
        task = "Build a user authentication system"
        logger.info(f"  Task: {task}")
        
        # Each agent contributes based on role
        contributions = {
            'analyst': "Analyzed requirements: JWT-based auth with refresh tokens",
            'developer': "Implemented auth endpoints and middleware",
            'tester': "Created unit and integration tests",
            'coordinator': "Orchestrated workflow and resolved conflicts"
        }
        
        for role, contribution in contributions.items():
            agent = self.agents[role]
            # Use filesystem tool to create artifact
            fs_tool = agent.tools['filesystem']
            
            result = await fs_tool.execute(
                action="write",
                file_path=f"{role}_contribution.txt",
                content=contribution
            )
            
            if result.success:
                logger.info(f"  ✅ {role.capitalize()}: {contribution}")
                
        self.metrics['tasks_processed'] += 1
        
        # Show partial observability
        logger.info("\n📊 Partial Observability:")
        for role, agent in self.agents.items():
            perception = self.environment.perceive(str(agent.agent_id))
            visible_entities = len(perception.get('entities', {}))
            logger.info(f"  - {role.capitalize()} can see {visible_entities} other agents")
            
        # Show resource constraints
        logger.info("\n⚠️ Resource Constraints:")
        usage = self.environment.resource_manager.get_resource_usage()
        logger.info(f"  - CPU Usage: {usage['cpu']['utilization']:.1f}%")
        logger.info(f"  - Memory Available: {usage['memory']['available']/1024/1024:.1f}MB")
        
        # Environmental dynamics
        logger.info("\n🔄 Environmental Dynamics:")
        logger.info(f"  - System Load: {env_state['dynamics']['system_load']:.1f}%")
        logger.info(f"  - Events Logged: {len(self.environment.event_log)}")
        
    async def simulate_complex_scenario(self):
        """Simulate a complex multi-agent scenario"""
        logger.info("\n" + "="*60)
        logger.info("🎬 COMPLEX SCENARIO: Building a Microservice")
        logger.info("="*60 + "\n")
        
        # Phase 1: Analysis
        logger.info("📋 Phase 1: Requirements Analysis")
        analyst = self.agents['analyst']
        await analyst.receive_message({
            'type': 'task',
            'content': 'Analyze requirements for user microservice'
        })
        await asyncio.sleep(1)  # Simulate processing
        
        # Phase 2: Design & Implementation
        logger.info("\n🛠️ Phase 2: Design & Implementation")
        developer = self.agents['developer']
        await developer.receive_message({
            'type': 'implement',
            'requirements': 'User CRUD operations with PostgreSQL'
        })
        await asyncio.sleep(1)
        
        # Phase 3: Testing
        logger.info("\n🧪 Phase 3: Testing")
        tester = self.agents['tester']
        await tester.receive_message({
            'type': 'test',
            'target': 'user_service'
        })
        await asyncio.sleep(1)
        
        # Phase 4: Coordination
        logger.info("\n🎯 Phase 4: Final Coordination")
        coordinator = self.agents['coordinator']
        
        # Check system state
        context = {
            'cpu_usage': self.environment.global_state['resources']['cpu']['utilization'],
            'task_status': 'completed',
            'error_count': 0
        }
        
        # Evaluate rules
        for rule_name, rule_func in coordinator.rules.items():
            if rule_func(context):
                logger.info(f"  ⚡ Rule triggered: {rule_name}")
                
        self.metrics['tasks_processed'] += 1
        logger.info("\n✅ Complex scenario completed successfully!")
        
    async def cleanup(self):
        """Clean up resources"""
        logger.info("\n🧹 Cleaning up...")
        
        # Stop agents
        for agent in self.agents.values():
            await agent.stop()
            
        # Release resources
        # Simply clear entities as resource_manager doesn't have release_all
        self.environment.entities.clear()
            
        logger.info("✅ Cleanup complete")


async def main():
    """Main demonstration"""
    print("\n" + "="*80)
    print("🚀 SIMPLE MULTI-AGENT SYSTEM DEMONSTRATION")
    print("Demonstrating Ferber's Core Principles")
    print("="*80 + "\n")
    
    # Create and initialize MAS
    mas = SimpleMASDemo()
    await mas.initialize()
    
    # Demonstrate principles
    await mas.demonstrate_principles()
    
    # Simulate complex scenario
    await mas.simulate_complex_scenario()
    
    # Final metrics
    print("\n" + "="*60)
    print("📊 FINAL METRICS")
    print("="*60)
    print(f"  - Agents Created: {mas.metrics['agents_created']}")
    print(f"  - Tasks Processed: {mas.metrics['tasks_processed']}")
    print(f"  - Messages Sent: {mas.metrics['messages_sent']}")
    print(f"  - Resources Allocated: {mas.metrics['resources_allocated']}")
    print("\n✅ DEMONSTRATION COMPLETE!")
    print("="*80)
    
    # Cleanup
    await mas.cleanup()


if __name__ == "__main__":
    asyncio.run(main())