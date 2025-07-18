# Autonomous Swarm Examples

This directory contains autonomous swarm implementations for the MAS Production System, demonstrating large-scale multi-agent coordination with mixed agent types.

## Overview

The autonomous swarm system enables:
- **Scalable coordination** of 5-100+ agents
- **Mixed agent types**: Reflexive, Cognitive, and Hybrid agents working together
- **Task decomposition** and parallel execution
- **Self-validation** through peer review
- **Real LLM integration** for cognitive agents

## Files

### Core Implementations

1. **`autonomous_swarm_example.py`**
   - Full-featured swarm implementation with networkx for task graphs
   - Supports 100+ agents with complex task decomposition
   - Includes validation phases and documentation generation
   - Best for complex, multi-phase projects

2. **`autonomous_swarm_demo.py`**
   - Simplified swarm implementation without networkx dependency
   - Optimized for 5-20 agents
   - Quick setup and execution
   - Best for demonstrations and smaller tasks

### Test and Demo Scripts

3. **`test_swarm_integration.py`**
   - Comprehensive test suite for swarm functionality
   - Tests simple swarm, large swarm, communication, and performance
   - Use this to verify swarm setup

4. **`run_autonomous_swarm.py`**
   - Interactive demonstration script
   - Provides menu-driven interface to explore swarm capabilities
   - Includes predefined and custom task execution

## Quick Start

### 1. Simple Swarm Demo (No Dependencies)

```bash
cd /app/examples
python autonomous_swarm_demo.py
```

This runs a quick demo with 5 agents executing three different tasks.

### 2. Interactive Swarm Demo

```bash
cd /app/examples
python run_autonomous_swarm.py
```

This provides an interactive menu to:
- Run simple swarm demos (5 agents)
- Run large swarm demos (20+ agents)
- Execute custom tasks with configurable agent counts

### 3. Full Test Suite

```bash
cd /app/examples
python test_swarm_integration.py
```

Runs all integration tests to verify swarm functionality.

## Usage Examples

### Example 1: Simple Task Execution

```python
from autonomous_swarm_demo import SimpleAutonomousSwarm

# Create small swarm
swarm = SimpleAutonomousSwarm(num_agents=5)
await swarm.initialize()

# Execute task
result = await swarm.execute_task("Analyze system performance")

# Check results
print(f"Success Rate: {result['success_rate']}%")
print(f"Duration: {result['total_duration']}s")

# Cleanup
await swarm.cleanup()
```

### Example 2: Complex Task with Large Swarm

```python
from autonomous_swarm_example import handle_extreme_request

# Execute complex task with 50 agents
result_json = await handle_extreme_request(
    "Create a complete compiler with lexer, parser, and optimizer",
    num_agents=50
)

# Parse results
import json
result = json.loads(result_json)
print(f"Completed: {result['completed_tasks']}/{result['total_tasks']}")
```

### Example 3: Custom Agent Distribution

```python
from autonomous_swarm_example import AutonomousSwarm

# Create swarm with custom configuration
swarm = AutonomousSwarm(num_agents=30)
await swarm.initialize(30)

# Decompose complex task
task_graph = swarm.decompose_task("Build distributed microservices system")

# Execute with swarm
await swarm.run_swarm(task_graph)

# Get aggregated results
summary = swarm.aggregate_results("Build distributed microservices system")
```

## Agent Types and Roles

### Agent Types
- **Reflexive**: Rule-based, fast response agents
- **Cognitive**: LLM-powered agents for complex reasoning
- **Hybrid**: Combination of rules and LLM capabilities

### Agent Roles
- **Planner**: Task decomposition and strategy
- **Executor**: Implementation and coding
- **Validator**: Quality assurance and testing
- **Documenter**: Documentation and reporting

## Configuration

### Environment Variables
- `LLM_BASE_URL`: LMStudio API endpoint (default: http://lmstudio:1234/v1)
- `LLM_MODEL`: Model to use (default: uses available model)
- `USE_MOCK_LLM`: Set to "false" for real LLM (default: true for demos)

### Swarm Parameters
- `num_agents`: Number of agents to spawn (5-100+)
- `topology`: Swarm organization (mesh, hierarchical, ring, star)
- `strategy`: Execution strategy (parallel, sequential, adaptive)

## Performance Considerations

### Small Tasks (5-15 agents)
- Use `SimpleAutonomousSwarm`
- Faster initialization
- Lower memory usage
- Good for demos and testing

### Large Tasks (20-100+ agents)
- Use `AutonomousSwarm` with networkx
- Better task decomposition
- More sophisticated coordination
- Suitable for production workloads

### Memory Usage
- Each agent uses ~10-50MB depending on type
- Cognitive agents use more memory due to LLM integration
- Monitor system resources for swarms > 50 agents

## Troubleshooting

### NetworkX Not Found
```bash
pip install networkx
```
Only needed for `autonomous_swarm_example.py`

### LLM Connection Issues
- Ensure LMStudio is running
- Check `LLM_BASE_URL` environment variable
- Set `USE_MOCK_LLM=false` for real LLM usage

### Agent Creation Failures
- Check system resources (memory/CPU)
- Reduce agent count
- Check logs in `/app/logs/`

## Advanced Usage

### Custom Task Decomposition
Override the `decompose_task` method to implement domain-specific task breakdown:

```python
class CustomSwarm(AutonomousSwarm):
    def decompose_task(self, task_desc: str) -> nx.DiGraph:
        # Your custom decomposition logic
        pass
```

### Custom Validation Logic
Implement domain-specific validation in the `self_play_validation` method:

```python
async def self_play_validation(self):
    # Your validation logic
    pass
```

## Next Steps

1. Run the interactive demo to explore capabilities
2. Modify agent counts and task types
3. Integrate with your specific use cases
4. Monitor performance and optimize as needed

For more information, see the main MAS documentation.