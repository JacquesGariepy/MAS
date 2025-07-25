"""
Hybrid Agent implementation - combines reflexive and cognitive capabilities
"""

from typing import Dict, List, Any, Optional
from uuid import UUID
import asyncio

from src.core.agents.base_agent import BaseAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HybridAgent(BaseAgent):
    """
    Hybrid agent that combines reflexive (fast, rule-based) and cognitive (slow, deliberative) processing
    Uses reflexive mode for quick responses and cognitive mode for complex reasoning
    """
    
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[Any] = None,
        reactive_rules: Optional[Dict[str, Any]] = None,
        cognitive_threshold: float = 0.7,
        **kwargs
    ):
        super().__init__(agent_id, name, role, capabilities, llm_service, **kwargs)
        
        # Initialize both subsystems
        self.reactive_rules = reactive_rules or {}
        self.cognitive_threshold = cognitive_threshold  # Complexity threshold for cognitive processing
        
        # Create internal reflexive and cognitive components
        self._init_subsystems()
        
        # Mode tracking
        self.current_mode = "reflexive"  # Can be "reflexive", "cognitive", or "mixed"
        self.mode_history = []
        
        logger.info(f"Initialized hybrid agent {name} with threshold {cognitive_threshold}")
    
    def _init_subsystems(self):
        """Initialize reflexive and cognitive subsystems"""
        # These are lightweight versions, not full agents
        self.reflexive_system = {
            "rules": self.reactive_rules.copy(),
            "responses": 0,
            "success_rate": 1.0
        }
        
        self.cognitive_system = {
            "reasoning_depth": 3,
            "context_window": 10,
            "responses": 0,
            "success_rate": 1.0
        }
    
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment and assess complexity"""
        # Ensure environment is not None
        if environment is None:
            environment = {}
            
        # Create basic perception structure
        perception = {
            "timestamp": asyncio.get_event_loop().time(),
            "environment": environment,
            "messages": environment.get("messages", []),
            "tasks": environment.get("tasks", []),
            "agents": environment.get("agents", []),
            "conflicts": environment.get("conflicts", [])
        }
        
        # Assess complexity of current situation
        complexity = self._assess_complexity(perception)
        perception["complexity"] = complexity
        
        # Determine processing mode
        if complexity < 0.3:
            perception["suggested_mode"] = "reflexive"
        elif complexity > self.cognitive_threshold:
            perception["suggested_mode"] = "cognitive"
        else:
            perception["suggested_mode"] = "mixed"
        
        logger.debug(f"Agent {self.name} perceived complexity: {complexity:.2f}, mode: {perception['suggested_mode']}")
        
        return perception
    
    def _assess_complexity(self, perception: Dict[str, Any]) -> float:
        """Assess the complexity of the current situation"""
        complexity = 0.0
        
        # Check message complexity
        messages = perception.get("messages", [])
        if messages is None:
            messages = []
        for msg in messages:
            # Complex performatives require more thinking
            if msg.get("performative") in ["propose", "negotiate", "query"]:
                complexity += 0.3
            # Long content suggests complexity
            content = msg.get("content", {})
            if isinstance(content, dict) and len(content) > 5:
                complexity += 0.2
            elif isinstance(content, str) and len(content) > 200:
                complexity += 0.2
        
        # Check task complexity
        tasks = perception.get("tasks", [])
        if tasks is None:
            tasks = []
        for task in tasks:
            if task.get("priority") == "critical":
                complexity += 0.4
            if task.get("task_type") in ["coordination", "negotiation", "planning"]:
                complexity += 0.3
        
        # Check environmental factors
        agents = perception.get("agents", [])
        if agents is None:
            agents = []
        if len(agents) > 5:
            complexity += 0.2  # Many agents require coordination
        
        conflicts = perception.get("conflicts", [])
        if conflicts is None:
            conflicts = []
        if conflicts:
            complexity += 0.5  # Conflicts require careful handling
        
        # Normalize to [0, 1]
        return min(complexity, 1.0)
    
    async def decide(self, perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make decisions using appropriate processing mode"""
        complexity = perception.get("complexity", 0.5)
        suggested_mode = perception.get("suggested_mode", "mixed")
        
        # Update mode
        self.current_mode = suggested_mode
        self.mode_history.append({
            "mode": suggested_mode,
            "complexity": complexity,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        actions = []
        
        if suggested_mode == "reflexive":
            # Use only reflexive processing
            actions = await self._reflexive_decide(perception)
            
        elif suggested_mode == "cognitive":
            # Use only cognitive processing
            actions = await self._cognitive_decide(perception)
            
        else:  # mixed mode
            # Try reflexive first, fall back to cognitive if needed
            reflexive_actions = await self._reflexive_decide(perception)
            
            if not reflexive_actions or self._needs_cognitive_override(reflexive_actions, perception):
                cognitive_actions = await self._cognitive_decide(perception)
                
                # Merge or replace actions based on confidence
                actions = self._merge_actions(reflexive_actions, cognitive_actions)
            else:
                actions = reflexive_actions
        
        logger.info(f"Agent {self.name} decided {len(actions)} actions in {suggested_mode} mode")
        
        return actions
    
    async def _reflexive_decide(self, perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make quick decisions based on rules"""
        actions = []
        
        # Check messages against rules
        for message in perception.get("messages", []):
            for rule_name, rule in self.reflexive_system["rules"].items():
                if self._match_rule(message, rule.get("condition", {})):
                    action = self._create_reflexive_action(rule.get("action", {}), message)
                    if action:
                        action["processing_mode"] = "reflexive"
                        action["rule_name"] = rule_name
                        actions.append(action)
        
        self.reflexive_system["responses"] += len(actions)
        
        return actions
    
    async def _cognitive_decide(self, perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make deliberative decisions using LLM"""
        if not self.llm_service:
            logger.warning(f"Agent {self.name} needs LLM for cognitive processing but none available")
            return []
        
        actions = []
        
        # Build context for reasoning
        context = self._build_cognitive_context(perception)
        
        # Generate reasoning prompt
        prompt = self._generate_reasoning_prompt(context)
        
        try:
            # Get LLM response
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
                json_response=True
            )
            
            # Check if response is valid
            if not response or not isinstance(response, dict):
                logger.warning(f"Invalid response from LLM for agent {self.name}: {response}")
                return []
            
            # Extract the actual response content
            if response.get('success') and response.get('response'):
                llm_response = response['response']
                
                # Parse response into actions
                if isinstance(llm_response, dict):
                    # If LLM returned JSON, extract actions directly
                    if 'actions' in llm_response:
                        parsed_actions = llm_response['actions'] if isinstance(llm_response['actions'], list) else []
                    else:
                        # Try to create action from the response
                        parsed_actions = [llm_response] if llm_response.get('type') else []
                elif isinstance(llm_response, str):
                    # Parse text response
                    parsed_actions = self._parse_cognitive_response(llm_response)
                else:
                    parsed_actions = []
                
                for action in parsed_actions:
                    if isinstance(action, dict):
                        action["processing_mode"] = "cognitive"
                        actions.append(action)
                
                self.cognitive_system["responses"] += len(actions)
            else:
                logger.warning(f"LLM response unsuccessful for agent {self.name}")
            
        except Exception as e:
            logger.error(f"Cognitive processing failed for agent {self.name}: {e}", exc_info=True)
        
        return actions
    
    def _match_rule(self, stimulus: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if a stimulus matches a rule condition"""
        for key, value in condition.items():
            if key not in stimulus:
                return False
            if stimulus[key] != value:
                return False
        return True
    
    def _create_reflexive_action(self, action_template: Dict[str, Any], stimulus: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an action from a reflexive template"""
        if not action_template:
            return None
        
        action = action_template.copy()
        action["in_response_to"] = stimulus.get("id")
        action["confidence"] = 0.8  # Reflexive actions have moderate confidence
        
        return action
    
    def _build_cognitive_context(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for cognitive processing"""
        return {
            "current_perception": perception,
            "recent_history": self.mode_history[-10:],
            "beliefs": self.bdi.beliefs,
            "desires": self.bdi.desires,
            "intentions": self.bdi.intentions,
            "capabilities": self.capabilities
        }
    
    def _generate_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for LLM reasoning"""
        prompt = f"""As a hybrid agent named {self.name} with role '{self.role}', analyze the situation and decide on actions.

Current situation:
- Messages: {len(context['current_perception'].get('messages', []))}
- Tasks: {len(context['current_perception'].get('tasks', []))}
- Complexity: {context['current_perception'].get('complexity', 0):.2f}

My capabilities: {', '.join(self.capabilities)}
My current beliefs: {self.bdi.beliefs}
My desires: {', '.join(self.bdi.desires)}

Return a JSON object with this structure:
{{
    "actions": [
        {{
            "type": "action_type",
            "target": "target_entity",
            "content": "action content if needed",
            "reasoning": "why this action"
        }}
    ]
}}

If no actions are needed, return: {{"actions": []}}
"""
        return prompt
    
    def _parse_cognitive_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into actions"""
        actions = []
        
        # Handle None or empty responses
        if not response:
            return actions
        
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
        
        # Simple parsing - in production this would be more sophisticated
        lines = response.strip().split('\n')
        current_action = {}
        
        for line in lines:
            if line.startswith("Action:"):
                if current_action:
                    actions.append(current_action)
                current_action = {"type": line.replace("Action:", "").strip()}
            elif line.startswith("Target:"):
                current_action["target"] = line.replace("Target:", "").strip()
            elif line.startswith("Content:"):
                current_action["content"] = line.replace("Content:", "").strip()
        
        if current_action and current_action.get("type"):
            actions.append(current_action)
        
        return actions
    
    def _needs_cognitive_override(self, reflexive_actions: List[Dict[str, Any]], perception: Dict[str, Any]) -> bool:
        """Determine if cognitive processing should override reflexive actions"""
        # Override if complexity is high
        if perception.get("complexity", 0) > 0.8:
            return True
        
        # Override if reflexive actions seem insufficient
        if not reflexive_actions and perception.get("messages"):
            return True
        
        # Override if dealing with critical tasks
        for task in perception.get("tasks", []):
            if task.get("priority") == "critical":
                return True
        
        return False
    
    def _merge_actions(self, reflexive_actions: List[Dict[str, Any]], cognitive_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge reflexive and cognitive actions intelligently"""
        if not cognitive_actions:
            return reflexive_actions
        
        if not reflexive_actions:
            return cognitive_actions
        
        # In mixed mode, prefer cognitive actions for complex tasks
        merged = []
        
        # Add all cognitive actions (they're more thoughtful)
        merged.extend(cognitive_actions)
        
        # Add reflexive actions that don't conflict
        for r_action in reflexive_actions:
            conflict = False
            for c_action in cognitive_actions:
                if (r_action.get("type") == c_action.get("type") and 
                    r_action.get("target") == c_action.get("target")):
                    conflict = True
                    break
            
            if not conflict:
                merged.append(r_action)
        
        return merged
    
    async def learn(self, feedback: Dict[str, Any]):
        """Learn from feedback to improve both subsystems"""
        success = feedback.get("success", False)
        mode = feedback.get("processing_mode", "unknown")
        
        # Update success rates
        if mode == "reflexive":
            total = self.reflexive_system["responses"]
            if total > 0:
                current_rate = self.reflexive_system["success_rate"]
                self.reflexive_system["success_rate"] = (current_rate * (total - 1) + (1 if success else 0)) / total
                
        elif mode == "cognitive":
            total = self.cognitive_system["responses"]
            if total > 0:
                current_rate = self.cognitive_system["success_rate"]
                self.cognitive_system["success_rate"] = (current_rate * (total - 1) + (1 if success else 0)) / total
        
        # Adjust cognitive threshold based on performance
        if self.reflexive_system["success_rate"] < 0.6:
            # Reflexive system struggling, use cognitive more
            self.cognitive_threshold = max(0.5, self.cognitive_threshold - 0.05)
        elif self.cognitive_system["success_rate"] > 0.9 and self.reflexive_system["success_rate"] > 0.8:
            # Both systems performing well, can rely more on reflexive
            self.cognitive_threshold = min(0.8, self.cognitive_threshold + 0.02)
        
        logger.info(f"Agent {self.name} adjusted threshold to {self.cognitive_threshold:.2f}")
    
    def get_mode_statistics(self) -> Dict[str, Any]:
        """Get statistics about mode usage"""
        total_decisions = len(self.mode_history)
        if total_decisions == 0:
            return {
                "total_decisions": 0,
                "reflexive_percent": 0,
                "cognitive_percent": 0,
                "mixed_percent": 0
            }
        
        mode_counts = {"reflexive": 0, "cognitive": 0, "mixed": 0}
        for entry in self.mode_history:
            mode_counts[entry["mode"]] += 1
        
        return {
            "total_decisions": total_decisions,
            "reflexive_percent": (mode_counts["reflexive"] / total_decisions) * 100,
            "cognitive_percent": (mode_counts["cognitive"] / total_decisions) * 100,
            "mixed_percent": (mode_counts["mixed"] / total_decisions) * 100,
            "current_threshold": self.cognitive_threshold,
            "reflexive_success_rate": self.reflexive_system["success_rate"],
            "cognitive_success_rate": self.cognitive_system["success_rate"]
        }
    
    async def deliberate(self) -> List[str]:
        """Deliberate based on current mode"""
        perception = await self.perceive(self.context.environment)
        complexity = perception.get("complexity", 0.5)
        
        if complexity < 0.3:
            # Simple situation - use reflexive deliberation
            intentions = []
            for rule_name in self.reflexive_system["rules"]:
                intentions.append(f"execute_rule_{rule_name}")
            return intentions
        else:
            # Complex situation - use cognitive deliberation
            intentions = []
            
            # Analyze desires and form intentions
            for desire in self.bdi.desires:
                if self._should_pursue_desire(desire, perception):
                    intentions.append(f"pursue_{desire}")
            
            # Add coordination intentions if needed
            if len(perception.get("agents", [])) > 2:
                intentions.append("coordinate_with_agents")
            
            return intentions
    
    def _should_pursue_desire(self, desire: str, perception: Dict[str, Any]) -> bool:
        """Check if a desire should be pursued given current perception"""
        # Simple heuristic - can be made more sophisticated
        if "urgent" in perception and desire in perception.get("urgent", []):
            return True
        if desire in ["complete_test", "demonstrate_capability"]:
            return True
        return False
    
    async def act(self) -> List[Dict[str, Any]]:
        """Act based on current mode and intentions"""
        perception = await self.perceive(self.context.environment)
        
        # Use decide method which handles mode selection
        actions = await self.decide(perception)
        
        return actions
    
    async def handle_message(self, message: Any):
        """Handle incoming message"""
        if "messages" not in self.context.environment:
            self.context.environment["messages"] = []
        self.context.environment["messages"].append(message)
        
        # Assess if message requires mode switch
        if hasattr(message, "performative"):
            if message.performative in ["propose", "negotiate"]:
                # Complex performatives may require cognitive mode
                self.current_mode = "cognitive"
        
        # Update metrics
        self.metrics["messages_processed"] = self.metrics.get("messages_processed", 0) + 1
        logger.debug(f"Hybrid agent {self.name} received message")
    
    async def handle_task(self, task: Any):
        """Handle assigned task"""
        if "tasks" not in self.context.environment:
            self.context.environment["tasks"] = []
        self.context.environment["tasks"].append(task)
        
        # Assess task complexity
        if hasattr(task, "priority") and task.priority == "critical":
            # Critical tasks may require cognitive mode
            self.current_mode = "cognitive"
        
        # Update metrics
        self.metrics["tasks_assigned"] = self.metrics.get("tasks_assigned", 0) + 1
        logger.debug(f"Hybrid agent {self.name} received task")