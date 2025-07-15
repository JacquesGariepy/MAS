"""
Base agent implementation with complete BDI architecture
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass, field

from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger(__name__)

@dataclass
class BDI:
    """Beliefs-Desires-Intentions model"""
    beliefs: Dict[str, Any] = field(default_factory=dict)
    desires: List[str] = field(default_factory=list)
    intentions: List[str] = field(default_factory=list)

@dataclass
class AgentContext:
    """Agent execution context"""
    agent_id: UUID
    environment: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    working_memory: List[Any] = field(default_factory=list)
    current_task: Optional[Any] = None

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[LLMService] = None,
        **kwargs
    ):
        self.agent_id = agent_id  # Add agent_id attribute
        self.id = agent_id  # Keep for compatibility
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.llm_service = llm_service
        
        # BDI model
        self.bdi = BDI(
            beliefs=kwargs.get('initial_beliefs', {}),
            desires=kwargs.get('initial_desires', []),
            intentions=[]
        )
        
        # Execution context
        self.context = AgentContext(agent_id=agent_id)
        
        # Tools
        self.tool_service = ToolService()
        self.tools = {}
        self._load_tools()
        
        # Runtime state
        self._running = False
        self._tasks = asyncio.Queue()
        self._message_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            "actions_executed": 0,
            "messages_processed": 0,
            "tasks_completed": 0,
            "errors": 0,
            "start_time": None,
            "total_runtime": 0
        }
    
    def _load_tools(self):
        """Load tools based on capabilities"""
        for capability in self.capabilities:
            tools = self.tool_service.get_tools_for_capability(capability)
            self.tools.update(tools)
    
    @abstractmethod
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment and extract relevant information"""
        pass
    
    @abstractmethod
    async def deliberate(self) -> List[str]:
        """Deliberate and form intentions based on beliefs and desires"""
        pass
    
    @abstractmethod
    async def act(self) -> List[Dict[str, Any]]:
        """Execute actions based on intentions"""
        pass
    
    async def update_beliefs(self, new_beliefs: Dict[str, Any]):
        """Update agent's beliefs"""
        self.bdi.beliefs.update(new_beliefs)
        logger.debug(f"Agent {self.name} updated beliefs: {new_beliefs}")
    
    async def add_desire(self, desire: str):
        """Add a new desire/goal"""
        if desire not in self.bdi.desires:
            self.bdi.desires.append(desire)
            logger.debug(f"Agent {self.name} added desire: {desire}")
    
    async def commit_to_intention(self, intention: str):
        """Commit to an intention"""
        if intention not in self.bdi.intentions:
            self.bdi.intentions.append(intention)
            logger.debug(f"Agent {self.name} committed to intention: {intention}")
    
    async def drop_intention(self, intention: str):
        """Drop an intention"""
        if intention in self.bdi.intentions:
            self.bdi.intentions.remove(intention)
            logger.debug(f"Agent {self.name} dropped intention: {intention}")
    
    async def run(self):
        """Main agent execution loop"""
        self._running = True
        self.metrics["start_time"] = datetime.utcnow()
        
        logger.info(f"Agent {self.name} starting...")
        
        try:
            while self._running:
                # Check for messages
                await self._process_messages()
                
                # Check for tasks
                await self._process_tasks()
                
                # BDI cycle
                await self._bdi_cycle()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in agent {self.name} loop: {str(e)}")
            self.metrics["errors"] += 1
            raise
        finally:
            runtime = datetime.utcnow() - self.metrics["start_time"]
            self.metrics["total_runtime"] += runtime.total_seconds()
            logger.info(f"Agent {self.name} stopped")
    
    async def _bdi_cycle(self):
        """Execute one BDI cycle"""
        try:
            # Perceive
            perceptions = await self.perceive(self.context.environment)
            await self.update_beliefs(perceptions)
            
            # Deliberate
            new_intentions = await self.deliberate()
            for intention in new_intentions:
                await self.commit_to_intention(intention)
            
            # Act
            if self.bdi.intentions:
                actions = await self.act()
                for action in actions:
                    await self._execute_action(action)
                    
        except Exception as e:
            logger.error(f"Error in BDI cycle for agent {self.name}: {str(e)}")
            self.metrics["errors"] += 1
    
    async def _execute_action(self, action: Dict[str, Any]):
        """Execute a single action"""
        action_type = action.get("type")
        
        if action_type == "tool_call":
            await self._execute_tool_call(action)
        elif action_type == "send_message":
            await self._send_message(action)
        elif action_type == "update_belief":
            await self.update_beliefs(action.get("beliefs", {}))
        else:
            logger.warning(f"Unknown action type: {action_type}")
        
        self.metrics["actions_executed"] += 1
    
    async def _execute_tool_call(self, action: Dict[str, Any]):
        """Execute a tool call"""
        tool_name = action.get("tool")
        params = action.get("params", {})
        
        if tool_name not in self.tools:
            logger.error(f"Tool {tool_name} not found")
            return
        
        try:
            tool = self.tools[tool_name]
            result = await tool.execute(params)
            
            # Update beliefs with result
            await self.update_beliefs({
                f"last_{tool_name}_result": result.data,
                f"last_{tool_name}_success": result.success
            })
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            await self.update_beliefs({
                f"last_{tool_name}_error": str(e)
            })
    
    async def _send_message(self, action: Dict[str, Any]):
        """Send a message to another agent"""
        # Implementation depends on messaging system
        pass
    
    async def _process_messages(self):
        """Process incoming messages"""
        while not self._message_queue.empty():
            message = await self._message_queue.get()
            try:
                await self.handle_message(message)
                self.metrics["messages_processed"] += 1
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                self.metrics["errors"] += 1
    
    async def _process_tasks(self):
        """Process assigned tasks"""
        while not self._tasks.empty():
            task = await self._tasks.get()
            self.context.current_task = task
            try:
                await self.handle_task(task)
                self.metrics["tasks_completed"] += 1
            except Exception as e:
                logger.error(f"Error processing task: {str(e)}")
                self.metrics["errors"] += 1
            finally:
                self.context.current_task = None
    
    @abstractmethod
    async def handle_message(self, message: Any):
        """Handle incoming message"""
        pass
    
    @abstractmethod
    async def handle_task(self, task: Any):
        """Handle assigned task"""
        pass
    
    async def receive_message(self, message: Any):
        """Receive a message (called by environment)"""
        await self._message_queue.put(message)
    
    async def add_task(self, task: Any):
        """Add a task to the agent's queue"""
        await self._tasks.put(task)
    
    async def stop(self):
        """Stop agent execution"""
        self._running = False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            **self.metrics,
            "current_beliefs": len(self.bdi.beliefs),
            "current_desires": len(self.bdi.desires),
            "current_intentions": len(self.bdi.intentions),
            "available_tools": len(self.tools),
            "working_memory_size": len(self.context.working_memory)
        }
    
    async def update_configuration(self, config: Dict[str, Any]):
        """Update agent configuration at runtime"""
        # Update relevant configuration
        if "capabilities" in config:
            self.capabilities = config["capabilities"]
            self._load_tools()
        
        # Allow subclasses to handle specific updates
        await self._handle_config_update(config)
    
    async def _handle_config_update(self, config: Dict[str, Any]):
        """Handle configuration updates (override in subclasses)"""
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} ({self.role})>"