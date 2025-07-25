# MAS Agent Architecture - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Agent Types](#agent-types)
3. [Core Architecture](#core-architecture)
4. [Communication Patterns](#communication-patterns)
5. [Agent Lifecycle](#agent-lifecycle)
6. [LLM Integration](#llm-integration)
7. [Task Execution](#task-execution)
8. [Tool Integration](#tool-integration)
9. [Memory and Learning](#memory-and-learning)
10. [Swarm Coordination](#swarm-coordination)
11. [Implementation Examples](#implementation-examples)

## Overview

The MAS (Multi-Agent System) production system implements a sophisticated agent architecture based on the BDI (Beliefs-Desires-Intentions) model. The system supports multiple agent types, each optimized for different scenarios, with seamless integration of Large Language Models (LLMs) for cognitive processing.

### Key Features
- **Three Agent Types**: Reflexive, Cognitive (Reactive), and Hybrid
- **BDI Architecture**: Full implementation of Beliefs, Desires, and Intentions
- **Asynchronous Execution**: Non-blocking agent operations with asyncio
- **Tool Integration**: Extensible tool system for agent capabilities
- **LLM Support**: Multiple providers (OpenAI, Ollama, LMStudio)
- **Swarm Coordination**: Large-scale multi-agent collaboration

## Agent Types

### 1. Reflexive Agents
Fast, rule-based agents for quick responses without deliberation.

**Characteristics:**
- Rule-based processing (stimulus-response patterns)
- No LLM dependency
- Minimal computational overhead
- Instant reactions to known patterns

**Use Cases:**
- System monitoring and alerts
- Simple data transformations
- Event routing and filtering
- Predefined workflows

**Key Components:**
```python
reactive_rules = {
    "alert_rule": {
        "condition": {"alert_level": "high"},
        "action": {"type": "notify", "content": "Alert triggered!"}
    }
}
```

### 2. Cognitive Agents (Reactive in API)
Intelligent agents using LLMs for reasoning and decision-making.

**Characteristics:**
- LLM-powered deliberation
- Complex reasoning capabilities
- Context-aware responses
- Dynamic problem-solving

**Use Cases:**
- Natural language understanding
- Complex analysis tasks
- Strategic planning
- Creative problem-solving

**Key Components:**
- LLM service integration
- Structured prompt templates
- JSON response validation
- Context management

### 3. Hybrid Agents
Adaptive agents combining reflexive and cognitive capabilities.

**Characteristics:**
- Mode switching based on complexity
- Reflexive mode for simple tasks
- Cognitive mode for complex reasoning
- Adaptive threshold management

**Use Cases:**
- Variable complexity environments
- Resource-optimized processing
- Fail-safe operations
- Learning systems

**Key Components:**
```python
cognitive_threshold = 0.7  # Complexity threshold for mode switching
current_mode = "reflexive"  # Can be "reflexive", "cognitive", or "mixed"
```

## Core Architecture

### Base Agent Class
All agents inherit from `BaseAgent`, providing:

```python
class BaseAgent(ABC):
    def __init__(self, agent_id, name, role, capabilities, llm_service=None):
        # Core attributes
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities
        
        # BDI model
        self.bdi = BDI(beliefs={}, desires=[], intentions=[])
        
        # Execution context
        self.context = AgentContext(agent_id=agent_id)
        
        # Communication
        self._message_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {...}
```

### BDI Model Implementation

**Beliefs**: Agent's knowledge about the world
```python
beliefs = {
    "environment_state": "normal",
    "task_complexity": 0.5,
    "available_resources": ["tool1", "tool2"],
    "team_members": ["agent1", "agent2"]
}
```

**Desires**: Agent's goals and objectives
```python
desires = [
    "complete_assigned_tasks",
    "optimize_performance",
    "collaborate_effectively"
]
```

**Intentions**: Committed plans to achieve desires
```python
intentions = [
    "execute_task_123",
    "coordinate_with_agent_456",
    "report_results"
]
```

### Agent Context
Maintains execution state and environment information:

```python
@dataclass
class AgentContext:
    agent_id: UUID
    environment: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    working_memory: List[Any] = field(default_factory=list)
    current_task: Optional[Any] = None
    software_location: Optional[Any] = None
    resource_allocation: Dict[str, float] = field(default_factory=dict)
```

## Communication Patterns

### Message Types (Performatives)
Based on FIPA-ACL standard:

```python
class MessageType:
    INFORM = "inform"      # Share information
    REQUEST = "request"    # Request action
    PROPOSE = "propose"    # Propose plan/solution
    QUERY = "query"       # Ask for information
    ACCEPT = "accept"     # Accept proposal
    REJECT = "reject"     # Reject proposal
    FAILURE = "failure"   # Report failure
```

### Message Structure
```python
class Message:
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    performative: str
    content: Dict[str, Any]
    conversation_id: UUID
    in_reply_to: Optional[UUID]
    created_at: datetime
```

### Communication Flow
1. **Agent A** creates message
2. **Message Broker** routes message
3. **Agent B** receives in message queue
4. **Agent B** processes during BDI cycle
5. **Agent B** may send response

## Agent Lifecycle

### 1. Initialization
```python
# Create agent via factory
agent = AgentFactory.create_agent(
    agent_type="cognitive",
    agent_id=uuid4(),
    name="Analyst",
    role="Data Analysis",
    capabilities=["analysis", "reporting"],
    llm_service=llm_service
)
```

### 2. Registration
```python
# Register with runtime
runtime = get_agent_runtime()
await runtime.register_agent(agent)
```

### 3. Startup
```python
# Start agent execution
await runtime.start_agent(agent)
```

### 4. Main Execution Loop
```python
async def run(self):
    while self._running:
        # Process messages
        await self._process_messages()
        
        # Process tasks
        await self._process_tasks()
        
        # BDI cycle (periodic)
        await self._bdi_cycle()
        
        await asyncio.sleep(0.1)
```

### 5. BDI Cycle
```python
async def _bdi_cycle(self):
    # Perceive environment
    perceptions = await self.perceive(self.context.environment)
    
    # Update beliefs
    await self.update_beliefs(perceptions)
    
    # Deliberate (form intentions)
    new_intentions = await self.deliberate()
    
    # Act on intentions
    actions = await self.act()
    
    # Execute actions
    for action in actions:
        await self._execute_action(action)
```

### 6. Shutdown
```python
# Stop agent
await runtime.stop_agent(agent_id)
```

## LLM Integration

### Service Configuration
```python
class LLMService:
    TIMEOUT_CONFIG = {
        'simple': 60,      # 1 minute
        'normal': 180,     # 3 minutes
        'complex': 300,    # 5 minutes
        'reasoning': 600   # 10 minutes
    }
```

### Provider Support
- **OpenAI**: GPT models
- **Ollama**: Local models (qwen, llama)
- **LMStudio**: Local deployment
- **Mock Mode**: Testing without API

### Cognitive Processing
```python
async def cognitive_decide(self, perception):
    # Build context
    context = self._build_cognitive_context(perception)
    
    # Generate prompt
    prompt = self._generate_reasoning_prompt(context)
    
    # Get LLM response
    response = await self.llm_service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        json_response=True
    )
    
    # Parse into actions
    return self._parse_cognitive_response(response)
```

## Task Execution

### Task Structure
```python
class Task:
    id: UUID
    title: str
    description: str
    task_type: str  # "analysis", "development", "coordination"
    priority: str   # "low", "medium", "high", "critical"
    assigned_to: UUID
    status: str     # "pending", "in_progress", "completed", "failed"
    metadata: Dict[str, Any]
```

### Task Processing Flow
1. **Assignment**: Task assigned to agent
2. **Analysis**: Agent analyzes requirements
3. **Planning**: Create execution plan
4. **Execution**: Carry out plan steps
5. **Validation**: Verify results
6. **Reporting**: Report completion

### Task Handlers
```python
async def handle_task(self, task: Task) -> Dict[str, Any]:
    # Analyze task
    analysis = await self._analyze_task(task)
    
    if analysis["can_complete"]:
        # Create execution plan
        plan = await self._create_execution_plan(task, analysis)
        
        # Execute plan
        result = await self._execute_plan(plan)
        
        return {
            "status": "completed",
            "result": result,
            "confidence": analysis["confidence"]
        }
    else:
        return {
            "status": "rejected",
            "reason": "Insufficient capabilities"
        }
```

## Tool Integration

### Tool System Architecture
```python
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Tool implementation
        pass
```

### Built-in Tools
1. **FileSystemTool**: File operations
2. **DatabaseTool**: Database queries
3. **HTTPTool**: Web requests
4. **GitTool**: Version control
5. **CodeTool**: Code generation/analysis
6. **WebSearchTool**: Information retrieval

### Tool Execution
```python
async def _execute_tool_call(self, action: Dict[str, Any]):
    tool_name = action.get("tool")
    params = action.get("params", {})
    
    tool = self.tools[tool_name]
    result = await tool.execute(params)
    
    # Update beliefs with result
    await self.update_beliefs({
        f"last_{tool_name}_result": result.data
    })
```

## Memory and Learning

### Memory Types
1. **Semantic Memory**: Facts and knowledge
2. **Episodic Memory**: Past experiences
3. **Working Memory**: Current context
4. **Procedural Memory**: Skills and procedures

### Memory Storage
```python
class Memory:
    id: UUID
    agent_id: UUID
    content: str
    memory_type: str
    importance: float
    embedding: List[float]  # Vector representation
    created_at: datetime
```

### Learning Mechanisms

**Reflexive Learning**: Rule adjustment
```python
def add_rule(self, rule_name: str, condition: Dict, action: Dict):
    self.reactive_rules[rule_name] = {
        "condition": condition,
        "action": action
    }
```

**Cognitive Learning**: Pattern recognition
```python
async def learn(self, feedback: Dict[str, Any]):
    # Update success rates
    if feedback["success"]:
        self.success_rate = (self.success_rate * n + 1) / (n + 1)
    
    # Adjust parameters
    if self.success_rate < 0.6:
        self.temperature += 0.1  # More exploration
```

**Hybrid Learning**: Threshold adaptation
```python
if reflexive_success_rate < 0.6:
    # Use cognitive mode more
    self.cognitive_threshold -= 0.05
elif both_rates > 0.8:
    # Can rely more on reflexive
    self.cognitive_threshold += 0.02
```

## Swarm Coordination

### Swarm Patterns

**1. Hierarchical Swarm**
```
    Coordinator
    /    |    \
Planner Executor Validator
```

**2. Mesh Swarm**
```
Agent1 -- Agent2
  |   \  /   |
  |    \/    |
  |    /\    |
  |   /  \   |
Agent3 -- Agent4
```

**3. Pipeline Swarm**
```
Analyzer -> Designer -> Implementer -> Tester -> Deployer
```

### Task Decomposition
```python
def decompose_task(self, task: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    
    phases = ["planning", "implementation", "testing", "validation"]
    
    for phase in phases:
        # Create subtasks for phase
        for i in range(agents_per_phase):
            graph.add_node(
                node_id,
                sub_task=f"{phase}_{i}",
                phase=phase,
                status="pending"
            )
```

### Coordination Protocols

**1. Contract Net Protocol**
- Manager announces task
- Agents bid based on capabilities
- Manager awards to best bidder
- Winner executes and reports

**2. Blackboard System**
- Shared knowledge space
- Agents contribute solutions
- Coordinator synthesizes results

**3. Gossip Protocol**
- Agents share local information
- Gradual convergence to consensus

## Implementation Examples

### Example 1: Creating a Cognitive Agent
```python
# Initialize LLM service
llm_service = LLMService()

# Create cognitive agent
analyst = AgentFactory.create_agent(
    agent_type="cognitive",
    agent_id=uuid4(),
    name="DataAnalyst",
    role="Analyze complex datasets",
    capabilities=["data_analysis", "statistics", "visualization"],
    llm_service=llm_service,
    initial_beliefs={
        "expertise": ["python", "pandas", "matplotlib"],
        "preferred_methods": ["regression", "clustering"]
    },
    initial_desires=[
        "provide_accurate_analysis",
        "identify_patterns",
        "generate_insights"
    ]
)

# Register and start
runtime = get_agent_runtime()
await runtime.register_agent(analyst)
await runtime.start_agent(analyst)
```

### Example 2: Creating a Reflexive Monitor
```python
# Create reflexive monitoring agent
monitor = AgentFactory.create_agent(
    agent_type="reflexive",
    agent_id=uuid4(),
    name="SystemMonitor",
    role="Monitor system health",
    capabilities=["monitoring", "alerting"],
    reactive_rules={
        "high_cpu": {
            "condition": {"metric": "cpu", "value": {"$gt": 80}},
            "action": {"type": "alert", "severity": "warning"}
        },
        "memory_critical": {
            "condition": {"metric": "memory", "value": {"$gt": 90}},
            "action": {"type": "alert", "severity": "critical"}
        }
    }
)
```

### Example 3: Creating a Hybrid Coordinator
```python
# Create hybrid coordination agent
coordinator = AgentFactory.create_agent(
    agent_type="hybrid",
    agent_id=uuid4(),
    name="ProjectCoordinator",
    role="Coordinate development team",
    capabilities=["planning", "coordination", "reporting"],
    llm_service=llm_service,
    cognitive_threshold=0.6,  # Use cognitive for >60% complexity
    reactive_rules={
        "daily_standup": {
            "condition": {"time": "09:00", "weekday": True},
            "action": {"type": "meeting", "duration": "15m"}
        }
    }
)
```

### Example 4: Agent Communication
```python
# Send message between agents
await runtime.send_message(
    from_agent=analyst.agent_id,
    to_agent=coordinator.agent_id,
    message={
        "performative": "inform",
        "content": {
            "analysis_complete": True,
            "findings": ["pattern_1", "anomaly_2"],
            "confidence": 0.85
        }
    }
)
```

### Example 5: Swarm Creation
```python
# Create a development swarm
swarm = AutonomousSwarm(num_agents=10)
await swarm.initialize(10)

# Decompose complex task
task_graph = swarm.decompose_task(
    "Build complete REST API with authentication"
)

# Execute swarm
await swarm.run_swarm(task_graph)

# Get results
results = swarm.aggregate_results(task)
```

## Best Practices

### 1. Agent Design
- Choose appropriate agent type for use case
- Define clear capabilities and constraints
- Implement proper error handling
- Monitor performance metrics

### 2. Communication
- Use appropriate performatives
- Keep messages concise and structured
- Implement conversation tracking
- Handle message failures gracefully

### 3. Task Management
- Decompose complex tasks appropriately
- Set realistic priorities
- Monitor task progress
- Implement timeout mechanisms

### 4. Resource Management
- Limit concurrent operations
- Implement backpressure mechanisms
- Monitor memory usage
- Clean up completed tasks

### 5. LLM Integration
- Use appropriate timeout values
- Implement retry logic
- Cache responses when possible
- Monitor token usage

## Performance Considerations

### 1. Agent Scaling
- Use reflexive agents for high-frequency tasks
- Reserve cognitive agents for complex reasoning
- Implement agent pooling for resource efficiency
- Monitor and balance agent workloads

### 2. Communication Optimization
- Batch messages when possible
- Use broadcast for group communication
- Implement message priorities
- Clean old conversation history

### 3. Memory Management
- Implement memory size limits
- Use embeddings for efficient retrieval
- Archive old memories
- Implement forgetting mechanisms

### 4. LLM Optimization
- Use streaming for long responses
- Implement response caching
- Choose appropriate models for tasks
- Monitor and optimize token usage

## Troubleshooting

### Common Issues

**1. Agent Not Responding**
- Check if agent is registered and running
- Verify message queue is not full
- Check for blocking operations
- Review agent logs

**2. LLM Timeouts**
- Increase timeout for complex tasks
- Use streaming for long responses
- Check network connectivity
- Consider using local models

**3. Memory Leaks**
- Monitor memory usage over time
- Clean up old conversations
- Limit working memory size
- Implement garbage collection

**4. Poor Performance**
- Review agent type selection
- Optimize BDI cycle frequency
- Check for unnecessary LLM calls
- Profile code for bottlenecks

## Future Enhancements

### Planned Features
1. **Advanced Learning**: Reinforcement learning integration
2. **Federated Agents**: Cross-system agent collaboration
3. **Visual Reasoning**: Image and diagram understanding
4. **Code Generation**: Enhanced programming capabilities
5. **Explainable AI**: Transparent decision-making

### Research Areas
1. **Emergent Behavior**: Swarm intelligence patterns
2. **Meta-Learning**: Learning how to learn
3. **Adversarial Robustness**: Security and reliability
4. **Quantum Integration**: Quantum computing for agents
5. **Neuromorphic Computing**: Brain-inspired architectures

## Conclusion

The MAS agent architecture provides a robust foundation for building intelligent, collaborative systems. By combining reflexive, cognitive, and hybrid agents with modern LLMs and asynchronous execution, the system can handle a wide range of tasks from simple automation to complex reasoning and coordination.

The modular design allows for easy extension and customization, while the comprehensive monitoring and metrics ensure system reliability and performance. Whether building a small team of specialized agents or a large swarm for complex problem-solving, the MAS architecture provides the tools and patterns needed for success.