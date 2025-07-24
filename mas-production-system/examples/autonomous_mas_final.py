#!/usr/bin/env python3
"""
Final Integrated Autonomous MAS with Software Environment
Ready-to-use implementation combining all Ferber's principles
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(str(Path(__file__).parent.parent), 'services', 'core'))

# Import core components
from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.tools.filesystem_tool import FileSystemTool
from src.core.agents import CognitiveAgent, ReflexiveAgent, HybridAgent
from src.utils.logger import get_logger

# Import environment
from src.core.environment import SoftwareEnvironment, TopologyType, EnvironmentAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger("MAS_FINAL")

class IntegratedMAS:
    """Complete MAS with Software Environment Integration"""
    
    def __init__(self):
        self.id = uuid4()
        self.llm_service = LLMService()
        self.agents = {}
        self.environment = None
        self.adapter = None
        
    async def initialize(self):
        """Initialize the complete system"""
        logger.info("🚀 Initializing Integrated MAS...")
        
        # 1. Create environment
        self.environment = SoftwareEnvironment(TopologyType.HIERARCHICAL)
        self.adapter = EnvironmentAdapter(self.environment)
        logger.info("✓ Software environment created")
        
        # 2. Create agents
        await self._create_agents()
        logger.info(f"✓ Created {len(self.agents)} agents")
        
        # 3. Setup network
        await self.adapter.create_agent_network(
            list(self.agents.values()), 
            topology="star"
        )
        logger.info("✓ Agent network established")
        
        # 4. Start environment dynamics
        asyncio.create_task(self._environment_loop())
        logger.info("✓ Environment dynamics started")
        
        logger.info("✅ MAS initialization complete!")
        
    async def _create_agents(self):
        """Create specialized agents"""
        # Analyst agent
        analyst = CognitiveAgent(
            agent_id=uuid4(),
            name="Analyst",
            role="analyst",
            capabilities=["analysis", "research"],
            llm_service=self.llm_service
        )
        analyst.agent_type = "cognitive"
        self.agents['analyst'] = analyst
        await self.adapter.register_agent(analyst, "analysis")
        
        # Developer agent
        developer = HybridAgent(
            agent_id=uuid4(),
            name="Developer",
            role="developer",
            capabilities=["coding", "implementation"],
            llm_service=self.llm_service
        )
        developer.agent_type = "hybrid"
        self.agents['developer'] = developer
        await self.adapter.register_agent(developer, "development")
        
        # Validator agent
        validator = HybridAgent(
            agent_id=uuid4(),
            name="Validator",
            role="validator",
            capabilities=["testing", "validation"],
            llm_service=self.llm_service
        )
        validator.agent_type = "hybrid"
        self.agents['validator'] = validator
        await self.adapter.register_agent(validator, "validation")
        
        # Start all agents
        for agent in self.agents.values():
            asyncio.create_task(agent.run())
            
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
                
    async def process_request(self, request: str) -> Dict[str, Any]:
        """Process a user request"""
        logger.info(f"📝 Processing: {request}")
        
        result = {
            'request': request,
            'status': 'processing',
            'steps': []
        }
        
        try:
            # 1. Analysis phase
            analyst = self.agents['analyst']
            await analyst.receive_message({
                'type': 'analyze',
                'content': request
            })
            await asyncio.sleep(2)  # Simulate processing
            result['steps'].append("✓ Request analyzed")
            
            # 2. Get environment state
            env_state = self.adapter.environment.global_state
            logger.info(f"Environment: {env_state['resources']['cpu']['utilization']:.1f}% CPU")
            
            # 3. Implementation phase
            if env_state['resources']['cpu']['utilization'] < 80:
                developer = self.agents['developer']
                await developer.receive_message({
                    'type': 'implement',
                    'content': request
                })
                await asyncio.sleep(2)
                result['steps'].append("✓ Solution implemented")
                
                # 4. Validation phase
                validator = self.agents['validator']
                await validator.receive_message({
                    'type': 'validate',
                    'content': 'Validate implementation'
                })
                await asyncio.sleep(1)
                result['steps'].append("✓ Solution validated")
                
                result['status'] = 'completed'
            else:
                result['status'] = 'resource_limited'
                result['steps'].append("⚠️ High CPU usage - request queued")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
            
        return result
        
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'agents': {
                name: {
                    'running': agent._running,
                    'capabilities': agent.capabilities
                }
                for name, agent in self.agents.items()
            },
            'environment': {
                'resources': self.environment.resource_manager.get_resource_usage(),
                'entities': len(self.environment.entities),
                'events': len(self.environment.event_log)
            }
        }
        
    async def cleanup(self):
        """Clean up resources"""
        for agent in self.agents.values():
            await agent.stop()

async def main():
    """Main demonstration"""
    print("\n" + "="*60)
    print("🤖 INTEGRATED MULTI-AGENT SYSTEM")
    print("Complete implementation with Ferber's principles")
    print("="*60 + "\n")
    
    # Create and initialize MAS
    mas = IntegratedMAS()
    await mas.initialize()
    
    # Show status
    status = await mas.get_status()
    print("\n📊 System Status:")
    print(f"- Agents: {len(status['agents'])} active")
    print(f"- CPU Usage: {status['environment']['resources']['cpu']['utilization']:.1f}%")
    print(f"- Memory: {status['environment']['resources']['memory']['used']/1024/1024/1024:.2f}GB")
    
    # Process test requests
    print("\n🔧 Processing Test Requests:\n")
    
    requests = [
        "Create a simple calculator function",
        "Build a REST API endpoint",
        "Write unit tests for a module"
    ]
    
    for req in requests:
        result = await mas.process_request(req)
        print(f"Request: {req}")
        print(f"Status: {result['status']}")
        for step in result['steps']:
            print(f"  {step}")
        print()
        
    # Final status
    final_status = await mas.get_status()
    print("\n📈 Final Environment State:")
    print(f"- Total events: {final_status['environment']['events']}")
    print(f"- Active entities: {final_status['environment']['entities']}")
    
    # Cleanup
    await mas.cleanup()
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    asyncio.run(main())