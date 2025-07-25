#!/usr/bin/env python3
"""
PRODUCTION-READY SWARM MAS
==========================
Enhanced Multi-Agent System that properly executes tasks with:
- Full task decomposition and subtask execution
- Real agent work with file creation
- Comprehensive validation and error handling
- Production-grade monitoring and logging
"""

import asyncio
import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

# Add parent directory to path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Import core components
try:
    from src.core.agents import AgentFactory, get_agent_runtime
    from src.core.agents.cognitive_agent import CognitiveAgent
    from src.core.agents.hybrid_agent import HybridAgent
    from src.services.llm_service import LLMService
    from src.services.tool_service import ToolService
    from src.utils.logger import get_logger
except ImportError:
    # Fallback imports
    from core.agents import AgentFactory, get_agent_runtime
    from core.agents.cognitive_agent import CognitiveAgent
    from core.agents.hybrid_agent import HybridAgent
    from services.llm_service import LLMService
    from services.tool_service import ToolService
    from utils.logger import get_logger

# Configure logging
log_dir = Path("/app/logs")
log_dir.mkdir(exist_ok=True)
LOG_FILE = log_dir / f"swarm_mas_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = get_logger(__name__)

# ==============================================================================
# ENUMS AND CONSTANTS
# ==============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    TESTER = "tester"
    CREATIVE = "creative"
    VALIDATOR = "validator"

# ==============================================================================
# TASK DEFINITIONS
# ==============================================================================

@dataclass
class Task:
    """Enhanced task with full execution tracking"""
    id: str
    description: str
    status: TaskStatus
    subtasks: List['Task'] = field(default_factory=list)
    assigned_agent: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    validation_score: Optional[float] = None
    files_created: List[str] = field(default_factory=list)

# ==============================================================================
# ENHANCED LLM SERVICE
# ==============================================================================

class ProductionLLMService(LLMService):
    """Extended LLM service with task-specific capabilities"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("PRODUCTION_LLM")
    
    async def analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze a request to understand its nature and complexity"""
        prompt = f"""Analyze the following request and determine how to approach it.

Request: {request}

Return a JSON object with:
{{
    "type": "technical|creative|analysis|general",
    "complexity": "simple|medium|complex",
    "components": ["list", "of", "main", "components"],
    "requires_code": true/false,
    "requires_files": true/false,
    "estimated_subtasks": number,
    "approach": "recommended approach"
}}"""
        
        self.logger.info(f"Analyzing request: {request[:100]}...")
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})
    
    async def decompose_task(self, task: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down a task into concrete subtasks"""
        prompt = f"""Decompose the following task into specific, actionable subtasks.

Task: {task}
Analysis: {json.dumps(analysis, indent=2)}

Each subtask should be concrete and implementable. For example:
- "Design system architecture" 
- "Implement core functionality"
- "Write unit tests"
- "Create documentation"

Return JSON:
{{
    "subtasks": [
        {{
            "id": "1",
            "description": "specific actionable task",
            "type": "development|testing|analysis|creative",
            "dependencies": [],
            "estimated_time": "minutes"
        }}
    ]
}}"""
        
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {}).get('subtasks', [])
    
    async def solve_subtask(self, subtask: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Solve a specific subtask with code generation"""
        prompt = f"""Solve the following subtask completely.

Subtask: {subtask['description']}
Type: {subtask.get('type', 'general')}
Context: {context}

If this involves creating code, provide complete, working implementations.
Structure your response with clear sections.

Return JSON:
{{
    "solution": "detailed solution description",
    "code": "complete code if applicable",
    "steps": ["step 1", "step 2"],
    "files_to_create": [
        {{
            "path": "filename.py",
            "content": "full file content",
            "description": "what this file does"
        }}
    ],
    "validation": "how to verify this works"
}}"""
        
        result = await self.generate(prompt, json_response=True, max_tokens=2000)
        return result.get('response', {})
    
    async def validate_solution(self, task: str, solution: Any) -> Dict[str, Any]:
        """Validate a solution for quality and completeness"""
        prompt = f"""Validate the following solution.

Task: {task}
Solution: {json.dumps(solution, indent=2) if isinstance(solution, dict) else str(solution)}

Assess:
1. Does it fully address the task?
2. Is the implementation correct?
3. Are there any issues?

Return JSON:
{{
    "is_valid": true/false,
    "score": 0-100,
    "strengths": ["list of strengths"],
    "issues": ["list of issues"],
    "verdict": "accepted|needs_revision|rejected"
}}"""
        
        result = await self.generate(prompt, json_response=True)
        return result.get('response', {})

# ==============================================================================
# PRODUCTION AGENT
# ==============================================================================

class ProductionAgent:
    """Enhanced agent with real execution capabilities"""
    
    def __init__(self, role: AgentRole, agent_id: str, name: str):
        self.role = role
        self.agent_id = agent_id
        self.name = name
        self.tasks_completed = 0
        self.logger = logging.getLogger(f"AGENT_{name}")
        
    async def execute_task(self, task: Task, llm_service: ProductionLLMService, 
                          workspace: str) -> Dict[str, Any]:
        """Execute a task with real file creation"""
        self.logger.info(f"Executing task: {task.description}")
        
        try:
            # Get solution from LLM
            subtask_data = {
                'description': task.description,
                'type': task.metadata.get('type', 'general')
            }
            
            context = self._build_context(task)
            solution = await llm_service.solve_subtask(subtask_data, context)
            
            # Create files if needed
            if solution.get('files_to_create'):
                created_files = await self._create_files(solution['files_to_create'], workspace)
                task.files_created.extend(created_files)
                solution['created_files'] = created_files
            
            # Mark task complete
            task.status = TaskStatus.COMPLETED
            task.result = solution
            task.completed_at = time.time()
            self.tasks_completed += 1
            
            self.logger.info(f"Task completed successfully: {task.id}")
            return solution
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"error": str(e)}
    
    def _build_context(self, task: Task) -> str:
        """Build context from task metadata and dependencies"""
        context_parts = []
        
        if task.parent_task_id:
            context_parts.append(f"Parent task: {task.parent_task_id}")
        
        if task.metadata:
            context_parts.append(f"Metadata: {json.dumps(task.metadata)}")
            
        return "\n".join(context_parts)
    
    async def _create_files(self, files: List[Dict[str, Any]], workspace: str) -> List[str]:
        """Create actual files in the workspace"""
        created = []
        
        for file_info in files:
            try:
                filepath = os.path.join(workspace, file_info['path'])
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                
                created.append(filepath)
                self.logger.info(f"Created file: {filepath}")
                
            except Exception as e:
                self.logger.error(f"Failed to create file {file_info['path']}: {e}")
                
        return created

