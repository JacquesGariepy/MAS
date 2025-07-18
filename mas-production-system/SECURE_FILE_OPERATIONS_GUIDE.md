# Secure File Operations Implementation Guide

## Quick Start: Enabling Secure File Creation for Agents

This guide provides practical steps to enable agents to create files securely in the MAS production system.

## 1. Immediate Solution (Can be implemented now)

### 1.1 Create Secure File Tool

Create a new file `/services/core/src/tools/secure_file_tools.py`:

```python
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID
import hashlib
from datetime import datetime

from src.services.tool_service import Tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SecureFileWriteTool(Tool):
    """Secure file writing with sandboxing and validation"""
    
    def __init__(self):
        super().__init__(
            "secure_file_write",
            "Securely write content to a file within agent workspace",
            {
                "filename": {"type": str, "required": True},
                "content": {"type": str, "required": True},
                "directory": {"type": str, "required": False},
                "mode": {"type": str, "required": False}
            }
        )
        # Base sandbox directory
        self.sandbox_base = Path("/app/agent_workspaces")
        self.sandbox_base.mkdir(parents=True, exist_ok=True)
        
        # Security limits
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_path_length = 255
        self.allowed_extensions = [
            '.txt', '.json', '.yaml', '.yml', '.md', '.csv',
            '.py', '.js', '.html', '.css', '.xml', '.log'
        ]
    
    def get_agent_workspace(self, agent_id: UUID) -> Path:
        """Get or create agent-specific workspace"""
        workspace = self.sandbox_base / str(agent_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace
    
    def validate_filename(self, filename: str) -> bool:
        """Validate filename for security"""
        # Check for path traversal
        if '..' in filename or filename.startswith('/'):
            raise ValueError("Invalid filename: path traversal detected")
        
        # Check length
        if len(filename) > self.max_path_length:
            raise ValueError(f"Filename too long (max {self.max_path_length})")
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext and ext not in self.allowed_extensions:
            raise ValueError(f"File extension {ext} not allowed")
        
        # Check for special characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in invalid_chars):
            raise ValueError("Filename contains invalid characters")
        
        return True
    
    async def execute(
        self,
        agent_id: UUID,
        filename: str,
        content: str,
        directory: str = "",
        mode: str = "w"
    ) -> Dict[str, Any]:
        """Execute secure file write"""
        try:
            # Validate inputs
            self.validate_filename(filename)
            
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > self.max_file_size:
                raise ValueError(f"Content too large ({content_size} bytes, max {self.max_file_size})")
            
            # Get agent workspace
            workspace = self.get_agent_workspace(agent_id)
            
            # Build safe path
            if directory:
                self.validate_filename(directory)  # Validate directory name too
                target_dir = workspace / directory
                target_dir.mkdir(parents=True, exist_ok=True)
                file_path = target_dir / filename
            else:
                file_path = workspace / filename
            
            # Ensure path is within workspace
            try:
                file_path = file_path.resolve()
                workspace = workspace.resolve()
                if not str(file_path).startswith(str(workspace)):
                    raise ValueError("Path escape detected")
            except:
                raise ValueError("Invalid path")
            
            # Write file
            if mode not in ['w', 'a']:
                mode = 'w'
            
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            # Set secure permissions (owner read/write only)
            os.chmod(file_path, 0o600)
            
            # Log operation
            logger.info(f"Agent {agent_id} wrote file: {file_path.relative_to(workspace)}")
            
            return {
                "success": True,
                "path": str(file_path.relative_to(workspace)),
                "absolute_path": str(file_path),
                "size": content_size,
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Secure file write failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class SecureFileReadTool(Tool):
    """Secure file reading within agent workspace"""
    
    def __init__(self):
        super().__init__(
            "secure_file_read",
            "Securely read files from agent workspace",
            {
                "filename": {"type": str, "required": True},
                "directory": {"type": str, "required": False}
            }
        )
        self.sandbox_base = Path("/app/agent_workspaces")
    
    async def execute(
        self,
        agent_id: UUID,
        filename: str,
        directory: str = ""
    ) -> Dict[str, Any]:
        """Execute secure file read"""
        try:
            # Get agent workspace
            workspace = self.sandbox_base / str(agent_id)
            
            # Build path
            if directory:
                file_path = workspace / directory / filename
            else:
                file_path = workspace / filename
            
            # Security check
            file_path = file_path.resolve()
            workspace = workspace.resolve()
            if not str(file_path).startswith(str(workspace)):
                raise ValueError("Path escape detected")
            
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filename}")
            
            # Read file
            content = file_path.read_text(encoding='utf-8')
            
            return {
                "success": True,
                "content": content,
                "path": str(file_path.relative_to(workspace)),
                "size": len(content),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Secure file read failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class SecureFileListTool(Tool):
    """List files in agent workspace"""
    
    def __init__(self):
        super().__init__(
            "secure_file_list",
            "List files in agent workspace",
            {
                "directory": {"type": str, "required": False},
                "pattern": {"type": str, "required": False}
            }
        )
        self.sandbox_base = Path("/app/agent_workspaces")
    
    async def execute(
        self,
        agent_id: UUID,
        directory: str = "",
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """List files in workspace"""
        try:
            workspace = self.sandbox_base / str(agent_id)
            
            if directory:
                search_path = workspace / directory
            else:
                search_path = workspace
            
            # Security check
            search_path = search_path.resolve()
            workspace = workspace.resolve()
            if not str(search_path).startswith(str(workspace)):
                raise ValueError("Path escape detected")
            
            # List files
            files = []
            if search_path.exists():
                for file_path in search_path.glob(pattern):
                    if file_path.is_file():
                        files.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(workspace)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat()
                        })
            
            return {
                "success": True,
                "files": files,
                "count": len(files),
                "directory": directory or "/"
            }
            
        except Exception as e:
            logger.error(f"Secure file list failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
```

