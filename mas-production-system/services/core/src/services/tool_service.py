"""
Tool Service for managing and executing agent tools
"""
import importlib
import inspect
from typing import Dict, Any, Callable, List, Optional, Type
import asyncio
from uuid import UUID

from src.utils.logger import get_logger
from src.monitoring import track_agent_action

logger = get_logger(__name__)

class Tool:
    """Base class for agent tools"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        raise NotImplementedError
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", False) and param_name not in params:
                raise ValueError(f"Required parameter '{param_name}' missing")
            
            if param_name in params:
                param_type = param_spec.get("type")
                if param_type and not isinstance(params[param_name], param_type):
                    raise TypeError(
                        f"Parameter '{param_name}' must be of type {param_type.__name__}"
                    )
        
        return True

class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._load_builtin_tools()
    
    def _load_builtin_tools(self):
        """Load built-in tools"""
        # Import coding tools
        try:
            from src.tools.coding_tools import CodingTools
            coding_tools = CodingTools()
            
            for tool_name, tool_func in coding_tools.tools.items():
                self.register_function_as_tool(
                    tool_name,
                    tool_func,
                    f"Coding tool: {tool_name}"
                )
        except Exception as e:
            logger.error(f"Failed to load coding tools: {e}")
        
        # Register other built-in tools
        self.register_tool(WebSearchTool())
        self.register_tool(FileReadTool())
        self.register_tool(FileWriteTool())
        self.register_tool(DatabaseQueryTool())
        self.register_tool(HTTPRequestTool())
    
    def register_tool(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_function_as_tool(
        self,
        name: str,
        func: Callable,
        description: str = ""
    ):
        """Register a function as a tool"""
        # Extract function signature
        sig = inspect.signature(func)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            param_info = {"required": param.default == param.empty}
            
            # Try to infer type from annotation
            if param.annotation != param.empty:
                param_info["type"] = param.annotation
            
            parameters[param_name] = param_info
        
        # Create tool wrapper
        class FunctionTool(Tool):
            def __init__(self):
                super().__init__(name, description, parameters)
                self.func = func
            
            async def execute(self, **kwargs) -> Dict[str, Any]:
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(self.func):
                    result = await self.func(**kwargs)
                else:
                    result = self.func(**kwargs)
                
                return {"result": result}
        
        self.register_tool(FunctionTool())
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]

class ToolService:
    """Service for executing tools on behalf of agents"""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.execution_history: Dict[UUID, List[Dict[str, Any]]] = {}
        
        # Capability to tools mapping
        self.capability_tools = {
            "conversation": ["web_search", "file_read"],
            "analyse": ["file_read", "db_query"],
            "conseil": ["web_search"],
            "coding": ["git_clone", "git_commit", "compile_code", "run_tests", "file_write"],
            "research": ["web_search", "file_read"],
            "planning": ["file_read", "file_write"],
            "communication": ["http_request"]
        }
    
    def get_tools_for_capability(self, capability: str) -> Dict[str, Tool]:
        """Get tools available for a given capability"""
        tool_names = self.capability_tools.get(capability, [])
        tools = {}
        
        for tool_name in tool_names:
            tool = self.registry.get_tool(tool_name)
            if tool:
                tools[tool_name] = tool
                
        return tools
    
    async def execute_tool(
        self,
        agent_id: UUID,
        tool_name: str,
        parameters: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Execute a tool for an agent"""
        tool = self.registry.get_tool(tool_name)
        
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Validate parameters
        try:
            tool.validate_parameters(parameters)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameters for tool {tool_name}: {e}")
            track_agent_action("unknown", f"tool_{tool_name}", success=False)
            return {
                "success": False,
                "error": str(e)
            }
        
        # Execute tool
        try:
            if dry_run:
                result = {
                    "success": True,
                    "data": {"message": "Dry run - no actual execution"},
                    "dry_run": True
                }
            else:
                result = await tool.execute(**parameters)
                result["success"] = True
            
            # Track execution
            track_agent_action("unknown", f"tool_{tool_name}", success=True)
            
            # Store in history
            if agent_id not in self.execution_history:
                self.execution_history[agent_id] = []
            
            self.execution_history[agent_id].append({
                "tool": tool_name,
                "parameters": parameters,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            track_agent_action("unknown", f"tool_{tool_name}", success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.registry.list_tools()
    
    def get_execution_history(
        self,
        agent_id: UUID,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get tool execution history for an agent"""
        history = self.execution_history.get(agent_id, [])
        
        if limit:
            return history[-limit:]
        
        return history
    
    def register_custom_tool(self, tool: Tool):
        """Register a custom tool"""
        self.registry.register_tool(tool)
    
    def register_custom_function(
        self,
        name: str,
        func: Callable,
        description: str = ""
    ):
        """Register a custom function as a tool"""
        self.registry.register_function_as_tool(name, func, description)

# Built-in tool implementations

class WebSearchTool(Tool):
    """Tool for web searching"""
    
    def __init__(self):
        super().__init__(
            "web_search",
            "Search the web for information",
            {
                "query": {"type": str, "required": True},
                "max_results": {"type": int, "required": False}
            }
        )
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute web search"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            return {
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise

class FileReadTool(Tool):
    """Tool for reading files"""
    
    def __init__(self):
        super().__init__(
            "file_read",
            "Read contents of a file",
            {
                "path": {"type": str, "required": True},
                "encoding": {"type": str, "required": False}
            }
        )
    
    async def execute(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read file contents"""
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "content": content,
                "size": len(content),
                "path": path
            }
        except Exception as e:
            logger.error(f"File read failed: {e}")
            raise

class FileWriteTool(Tool):
    """Tool for writing files"""
    
    def __init__(self):
        super().__init__(
            "file_write",
            "Write content to a file",
            {
                "path": {"type": str, "required": True},
                "content": {"type": str, "required": True},
                "mode": {"type": str, "required": False},
                "encoding": {"type": str, "required": False}
            }
        )
    
    async def execute(
        self,
        path: str,
        content: str,
        mode: str = "w",
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """Write content to file"""
        try:
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "path": path,
                "size": len(content),
                "mode": mode
            }
        except Exception as e:
            logger.error(f"File write failed: {e}")
            raise

class DatabaseQueryTool(Tool):
    """Tool for database queries"""
    
    def __init__(self):
        super().__init__(
            "db_query",
            "Execute database query",
            {
                "query": {"type": str, "required": True},
                "params": {"type": dict, "required": False}
            }
        )
    
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute database query"""
        from src.database import get_db
        
        try:
            async with get_db() as db:
                result = await db.execute(query, params or {})
                rows = result.fetchall()
            
            return {
                "rows": [dict(row) for row in rows],
                "count": len(rows)
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

class HTTPRequestTool(Tool):
    """Tool for making HTTP requests"""
    
    def __init__(self):
        super().__init__(
            "http_request",
            "Make HTTP request",
            {
                "url": {"type": str, "required": True},
                "method": {"type": str, "required": False},
                "headers": {"type": dict, "required": False},
                "data": {"type": dict, "required": False}
            }
        )
    
    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=data if method != "GET" else None,
                    params=data if method == "GET" else None
                )
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise

# Global instance
_tool_service: Optional[ToolService] = None

def get_tool_service() -> ToolService:
    """Get or create tool service instance"""
    global _tool_service
    if _tool_service is None:
        _tool_service = ToolService()
    return _tool_service

__all__ = ["Tool", "ToolRegistry", "ToolService", "get_tool_service"]