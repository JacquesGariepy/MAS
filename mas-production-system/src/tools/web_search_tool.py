"""
Web Search Tool for MAS Agents
Provides web search and content retrieval capabilities
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from urllib.parse import quote_plus, urlparse
import re
from bs4 import BeautifulSoup

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for web search and content retrieval"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/app/agent_workspace"):
        super().__init__(
            name="WebSearchTool",
            description="Search the web and retrieve content",
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["search", "fetch", "extract", "summarize"],
                    "description": "Action to perform"
                },
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "url": {
                    "type": "string",
                    "description": "URL to fetch content from"
                },
                "engine": {
                    "type": "string",
                    "enum": ["duckduckgo", "google", "bing"],
                    "description": "Search engine to use"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results"
                },
                "extract_type": {
                    "type": "string",
                    "enum": ["text", "links", "images", "metadata"],
                    "description": "Type of content to extract"
                }
            },
            required=["action"]
        )
        self.agent_id = agent_id
        self.workspace_root = workspace_root
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def execute(self, **kwargs) -> ToolResult:
        """Execute web search tool action"""
        action = kwargs.get("action")
        
        # Create session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
            
        try:
            if action == "search":
                return await self._search_web(kwargs)
            elif action == "fetch":
                return await self._fetch_content(kwargs)
            elif action == "extract":
                return await self._extract_content(kwargs)
            elif action == "summarize":
                return await self._summarize_content(kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
        finally:
            # Clean up session if we created it
            if self.session and not hasattr(self, '_in_context'):
                await self.session.close()
                self.session = None
                
    async def _search_web(self, params: Dict[str, Any]) -> ToolResult:
        """Perform web search"""
        query = params.get("query")
        if not query:
            return ToolResult(success=False, error="Query required")
            
        engine = params.get("engine", "duckduckgo")
        limit = params.get("limit", 10)
        
        try:
            if engine == "duckduckgo":
                results = await self._search_duckduckgo(query, limit)
            else:
                # Fallback to DuckDuckGo for other engines
                results = await self._search_duckduckgo(query, limit)
                
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "engine": engine,
                    "results": results,
                    "count": len(results)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
            
    async def _search_duckduckgo(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML version"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find result links
                    for i, result in enumerate(soup.find_all('a', class_='result__a')):
                        if i >= limit:
                            break
                            
                        title = result.get_text(strip=True)
                        link = result.get('href', '')
                        
                        # Find snippet
                        snippet_elem = result.find_next('a', class_='result__snippet')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if title and link:
                            results.append({
                                "title": title,
                                "url": link,
                                "snippet": snippet,
                                "position": i + 1
                            })
                            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            
        return results
        
    async def _fetch_content(self, params: Dict[str, Any]) -> ToolResult:
        """Fetch content from URL"""
        url = params.get("url")
        if not url:
            return ToolResult(success=False, error="URL required")
            
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'text/html' in content_type:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract text content
                        text = self._extract_text_from_html(soup)
                        
                        # Extract metadata
                        metadata = self._extract_metadata(soup)
                        
                        return ToolResult(
                            success=True,
                            data={
                                "url": url,
                                "content": text,
                                "metadata": metadata,
                                "content_type": content_type,
                                "length": len(text)
                            }
                        )
                    else:
                        # Non-HTML content
                        content = await response.read()
                        return ToolResult(
                            success=True,
                            data={
                                "url": url,
                                "content_type": content_type,
                                "size": len(content),
                                "binary": True
                            }
                        )
                else:
                    return ToolResult(
                        success=False,
                        error=f"HTTP {response.status}: Failed to fetch {url}"
                    )
                    
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Timeout fetching {url}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error fetching {url}: {str(e)}"
            )
            
    async def _extract_content(self, params: Dict[str, Any]) -> ToolResult:
        """Extract specific content from URL"""
        url = params.get("url")
        if not url:
            return ToolResult(success=False, error="URL required")
            
        extract_type = params.get("extract_type", "text")
        
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if extract_type == "text":
                        content = self._extract_text_from_html(soup)
                    elif extract_type == "links":
                        content = self._extract_links(soup, url)
                    elif extract_type == "images":
                        content = self._extract_images(soup, url)
                    elif extract_type == "metadata":
                        content = self._extract_metadata(soup)
                    else:
                        content = {}
                        
                    return ToolResult(
                        success=True,
                        data={
                            "url": url,
                            "extract_type": extract_type,
                            "content": content
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"HTTP {response.status}: Failed to fetch {url}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error extracting from {url}: {str(e)}"
            )
            
    async def _summarize_content(self, params: Dict[str, Any]) -> ToolResult:
        """Summarize web content"""
        url = params.get("url")
        if not url:
            return ToolResult(success=False, error="URL required")
            
        # First fetch the content
        fetch_result = await self._fetch_content({"url": url})
        
        if not fetch_result.success:
            return fetch_result
            
        content = fetch_result.data.get("content", "")
        
        # Simple summarization (would use LLM in practice)
        summary = self._simple_summarize(content)
        
        return ToolResult(
            success=True,
            data={
                "url": url,
                "summary": summary,
                "original_length": len(content),
                "summary_length": len(summary)
            }
        )
        
    def _extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from HTML"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Make absolute URL
            if href.startswith('http'):
                absolute_url = href
            elif href.startswith('/'):
                absolute_url = f"{urlparse(base_url).scheme}://{base_domain}{href}"
            else:
                continue
                
            links.append({
                "url": absolute_url,
                "text": text,
                "internal": base_domain in absolute_url
            })
            
        return links
        
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images from HTML"""
        images = []
        base_domain = urlparse(base_url).netloc
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if not src:
                continue
                
            # Make absolute URL
            if src.startswith('http'):
                absolute_url = src
            elif src.startswith('/'):
                absolute_url = f"{urlparse(base_url).scheme}://{base_domain}{src}"
            else:
                continue
                
            images.append({
                "url": absolute_url,
                "alt": alt,
                "width": img.get('width', ''),
                "height": img.get('height', '')
            })
            
        return images
        
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {
            "title": "",
            "description": "",
            "keywords": "",
            "author": "",
            "og": {}
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
            
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif property.startswith('og:'):
                metadata["og"][property] = content
                
        return metadata
        
    def _simple_summarize(self, text: str, max_length: int = 500) -> str:
        """Simple text summarization"""
        if len(text) <= max_length:
            return text
            
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Take first few sentences up to max_length
        summary = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence)
            else:
                break
                
        return '. '.join(summary) + '.'