"""
Reflexive agent with stimulus-response behavior
"""

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime

from src.core.agents.base_agent import BaseAgent
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ReflexiveAgent(BaseAgent):
    """Reflexive agent that responds immediately to stimuli without deliberation"""
    
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[LLMService] = None,
        **kwargs
    ):
        # Reflexive agents don't need LLM for simple rule-based reactions
        super().__init__(agent_id, name, role, capabilities, llm_service, **kwargs)
        
        # Reactive rules define stimulus-response mappings
        self.reactive_rules = kwargs.get('reactive_rules', {})
        
        # Response time tracking
        self.response_threshold_ms = kwargs.get('response_threshold_ms', 100)
        
        # Rule priorities (higher priority rules execute first)
        self.rule_priorities = kwargs.get('rule_priorities', {})
        
        # Simple state for rule conditions
        self.reactive_state = {
            "last_stimulus": None,
            "stimulus_count": 0,
            "active_responses": []
        }
        
        # Performance metrics specific to reflexive behavior
        self.reflex_metrics = {
            "total_stimuli": 0,
            "total_responses": 0,
            "average_response_time_ms": 0,
            "rules_triggered": {},
            "fastest_response_ms": float('inf'),
            "slowest_response_ms": 0
        }
        
        # Initialize default reactive rules
        self._initialize_default_rules()
        
        logger.info(f"Initialized reflexive agent {name} with {len(self.reactive_rules)} rules")
    
    def _initialize_default_rules(self):
        """Initialize default reactive rules based on role"""
        
        # Add default rules based on capabilities
        if "emergency_response" in self.capabilities:
            self.reactive_rules["emergency_stop"] = {
                "condition": lambda s: s.get("type") == "emergency" and s.get("severity", 0) > 8,
                "action": {"type": "stop_all", "broadcast": True},
                "priority": 100
            }
        
        if "monitoring" in self.capabilities:
            self.reactive_rules["threshold_alert"] = {
                "condition": lambda s: s.get("type") == "metric" and s.get("value", 0) > s.get("threshold", 100),
                "action": {"type": "alert", "level": "warning"},
                "priority": 50
            }
        
        if "communication" in self.capabilities:
            self.reactive_rules["acknowledge_message"] = {
                "condition": lambda s: s.get("type") == "message" and s.get("requires_ack", False),
                "action": {"type": "send_ack", "content": "Message received"},
                "priority": 20
            }
    
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Simple perception - extract immediate stimuli"""
        
        start_time = datetime.utcnow()
        
        # Extract relevant stimuli from environment
        stimuli = {
            "timestamp": start_time.isoformat(),
            "raw_stimuli": []
        }
        
        # Check for messages
        if "messages" in environment:
            for msg in environment["messages"]:
                stimuli["raw_stimuli"].append({
                    "type": "message",
                    "source": msg.get("sender"),
                    "content": msg.get("content"),
                    "performative": msg.get("performative"),
                    "requires_ack": msg.get("requires_ack", False),
                    "id": msg.get("id")
                })
        
        # Check for events
        if "events" in environment:
            for event in environment["events"]:
                stimuli["raw_stimuli"].append({
                    "type": "event",
                    "name": event.get("name"),
                    "data": event.get("data"),
                    "severity": event.get("severity", 0)
                })
        
        # Check for sensor data
        if "sensors" in environment:
            for sensor_name, sensor_data in environment["sensors"].items():
                stimuli["raw_stimuli"].append({
                    "type": "sensor",
                    "sensor": sensor_name,
                    "value": sensor_data.get("value"),
                    "threshold": sensor_data.get("threshold"),
                    "unit": sensor_data.get("unit")
                })
        
        # Check for direct commands
        if "commands" in environment:
            for cmd in environment["commands"]:
                stimuli["raw_stimuli"].append({
                    "type": "command",
                    "action": cmd.get("action"),
                    "params": cmd.get("params", {}),
                    "priority": cmd.get("priority", 0)
                })
        
        # Update metrics
        self.reflex_metrics["total_stimuli"] += len(stimuli["raw_stimuli"])
        self.reactive_state["stimulus_count"] += len(stimuli["raw_stimuli"])
        
        return stimuli
    
    async def deliberate(self) -> List[str]:
        """Reflexive agents don't deliberate - immediate rule matching only"""
        
        # For reflexive agents, we return immediate intentions based on active rules
        # No complex reasoning or planning
        
        intentions = []
        
        # Check if any high-priority rules are waiting to fire
        for rule_name, rule in sorted(
            self.reactive_rules.items(), 
            key=lambda x: self.rule_priorities.get(x[0], 0),
            reverse=True
        ):
            if self.reactive_state.get(f"pending_{rule_name}"):
                intentions.append(f"execute_rule_{rule_name}")
        
        return intentions
    
    async def act(self) -> List[Dict[str, Any]]:
        """Generate immediate actions based on stimuli and rules"""
        
        start_time = datetime.utcnow()
        actions = []
        
        # Get the last perceived stimuli
        if not self.reactive_state["last_stimulus"]:
            return actions
        
        stimuli = self.reactive_state["last_stimulus"]
        
        # Sort rules by priority
        sorted_rules = sorted(
            self.reactive_rules.items(),
            key=lambda x: self.rule_priorities.get(x[0], 0),
            reverse=True
        )
        
        # Check each stimulus against rules
        for stimulus in stimuli.get("raw_stimuli", []):
            for rule_name, rule in sorted_rules:
                # Check if rule condition matches
                condition = rule.get("condition")
                
                if condition:
                    # Evaluate condition
                    matches = False
                    
                    if callable(condition):
                        # Lambda or function condition
                        try:
                            matches = condition(stimulus)
                        except Exception as e:
                            logger.error(f"Error evaluating rule {rule_name}: {str(e)}")
                    elif isinstance(condition, dict):
                        # Dictionary condition matching
                        matches = self._match_dict_condition(stimulus, condition)
                    
                    if matches:
                        # Create action from rule
                        action = self._create_reflex_action(rule.get("action", {}), stimulus)
                        
                        if action:
                            action["rule"] = rule_name
                            action["stimulus_id"] = stimulus.get("id")
                            actions.append(action)
                            
                            # Update metrics
                            if rule_name not in self.reflex_metrics["rules_triggered"]:
                                self.reflex_metrics["rules_triggered"][rule_name] = 0
                            self.reflex_metrics["rules_triggered"][rule_name] += 1
                            
                            # Only fire first matching rule per stimulus (unless specified)
                            if not rule.get("continue_matching", False):
                                break
        
        # Calculate response time
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Update performance metrics
        self.reflex_metrics["total_responses"] += len(actions)
        if response_time_ms < self.reflex_metrics["fastest_response_ms"]:
            self.reflex_metrics["fastest_response_ms"] = response_time_ms
        if response_time_ms > self.reflex_metrics["slowest_response_ms"]:
            self.reflex_metrics["slowest_response_ms"] = response_time_ms
        
        # Update average response time
        total_responses = self.reflex_metrics["total_responses"]
        if total_responses > 0:
            avg_time = self.reflex_metrics["average_response_time_ms"]
            self.reflex_metrics["average_response_time_ms"] = (
                (avg_time * (total_responses - len(actions)) + response_time_ms * len(actions)) 
                / total_responses
            )
        
        # Clear processed stimulus
        self.reactive_state["last_stimulus"] = None
        
        return actions
    
    def _match_dict_condition(self, stimulus: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match stimulus against dictionary condition"""
        
        for key, expected_value in condition.items():
            stimulus_value = stimulus.get(key)
            
            # Handle special operators
            if isinstance(expected_value, dict) and len(expected_value) == 1:
                operator, value = list(expected_value.items())[0]
                
                if operator == "$gt":
                    if not (stimulus_value and stimulus_value > value):
                        return False
                elif operator == "$lt":
                    if not (stimulus_value and stimulus_value < value):
                        return False
                elif operator == "$gte":
                    if not (stimulus_value and stimulus_value >= value):
                        return False
                elif operator == "$lte":
                    if not (stimulus_value and stimulus_value <= value):
                        return False
                elif operator == "$eq":
                    if stimulus_value != value:
                        return False
                elif operator == "$ne":
                    if stimulus_value == value:
                        return False
                elif operator == "$in":
                    if stimulus_value not in value:
                        return False
                elif operator == "$regex":
                    import re
                    if not (stimulus_value and re.match(value, str(stimulus_value))):
                        return False
            else:
                # Direct equality check
                if stimulus_value != expected_value:
                    return False
        
        return True
    
    def _create_reflex_action(self, action_template: Dict[str, Any], stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Create an action from template and stimulus"""
        
        action = action_template.copy()
        
        # Add timestamp
        action["timestamp"] = datetime.utcnow().isoformat()
        
        # Substitute variables from stimulus
        if "content" in action:
            content = action["content"]
            if isinstance(content, str):
                # Simple string substitution
                for key, value in stimulus.items():
                    content = content.replace(f"{{{key}}}", str(value))
                action["content"] = content
            elif isinstance(content, dict):
                # Recursive substitution for nested content
                action["content"] = self._substitute_variables(content, stimulus)
        
        # Add receiver if it's a response to a message
        if stimulus.get("type") == "message" and action.get("type") == "send_message":
            action["receiver"] = stimulus.get("source")
        
        # Add reference to triggering stimulus
        action["triggered_by"] = {
            "type": stimulus.get("type"),
            "id": stimulus.get("id"),
            "timestamp": stimulus.get("timestamp", datetime.utcnow().isoformat())
        }
        
        return action
    
    def _substitute_variables(self, template: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in template"""
        
        if isinstance(template, str):
            result = template
            for key, value in variables.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result
        elif isinstance(template, dict):
            return {k: self._substitute_variables(v, variables) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._substitute_variables(item, variables) for item in template]
        else:
            return template
    
    def add_rule(self, rule_name: str, condition: Any, action: Dict[str, Any], priority: int = 0):
        """Add a new reactive rule"""
        
        self.reactive_rules[rule_name] = {
            "condition": condition,
            "action": action
        }
        self.rule_priorities[rule_name] = priority
        
        logger.info(f"Added reactive rule '{rule_name}' with priority {priority}")
    
    def remove_rule(self, rule_name: str):
        """Remove a reactive rule"""
        
        if rule_name in self.reactive_rules:
            del self.reactive_rules[rule_name]
            if rule_name in self.rule_priorities:
                del self.rule_priorities[rule_name]
            logger.info(f"Removed reactive rule '{rule_name}'")
    
    def get_reflex_metrics(self) -> Dict[str, Any]:
        """Get reflexive behavior metrics"""
        
        return {
            **self.reflex_metrics,
            "rule_count": len(self.reactive_rules),
            "average_rules_per_stimulus": (
                self.reflex_metrics["total_responses"] / max(1, self.reflex_metrics["total_stimuli"])
            )
        }
    
    async def handle_message(self, message: Any):
        """Handle incoming message as stimulus"""
        
        # Convert message to stimulus format
        stimulus = {
            "type": "message",
            "source": message.sender,
            "content": message.content,
            "performative": message.performative,
            "id": message.id if hasattr(message, 'id') else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store as last stimulus for immediate reaction
        if "raw_stimuli" not in self.reactive_state.get("last_stimulus", {}):
            self.reactive_state["last_stimulus"] = {"raw_stimuli": []}
        
        self.reactive_state["last_stimulus"]["raw_stimuli"].append(stimulus)
        
        # Trigger immediate action cycle
        actions = await self.act()
        
        # Execute actions immediately
        for action in actions:
            await self._execute_action(action)
    
    async def handle_task(self, task: Any):
        """Handle task as command stimulus"""
        
        # Convert task to stimulus format
        stimulus = {
            "type": "command",
            "action": "execute_task",
            "params": {
                "task_id": task.id if hasattr(task, 'id') else None,
                "task_type": task.type if hasattr(task, 'type') else "unknown",
                "description": str(task)
            },
            "priority": getattr(task, 'priority', 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store as last stimulus
        if "raw_stimuli" not in self.reactive_state.get("last_stimulus", {}):
            self.reactive_state["last_stimulus"] = {"raw_stimuli": []}
        
        self.reactive_state["last_stimulus"]["raw_stimuli"].append(stimulus)
        
        # Trigger immediate action cycle
        actions = await self.act()
        
        # Execute actions
        for action in actions:
            await self._execute_action(action)