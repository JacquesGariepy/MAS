"""
HTTP Client Tool for MAS Agents
Provides HTTP request capabilities and API interactions
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
import base64
from urllib.parse import urljoin, urlparse

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class HTTPTool(BaseTool):
    """Tool for making HTTP requests"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/app/agent_workspace"):
        super().__init__(
            name="HTTPTool",
            description="Make HTTP requests and interact with APIs",
            parameters={
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                    "description": "HTTP method"
                },
                "url": {
                    "type": "string",
                    "description": "URL to request"
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters"
                },
                "data": {
                    "type": "object",
                    "description": "Request body data (JSON)"
                },
                "form_data": {
                    "type": "object",
                    "description": "Form data for POST requests"
                },
                "auth": {
                    "type": "object",
                    "description": "Authentication credentials"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow redirects"
                }
            },
            required=["method", "url"]
        )
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root)
        self.session = None
        self.default_headers = {
            'User-Agent': f'MAS-Agent/{agent_id}'
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def execute(self, **kwargs) -> ToolResult:
        """Execute HTTP request"""
        method = kwargs.get("method", "GET").upper()
        url = kwargs.get("url")
        
        if not url:
            return ToolResult(success=False, error="URL required")
            
        # Create session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            # Prepare request
            request_kwargs = await self._prepare_request(kwargs)
            
            # Make request
            async with self.session.request(method, url, **request_kwargs) as response:
                result = await self._process_response(response)
                
            return result
            
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Request timed out"
            )
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"HTTP client error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"HTTP tool error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
        finally:
            # Clean up session if we created it
            if self.session and not hasattr(self, '_in_context'):
                await self.session.close()
                self.session = None
                
    async def _prepare_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request parameters"""
        request_kwargs = {}
        
        # Headers
        headers = self.default_headers.copy()
        if params.get("headers"):
            headers.update(params["headers"])
        request_kwargs["headers"] = headers
        
        # Query parameters
        if params.get("params"):
            request_kwargs["params"] = params["params"]
            
        # Request body
        if params.get("data"):
            # JSON data
            request_kwargs["json"] = params["data"]
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
                
        elif params.get("form_data"):
            # Form data
            request_kwargs["data"] = params["form_data"]
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                
        # Authentication
        if params.get("auth"):
            auth_type = params["auth"].get("type", "basic")
            
            if auth_type == "basic":
                username = params["auth"].get("username", "")
                password = params["auth"].get("password", "")
                auth_header = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {auth_header}"
                
            elif auth_type == "bearer":
                token = params["auth"].get("token", "")
                headers["Authorization"] = f"Bearer {token}"
                
            elif auth_type == "api_key":
                key_name = params["auth"].get("key_name", "X-API-Key")
                key_value = params["auth"].get("key_value", "")
                headers[key_name] = key_value
                
        # Timeout
        timeout = aiohttp.ClientTimeout(total=params.get("timeout", 30))
        request_kwargs["timeout"] = timeout
        
        # Redirects
        request_kwargs["allow_redirects"] = params.get("follow_redirects", True)
        
        return request_kwargs
        
    async def _process_response(self, response: aiohttp.ClientResponse) -> ToolResult:
        """Process HTTP response"""
        try:
            # Get response info
            response_data = {
                "status_code": response.status,
                "reason": response.reason,
                "headers": dict(response.headers),
                "url": str(response.url),
                "method": response.method,
                "content_type": response.content_type,
                "encoding": response.get_encoding()
            }
            
            # Get response body
            content_type = response.content_type
            
            if content_type and "application/json" in content_type:
                try:
                    body = await response.json()
                    response_data["body"] = body
                    response_data["body_type"] = "json"
                except json.JSONDecodeError:
                    # Fallback to text
                    body = await response.text()
                    response_data["body"] = body
                    response_data["body_type"] = "text"
                    
            elif content_type and ("text" in content_type or "html" in content_type):
                body = await response.text()
                response_data["body"] = body
                response_data["body_type"] = "text"
                
            elif content_type and "image" in content_type:
                # Save image to workspace
                body = await response.read()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = content_type.split("/")[-1]
                filename = f"http_response_{timestamp}.{extension}"
                filepath = self.workspace_root / "downloads" / filename
                filepath.parent.mkdir(exist_ok=True)
                filepath.write_bytes(body)
                
                response_data["body"] = str(filepath)
                response_data["body_type"] = "file"
                response_data["file_size"] = len(body)
                
            else:
                # Binary data
                body = await response.read()
                if len(body) < 1024:  # Small binary, include as base64
                    response_data["body"] = base64.b64encode(body).decode()
                    response_data["body_type"] = "base64"
                else:
                    # Save to file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"http_response_{timestamp}.bin"
                    filepath = self.workspace_root / "downloads" / filename
                    filepath.parent.mkdir(exist_ok=True)
                    filepath.write_bytes(body)
                    
                    response_data["body"] = str(filepath)
                    response_data["body_type"] = "file"
                    response_data["file_size"] = len(body)
                    
            # Check success
            success = 200 <= response.status < 300
            
            return ToolResult(
                success=success,
                data=response_data,
                error=None if success else f"HTTP {response.status}: {response.reason}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error processing response: {str(e)}"
            )
            
    async def download_file(self, url: str, destination: Optional[Path] = None) -> ToolResult:
        """Download a file from URL"""
        if not destination:
            filename = urlparse(url).path.split("/")[-1] or "download"
            destination = self.workspace_root / "downloads" / filename
            
        destination.parent.mkdir(exist_ok=True)
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    with open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            
                    return ToolResult(
                        success=True,
                        data={
                            "message": f"File downloaded successfully",
                            "path": str(destination),
                            "size": destination.stat().st_size,
                            "content_type": response.content_type
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"HTTP {response.status}: Failed to download {url}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Download failed: {str(e)}"
            )
        finally:
            if self.session and not hasattr(self, '_in_context'):
                await self.session.close()
                self.session = None
                
    async def upload_file(self, url: str, file_path: Path, 
                         field_name: str = "file",
                         additional_data: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Upload a file to URL"""
        if not file_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {file_path}"
            )
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            # Prepare multipart form data
            data = aiohttp.FormData()
            
            # Add file
            with open(file_path, 'rb') as f:
                data.add_field(
                    field_name,
                    f,
                    filename=file_path.name,
                    content_type='application/octet-stream'
                )
                
            # Add additional fields
            if additional_data:
                for key, value in additional_data.items():
                    data.add_field(key, str(value))
                    
            async with self.session.post(url, data=data) as response:
                result = await self._process_response(response)
                
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Upload failed: {str(e)}"
            )
        finally:
            if self.session and not hasattr(self, '_in_context'):
                await self.session.close()
                self.session = None
                
    async def test_api_endpoint(self, base_url: str, 
                               endpoints: List[Dict[str, Any]]) -> ToolResult:
        """Test multiple API endpoints"""
        results = []
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            for endpoint in endpoints:
                url = urljoin(base_url, endpoint.get("path", ""))
                method = endpoint.get("method", "GET")
                
                # Prepare request
                request_kwargs = await self._prepare_request(endpoint)
                
                # Make request
                start_time = asyncio.get_event_loop().time()
                
                try:
                    async with self.session.request(method, url, **request_kwargs) as response:
                        response_time = asyncio.get_event_loop().time() - start_time
                        
                        results.append({
                            "endpoint": endpoint.get("name", url),
                            "url": url,
                            "method": method,
                            "status_code": response.status,
                            "response_time": round(response_time * 1000, 2),  # ms
                            "success": 200 <= response.status < 300
                        })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint.get("name", url),
                        "url": url,
                        "method": method,
                        "error": str(e),
                        "success": False
                    })
                    
            # Summary
            total = len(results)
            successful = sum(1 for r in results if r.get("success", False))
            avg_response_time = sum(
                r.get("response_time", 0) for r in results if "response_time" in r
            ) / max(successful, 1)
            
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "summary": {
                        "total_endpoints": total,
                        "successful": successful,
                        "failed": total - successful,
                        "average_response_time": round(avg_response_time, 2)
                    }
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"API test failed: {str(e)}"
            )
        finally:
            if self.session and not hasattr(self, '_in_context'):
                await self.session.close()
                self.session = None