### 1.2 Update Tool Service

Modify `/services/core/src/services/tool_service.py` to include secure tools:

```python
# In _load_builtin_tools method, add:
from src.tools.secure_file_tools import (
    SecureFileWriteTool, 
    SecureFileReadTool, 
    SecureFileListTool
)

# Register secure tools
self.register_tool(SecureFileWriteTool())
self.register_tool(SecureFileReadTool())
self.register_tool(SecureFileListTool())

# Update capability mappings
self.capability_tools = {
    "conversation": ["web_search", "secure_file_read"],
    "analyse": ["secure_file_read", "db_query"],
    "conseil": ["web_search"],
    "coding": [
        "git_clone", "git_commit", "compile_code", 
        "run_tests", "secure_file_write", "secure_file_read",
        "secure_file_list"
    ],
    "research": ["web_search", "secure_file_read"],
    "planning": ["secure_file_read", "secure_file_write"],
    "communication": ["http_request"]
}
```

### 1.3 Update Docker Compose

Add workspace volume to `docker-compose.dev.yml`:

```yaml
services:
  core:
    volumes:
      - ./services/core/src:/app/src
      - ./logs:/app/logs
      - ./examples:/app/examples
      - agent_workspaces:/app/agent_workspaces  # Add this
    environment:
      - AGENT_WORKSPACE_PATH=/app/agent_workspaces

volumes:
  agent_workspaces:  # Add this
  postgres-data:
  redis-data:
```

## 2. Usage Example

### 2.1 Agent Using Secure File Operations

```python
# Example: Agent creating a report
class ReportingAgent(BaseAgent):
    async def create_report(self, data: Dict[str, Any]):
        # Use secure file write
        result = await self.tool_service.execute_tool(
            self.agent_id,
            "secure_file_write",
            {
                "filename": "analysis_report.md",
                "content": self.generate_report(data),
                "directory": "reports"
            }
        )
        
        if result["success"]:
            logger.info(f"Report saved to: {result['path']}")
        else:
            logger.error(f"Failed to save report: {result['error']}")
```

### 2.2 Test Script

Create `/examples/test_secure_file_ops.py`:

