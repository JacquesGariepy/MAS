"""
Hybrid agent combining reflexive and cognitive capabilities
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from src.core.agents.base_agent import BaseAgent
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OperationMode(Enum):
    """Agent operation modes"""
    REFLEXIVE = "reflexive"
    COGNITIVE = "cognitive"
    HYBRID = "hybrid"

class ComplexityLevel(Enum):
    """Task complexity levels"""
    TRIVIAL = 0
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    VERY_COMPLEX = 4

class HybridAgent(BaseAgent):
    """Hybrid agent that can switch between reflexive and cognitive modes"""
    
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[LLMService] = None,
        **kwargs
    ):
        super().__init__(agent_id, name, role, capabilities, llm_service, **kwargs)
        
        # Hybrid-specific configuration
        self.mode = OperationMode.HYBRID
        self.complexity_threshold = kwargs.get('complexity_threshold', 2.0)
        self.learning_rate = kwargs.get('learning_rate', 0.1)
        
        # Reflexive components
        self.reactive_rules = kwargs.get('reactive_rules', {})
        self.rule_priorities = kwargs.get('rule_priorities', {})
        self.response_threshold_ms = kwargs.get('response_threshold_ms', 100)
        
        # Cognitive components
        self.reasoning_depth = kwargs.get('reasoning_depth', 3)
        self.planning_horizon = kwargs.get('planning_horizon', 5)
        self.learning_enabled = kwargs.get('learning_enabled', True)
        
        # Hybrid state
        self.hybrid_state = {
            "mode_history": [],
            "complexity_assessments": [],
            "mode_switches": 0,
            "learned_thresholds": {},
            "performance_by_mode": {
                "reflexive": {"success": 0, "failure": 0, "avg_time": 0},
                "cognitive": {"success": 0, "failure": 0, "avg_time": 0}
            }
        }
        
        # Performance metrics
        self.hybrid_metrics = {
            "reflexive_actions": 0,
            "cognitive_actions": 0,
            "mode_switches": 0,
            "complexity_misjudgments": 0,
            "adaptive_threshold_changes": 0
        }
        
        # Experience buffer for learning
        self.experience_buffer = []
        self.max_experience_buffer = kwargs.get('max_experience_buffer', 1000)
        
        # Initialize reactive rules
        self._initialize_default_rules()
        
        # Cognitive reasoning templates
        self.reasoning_templates = self._initialize_reasoning_templates()
        
        logger.info(f"Initialized hybrid agent {name} with threshold {self.complexity_threshold}")
    
    def _initialize_default_rules(self):
        """Initialize default reactive rules"""
        
        # Emergency response rules
        if "emergency_response" in self.capabilities:
            self.reactive_rules["emergency_stop"] = {
                "condition": lambda s: s.get("type") == "emergency" and s.get("severity", 0) > 8,
                "action": {"type": "stop_all", "broadcast": True},
                "priority": 100
            }
        
        # Quick acknowledgment rules
        if "communication" in self.capabilities:
            self.reactive_rules["quick_ack"] = {
                "condition": lambda s: s.get("type") == "message" and s.get("requires_ack", False),
                "action": {"type": "send_ack", "content": "Acknowledged"},
                "priority": 90
            }
        
        # Simple metric alerts
        if "monitoring" in self.capabilities:
            self.reactive_rules["threshold_alert"] = {
                "condition": lambda s: s.get("type") == "metric" and s.get("value", 0) > s.get("threshold", 100),
                "action": {"type": "alert", "level": "warning"},
                "priority": 50
            }
    
    def _initialize_reasoning_templates(self) -> Dict[str, Any]:
        """Initialize cognitive reasoning templates"""
        
        return {
            "problem_analysis": {
                "steps": ["identify_constraints", "analyze_dependencies", "evaluate_options"],
                "depth": 3
            },
            "planning": {
                "steps": ["goal_decomposition", "resource_allocation", "timeline_creation"],
                "depth": 5
            },
            "learning": {
                "steps": ["pattern_extraction", "rule_generation", "threshold_adjustment"],
                "depth": 2
            }
        }
    
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment with complexity assessment"""
        
        start_time = datetime.utcnow()
        
        # Basic perception
        perceptions = {
            "timestamp": start_time.isoformat(),
            "stimuli": [],
            "complexity_indicators": {}
        }
        
        # Extract stimuli
        stimuli_count = 0
        unique_types = set()
        max_priority = 0
        requires_reasoning = False
        
        # Messages
        if "messages" in environment:
            for msg in environment["messages"]:
                stimulus = {
                    "type": "message",
                    "source": msg.get("sender"),
                    "content": msg.get("content"),
                    "performative": msg.get("performative"),
                    "complexity": self._assess_message_complexity(msg)
                }
                perceptions["stimuli"].append(stimulus)
                stimuli_count += 1
                unique_types.add("message")
                
                # Check if message requires reasoning
                if msg.get("performative") in ["query", "request", "propose"]:
                    requires_reasoning = True
        
        # Events
        if "events" in environment:
            for event in environment["events"]:
                stimulus = {
                    "type": "event",
                    "name": event.get("name"),
                    "data": event.get("data"),
                    "severity": event.get("severity", 0),
                    "complexity": self._assess_event_complexity(event)
                }
                perceptions["stimuli"].append(stimulus)
                stimuli_count += 1
                unique_types.add("event")
                max_priority = max(max_priority, event.get("severity", 0))
        
        # Tasks
        if "tasks" in environment:
            for task in environment["tasks"]:
                stimulus = {
                    "type": "task",
                    "id": task.get("id"),
                    "description": task.get("description"),
                    "requirements": task.get("requirements", []),
                    "complexity": self._assess_task_complexity(task)
                }
                perceptions["stimuli"].append(stimulus)
                stimuli_count += 1
                unique_types.add("task")
                requires_reasoning = True
        
        # Assess overall complexity
        perceptions["complexity_indicators"] = {
            "stimuli_count": stimuli_count,
            "unique_types": len(unique_types),
            "max_priority": max_priority,
            "requires_reasoning": requires_reasoning,
            "interdependencies": self._detect_interdependencies(perceptions["stimuli"])
        }
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(perceptions["complexity_indicators"])
        perceptions["complexity_score"] = complexity_score
        
        # Determine recommended mode
        perceptions["recommended_mode"] = self._recommend_mode(complexity_score)
        
        # Store complexity assessment for learning
        self.hybrid_state["complexity_assessments"].append({
            "timestamp": start_time.isoformat(),
            "score": complexity_score,
            "indicators": perceptions["complexity_indicators"]
        })
        
        return perceptions
    
    def _assess_message_complexity(self, message: Dict[str, Any]) -> float:
        """Assess complexity of a message"""
        
        complexity = 0.0
        
        # Performative complexity
        performative_weights = {
            "inform": 0.1,
            "request": 0.5,
            "query": 0.6,
            "propose": 0.8,
            "negotiate": 0.9
        }
        complexity += performative_weights.get(message.get("performative", "inform"), 0.3)
        
        # Content complexity (simple heuristic based on length and structure)
        content = message.get("content", "")
        if isinstance(content, str):
            complexity += min(len(content) / 500, 0.5)  # Normalize by typical message length
        elif isinstance(content, dict):
            complexity += min(len(json.dumps(content)) / 1000, 0.7)
        
        # Check for questions or complex requests
        if isinstance(content, str):
            if any(q in content.lower() for q in ["how", "why", "analyze", "compare", "evaluate"]):
                complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _assess_event_complexity(self, event: Dict[str, Any]) -> float:
        """Assess complexity of an event"""
        
        complexity = 0.0
        
        # Severity contributes to complexity
        severity = event.get("severity", 0)
        complexity += severity / 10.0
        
        # Data complexity
        data = event.get("data", {})
        if isinstance(data, dict):
            complexity += min(len(data) / 20, 0.3)
        
        # Event type complexity
        complex_events = ["system_failure", "coordination_required", "multi_agent_task"]
        if event.get("name") in complex_events:
            complexity += 0.4
        
        return min(complexity, 1.0)
    
    def _assess_task_complexity(self, task: Dict[str, Any]) -> float:
        """Assess complexity of a task"""
        
        complexity = 0.0
        
        # Requirements count
        requirements = task.get("requirements", [])
        complexity += min(len(requirements) / 5, 0.4)
        
        # Description analysis
        description = task.get("description", "")
        if len(description) > 200:
            complexity += 0.2
        
        # Check for complex keywords
        complex_keywords = ["optimize", "analyze", "design", "integrate", "coordinate"]
        if any(keyword in description.lower() for keyword in complex_keywords):
            complexity += 0.3
        
        # Multi-step indicator
        if "steps" in task or "subtasks" in task:
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _detect_interdependencies(self, stimuli: List[Dict[str, Any]]) -> int:
        """Detect interdependencies between stimuli"""
        
        dependencies = 0
        
        # Check for related IDs or references
        ids = set()
        references = set()
        
        for stimulus in stimuli:
            if "id" in stimulus:
                ids.add(stimulus["id"])
            if "reference" in stimulus:
                references.add(stimulus["reference"])
            if "depends_on" in stimulus:
                dependencies += len(stimulus["depends_on"])
        
        # Count cross-references
        dependencies += len(ids.intersection(references))
        
        return dependencies
    
    def _calculate_complexity_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall complexity score"""
        
        score = 0.0
        
        # Weighted factors
        score += indicators["stimuli_count"] * 0.1
        score += indicators["unique_types"] * 0.2
        score += indicators["max_priority"] * 0.1
        score += indicators["interdependencies"] * 0.3
        
        if indicators["requires_reasoning"]:
            score += 1.0
        
        # Apply learned adjustments
        for factor, adjustment in self.hybrid_state["learned_thresholds"].items():
            if factor in indicators:
                score *= adjustment
        
        return score
    
    def _recommend_mode(self, complexity_score: float) -> OperationMode:
        """Recommend operation mode based on complexity"""
        
        if complexity_score < self.complexity_threshold * 0.5:
            return OperationMode.REFLEXIVE
        elif complexity_score > self.complexity_threshold * 1.5:
            return OperationMode.COGNITIVE
        else:
            return OperationMode.HYBRID
    
    async def deliberate(self) -> List[str]:
        """Deliberate based on current mode"""
        
        current_mode = self._determine_current_mode()
        
        if current_mode == OperationMode.REFLEXIVE:
            return await self._reflexive_deliberate()
        elif current_mode == OperationMode.COGNITIVE:
            return await self._cognitive_deliberate()
        else:
            return await self._hybrid_deliberate()
    
    def _determine_current_mode(self) -> OperationMode:
        """Determine current operation mode"""
        
        if self.mode != OperationMode.HYBRID:
            return self.mode
        
        # In hybrid mode, check recent perceptions
        if self.context.environment.get("perceptions"):
            recommended = self.context.environment["perceptions"].get("recommended_mode")
            if recommended:
                return recommended
        
        return OperationMode.HYBRID
    
    async def _reflexive_deliberate(self) -> List[str]:
        """Simple reflexive deliberation"""
        
        intentions = []
        
        # Check for pending reactive rules
        for rule_name in self.reactive_rules:
            if self.context.environment.get(f"pending_{rule_name}"):
                intentions.append(f"execute_rule_{rule_name}")
        
        return intentions
    
    async def _cognitive_deliberate(self) -> List[str]:
        """Complex cognitive deliberation"""
        
        intentions = []
        
        # Analyze goals and current state
        for desire in self.bdi.desires:
            # Use LLM for complex reasoning if available
            if self.llm_service:
                analysis = await self._analyze_goal_with_llm(desire)
                if analysis.get("achievable"):
                    plan = await self._create_plan_with_llm(desire, analysis)
                    for step in plan.get("steps", []):
                        intentions.append(step["intention"])
            else:
                # Fallback to template-based reasoning
                if self._is_goal_achievable(desire):
                    steps = self._decompose_goal(desire)
                    intentions.extend(steps)
        
        return intentions
    
    async def _hybrid_deliberate(self) -> List[str]:
        """Hybrid deliberation combining both approaches"""
        
        intentions = []
        
        # First, handle urgent reflexive responses
        reflexive_intentions = await self._reflexive_deliberate()
        intentions.extend(reflexive_intentions)
        
        # Then, if capacity remains, add cognitive planning
        if len(intentions) < 5:  # Arbitrary capacity limit
            cognitive_intentions = await self._cognitive_deliberate()
            intentions.extend(cognitive_intentions[:5 - len(intentions)])
        
        return intentions
    
    async def act(self) -> List[Dict[str, Any]]:
        """Execute actions based on current mode and intentions"""
        
        start_time = datetime.utcnow()
        current_mode = self._determine_current_mode()
        actions = []
        
        if current_mode == OperationMode.REFLEXIVE:
            actions = await self._reflexive_act()
        elif current_mode == OperationMode.COGNITIVE:
            actions = await self._cognitive_act()
        else:
            actions = await self._hybrid_act()
        
        # Track performance
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self._update_performance_metrics(current_mode, actions, execution_time)
        
        # Store experience for learning
        if self.learning_enabled:
            self._store_experience(current_mode, actions, execution_time)
        
        return actions
    
    async def _reflexive_act(self) -> List[Dict[str, Any]]:
        """Generate reflexive actions"""
        
        actions = []
        
        # Get stimuli from perceptions
        perceptions = self.context.environment.get("perceptions", {})
        stimuli = perceptions.get("stimuli", [])
        
        # Apply reactive rules
        for stimulus in stimuli:
            for rule_name, rule in sorted(
                self.reactive_rules.items(),
                key=lambda x: self.rule_priorities.get(x[0], 0),
                reverse=True
            ):
                condition = rule.get("condition")
                if condition and self._evaluate_condition(condition, stimulus):
                    action = self._create_action_from_rule(rule, stimulus)
                    if action:
                        action["mode"] = "reflexive"
                        action["rule"] = rule_name
                        actions.append(action)
                        
                        if not rule.get("continue_matching", False):
                            break
        
        self.hybrid_metrics["reflexive_actions"] += len(actions)
        return actions
    
    async def _cognitive_act(self) -> List[Dict[str, Any]]:
        """Generate cognitive actions with reasoning"""
        
        actions = []
        
        for intention in self.bdi.intentions[:3]:  # Limit concurrent intentions
            # Use LLM for action generation if available
            if self.llm_service:
                action = await self._generate_action_with_llm(intention)
                if action:
                    action["mode"] = "cognitive"
                    action["intention"] = intention
                    actions.append(action)
            else:
                # Template-based action generation
                action = self._generate_action_from_template(intention)
                if action:
                    action["mode"] = "cognitive"
                    action["intention"] = intention
                    actions.append(action)
        
        self.hybrid_metrics["cognitive_actions"] += len(actions)
        return actions
    
    async def _hybrid_act(self) -> List[Dict[str, Any]]:
        """Generate hybrid actions combining both modes"""
        
        actions = []
        
        # First, get reflexive actions for urgent matters
        reflexive_actions = await self._reflexive_act()
        actions.extend(reflexive_actions)
        
        # Then add cognitive actions for complex tasks
        if len(actions) < 5:  # Action limit
            cognitive_actions = await self._cognitive_act()
            actions.extend(cognitive_actions[:5 - len(actions)])
        
        return actions
    
    def _evaluate_condition(self, condition: Any, stimulus: Dict[str, Any]) -> bool:
        """Evaluate rule condition"""
        
        if callable(condition):
            try:
                return condition(stimulus)
            except Exception as e:
                logger.error(f"Error evaluating condition: {str(e)}")
                return False
        elif isinstance(condition, dict):
            return self._match_dict_condition(stimulus, condition)
        
        return False
    
    def _match_dict_condition(self, stimulus: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match stimulus against dictionary condition"""
        
        for key, expected in condition.items():
            actual = stimulus.get(key)
            
            if isinstance(expected, dict) and len(expected) == 1:
                # Handle operators
                op, value = list(expected.items())[0]
                if op == "$gt" and not (actual and actual > value):
                    return False
                elif op == "$lt" and not (actual and actual < value):
                    return False
                elif op == "$eq" and actual != value:
                    return False
                elif op == "$in" and actual not in value:
                    return False
            else:
                if actual != expected:
                    return False
        
        return True
    
    def _create_action_from_rule(self, rule: Dict[str, Any], stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Create action from rule template"""
        
        action = rule.get("action", {}).copy()
        action["timestamp"] = datetime.utcnow().isoformat()
        action["triggered_by"] = {
            "type": stimulus.get("type"),
            "id": stimulus.get("id")
        }
        
        return action
    
    async def _analyze_goal_with_llm(self, goal: str) -> Dict[str, Any]:
        """Analyze goal achievability using LLM"""
        
        prompt = f"""Analyze the following goal for achievability:
Goal: {goal}
Current beliefs: {json.dumps(self.bdi.beliefs, indent=2)}
Available capabilities: {self.capabilities}

Provide analysis including:
1. Is the goal achievable?
2. What resources are needed?
3. What are the main challenges?
4. Estimated complexity (1-10)
"""
        
        await self.llm_service.generate(prompt)
        
        # Parse response (simplified)
        return {
            "achievable": True,  # Would parse from response
            "complexity": 5,
            "resources": [],
            "challenges": []
        }
    
    async def _create_plan_with_llm(self, goal: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create action plan using LLM"""
        
        prompt = f"""Create a step-by-step plan for achieving:
Goal: {goal}
Analysis: {json.dumps(analysis, indent=2)}

Provide a structured plan with specific actions.
"""
        
        await self.llm_service.generate(prompt)
        
        # Parse response into plan structure
        return {
            "steps": [
                {"intention": "step1", "action": "action1"},
                {"intention": "step2", "action": "action2"}
            ]
        }
    
    async def _generate_action_with_llm(self, intention: str) -> Dict[str, Any]:
        """Generate specific action using LLM"""
        
        prompt = f"""Generate a specific action for the intention:
Intention: {intention}
Current context: {json.dumps(self.context.environment, indent=2)}
Available tools: {list(self.tools.keys())}

Provide a structured action specification.
"""
        
        await self.llm_service.generate(prompt)
        
        # Parse response into action
        return {
            "type": "tool_call",
            "tool": "example_tool",
            "params": {}
        }
    
    def _is_goal_achievable(self, goal: str) -> bool:
        """Simple goal achievability check"""
        
        # Check if we have required capabilities
        required_capabilities = {
            "communicate": ["communication"],
            "analyze": ["analysis", "reasoning"],
            "monitor": ["monitoring"],
            "coordinate": ["coordination", "communication"]
        }
        
        for keyword, caps in required_capabilities.items():
            if keyword in goal.lower():
                return any(cap in self.capabilities for cap in caps)
        
        return True
    
    def _decompose_goal(self, goal: str) -> List[str]:
        """Decompose goal into intentions"""
        
        intentions = []
        
        # Simple keyword-based decomposition
        if "analyze" in goal.lower():
            intentions.extend(["gather_data", "process_data", "generate_insights"])
        elif "communicate" in goal.lower():
            intentions.extend(["compose_message", "send_message", "await_response"])
        elif "monitor" in goal.lower():
            intentions.extend(["setup_monitoring", "collect_metrics", "alert_on_threshold"])
        else:
            intentions.append(f"achieve_{goal.lower().replace(' ', '_')}")
        
        return intentions
    
    def _generate_action_from_template(self, intention: str) -> Dict[str, Any]:
        """Generate action from template"""
        
        # Map intentions to actions
        action_templates = {
            "gather_data": {"type": "tool_call", "tool": "data_collector"},
            "send_message": {"type": "send_message", "content": ""},
            "alert_on_threshold": {"type": "alert", "level": "info"}
        }
        
        template = action_templates.get(intention, {"type": "custom", "intention": intention})
        return template.copy()
    
    def _update_performance_metrics(self, mode: OperationMode, actions: List[Dict[str, Any]], execution_time: float):
        """Update performance metrics"""
        
        mode_str = mode.value
        perf = self.hybrid_state["performance_by_mode"][mode_str]
        
        # Update success/failure (simplified - would need actual feedback)
        if actions:
            perf["success"] += 1
        else:
            perf["failure"] += 1
        
        # Update average time
        total = perf["success"] + perf["failure"]
        perf["avg_time"] = ((perf["avg_time"] * (total - 1)) + execution_time) / total
    
    def _store_experience(self, mode: OperationMode, actions: List[Dict[str, Any]], execution_time: float):
        """Store experience for learning"""
        
        experience = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": mode.value,
            "complexity_score": self.context.environment.get("perceptions", {}).get("complexity_score", 0),
            "actions": len(actions),
            "execution_time": execution_time,
            "success": len(actions) > 0  # Simplified
        }
        
        self.experience_buffer.append(experience)
        
        # Maintain buffer size
        if len(self.experience_buffer) > self.max_experience_buffer:
            self.experience_buffer.pop(0)
        
        # Trigger learning periodically
        if len(self.experience_buffer) % 100 == 0:
            self._learn_from_experience()
    
    def _learn_from_experience(self):
        """Learn from accumulated experience to adjust thresholds"""
        
        if len(self.experience_buffer) < 50:
            return
        
        # Analyze performance by complexity ranges
        complexity_ranges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
        
        for low, high in complexity_ranges:
            # Get experiences in this range
            range_experiences = [
                exp for exp in self.experience_buffer
                if low <= exp["complexity_score"] < high
            ]
            
            if not range_experiences:
                continue
            
            # Calculate success rates by mode
            mode_performance = {}
            for mode in ["reflexive", "cognitive"]:
                mode_exps = [exp for exp in range_experiences if exp["mode"] == mode]
                if mode_exps:
                    success_rate = sum(1 for exp in mode_exps if exp["success"]) / len(mode_exps)
                    avg_time = sum(exp["execution_time"] for exp in mode_exps) / len(mode_exps)
                    mode_performance[mode] = {
                        "success_rate": success_rate,
                        "avg_time": avg_time
                    }
            
            # Adjust threshold if one mode significantly outperforms
            if len(mode_performance) == 2:
                ref_perf = mode_performance.get("reflexive", {})
                cog_perf = mode_performance.get("cognitive", {})
                
                if ref_perf.get("success_rate", 0) > cog_perf.get("success_rate", 0) + 0.2:
                    # Reflexive is much better - increase threshold for this range
                    self.complexity_threshold += self.learning_rate * 0.1
                    self.hybrid_metrics["adaptive_threshold_changes"] += 1
                elif cog_perf.get("success_rate", 0) > ref_perf.get("success_rate", 0) + 0.2:
                    # Cognitive is much better - decrease threshold
                    self.complexity_threshold -= self.learning_rate * 0.1
                    self.hybrid_metrics["adaptive_threshold_changes"] += 1
        
        # Ensure threshold stays in reasonable range
        self.complexity_threshold = max(0.5, min(4.0, self.complexity_threshold))
        
        logger.info(f"Adjusted complexity threshold to {self.complexity_threshold}")
    
    async def handle_message(self, message: Any):
        """Handle incoming message with mode selection"""
        
        # Quick assessment of message complexity
        complexity = self._assess_message_complexity({
            "content": message.content,
            "performative": getattr(message, "performative", "inform")
        })
        
        if complexity < self.complexity_threshold * 0.5:
            # Handle reflexively
            await self._handle_message_reflexive(message)
        else:
            # Handle cognitively
            await self._handle_message_cognitive(message)
    
    async def _handle_message_reflexive(self, message: Any):
        """Handle message using reflexive approach"""
        
        # Convert to stimulus and process with rules
        stimulus = {
            "type": "message",
            "source": message.sender,
            "content": message.content,
            "performative": getattr(message, "performative", "inform")
        }
        
        # Check reactive rules
        for rule_name, rule in self.reactive_rules.items():
            if self._evaluate_condition(rule.get("condition"), stimulus):
                action = self._create_action_from_rule(rule, stimulus)
                if action:
                    await self._execute_action(action)
                    break
    
    async def _handle_message_cognitive(self, message: Any):
        """Handle message using cognitive approach"""
        
        # Update beliefs with message content
        await self.update_beliefs({
            "last_message": {
                "sender": message.sender,
                "content": message.content,
                "performative": getattr(message, "performative", "inform"),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Add goal to respond appropriately
        await self.add_desire(f"respond_to_message_from_{message.sender}")
        
        # Trigger deliberation cycle
        await self._bdi_cycle()
    
    async def handle_task(self, task: Any):
        """Handle task with appropriate mode"""
        
        # Assess task complexity
        complexity = self._assess_task_complexity({
            "description": str(task),
            "requirements": getattr(task, "requirements", [])
        })
        
        if complexity < self.complexity_threshold:
            # Simple task - use reflexive approach
            await self._handle_task_reflexive(task)
        else:
            # Complex task - use cognitive approach
            await self._handle_task_cognitive(task)
    
    async def _handle_task_reflexive(self, task: Any):
        """Handle task using reflexive approach"""
        
        # Look for matching task patterns
        task_type = getattr(task, "type", "unknown")
        
        if task_type in self.reactive_rules:
            rule = self.reactive_rules[task_type]
            action = self._create_action_from_rule(rule, {"type": "task", "task": task})
            if action:
                await self._execute_action(action)
    
    async def _handle_task_cognitive(self, task: Any):
        """Handle task using cognitive approach"""
        
        # Add task as a desire
        await self.add_desire(f"complete_task_{task.id if hasattr(task, 'id') else 'unknown'}")
        
        # Update beliefs with task details
        await self.update_beliefs({
            "current_task": {
                "id": task.id if hasattr(task, 'id') else None,
                "type": getattr(task, "type", "unknown"),
                "description": str(task),
                "assigned_at": datetime.utcnow().isoformat()
            }
        })
        
        # Trigger cognitive processing
        await self._bdi_cycle()
    
    def switch_mode(self, mode: OperationMode):
        """Manually switch operation mode"""
        
        old_mode = self.mode
        self.mode = mode
        
        # Track mode switch
        self.hybrid_state["mode_switches"] += 1
        self.hybrid_metrics["mode_switches"] += 1
        
        self.hybrid_state["mode_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "from": old_mode.value,
            "to": mode.value
        })
        
        logger.info(f"Switched from {old_mode.value} to {mode.value} mode")
    
    def get_hybrid_metrics(self) -> Dict[str, Any]:
        """Get hybrid-specific metrics"""
        
        base_metrics = asyncio.run(self.get_metrics())
        
        return {
            **base_metrics,
            **self.hybrid_metrics,
            "current_mode": self.mode.value,
            "complexity_threshold": self.complexity_threshold,
            "total_experiences": len(self.experience_buffer),
            "mode_performance": self.hybrid_state["performance_by_mode"]
        }
    
    def add_reactive_rule(self, name: str, condition: Any, action: Dict[str, Any], priority: int = 0):
        """Add a new reactive rule"""
        
        self.reactive_rules[name] = {
            "condition": condition,
            "action": action
        }
        self.rule_priorities[name] = priority
        
        logger.info(f"Added reactive rule '{name}' with priority {priority}")
    
    def adjust_complexity_threshold(self, adjustment: float):
        """Manually adjust complexity threshold"""
        
        old_threshold = self.complexity_threshold
        self.complexity_threshold = max(0.1, min(5.0, self.complexity_threshold + adjustment))
        
        logger.info(f"Adjusted complexity threshold from {old_threshold} to {self.complexity_threshold}")
    
    async def _handle_config_update(self, config: Dict[str, Any]):
        """Handle configuration updates"""
        
        if "mode" in config:
            self.switch_mode(OperationMode(config["mode"]))
        
        if "complexity_threshold" in config:
            self.complexity_threshold = config["complexity_threshold"]
        
        if "learning_rate" in config:
            self.learning_rate = config["learning_rate"]
        
        if "reactive_rules" in config:
            self.reactive_rules.update(config["reactive_rules"])
        
        if "learning_enabled" in config:
            self.learning_enabled = config["learning_enabled"]