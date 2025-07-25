"""
Enhanced Task Execution System for MAS

This module provides comprehensive task execution capabilities including:
1. Proper task decomposition into actionable subtasks
2. Intelligent assignment to appropriate agents
3. Real work execution including file creation
4. Result validation and error handling
5. Graceful error recovery and retries
"""

import asyncio
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum

from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    DECOMPOSING = "decomposing"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SubtaskType(Enum):
    """Types of subtasks for proper routing"""
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class EnhancedTaskExecutor:
    """Enhanced task execution with proper decomposition and validation"""
    
    def __init__(
        self,
        llm_service: LLMService,
        tool_service: Optional[ToolService] = None,
        workspace_path: str = "./agent_workspace",
        max_retries: int = 3
    ):
        self.llm_service = llm_service
        self.tool_service = tool_service or ToolService()
        self.workspace_path = Path(workspace_path)
        self.max_retries = max_retries
        
        # Task tracking
        self.active_tasks: Dict[UUID, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.subtask_results: Dict[UUID, Dict[str, Any]] = {}
        
        # Agent capabilities mapping
        self.agent_capabilities = {
            "architect": [SubtaskType.DESIGN, SubtaskType.ANALYSIS],
            "developer": [SubtaskType.IMPLEMENTATION, SubtaskType.DEPLOYMENT],
            "tester": [SubtaskType.TESTING, SubtaskType.VALIDATION],
            "analyst": [SubtaskType.ANALYSIS, SubtaskType.MONITORING],
            "documenter": [SubtaskType.DOCUMENTATION],
        }
        
        # Ensure workspace exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    async def execute_task(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        agents: Optional[Dict[UUID, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete task with proper decomposition and validation
        
        Args:
            request: The task request/description
            context: Optional context information
            agents: Available agents for task assignment
            
        Returns:
            Complete task execution result with all outputs
        """
        task_id = uuid4()
        start_time = datetime.utcnow()
        
        task_record = {
            "id": task_id,
            "request": request,
            "context": context or {},
            "status": TaskStatus.PENDING,
            "start_time": start_time,
            "subtasks": [],
            "results": {},
            "errors": [],
            "retries": 0
        }
        
        self.active_tasks[task_id] = task_record
        
        try:
            # 1. Analyze the request
            logger.info(f"Task {task_id}: Analyzing request...")
            task_record["status"] = TaskStatus.ANALYZING
            analysis = await self._analyze_request(request, context)
            task_record["analysis"] = analysis
            
            # 2. Decompose into subtasks
            logger.info(f"Task {task_id}: Decomposing into subtasks...")
            task_record["status"] = TaskStatus.DECOMPOSING
            subtasks = await self._decompose_task(request, analysis)
            task_record["subtasks"] = subtasks
            
            # 3. Assign subtasks to agents
            logger.info(f"Task {task_id}: Assigning subtasks to agents...")
            task_record["status"] = TaskStatus.ASSIGNED
            assignments = await self._assign_subtasks(subtasks, agents)
            task_record["assignments"] = assignments
            
            # 4. Execute subtasks
            logger.info(f"Task {task_id}: Executing {len(subtasks)} subtasks...")
            task_record["status"] = TaskStatus.EXECUTING
            results = await self._execute_subtasks(task_id, subtasks, assignments)
            task_record["results"] = results
            
            # 5. Validate results
            logger.info(f"Task {task_id}: Validating results...")
            task_record["status"] = TaskStatus.VALIDATING
            validation = await self._validate_results(request, results, analysis)
            task_record["validation"] = validation
            
            # 6. Handle validation failures
            if not validation["is_valid"]:
                if task_record["retries"] < self.max_retries:
                    logger.warning(f"Task {task_id}: Validation failed, retrying...")
                    task_record["retries"] += 1
                    task_record["status"] = TaskStatus.RETRYING
                    return await self._retry_task(task_id, validation["issues"])
                else:
                    raise Exception(f"Task failed validation after {self.max_retries} retries")
            
            # Success!
            task_record["status"] = TaskStatus.COMPLETED
            task_record["end_time"] = datetime.utcnow()
            task_record["duration"] = (task_record["end_time"] - start_time).total_seconds()
            
            # Move to history
            self.task_history.append(task_record)
            del self.active_tasks[task_id]
            
            return {
                "success": True,
                "task_id": str(task_id),
                "request": request,
                "analysis": analysis,
                "subtasks": len(subtasks),
                "results": results,
                "validation": validation,
                "duration": task_record["duration"],
                "outputs": self._collect_outputs(results)
            }
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            task_record["status"] = TaskStatus.FAILED
            task_record["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            # Move to history
            self.task_history.append(task_record)
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            return {
                "success": False,
                "task_id": str(task_id),
                "request": request,
                "error": str(e),
                "errors": task_record["errors"]
            }
    
    async def _analyze_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze the request to understand intent and requirements"""
        try:
            # Use LLM to analyze the request
            analysis = await self.llm_service.analyze_request(request)
            
            # Enhance with context
            if context:
                analysis["context"] = context
            
            # Determine task type and complexity
            analysis["task_type"] = self._determine_task_type(request, analysis)
            analysis["complexity"] = self._estimate_complexity(request, analysis)
            analysis["required_outputs"] = self._identify_outputs(request, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze request: {str(e)}")
            # Fallback analysis
            return {
                "objective": request,
                "task_type": "general",
                "complexity": "medium",
                "required_outputs": ["implementation"],
                "components": [request]
            }
    
    async def _decompose_task(
        self,
        request: str,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Decompose task into actionable subtasks"""
        try:
            # Use LLM for decomposition
            decomposition = await self.llm_service.decompose_task(request, analysis)
            
            # Ensure proper structure
            subtasks = []
            for idx, item in enumerate(decomposition):
                subtask = {
                    "id": str(uuid4()),
                    "index": idx,
                    "description": item.get("description", f"Subtask {idx + 1}"),
                    "type": self._classify_subtask(item),
                    "dependencies": item.get("dependencies", []),
                    "priority": item.get("priority", "medium"),
                    "estimated_time": item.get("estimated_time", 300),  # 5 min default
                    "required_tools": item.get("required_tools", []),
                    "success_criteria": item.get("success_criteria", []),
                    "status": TaskStatus.PENDING
                }
                subtasks.append(subtask)
            
            # If no subtasks generated, create default ones
            if not subtasks:
                subtasks = self._create_default_subtasks(request, analysis)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Failed to decompose task: {str(e)}")
            return self._create_default_subtasks(request, analysis)
    
    def _create_default_subtasks(
        self,
        request: str,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create default subtasks based on task type"""
        task_type = analysis.get("task_type", "general")
        
        if "test" in request.lower():
            return [
                {
                    "id": str(uuid4()),
                    "index": 0,
                    "description": "Design test structure and strategy",
                    "type": SubtaskType.DESIGN,
                    "dependencies": [],
                    "priority": "high",
                    "estimated_time": 300,
                    "required_tools": ["code_generator"],
                    "success_criteria": ["test_plan_created"],
                    "status": TaskStatus.PENDING
                },
                {
                    "id": str(uuid4()),
                    "index": 1,
                    "description": "Implement test cases with assertions",
                    "type": SubtaskType.IMPLEMENTATION,
                    "dependencies": [0],
                    "priority": "high",
                    "estimated_time": 600,
                    "required_tools": ["code_generator", "file_writer"],
                    "success_criteria": ["tests_implemented"],
                    "status": TaskStatus.PENDING
                },
                {
                    "id": str(uuid4()),
                    "index": 2,
                    "description": "Validate test execution",
                    "type": SubtaskType.VALIDATION,
                    "dependencies": [1],
                    "priority": "medium",
                    "estimated_time": 300,
                    "required_tools": ["test_runner"],
                    "success_criteria": ["tests_pass"],
                    "status": TaskStatus.PENDING
                }
            ]
        else:
            # Generic implementation task
            return [
                {
                    "id": str(uuid4()),
                    "index": 0,
                    "description": f"Analyze requirements for: {request}",
                    "type": SubtaskType.ANALYSIS,
                    "dependencies": [],
                    "priority": "high",
                    "estimated_time": 300,
                    "required_tools": [],
                    "success_criteria": ["requirements_analyzed"],
                    "status": TaskStatus.PENDING
                },
                {
                    "id": str(uuid4()),
                    "index": 1,
                    "description": "Design solution architecture",
                    "type": SubtaskType.DESIGN,
                    "dependencies": [0],
                    "priority": "high",
                    "estimated_time": 300,
                    "required_tools": [],
                    "success_criteria": ["design_completed"],
                    "status": TaskStatus.PENDING
                },
                {
                    "id": str(uuid4()),
                    "index": 2,
                    "description": "Implement core functionality",
                    "type": SubtaskType.IMPLEMENTATION,
                    "dependencies": [1],
                    "priority": "high",
                    "estimated_time": 900,
                    "required_tools": ["code_generator", "file_writer"],
                    "success_criteria": ["code_implemented"],
                    "status": TaskStatus.PENDING
                },
                {
                    "id": str(uuid4()),
                    "index": 3,
                    "description": "Create tests and validate",
                    "type": SubtaskType.TESTING,
                    "dependencies": [2],
                    "priority": "medium",
                    "estimated_time": 600,
                    "required_tools": ["code_generator", "test_runner"],
                    "success_criteria": ["tests_pass"],
                    "status": TaskStatus.PENDING
                }
            ]
    
    async def _assign_subtasks(
        self,
        subtasks: List[Dict[str, Any]],
        agents: Optional[Dict[UUID, Any]] = None
    ) -> Dict[str, UUID]:
        """Assign subtasks to appropriate agents"""
        assignments = {}
        
        if not agents:
            # No agents available, assign to virtual agents
            for subtask in subtasks:
                assignments[subtask["id"]] = uuid4()
            return assignments
        
        # Group agents by capability
        agents_by_capability = {}
        for agent_id, agent in agents.items():
            role = agent.role if hasattr(agent, 'role') else 'general'
            if role not in agents_by_capability:
                agents_by_capability[role] = []
            agents_by_capability[role].append(agent_id)
        
        # Assign based on subtask type and agent capabilities
        for subtask in subtasks:
            subtask_type = subtask["type"]
            assigned = False
            
            # Find agents that can handle this subtask type
            for role, capabilities in self.agent_capabilities.items():
                if subtask_type in capabilities and role in agents_by_capability:
                    # Use round-robin assignment
                    agent_list = agents_by_capability[role]
                    agent_id = agent_list[len(assignments) % len(agent_list)]
                    assignments[subtask["id"]] = agent_id
                    assigned = True
                    break
            
            # Fallback: assign to any available agent
            if not assigned:
                all_agents = list(agents.keys())
                assignments[subtask["id"]] = all_agents[len(assignments) % len(all_agents)]
        
        return assignments
    
    async def _execute_subtasks(
        self,
        task_id: UUID,
        subtasks: List[Dict[str, Any]],
        assignments: Dict[str, UUID]
    ) -> Dict[str, Any]:
        """Execute subtasks in dependency order"""
        results = {}
        completed = set()
        
        # Execute subtasks respecting dependencies
        while len(completed) < len(subtasks):
            # Find subtasks ready to execute
            ready_subtasks = []
            for subtask in subtasks:
                if subtask["id"] in completed:
                    continue
                
                # Check if dependencies are satisfied
                deps_satisfied = all(
                    subtasks[dep]["id"] in completed
                    for dep in subtask["dependencies"]
                )
                
                if deps_satisfied:
                    ready_subtasks.append(subtask)
            
            if not ready_subtasks:
                logger.error("No subtasks ready to execute - possible circular dependency")
                break
            
            # Execute ready subtasks in parallel
            execution_tasks = []
            for subtask in ready_subtasks:
                agent_id = assignments.get(subtask["id"])
                execution_tasks.append(
                    self._execute_single_subtask(task_id, subtask, agent_id, results)
                )
            
            # Wait for completion
            subtask_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Process results
            for subtask, result in zip(ready_subtasks, subtask_results):
                if isinstance(result, Exception):
                    logger.error(f"Subtask {subtask['id']} failed: {str(result)}")
                    results[subtask["id"]] = {
                        "success": False,
                        "error": str(result),
                        "subtask": subtask
                    }
                else:
                    results[subtask["id"]] = result
                
                completed.add(subtask["id"])
        
        return results
    
    async def _execute_single_subtask(
        self,
        task_id: UUID,
        subtask: Dict[str, Any],
        agent_id: Optional[UUID],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single subtask"""
        try:
            logger.info(f"Executing subtask: {subtask['description']}")
            
            # Build context from previous results
            context = {
                "task_id": str(task_id),
                "subtask_id": subtask["id"],
                "previous_results": {
                    str(dep): previous_results.get(subtasks[dep]["id"], {})
                    for dep in subtask["dependencies"]
                    if dep < len(subtasks)
                } if "subtasks" in locals() else {}
            }
            
            # Execute based on subtask type
            if subtask["type"] == SubtaskType.IMPLEMENTATION:
                result = await self._execute_implementation(subtask, context)
            elif subtask["type"] == SubtaskType.TESTING:
                result = await self._execute_testing(subtask, context)
            elif subtask["type"] == SubtaskType.DESIGN:
                result = await self._execute_design(subtask, context)
            elif subtask["type"] == SubtaskType.ANALYSIS:
                result = await self._execute_analysis(subtask, context)
            else:
                result = await self._execute_generic(subtask, context)
            
            return {
                "success": True,
                "subtask": subtask,
                "agent_id": str(agent_id) if agent_id else None,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute subtask {subtask['id']}: {str(e)}")
            raise
    
    async def _execute_implementation(
        self,
        subtask: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute implementation subtask - creates actual files"""
        try:
            # Generate code using LLM
            prompt = f"""
            Task: {subtask['description']}
            
            Context: {json.dumps(context, indent=2)}
            
            Generate complete, working code that implements this task.
            Include proper error handling and documentation.
            """
            
            code = await self.llm_service.generate_code(prompt)
            
            # Determine filename
            filename = self._generate_filename(subtask['description'])
            filepath = self.workspace_path / filename
            
            # Write code to file
            filepath.write_text(code)
            logger.info(f"Created file: {filepath}")
            
            # Also save to subtask results
            self.subtask_results[subtask["id"]] = {
                "type": "implementation",
                "file": str(filepath),
                "content": code,
                "size": len(code)
            }
            
            return {
                "type": "implementation",
                "outputs": {
                    "file": str(filepath),
                    "filename": filename,
                    "size": len(code),
                    "language": self._detect_language(filename)
                }
            }
            
        except Exception as e:
            logger.error(f"Implementation failed: {str(e)}")
            raise
    
    async def _execute_testing(
        self,
        subtask: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute testing subtask"""
        try:
            # Generate test code
            prompt = f"""
            Task: {subtask['description']}
            
            Context: {json.dumps(context, indent=2)}
            
            Generate comprehensive test cases with proper assertions.
            Include edge cases and error scenarios.
            """
            
            test_code = await self.llm_service.generate_code(prompt)
            
            # Write test file
            filename = self._generate_filename(subtask['description'], prefix="test_")
            filepath = self.workspace_path / filename
            filepath.write_text(test_code)
            
            logger.info(f"Created test file: {filepath}")
            
            return {
                "type": "testing",
                "outputs": {
                    "file": str(filepath),
                    "filename": filename,
                    "test_count": test_code.count("def test_"),
                    "assertions": test_code.count("assert")
                }
            }
            
        except Exception as e:
            logger.error(f"Testing failed: {str(e)}")
            raise
    
    async def _execute_design(
        self,
        subtask: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute design subtask"""
        try:
            # Generate design document
            prompt = f"""
            Task: {subtask['description']}
            
            Context: {json.dumps(context, indent=2)}
            
            Create a detailed design document including:
            - Architecture overview
            - Component descriptions
            - Data flow
            - Key design decisions
            """
            
            design = await self.llm_service.analyze_request(prompt)
            
            # Save design document
            filename = self._generate_filename(subtask['description'], ext=".md")
            filepath = self.workspace_path / filename
            
            design_content = f"""# Design Document

## Task: {subtask['description']}

## Overview
{design.get('overview', 'Design overview')}

## Architecture
{design.get('architecture', 'Architecture details')}

## Components
{json.dumps(design.get('components', []), indent=2)}

## Implementation Plan
{json.dumps(design.get('plan', []), indent=2)}

Generated at: {datetime.utcnow().isoformat()}
"""
            
            filepath.write_text(design_content)
            logger.info(f"Created design document: {filepath}")
            
            return {
                "type": "design",
                "outputs": {
                    "file": str(filepath),
                    "filename": filename,
                    "design": design
                }
            }
            
        except Exception as e:
            logger.error(f"Design failed: {str(e)}")
            raise
    
    async def _execute_analysis(
        self,
        subtask: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute analysis subtask"""
        try:
            # Perform analysis
            analysis = await self.llm_service.analyze_request(subtask['description'])
            
            # Save analysis report
            filename = self._generate_filename(subtask['description'], prefix="analysis_", ext=".json")
            filepath = self.workspace_path / filename
            
            analysis_data = {
                "subtask": subtask,
                "context": context,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            filepath.write_text(json.dumps(analysis_data, indent=2))
            logger.info(f"Created analysis report: {filepath}")
            
            return {
                "type": "analysis",
                "outputs": {
                    "file": str(filepath),
                    "filename": filename,
                    "findings": analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    async def _execute_generic(
        self,
        subtask: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute generic subtask"""
        try:
            # Use LLM to execute generic task
            result = await self.llm_service.analyze_request(subtask['description'])
            
            # Save result
            filename = self._generate_filename(subtask['description'], ext=".json")
            filepath = self.workspace_path / filename
            
            result_data = {
                "subtask": subtask,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            filepath.write_text(json.dumps(result_data, indent=2))
            
            return {
                "type": "generic",
                "outputs": {
                    "file": str(filepath),
                    "filename": filename,
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Generic execution failed: {str(e)}")
            raise
    
    async def _validate_results(
        self,
        request: str,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that results meet requirements"""
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "summary": {}
        }
        
        try:
            # Check if all subtasks completed successfully
            failed_subtasks = [
                sid for sid, result in results.items()
                if not result.get("success", False)
            ]
            
            if failed_subtasks:
                validation["is_valid"] = False
                validation["issues"].append(f"Failed subtasks: {failed_subtasks}")
            
            # Check if required outputs were created
            required_outputs = analysis.get("required_outputs", ["implementation"])
            created_outputs = self._collect_outputs(results)
            
            for required in required_outputs:
                if required not in created_outputs:
                    validation["is_valid"] = False
                    validation["issues"].append(f"Missing required output: {required}")
            
            # Validate file creation
            created_files = []
            for result in results.values():
                if result.get("success") and "result" in result:
                    outputs = result["result"].get("outputs", {})
                    if "file" in outputs:
                        filepath = Path(outputs["file"])
                        if filepath.exists():
                            created_files.append(str(filepath))
                        else:
                            validation["warnings"].append(f"File not found: {filepath}")
            
            validation["summary"]["total_subtasks"] = len(results)
            validation["summary"]["successful_subtasks"] = len(results) - len(failed_subtasks)
            validation["summary"]["created_files"] = len(created_files)
            validation["summary"]["files"] = created_files
            
            # Use LLM to validate completeness
            llm_validation = await self._llm_validate_results(request, results, analysis)
            if not llm_validation.get("complete", True):
                validation["warnings"].append(llm_validation.get("reason", "Incomplete implementation"))
            
            return validation
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            validation["is_valid"] = False
            validation["issues"].append(f"Validation error: {str(e)}")
            return validation
    
    async def _llm_validate_results(
        self,
        request: str,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to validate if results meet the request"""
        try:
            prompt = f"""
            Validate if the following results successfully complete the requested task.
            
            Original Request: {request}
            
            Analysis: {json.dumps(analysis, indent=2)}
            
            Results Summary:
            {self._summarize_results(results)}
            
            Return JSON with:
            - complete: boolean
            - reason: string (if not complete)
            - suggestions: list of improvements
            """
            
            validation = await self.llm_service.analyze_request(prompt)
            return validation
            
        except Exception as e:
            logger.error(f"LLM validation failed: {str(e)}")
            return {"complete": True}  # Assume complete if validation fails
    
    async def _retry_task(
        self,
        task_id: UUID,
        issues: List[str]
    ) -> Dict[str, Any]:
        """Retry task with corrections based on validation issues"""
        task_record = self.active_tasks.get(task_id)
        if not task_record:
            raise Exception(f"Task {task_id} not found for retry")
        
        # Add issues to context for retry
        enhanced_context = task_record.get("context", {})
        enhanced_context["retry_issues"] = issues
        enhanced_context["previous_results"] = task_record.get("results", {})
        
        # Re-execute with enhanced context
        return await self.execute_task(
            request=task_record["request"],
            context=enhanced_context,
            agents=task_record.get("agents")
        )
    
    def _determine_task_type(self, request: str, analysis: Dict[str, Any]) -> str:
        """Determine the type of task from request"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["test", "testing", "unittest"]):
            return "testing"
        elif any(word in request_lower for word in ["implement", "create", "build", "develop"]):
            return "implementation"
        elif any(word in request_lower for word in ["design", "architect", "plan"]):
            return "design"
        elif any(word in request_lower for word in ["analyze", "review", "assess"]):
            return "analysis"
        elif any(word in request_lower for word in ["deploy", "release", "publish"]):
            return "deployment"
        else:
            return "general"
    
    def _estimate_complexity(self, request: str, analysis: Dict[str, Any]) -> str:
        """Estimate task complexity"""
        components = analysis.get("components", [])
        
        if len(components) <= 2:
            return "simple"
        elif len(components) <= 5:
            return "medium"
        else:
            return "complex"
    
    def _identify_outputs(self, request: str, analysis: Dict[str, Any]) -> List[str]:
        """Identify required outputs from the task"""
        outputs = []
        request_lower = request.lower()
        
        if "test" in request_lower:
            outputs.extend(["tests", "test_results"])
        if any(word in request_lower for word in ["implement", "create", "build"]):
            outputs.append("implementation")
        if "document" in request_lower:
            outputs.append("documentation")
        if "deploy" in request_lower:
            outputs.append("deployment")
        
        if not outputs:
            outputs = ["implementation"]
        
        return outputs
    
    def _classify_subtask(self, subtask_data: Dict[str, Any]) -> SubtaskType:
        """Classify subtask type based on description"""
        description = subtask_data.get("description", "").lower()
        
        if any(word in description for word in ["test", "validate", "verify"]):
            return SubtaskType.TESTING
        elif any(word in description for word in ["implement", "code", "develop"]):
            return SubtaskType.IMPLEMENTATION
        elif any(word in description for word in ["design", "architect", "plan"]):
            return SubtaskType.DESIGN
        elif any(word in description for word in ["analyze", "review", "assess"]):
            return SubtaskType.ANALYSIS
        elif any(word in description for word in ["document", "docs"]):
            return SubtaskType.DOCUMENTATION
        elif any(word in description for word in ["deploy", "release"]):
            return SubtaskType.DEPLOYMENT
        else:
            return SubtaskType.IMPLEMENTATION
    
    def _generate_filename(
        self,
        description: str,
        prefix: str = "",
        ext: str = ".py"
    ) -> str:
        """Generate filename from description"""
        # Clean description for filename
        clean_desc = description.lower()
        clean_desc = clean_desc.replace(" ", "_")
        clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "_")
        clean_desc = clean_desc[:50]  # Limit length
        
        # Add unique suffix
        unique_suffix = str(uuid4())[:8]
        
        filename = f"{prefix}{clean_desc}_{unique_suffix}{ext}"
        return filename
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        ext = Path(filename).suffix.lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".m": "matlab",
            ".jl": "julia",
            ".sh": "bash",
            ".ps1": "powershell",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".md": "markdown",
            ".txt": "text"
        }
        
        return language_map.get(ext, "unknown")
    
    def _collect_outputs(self, results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Collect all outputs from results"""
        outputs = {}
        
        for result in results.values():
            if result.get("success") and "result" in result:
                output_type = result["result"].get("type", "unknown")
                output_data = result["result"].get("outputs", {})
                
                if output_type not in outputs:
                    outputs[output_type] = []
                
                if "file" in output_data:
                    outputs[output_type].append(output_data["file"])
        
        return outputs
    
    def _summarize_results(self, results: Dict[str, Any]) -> str:
        """Create a summary of results for validation"""
        summary_parts = []
        
        for sid, result in results.items():
            if result.get("success"):
                subtask = result.get("subtask", {})
                outputs = result.get("result", {}).get("outputs", {})
                summary_parts.append(
                    f"- {subtask.get('description', 'Unknown')}: "
                    f"Created {outputs.get('filename', 'output')}"
                )
            else:
                summary_parts.append(
                    f"- Failed: {result.get('error', 'Unknown error')}"
                )
        
        return "\n".join(summary_parts)
    
    def get_task_status(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "id": str(task_id),
                "status": task["status"].value,
                "subtasks_total": len(task.get("subtasks", [])),
                "subtasks_completed": len(task.get("results", {})),
                "start_time": task["start_time"].isoformat(),
                "duration": (datetime.utcnow() - task["start_time"]).total_seconds()
            }
        
        # Check history
        for task in self.task_history:
            if task["id"] == task_id:
                return {
                    "id": str(task_id),
                    "status": task["status"].value,
                    "subtasks_total": len(task.get("subtasks", [])),
                    "subtasks_completed": len(task.get("results", {})),
                    "start_time": task["start_time"].isoformat(),
                    "end_time": task.get("end_time", datetime.utcnow()).isoformat(),
                    "duration": task.get("duration", 0)
                }
        
        return None
    
    def get_workspace_files(self) -> List[Dict[str, Any]]:
        """Get list of files created in workspace"""
        files = []
        
        for file_path in self.workspace_path.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "language": self._detect_language(file_path.name)
                })
        
        return sorted(files, key=lambda f: f["modified"], reverse=True)