```python
import asyncio
from uuid import uuid4
from pathlib import Path

async def test_secure_file_operations():
    """Test secure file operations"""
    
    # Initialize tool service
    from src.services.tool_service import get_tool_service
    tool_service = get_tool_service()
    
    # Create test agent ID
    agent_id = uuid4()
    print(f"Testing with agent ID: {agent_id}")
    
    # Test 1: Write file
    print("\n1. Testing secure file write...")
    result = await tool_service.execute_tool(
        agent_id,
        "secure_file_write",
        {
            "filename": "test_report.txt",
            "content": "This is a secure test file.\nCreated by agent.",
            "directory": "test"
        }
    )
    print(f"Write result: {result}")
    
    # Test 2: List files
    print("\n2. Testing file list...")
    result = await tool_service.execute_tool(
        agent_id,
        "secure_file_list",
        {
            "directory": "test"
        }
    )
    print(f"List result: {result}")
    
    # Test 3: Read file
    print("\n3. Testing secure file read...")
    result = await tool_service.execute_tool(
        agent_id,
        "secure_file_read",
        {
            "filename": "test_report.txt",
            "directory": "test"
        }
    )
    print(f"Read result: {result}")
    
    # Test 4: Security test - path traversal
    print("\n4. Testing security - path traversal...")
    result = await tool_service.execute_tool(
        agent_id,
        "secure_file_write",
        {
            "filename": "../../../etc/passwd",
            "content": "malicious content"
        }
    )
    print(f"Security test result: {result}")

if __name__ == "__main__":
    asyncio.run(test_secure_file_operations())
```

## 3. Security Configuration

### 3.1 Environment Variables

Add to `.env`:

```bash
# Agent workspace configuration
AGENT_WORKSPACE_PATH=/app/agent_workspaces
AGENT_WORKSPACE_MAX_SIZE=1073741824  # 1GB per agent
AGENT_FILE_MAX_SIZE=10485760  # 10MB per file
AGENT_ALLOWED_EXTENSIONS=.txt,.json,.yaml,.yml,.md,.csv,.py,.js,.html,.css,.xml,.log
```

### 3.2 Monitoring Script

Create `/scripts/monitor_agent_files.py`:

```python
#!/usr/bin/env python3
import os
from pathlib import Path
import json
from datetime import datetime

def monitor_agent_workspaces():
    """Monitor agent file operations"""
    workspace_base = Path("/app/agent_workspaces")
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {}
    }
    
    if workspace_base.exists():
        for agent_dir in workspace_base.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name
                files = []
                total_size = 0
                
                for file_path in agent_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        total_size += size
                        files.append({
                            "path": str(file_path.relative_to(agent_dir)),
                            "size": size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat()
                        })
                
                report["agents"][agent_id] = {
                    "files_count": len(files),
                    "total_size": total_size,
                    "files": files
                }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    monitor_agent_workspaces()
```

## 4. Deployment Steps

1. **Stop current services:**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

2. **Create secure file tools:**
   - Copy the secure_file_tools.py to the correct location
   - Update tool_service.py

3. **Update Docker configuration:**
   - Add workspace volume to docker-compose.dev.yml

4. **Start services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. **Test the implementation:**
   ```bash
   docker-compose -f docker-compose.dev.yml exec core python /app/examples/test_secure_file_ops.py
   ```

## 5. Best Practices for Agents

### 5.1 File Naming Conventions

```python
# Good practices for agents
filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_analysis_report.md"
filename = f"agent_{self.agent_id}_output.json"
filename = "data/processed/results.csv"

# Bad practices (will be rejected)
filename = "../../../etc/passwd"  # Path traversal
filename = "file_with_<script>.html"  # Invalid characters
filename = "executable.exe"  # Disallowed extension
```

### 5.2 Content Organization

```python
# Organize files by purpose
await self.write_file("reports/daily/2024-01-15.md", report_content)
await self.write_file("data/raw/input.json", raw_data)
await self.write_file("analysis/results.csv", processed_data)
```

## 6. Troubleshooting

### Common Issues:

1. **Permission Denied:**
   - Check Docker volume permissions
   - Ensure workspace directory exists

2. **Path Traversal Blocked:**
   - Use relative paths within workspace
   - Don't use .. or absolute paths

3. **File Too Large:**
   - Split large files
   - Compress data before writing

### Debug Commands:

```bash
# Check workspace permissions
docker-compose exec core ls -la /app/agent_workspaces

# Monitor agent file creation
docker-compose exec core python /scripts/monitor_agent_files.py

# Check agent workspace usage
docker-compose exec core du -sh /app/agent_workspaces/*
```

## Conclusion

This implementation provides:
- ✅ Secure file operations for agents
- ✅ Path traversal protection
- ✅ File size limits
- ✅ Extension validation
- ✅ Per-agent isolation
- ✅ Easy monitoring

Agents can now safely create and manage files within their sandboxed workspaces without compromising system security.