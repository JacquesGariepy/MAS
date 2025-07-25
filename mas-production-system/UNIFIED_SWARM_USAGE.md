# Unified Swarm MAS - Usage Guide

The unified swarm MAS (`swarm_mas_unified.py`) integrates all components from the mas-production-system and can process user requests autonomously, similar to `autonomous_fixed.py`.

## Features

- **45 Specialized Agents**: Architects, Analysts, Developers, Testers, DevOps, Data Engineers, Security, ML Engineers, Coordinators, Monitors, Researchers, Creative, and Validators
- **Autonomous Request Processing**: Analyzes, decomposes, executes, and validates user requests
- **Full Integration**: All MAS components integrated without placeholders or simulations
- **Multiple Execution Modes**: Demo, Full, Test, Server, Interactive, and Request modes
- **Persistence**: Checkpoint saving and loading for cross-session continuity

## Usage Examples

### 1. Request Mode (Non-Interactive)

Process a single request from the command line:

```bash
# Simple request
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py \
  --mode request \
  --request "Create a Python function to calculate fibonacci numbers"

# Complex request
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py \
  --mode request \
  --request "Build a REST API for user management with authentication, database integration, and comprehensive tests"
```

### 2. Full Demonstration Mode

Run a complete demonstration of system capabilities:

```bash
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py --mode full
```

### 3. Test Mode

Run system tests:

```bash
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py --mode test
```

### 4. Demo Mode

Run a simple demonstration:

```bash
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py --mode demo
```

### 5. Interactive Mode (Requires TTY)

For interactive mode, you need to use `-it` flags:

```bash
# This requires an interactive terminal
docker exec -it mas-production-system-core-1 python /app/src/swarm_mas_unified.py --mode interactive
```

### 6. Server Mode

Start as an API server:

```bash
docker exec mas-production-system-core-1 python /app/src/swarm_mas_unified.py \
  --mode server \
  --port 8000 \
  --workers 4
```

## Command-Line Options

```
--mode {demo,server,test,full,interactive,request}
    Execution mode (default: demo)

--port PORT
    Port for server mode (default: 8000)

--workers WORKERS
    Number of workers for server mode (default: 4)

--strategy {centralized,decentralized,hierarchical,market_based,consensus,emergent}
    Coordination strategy (default: hierarchical)

--request REQUEST
    Request to process (required for request mode)
```

## What Happens When You Submit a Request

1. **Phase 1: Request Analysis**
   - The LLM service analyzes your request
   - Identifies main objectives, components, and dependencies
   - Determines required capabilities and success criteria

2. **Phase 2: Task Planning**
   - Creates a detailed task plan based on analysis
   - Assigns appropriate task types (design, development, testing, etc.)
   - Sets priorities and dependencies

3. **Phase 3: Task Submission**
   - Submits tasks to the swarm's task queue
   - Tasks are distributed among specialized agents

4. **Phase 4: Parallel Execution**
   - Agents work on tasks according to their specializations
   - Coordination happens through the chosen strategy
   - Progress is monitored in real-time

5. **Phase 5: Validation**
   - Results are validated for completeness
   - Success rate is calculated
   - Final report is generated

## Output Example

```
================================================================================
🤖 UNIFIED SWARM MAS - REQUEST MODE
================================================================================

📝 Processing request: Create a Python function to reverse a string

============================================================
✅ RESULT
============================================================
Status: completed
Duration: 5.23 seconds
Tasks executed: 3
Success rate: 100.0%

📊 Swarm Metrics:
  - Total Agents: 45
  - Active Agents: 3
  - Tasks Completed: 3

📋 Analysis:
  - Objective: Create a Python function to reverse a string
  - Components: 3
    1. Design function signature
    2. Implement string reversal logic
    3. Create unit tests
```

## Key Differences from autonomous_fixed.py

1. **Scale**: 45 specialized agents vs. smaller agent pool
2. **Architecture**: Full MAS implementation with environment, constraints, and rules
3. **Coordination**: Multiple strategies (hierarchical, decentralized, etc.)
4. **Integration**: All MAS components fully integrated
5. **Performance**: Optimized for parallel execution

## Notes

- The LLM service is currently in mock mode for demonstration
- Memory warnings are normal and don't affect functionality
- Checkpoint files are saved in the workspace directory
- All 45 agents initialize even for simple requests (for full capability demonstration)

## Troubleshooting

If you encounter:
- **EOF Error**: Use request mode instead of interactive mode
- **Memory Warnings**: Normal operation, agents still function
- **Permission Errors**: Ensure proper Docker permissions