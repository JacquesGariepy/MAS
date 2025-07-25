"""
Reflexive Agent implementation - rule-based reactive behavior
"""

from typing import Dict, List, Any, Optional
from uuid import UUID

from src.core.agents.base_agent import BaseAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ReflexiveAgent(BaseAgent):
    """
    Reflexive agent that responds to stimuli with predefined rules
    No deliberation or planning, just stimulus-response patterns
    """
    
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[Any] = None,
        reactive_rules: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(agent_id, name, role, capabilities, llm_service, **kwargs)
        
        # Reactive rules define stimulus-response patterns
        self.reactive_rules = reactive_rules or {}
        
        # Rule format: 
        # {
        #   "condition": {"type": "message", "performative": "request"},
        #   "action": {"type": "respond", "performative": "inform"}
        # }
        
        logger.info(f"Initialized reflexive agent {name} with {len(self.reactive_rules)} rules")
    
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment and extract relevant stimuli"""
        stimuli = {
            "messages": environment.get("messages", []),
            "events": environment.get("events", []),
            "state_changes": environment.get("state_changes", [])
        }
        
        logger.debug(f"Agent {self.name} perceived stimuli: {len(stimuli['messages'])} messages")
        return stimuli
    
    async def decide(self, perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make decisions based on reactive rules"""
        actions = []
        
        # Check messages against rules
        for message in perception.get("messages", []):
            for rule_name, rule in self.reactive_rules.items():
                if self._match_rule(message, rule.get("condition", {})):
                    action = self._create_action(rule.get("action", {}), message)
                    if action:
                        actions.append(action)
                        logger.debug(f"Agent {self.name} triggered rule {rule_name}")
        
        # Check events against rules
        for event in perception.get("events", []):
            for rule_name, rule in self.reactive_rules.items():
                if self._match_rule(event, rule.get("condition", {})):
                    action = self._create_action(rule.get("action", {}), event)
                    if action:
                        actions.append(action)
        
        return actions
    
    def _match_rule(self, stimulus: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if a stimulus matches a rule condition"""
        for key, value in condition.items():
            if key not in stimulus:
                return False
            
            # Handle nested conditions
            if isinstance(value, dict) and isinstance(stimulus[key], dict):
                if not self._match_rule(stimulus[key], value):
                    return False
            elif stimulus[key] != value:
                return False
        
        return True
    
    def _create_action(self, action_template: Dict[str, Any], stimulus: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an action from a template"""
        if not action_template:
            return None
        
        action = action_template.copy()
        
        # Substitute variables from stimulus
        if "content" in action and isinstance(action["content"], str):
            # Simple template substitution
            for key, value in stimulus.items():
                action["content"] = action["content"].replace(f"{{{key}}}", str(value))
        
        # Add stimulus reference
        action["in_response_to"] = stimulus.get("id")
        
        return action
    
    async def execute_action(self, action: Dict[str, Any], db_session: Any = None) -> bool:
        """Execute a single action"""
        action_type = action.get("type", "unknown")
        
        try:
            if action_type == "respond":
                # Send a response message
                await self._send_message(
                    receiver_id=action.get("receiver_id"),
                    performative=action.get("performative", "inform"),
                    content=action.get("content", {}),
                    in_reply_to=action.get("in_response_to")
                )
                
            elif action_type == "update_state":
                # Update internal state
                state_update = action.get("state_update", {})
                for key, value in state_update.items():
                    if key == "beliefs":
                        self.beliefs.update(value)
                    elif key == "status":
                        self.status = value
                
            elif action_type == "trigger_event":
                # Trigger an event
                event_data = action.get("event", {})
                await self._publish_event(event_data.get("name"), event_data.get("data"))
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
            
            self.metrics["total_actions"] += 1
            self.metrics["successful_actions"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute action {action_type}: {e}")
            self.metrics["total_actions"] += 1
            return False
    
    async def _send_message(self, receiver_id: UUID, performative: str, content: Any, in_reply_to: Optional[UUID] = None):
        """Send a message to another agent"""
        # This would integrate with the message broker
        logger.info(f"Agent {self.name} sending {performative} message to {receiver_id}")
        
        # Update metrics
        self.metrics["messages_sent"] = self.metrics.get("messages_sent", 0) + 1
    
    async def _publish_event(self, event_name: str, event_data: Any):
        """Publish an event"""
        logger.info(f"Agent {self.name} publishing event {event_name}")
        
        # Update metrics
        self.metrics["events_published"] = self.metrics.get("events_published", 0) + 1
    
    def add_rule(self, rule_name: str, condition: Dict[str, Any], action: Dict[str, Any]):
        """Add a new reactive rule"""
        self.reactive_rules[rule_name] = {
            "condition": condition,
            "action": action
        }
        logger.info(f"Added rule {rule_name} to agent {self.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a reactive rule"""
        if rule_name in self.reactive_rules:
            del self.reactive_rules[rule_name]
            logger.info(f"Removed rule {rule_name} from agent {self.name}")
    
    async def learn(self, feedback: Dict[str, Any]):
        """Reflexive agents don't learn - they only follow rules"""
        logger.debug(f"Reflexive agent {self.name} received feedback but doesn't learn")
    
    async def deliberate(self) -> List[str]:
        """Reflexive agents don't deliberate - they react immediately"""
        # For reflexive agents, intentions are formed from active rules
        intentions = []
        for rule_name in self.reactive_rules:
            intentions.append(f"execute_rule_{rule_name}")
        return intentions
    
    async def act(self) -> List[Dict[str, Any]]:
        """Execute actions based on current stimuli and rules"""
        # Get current perception
        perception = await self.perceive(self.context.environment)
        
        # Decide based on rules
        actions = await self.decide(perception)
        
        return actions
    
    async def handle_message(self, message: Any):
        """Handle incoming message by adding to environment"""
        if "messages" not in self.context.environment:
            self.context.environment["messages"] = []
        self.context.environment["messages"].append(message)
        
        # Update metrics
        self.metrics["messages_processed"] = self.metrics.get("messages_processed", 0) + 1
        logger.debug(f"Reflexive agent {self.name} received message")
    
    async def handle_task(self, task: Any):
        """Handle assigned task by converting to stimulus"""
        if "tasks" not in self.context.environment:
            self.context.environment["tasks"] = []
        self.context.environment["tasks"].append(task)
        
        # Update metrics
        self.metrics["tasks_assigned"] = self.metrics.get("tasks_assigned", 0) + 1
        logger.debug(f"Reflexive agent {self.name} received task")