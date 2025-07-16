#!/usr/bin/env python3
"""
Examples of using MAS agents and swarms
"""

import asyncio
import requests
from typing import Dict, Any, List

# Configuration (Note: Port changed to 8080 to avoid conflicts)
API_BASE_URL = "http://localhost:8088"
HEADERS = {"Content-Type": "application/json"}


class MASClient:
    """Simple client for MAS API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def create_agent(self, name: str, agent_type: str = "cognitive", **config) -> Dict[str, Any]:
        """Create a new agent"""
        data = {
            "name": name,
            "type": agent_type,
            "config": config
        }
        response = self.session.post(f"{self.base_url}/api/v1/agents", json=data)
        response.raise_for_status()
        return response.json()
    
    def execute_agent_task(self, agent_id: str, task: str, **kwargs) -> Dict[str, Any]:
        """Execute a task with an agent"""
        data = {
            "task": task,
            **kwargs
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/agents/{agent_id}/execute",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_swarm(self, name: str, agents: List[Dict], topology: str = "mesh") -> Dict[str, Any]:
        """Create a new swarm"""
        data = {
            "name": name,
            "agents": agents,
            "topology": topology
        }
        response = self.session.post(f"{self.base_url}/api/v1/swarms", json=data)
        response.raise_for_status()
        return response.json()
    
    def execute_swarm_task(self, swarm_id: str, task: str, **kwargs) -> Dict[str, Any]:
        """Execute a task with a swarm"""
        data = {
            "task": task,
            **kwargs
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/swarms/{swarm_id}/execute",
            json=data
        )
        response.raise_for_status()
        return response.json()


def example_single_agent():
    """Example: Create and use a single agent"""
    print("=== Single Agent Example ===")
    
    client = MASClient()
    
    # Create an agent
    agent = client.create_agent(
        name="CodeAssistant",
        agent_type="cognitive",
        llm_provider="ollama",
        model="qwen3:4b",
        temperature=0.7
    )
    print(f"Created agent: {agent['id']}")
    
    # Execute a simple task
    result = client.execute_agent_task(
        agent['id'],
        "Write a Python function to calculate the factorial of a number",
        max_tokens=500
    )
    print(f"Task result: {result}")
    
    return agent['id']


def example_code_review_agent():
    """Example: Agent for code review"""
    print("\n=== Code Review Agent Example ===")
    
    client = MASClient()
    
    # Create specialized agent
    agent = client.create_agent(
        name="CodeReviewer",
        agent_type="cognitive",
        llm_provider="ollama",
        model="codellama",
        temperature=0.3,
        tools=["code_analyzer", "security_scanner"]
    )
    
    # Review code
    code_to_review = '''
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    result = db.execute(query)
    return result
    '''
    
    result = client.execute_agent_task(
        agent['id'],
        "Review this code for security issues and best practices",
        context={"code": code_to_review},
        analysis_depth="comprehensive"
    )
    print(f"Code review result: {result}")


def example_development_swarm():
    """Example: Create a development team swarm"""
    print("\n=== Development Swarm Example ===")
    
    client = MASClient()
    
    # Define swarm agents
    swarm_agents = [
        {
            "name": "Architect",
            "type": "cognitive",
            "role": "system_design",
            "config": {
                "model": "qwen3:4b",
                "temperature": 0.5,
                "expertise": ["architecture", "patterns", "scalability"]
            }
        },
        {
            "name": "Backend_Dev",
            "type": "cognitive", 
            "role": "implementation",
            "config": {
                "model": "codellama",
                "temperature": 0.7,
                "expertise": ["python", "fastapi", "postgresql"]
            }
        },
        {
            "name": "Frontend_Dev",
            "type": "cognitive",
            "role": "implementation",
            "config": {
                "model": "codellama",
                "temperature": 0.7,
                "expertise": ["javascript", "react", "css"]
            }
        },
        {
            "name": "QA_Engineer",
            "type": "cognitive",
            "role": "testing",
            "config": {
                "model": "qwen3:4b",
                "temperature": 0.3,
                "expertise": ["testing", "pytest", "selenium"]
            }
        }
    ]
    
    # Create swarm
    swarm = client.create_swarm(
        name="WebAppTeam",
        agents=swarm_agents,
        topology="hierarchical"
    )
    print(f"Created swarm: {swarm['id']}")
    
    # Execute complex task
    result = client.execute_swarm_task(
        swarm['id'],
        task="Design and implement a user authentication system with email verification",
        requirements=[
            "JWT-based authentication",
            "Email verification flow",
            "Password reset functionality",
            "Rate limiting",
            "Comprehensive tests"
        ],
        strategy="collaborative",
        max_rounds=10
    )
    print(f"Swarm task result: {result}")


def example_data_analysis_swarm():
    """Example: Data analysis swarm"""
    print("\n=== Data Analysis Swarm Example ===")
    
    client = MASClient()
    
    # Create specialized analysis swarm
    analysis_agents = [
        {
            "name": "DataScientist",
            "type": "cognitive",
            "role": "analysis",
            "config": {
                "model": "qwen3:4b",
                "tools": ["python_executor", "data_visualizer"]
            }
        },
        {
            "name": "Statistician",
            "type": "cognitive",
            "role": "analysis",
            "config": {
                "model": "qwen3:4b",
                "expertise": ["statistics", "hypothesis_testing"]
            }
        },
        {
            "name": "ReportWriter",
            "type": "cognitive",
            "role": "documentation",
            "config": {
                "model": "qwen3:4b",
                "temperature": 0.8
            }
        }
    ]
    
    swarm = client.create_swarm(
        name="DataTeam",
        agents=analysis_agents,
        topology="mesh"
    )
    
    # Analyze data
    result = client.execute_swarm_task(
        swarm['id'],
        task="Analyze sales trends and create executive report",
        data_context={
            "dataset": "Q4_sales_data.csv",
            "metrics": ["revenue", "units_sold", "customer_segments"]
        },
        deliverables=[
            "Statistical analysis",
            "Trend visualizations",
            "Executive summary",
            "Recommendations"
        ]
    )
    print(f"Analysis result: {result}")


def example_debugging_agent():
    """Example: Debugging assistant"""
    print("\n=== Debugging Agent Example ===")
    
    client = MASClient()
    
    agent = client.create_agent(
        name="Debugger",
        agent_type="cognitive",
        llm_provider="ollama",
        model="codellama",
        temperature=0.2,
        tools=["code_executor", "error_analyzer", "stack_trace_reader"]
    )
    
    # Debug code
    error_context = {
        "error": "AttributeError: 'NoneType' object has no attribute 'split'",
        "code": '''
def process_text(text):
    words = text.split()
    return [w.upper() for w in words]

result = process_text(None)
        ''',
        "stack_trace": "Traceback (most recent call last)..."
    }
    
    result = client.execute_agent_task(
        agent['id'],
        "Debug this code and provide a fix",
        context=error_context,
        explain=True
    )
    print(f"Debug result: {result}")


def example_async_operations():
    """Example: Async operations with multiple agents"""
    print("\n=== Async Operations Example ===")
    
    async def run_parallel_agents():
        # This would use the async version of the client
        # For demonstration, showing the pattern
        
        tasks = []
        for i in range(3):
            # Create task for each agent
            task = {
                "agent_name": f"Worker_{i}",
                "task": f"Process batch {i} of data"
            }
            tasks.append(task)
        
        # In real implementation, these would run in parallel
        print(f"Would run {len(tasks)} agents in parallel")
    
    # Run async example
    # asyncio.run(run_parallel_agents())
    print("Async pattern demonstrated")


def main():
    """Run all examples"""
    print("MAS Agent and Swarm Examples")
    print("============================")
    
    try:
        # Check if API is available
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code != 200:
            print("Error: MAS API is not running on http://localhost:8000")
            print("Please start the MAS system first")
            return
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to MAS API")
        print("Please ensure MAS is running with one of these commands:")
        print("  - Docker mode: docker-compose -f docker-compose.dev.yml up")
        print("  - Hybrid mode: Start DB/Redis in Docker, then run the app locally")
        print("  - Local mode: Ensure all services are running locally")
        return
    
    # Run examples
    try:
        example_single_agent()
        example_code_review_agent()
        example_development_swarm()
        example_data_analysis_swarm()
        example_debugging_agent()
        example_async_operations()
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure the API endpoints are implemented and working")


if __name__ == "__main__":
    main()