"""
Agent Runtime - Manages agent lifecycle and execution
Provides a centralized runtime for all agents in the MAS
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from uuid import UUID
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global runtime instance
_runtime_instance: Optional['AgentRuntime'] = None

class AgentRuntime:
    """
    Centralized runtime for managing agent lifecycle
    Handles agent registration, startup, communication, and shutdown
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self.running_agents: Set[str] = set()
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.environment = None  # Will be set when integrated with environment
        self._started = False
        
        logger.info("Agent runtime initialized")
        
    async def register_agent(self, agent: Any) -> bool:
        """Register an agent with the runtime"""
        agent_id = str(agent.agent_id) if hasattr(agent, 'agent_id') else str(agent.id)
        
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} already registered")
            return False
            
        self.agents[agent_id] = agent
        self.message_queues[agent_id] = asyncio.Queue()
        
        logger.info(f"Agent {agent.name} ({agent_id}) registered with runtime")
        return True
        
    async def start_agent(self, agent: Any) -> bool:
        """Start an agent's execution"""
        agent_id = str(agent.agent_id) if hasattr(agent, 'agent_id') else str(agent.id)
        
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not registered")
            return False
            
        if agent_id in self.running_agents:
            logger.warning(f"Agent {agent_id} already running")
            return False
            
        try:
            # Create agent task
            if hasattr(agent, 'run'):
                task = asyncio.create_task(agent.run())
                self.agent_tasks[agent_id] = task
                self.running_agents.add(agent_id)
                logger.info(f"Started agent {agent.name} ({agent_id})")
                return True
            else:
                logger.error(f"Agent {agent_id} has no run method")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {e}")
            return False
            
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent"""
        agent_id = str(agent_id)
        
        if agent_id not in self.running_agents:
            logger.warning(f"Agent {agent_id} not running")
            return False
            
        try:
            # Stop the agent
            agent = self.agents.get(agent_id)
            if agent and hasattr(agent, 'stop'):
                await agent.stop()
                
            # Cancel the task
            if agent_id in self.agent_tasks:
                task = self.agent_tasks[agent_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.agent_tasks[agent_id]
                
            self.running_agents.remove(agent_id)
            logger.info(f"Stopped agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
            
    async def send_message(self, from_agent: str, to_agent: str, message: Any):
        """Send a message between agents"""
        to_agent = str(to_agent)
        
        if to_agent not in self.agents:
            logger.error(f"Target agent {to_agent} not found")
            return False
            
        try:
            # Add message to target's queue
            await self.message_queues[to_agent].put({
                'from': from_agent,
                'to': to_agent,
                'message': message,
                'timestamp': datetime.utcnow()
            })
            
            # If agent has receive_message method, call it
            agent = self.agents[to_agent]
            if hasattr(agent, 'receive_message'):
                await agent.receive_message(message)
                
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get an agent by ID"""
        return self.agents.get(str(agent_id))
        
    def list_agents(self) -> List[Any]:
        """List all registered agents"""
        return list(self.agents.values())
        
    def list_running_agents(self) -> List[str]:
        """List IDs of running agents"""
        return list(self.running_agents)
        
    async def broadcast_message(self, from_agent: str, message: Any, filter_func=None):
        """Broadcast a message to multiple agents"""
        tasks = []
        for agent_id, agent in self.agents.items():
            if agent_id == from_agent:
                continue
            if filter_func and not filter_func(agent):
                continue
            tasks.append(self.send_message(from_agent, agent_id, message))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def shutdown(self):
        """Shutdown the runtime and all agents"""
        logger.info("Shutting down agent runtime...")
        
        # Stop all running agents
        agent_ids = list(self.running_agents)
        for agent_id in agent_ids:
            await self.stop_agent(agent_id)
            
        # Clear registrations
        self.agents.clear()
        self.message_queues.clear()
        
        logger.info("Agent runtime shutdown complete")
        
    def set_environment(self, environment):
        """Set the environment for agent integration"""
        self.environment = environment
        logger.info("Environment set for runtime")
        
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status information for an agent"""
        agent_id = str(agent_id)
        agent = self.agents.get(agent_id)
        
        if not agent:
            return {'status': 'not_found'}
            
        return {
            'id': agent_id,
            'name': getattr(agent, 'name', 'Unknown'),
            'role': getattr(agent, 'role', 'Unknown'),
            'running': agent_id in self.running_agents,
            'capabilities': getattr(agent, 'capabilities', []),
            'messages_pending': self.message_queues[agent_id].qsize()
        }
        
    async def wait_for_agents(self, timeout: Optional[float] = None):
        """Wait for all running agents to complete"""
        if not self.agent_tasks:
            return
            
        tasks = list(self.agent_tasks.values())
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for agents to complete")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get runtime metrics"""
        return {
            'total_agents': len(self.agents),
            'running_agents': len(self.running_agents),
            'total_messages': sum(q.qsize() for q in self.message_queues.values()),
            'agents': {
                agent_id: self.get_agent_status(agent_id)
                for agent_id in self.agents
            }
        }

def get_agent_runtime() -> AgentRuntime:
    """Get or create the global agent runtime instance"""
    global _runtime_instance
    
    if _runtime_instance is None:
        _runtime_instance = AgentRuntime()
        
    return _runtime_instance

def reset_runtime():
    """Reset the global runtime (mainly for testing)"""
    global _runtime_instance
    _runtime_instance = None