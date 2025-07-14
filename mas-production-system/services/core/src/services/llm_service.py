"""
LLM Service for agent reasoning
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.utils.logger import get_logger
from src.monitoring import track_llm_request

logger = get_logger(__name__)

class LLMService:
    """Service for interacting with Language Models"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
        
        # Model-specific settings
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        
        logger.info(f"Initialized LLM service with model: {self.model}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate text completion"""
        
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if stop:
            payload["stop"] = stop
        
        # Handle different response formats
        if response_format == "json":
            # For OpenAI-compatible APIs
            if "gpt" in self.model.lower():
                payload["response_format"] = {"type": "json_object"}
            # Add JSON instruction to prompt
            messages[-1]["content"] += "\n\nRespond with valid JSON only."
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Track metrics
            input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = data.get("usage", {}).get("completion_tokens", 0)
            track_llm_request(
                model=self.model,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            track_llm_request(model=self.model, success=False)
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            track_llm_request(model=self.model, success=False)
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts"""
        
        embedding_model = model or "text-embedding-ada-002"
        
        payload = {
            "model": embedding_model,
            "input": texts
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            
            track_llm_request(
                model=embedding_model,
                success=True,
                input_tokens=len(texts) * 10  # Approximate
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding request failed: {str(e)}")
            track_llm_request(model=embedding_model, success=False)
            raise
    
    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Analyze code using LLM"""
        
        prompts = {
            "general": f"Analyze this {language} code and provide insights about its structure, quality, and potential improvements.",
            "security": f"Analyze this {language} code for security vulnerabilities and provide recommendations.",
            "performance": f"Analyze this {language} code for performance issues and optimization opportunities.",
            "bugs": f"Analyze this {language} code for potential bugs and logic errors."
        }
        
        system_prompt = "You are an expert code analyst. Provide detailed, actionable feedback."
        
        prompt = f"""{prompts.get(analysis_type, prompts["general"])}

Code:
```{language}
{code}
```

Provide your analysis in JSON format with the following structure:
{{
    "summary": "Brief summary of the analysis",
    "issues": [
        {{
            "type": "issue type (e.g., bug, security, performance)",
            "severity": "low|medium|high|critical",
            "line": line_number_if_applicable,
            "description": "Description of the issue",
            "suggestion": "How to fix it"
        }}
    ],
    "improvements": [
        {{
            "category": "improvement category",
            "description": "Improvement suggestion",
            "example": "Code example if applicable"
        }}
    ],
    "metrics": {{
        "complexity": "low|medium|high",
        "maintainability": "score 1-10",
        "test_coverage_estimate": "percentage"
    }}
}}"""
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return {
                "summary": response,
                "issues": [],
                "improvements": [],
                "metrics": {}
            }
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Optional[str] = None,
        constraints: Optional[List[str]] = None
    ) -> str:
        """Generate code based on description"""
        
        prompt = f"""Generate {language} code for the following requirement:

{description}
"""
        
        if context:
            prompt += f"\nContext:\n{context}\n"
        
        if constraints:
            prompt += f"\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints) + "\n"
        
        prompt += f"\nProvide only the code without explanations. Use proper {language} syntax and best practices."
        
        system_prompt = f"You are an expert {language} developer. Generate clean, efficient, and well-structured code."
        
        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            stop=["```"]
        )
    
    async def explain_code(
        self,
        code: str,
        language: str = "python",
        target_audience: str = "developer"
    ) -> str:
        """Explain code in natural language"""
        
        audience_prompts = {
            "beginner": "Explain in simple terms suitable for someone new to programming.",
            "developer": "Explain technically but clearly, assuming programming knowledge.",
            "expert": "Provide a detailed technical explanation with advanced concepts."
        }
        
        prompt = f"""Explain this {language} code:

```{language}
{code}
```

{audience_prompts.get(target_audience, audience_prompts["developer"])}"""
        
        system_prompt = "You are an expert code educator. Provide clear, comprehensive explanations."
        
        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5
        )

# Global instance for easy access
_llm_service: Optional[LLMService] = None

async def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

__all__ = ["LLMService", "get_llm_service"]