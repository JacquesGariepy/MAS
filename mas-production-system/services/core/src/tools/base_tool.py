"""
Base class for all tools in the MAS system
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseTool:
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.parameters = {}
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        # Basic validation - can be overridden by subclasses
        return True