#!/usr/bin/env python3
"""
Simplified Complete Autonomous Multi-Agent System Demo
Demonstrating all Ferber's principles with all tools
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

# Import MAS components
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.tools.filesystem_tool import FileSystemTool
from src.tools.code_tool import CodeTool
from src.tools.git_tool import GitTool
from src.tools.web_search_tool import WebSearchTool
from src.tools.database_tool import DatabaseTool
from src.tools.http_tool import HTTPTool

# Import agents
from src.core.agents import CognitiveAgent, ReflexiveAgent, HybridAgent

# Import environment
from src.core.environment import (
    SoftwareEnvironment,
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
logger = get_logger("MAS_DEMO")


class CompleteMASDemo:
    """Complete Multi-Agent System with all features"""
    
    def __init__(self):
        self.id = uuid4()
        self.name = f"CompleteMAS-{str(self.id)[:8]}"
        
        # Services
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        self.runtime = get_agent_runtime()
        
        # Agents
        self.agents = {}
        
        # Environment
        self.environment = SoftwareEnvironment(TopologyType.PROCESS_TREE)
        self.adapter = EnvironmentAdapter(self.environment)
        
        # Workspace
        self.workspace = Path(f"/app/agent_workspace/mas_demo/{self.id}")
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Metrics
        self.metrics = {
            'agents_created': 0,
            'tasks_processed': 0,
            'tools_loaded': 0,
            'resources_allocated': 0
        }
        
    async def initialize(self):
        """Initialize the complete MAS system"""
        logger.info(f"🚀 Initializing {self.name}...")
        
        # Create specialized agents
        await self._create_agents()
        
        # Start environment dynamics
        asyncio.create_task(self._environment_loop())
        
        logger.info("✅ System initialized successfully!")
        
    async def _create_agents(self):
        """Create all specialized agents with tools"""
        agent_configs = [
            {
                'name': 'Architect',
                'type': CognitiveAgent,
                'role': 'architect',
                'capabilities': ['design', 'architecture', 'planning'],
                'tools': [FileSystemTool, CodeTool]
            },
            {
                'name': 'Analyst',
                'type': CognitiveAgent,
                'role': 'analyst',
                'capabilities': ['analysis', 'research', 'understanding'],
                'tools': [WebSearchTool, FileSystemTool]
            },
            {
                'name': 'Developer',
                'type': HybridAgent,
                'role': 'developer',
                'capabilities': ['coding', 'implementation', 'debugging'],
                'tools': [CodeTool, GitTool, FileSystemTool]
            },
            {
                'name': 'Tester',
                'type': HybridAgent,
                'role': 'tester',
                'capabilities': ['testing', 'validation', 'quality'],
                'tools': [CodeTool, FileSystemTool]
            },
            {
                'name': 'DevOps',
                'type': HybridAgent,
                'role': 'devops',
                'capabilities': ['deployment', 'automation', 'monitoring'],
                'tools': [GitTool, HTTPTool, FileSystemTool]
            },
            {
                'name': 'DataEngineer',
                'type': HybridAgent,
                'role': 'data_engineer',
                'capabilities': ['data_processing', 'etl', 'analytics'],
                'tools': [DatabaseTool, FileSystemTool]
            },
            {
                'name': 'Coordinator',
                'type': ReflexiveAgent,
                'role': 'coordinator',
                'capabilities': ['coordination', 'orchestration', 'monitoring'],
                'tools': [FileSystemTool]
            }
        ]
        
        for config in agent_configs:
            agent = await self._create_agent(config)
            if agent:
                self.agents[config['role']] = agent
                
        # Create agent network
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
            agent = agent_class(
                agent_id=uuid4(),
                name=f"{config['name']}-{self.name}",
                role=config['role'],
                capabilities=config['capabilities'],
                llm_service=self.llm_service
            )
            
            # Load tools
            for tool_class in config['tools']:
                # Different tools have different constructors
                if tool_class.__name__ == 'FileSystemTool':
                    tool = tool_class()
                else:
                    # Our custom tools accept these parameters
                    tool = tool_class(
                        agent_id=str(agent.agent_id),
                        workspace_root=str(self.workspace)
                    )
                agent.tools[tool.name] = tool
                self.metrics['tools_loaded'] += 1
                
            # Register with runtime
            await self.runtime.register_agent(agent)
            await self.runtime.start_agent(agent)
            
            # Register with environment
            await self.adapter.register_agent(agent, namespace=f"mas/{config['role']}")
            
            # Set visibility
            if isinstance(agent, CognitiveAgent):
                visibility = VisibilityLevel.FULL
            elif isinstance(agent, HybridAgent):
                visibility = VisibilityLevel.NAMESPACE
            else:
                visibility = VisibilityLevel.PROCESS
                
            self.environment.observability.set_visibility(
                str(agent.agent_id), 
                visibility
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
                
            self.metrics['agents_created'] += 1
            logger.info(f"✅ Created {config['name']} agent with {len(config['tools'])} tools")
            
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
                
    async def demonstrate_capabilities(self):
        """Demonstrate the complete MAS capabilities"""
        logger.info("\n" + "="*60)
        logger.info("🎯 DEMONSTRATING MAS CAPABILITIES")
        logger.info("="*60 + "\n")
        
        # 1. Code Analysis and Generation
        logger.info("1️⃣ Code Analysis and Generation")
        developer = self.agents['developer']
        code_tool = developer.tools.get('CodeTool')
        
        if code_tool:
            result = await code_tool.execute(
                action="generate",
                language="python",
                requirements={
                    "name": "calculator",
                    "description": "Simple calculator with basic operations",
                    "functions": [
                        {
                            "name": "add",
                            "args": ["a", "b"],
                            "description": "Add two numbers",
                            "body": "return a + b"
                        },
                        {
                            "name": "multiply",
                            "args": ["a", "b"],
                            "description": "Multiply two numbers",
                            "body": "return a * b"
                        }
                    ],
                    "main": True
                }
            )
            
            if result.success:
                logger.info(f"✅ Generated code saved to: {result.data['file_path']}")
            else:
                logger.error(f"❌ Code generation failed: {result.error}")
                
        # 2. Git Repository Management
        logger.info("\n2️⃣ Git Repository Management")
        devops = self.agents['devops']
        git_tool = devops.tools.get('GitTool')
        
        if git_tool:
            # Initialize repo
            result = await git_tool.execute(
                action="init",
                repository="demo_project"
            )
            
            if result.success:
                logger.info(f"✅ Git repository initialized: {result.data['path']}")
                
        # 3. Web Search Capability
        logger.info("\n3️⃣ Web Search and Analysis")
        analyst = self.agents['analyst']
        search_tool = analyst.tools.get('WebSearchTool')
        
        if search_tool:
            result = await search_tool.execute(
                action="search",
                query="multi-agent systems Ferber",
                limit=3
            )
            
            if result.success:
                logger.info(f"✅ Found {result.data['count']} search results")
                for r in result.data['results']:
                    logger.info(f"  - {r['title']}")
                    
        # 4. Database Operations
        logger.info("\n4️⃣ Database Operations")
        data_engineer = self.agents['data_engineer']
        db_tool = data_engineer.tools.get('DatabaseTool')
        
        if db_tool:
            # Connect to SQLite
            result = await db_tool.execute(
                action="connect",
                db_type="sqlite",
                connection={"path": str(self.workspace / "demo.db")}
            )
            
            if result.success:
                logger.info("✅ Connected to database")
                
                # Create table
                result = await db_tool.execute(
                    action="create_table",
                    db_type="sqlite",
                    table="agents",
                    schema={
                        "id": {"type": "INTEGER", "primary_key": True},
                        "name": {"type": "TEXT", "not_null": True},
                        "role": {"type": "TEXT"},
                        "created": {"type": "TIMESTAMP"}
                    }
                )
                
                if result.success:
                    logger.info("✅ Created agents table")
                    
        # 5. HTTP Client Operations
        logger.info("\n5️⃣ HTTP Client Operations")
        http_tool = devops.tools.get('HTTPTool')
        
        if http_tool:
            # Test API endpoint
            result = await http_tool.execute(
                method="GET",
                url="https://api.github.com",
                headers={"Accept": "application/json"}
            )
            
            if result.success:
                logger.info(f"✅ HTTP request successful: {result.data['status_code']}")
                
        # 6. Environment and Resource Status
        logger.info("\n6️⃣ Environment and Resource Management")
        env_state = self.environment.global_state
        resources = env_state['resources']
        
        logger.info("📊 Resource Usage:")
        logger.info(f"  - CPU: {resources['cpu']['utilization']:.1f}%")
        logger.info(f"  - Memory: {resources['memory']['used']/1024/1024:.1f}MB used")
        logger.info(f"  - Entities: {len(self.environment.entities)}")
        logger.info(f"  - Events: {len(self.environment.event_log)}")
        
        # 7. Agent Coordination
        logger.info("\n7️⃣ Agent Coordination and Communication")
        coordinator = self.agents['coordinator']
        
        # Send coordination message
        await coordinator.receive_message({
            'type': 'coordinate',
            'task': 'Review system status',
            'priority': 'high'
        })
        
        logger.info("✅ Coordination message sent")
        
        # 8. Metrics Summary
        logger.info("\n📊 System Metrics:")
        logger.info(f"  - Agents Created: {self.metrics['agents_created']}")
        logger.info(f"  - Tools Loaded: {self.metrics['tools_loaded']}")
        logger.info(f"  - Resources Allocated: {self.metrics['resources_allocated']}")
        
        self.metrics['tasks_processed'] += 7
        
    async def process_complex_task(self, task: str):
        """Process a complex task using the MAS"""
        logger.info(f"\n🔧 Processing Complex Task: {task}")
        
        # 1. Analysis phase
        analyst = self.agents['analyst']
        await analyst.receive_message({
            'type': 'analyze',
            'content': task
        })
        
        # 2. Design phase
        architect = self.agents['architect']
        await architect.receive_message({
            'type': 'design',
            'requirements': task
        })
        
        # 3. Implementation phase
        developer = self.agents['developer']
        await developer.receive_message({
            'type': 'implement',
            'specification': task
        })
        
        # 4. Testing phase
        tester = self.agents['tester']
        await tester.receive_message({
            'type': 'test',
            'implementation': task
        })
        
        # 5. Deployment phase
        devops = self.agents['devops']
        await devops.receive_message({
            'type': 'deploy',
            'artifact': task
        })
        
        self.metrics['tasks_processed'] += 1
        logger.info("✅ Complex task processed through all phases")
        
    async def cleanup(self):
        """Clean up resources"""
        logger.info("\n🧹 Cleaning up...")
        
        # Stop agents
        for agent in self.agents.values():
            await agent.stop()
            
        # Release resources
        for entity_id in list(self.environment.entities.keys()):
            self.environment.resource_manager.release_all(entity_id)
            
        logger.info("✅ Cleanup complete")


async def main():
    """Main demonstration"""
    print("\n" + "="*80)
    print("🚀 COMPLETE MULTI-AGENT SYSTEM DEMONSTRATION")
    print("With All Tools and Ferber's Principles")
    print("="*80 + "\n")
    
    # Create and initialize MAS
    mas = CompleteMASDemo()
    await mas.initialize()
    
    # Demonstrate capabilities
    await mas.demonstrate_capabilities()
    
    # Process a complex task
    await mas.process_complex_task(
        "Create a REST API with database integration and automated testing"
    )
    
    # Final status
    print("\n" + "="*60)
    print("✅ DEMONSTRATION COMPLETE!")
    print(f"Total Tasks Processed: {mas.metrics['tasks_processed']}")
    print("="*60)
    
    # Cleanup
    await mas.cleanup()


if __name__ == "__main__":
    asyncio.run(main())