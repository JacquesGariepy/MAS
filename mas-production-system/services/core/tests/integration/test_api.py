"""
Integration tests for API endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data

@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    assert "mas_http_requests_total" in response.text
    assert "mas_active_agents" in response.text

@pytest.mark.asyncio
async def test_openapi_schema():
    """Test OpenAPI schema is accessible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
    
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert schema["info"]["title"] == "Multi-Agent System API"
    assert schema["info"]["version"] == "2.0.0"

@pytest.mark.asyncio
async def test_docs_redirect():
    """Test documentation redirect"""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/docs")
    
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "/docs"