# ==============================================================================
# SWARM COORDINATOR
# ==============================================================================

class ProductionSwarmCoordinator:
    """Production-ready swarm coordinator with full task execution"""
    
    def __init__(self, workspace_root: str = "/app/agent_workspace"):
        self.swarm_id = str(uuid4())
        self.name = f"ProductionSwarm-{self.swarm_id[:8]}"
        self.workspace_root = workspace_root
        self.llm_service = ProductionLLMService()
        self.agents: Dict[str, ProductionAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: List[str] = []
        self.completed_tasks: List[str] = []
        self.logger = logging.getLogger("SWARM_COORDINATOR")
        
        # Create workspace
        self.workspace = os.path.join(workspace_root, f"swarm_{self.swarm_id[:8]}")
        os.makedirs(self.workspace, exist_ok=True)
        
        self.logger.info(f"Initialized {self.name} with workspace: {self.workspace}")
    
    async def initialize(self):
        """Initialize the swarm with agents"""
        self.logger.info("Initializing swarm agents...")
        
        # Create diverse agent pool
        agent_configs = [
            (AgentRole.COORDINATOR, "coordinator", "Chief Coordinator"),
            (AgentRole.ANALYST, "analyst1", "Senior Analyst"),
            (AgentRole.ANALYST, "analyst2", "Data Analyst"),
            (AgentRole.DEVELOPER, "dev1", "Lead Developer"),
            (AgentRole.DEVELOPER, "dev2", "Backend Developer"),
            (AgentRole.DEVELOPER, "dev3", "Frontend Developer"),
            (AgentRole.TESTER, "tester1", "QA Engineer"),
            (AgentRole.CREATIVE, "creative1", "Creative Designer"),
            (AgentRole.VALIDATOR, "validator1", "Quality Validator")
        ]
        
        for role, agent_id, name in agent_configs:
            agent = ProductionAgent(role, agent_id, name)
            self.agents[agent_id] = agent
            self.logger.info(f"Created agent: {name} ({role.value})")
        
        self.logger.info(f"Swarm initialized with {len(self.agents)} agents")
    
    async def process_request(self, request: str) -> Dict[str, Any]:
        """Process a request with full task decomposition and execution"""
        self.logger.info("="*80)
        self.logger.info(f"🤖 PROCESSING REQUEST: {request}")
        self.logger.info("="*80)
        
        start_time = time.time()
        
        try:
            # Create main task
            main_task = Task(
                id=str(uuid4()),
                description=request,
                status=TaskStatus.ANALYZING
            )
            self.tasks[main_task.id] = main_task
            
            # Phase 1: Analyze request
            self.logger.info("Phase 1: Analyzing request...")
            analysis = await self.llm_service.analyze_request(request)
            self.logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
            
            # Phase 2: Decompose into subtasks
            main_task.status = TaskStatus.PLANNING
            self.logger.info("Phase 2: Decomposing into subtasks...")
            subtasks_data = await self.llm_service.decompose_task(request, analysis)
            
            # Create subtask objects
            for st_data in subtasks_data:
                subtask = Task(
                    id=st_data.get('id', str(uuid4())),
                    description=st_data.get('description', ''),
                    status=TaskStatus.PENDING,
                    parent_task_id=main_task.id,
                    metadata=st_data,
                    dependencies=st_data.get('dependencies', [])
                )
                main_task.subtasks.append(subtask)
                self.tasks[subtask.id] = subtask
            
            self.logger.info(f"Created {len(main_task.subtasks)} subtasks")
            
            # Phase 3: Execute subtasks
            main_task.status = TaskStatus.EXECUTING
            self.logger.info("Phase 3: Executing subtasks...")
            
            results = await self._execute_subtasks(main_task.subtasks)
            
            # Phase 4: Validate results
            main_task.status = TaskStatus.VALIDATING
            self.logger.info("Phase 4: Validating results...")
            
            validations = []
            for subtask, result in zip(main_task.subtasks, results):
                validation = await self.llm_service.validate_solution(
                    subtask.description, 
                    result
                )
                validations.append(validation)
                subtask.validation_score = validation.get('score', 0)
            
            # Phase 5: Generate summary
            main_task.status = TaskStatus.COMPLETED
            main_task.completed_at = time.time()
            duration = main_task.completed_at - main_task.created_at
            
            # Calculate metrics
            total_files = sum(len(st.files_created) for st in main_task.subtasks)
            success_count = sum(1 for v in validations if v.get('is_valid', False))
            success_rate = (success_count / len(validations) * 100) if validations else 0
            
            # Generate report
            report = self._generate_report(main_task, results, validations)
            
            result = {
                "status": "completed",
                "duration": f"{duration:.2f} seconds",
                "request": request,
                "analysis": analysis,
                "subtasks_executed": len(main_task.subtasks),
                "files_created": total_files,
                "success_rate": f"{success_rate:.1f}%",
                "workspace": self.workspace,
                "report": report,
                "subtask_results": results,
                "validations": validations
            }
            
            self.logger.info("="*80)
            self.logger.info("✅ REQUEST COMPLETED SUCCESSFULLY")
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info(f"Success rate: {success_rate:.1f}%")
            self.logger.info(f"Files created: {total_files}")
            self.logger.info("="*80)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Request processing failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _execute_subtasks(self, subtasks: List[Task]) -> List[Dict[str, Any]]:
        """Execute subtasks with dependency management"""
        results = []
        completed = set()
        
        while len(completed) < len(subtasks):
            # Find executable tasks
            executable = []
            for i, task in enumerate(subtasks):
                if i in completed:
                    continue
                    
                # Check dependencies
                deps_met = all(
                    int(d) - 1 in completed 
                    for d in task.dependencies 
                    if d.isdigit()
                )
                
                if deps_met:
                    executable.append((i, task))
            
            if not executable:
                self.logger.error("Dependency deadlock detected!")
                break
            
            # Execute tasks in parallel
            batch_results = await asyncio.gather(*[
                self._execute_single_task(task) 
                for _, task in executable
            ])
            
            # Process results
            for (idx, task), result in zip(executable, batch_results):
                results.append(result)
                completed.add(idx)
                self.logger.info(f"Completed subtask {idx + 1}/{len(subtasks)}")
        
        return results
    
    async def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with agent assignment"""
        # Find suitable agent
        agent = self._find_suitable_agent(task)
        task.assigned_agent = agent.agent_id
        
        # Execute task
        result = await agent.execute_task(task, self.llm_service, self.workspace)
        
        return result
    
    def _find_suitable_agent(self, task: Task) -> ProductionAgent:
        """Find the most suitable agent for a task"""
        task_type = task.metadata.get('type', 'general')
        
        # Type to role mapping
        type_mapping = {
            'development': AgentRole.DEVELOPER,
            'testing': AgentRole.TESTER,
            'analysis': AgentRole.ANALYST,
            'creative': AgentRole.CREATIVE,
            'validation': AgentRole.VALIDATOR
        }
        
        preferred_role = type_mapping.get(task_type, AgentRole.COORDINATOR)
        
        # Find agent with preferred role and lowest task count
        suitable_agents = [
            agent for agent in self.agents.values() 
            if agent.role == preferred_role
        ]
        
        if not suitable_agents:
            suitable_agents = list(self.agents.values())
        
        # Return agent with lowest task count
        return min(suitable_agents, key=lambda a: a.tasks_completed)
    
    def _generate_report(self, main_task: Task, results: List[Dict[str, Any]], 
                        validations: List[Dict[str, Any]]) -> str:
        """Generate a detailed execution report"""
        report_lines = [
            f"# Execution Report",
            f"## Request: {main_task.description}",
            f"## Status: {main_task.status.value}",
            f"## Duration: {main_task.completed_at - main_task.created_at:.2f}s",
            "",
            "## Subtasks Executed:"
        ]
        
        for i, (subtask, result, validation) in enumerate(zip(main_task.subtasks, results, validations)):
            report_lines.extend([
                f"### {i+1}. {subtask.description}",
                f"- Agent: {self.agents[subtask.assigned_agent].name}",
                f"- Status: {subtask.status.value}",
                f"- Validation: {validation.get('verdict', 'unknown')} (Score: {validation.get('score', 0)})",
                f"- Files created: {len(subtask.files_created)}"
            ])
            
            if subtask.files_created:
                report_lines.append("- Files:")
                for file in subtask.files_created:
                    report_lines.append(f"  - {file}")
        
        report_lines.extend([
            "",
            "## Summary:",
            f"- Total subtasks: {len(main_task.subtasks)}",
            f"- Successful: {sum(1 for v in validations if v.get('is_valid', False))}",
            f"- Files created: {sum(len(st.files_created) for st in main_task.subtasks)}",
            f"- Workspace: {self.workspace}"
        ])
        
        return "\n".join(report_lines)

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production-Ready Swarm MAS")
    parser.add_argument("--mode", choices=["interactive", "request"], default="interactive")
    parser.add_argument("--request", type=str, help="Request to process (for request mode)")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🤖 PRODUCTION-READY SWARM MAS")
    print("="*80)
    
    # Initialize swarm
    coordinator = ProductionSwarmCoordinator()
    await coordinator.initialize()
    
    if args.mode == "request":
        if not args.request:
            print("❌ Error: --request argument required for request mode")
            return
        
        print(f"\n📝 Processing request: {args.request}")
        result = await coordinator.process_request(args.request)
        
        print("\n" + "="*60)
        print("✅ RESULT")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Duration: {result.get('duration', 'N/A')}")
        print(f"Tasks executed: {result.get('subtasks_executed', 0)}")
        print(f"Success rate: {result.get('success_rate', 'N/A')}")
        print(f"Files created: {result.get('files_created', 0)}")
        
        if result.get('workspace'):
            print(f"\n📁 Files created in: {result['workspace']}")
        
        # Save report
        if result.get('report'):
            report_file = os.path.join(coordinator.workspace, "execution_report.md")
            with open(report_file, 'w') as f:
                f.write(result['report'])
            print(f"📄 Detailed report saved to: {report_file}")
    
    else:  # Interactive mode
        print("\nInteractive mode. Enter requests or 'quit' to exit.")
        print("Example requests:")
        print("- create python sample lib")
        print("- build a REST API with authentication")
        print("- create unit tests for a calculator")
        
        while True:
            try:
                request = input("\n📝 Enter request: ").strip()
                if request.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not request:
                    continue
                
                result = await coordinator.process_request(request)
                
                print(f"\n✅ Completed!")
                print(f"Files created: {result.get('files_created', 0)}")
                print(f"Success rate: {result.get('success_rate', 'N/A')}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                logger.error(traceback.format_exc())
    
    print("\n👋 Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())