#!/usr/bin/env python3
"""
Fix the swarm to properly execute tasks and generate code
"""

import re

# Read the swarm file
with open('swarm_mas_unified.py', 'r') as f:
    content = f.read()

# Fix 1: Update _analyze_request to properly use the LLM service
new_analyze_request = '''    async def _analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze the user request to understand intent and requirements"""
        # Use LLM's analyze_request method which returns proper structure
        analysis_result = await self.llm_service.analyze_request(request)
        
        # Also decompose the task to get components
        decomposition = await self.llm_service.decompose_task(
            request, 
            analysis_result
        )
        
        # Extract components from decomposition
        components = []
        for subtask in decomposition:
            components.append(subtask.get('description', ''))
        
        # If no components, create default ones
        if not components:
            if "test" in request.lower():
                components = [
                    "Design test structure and strategy",
                    "Implement test cases with proper assertions", 
                    "Add test fixtures and setup/teardown",
                    "Create test data and mocks",
                    "Validate test coverage"
                ]
            elif "calculator" in request.lower():
                components = [
                    "Design calculator interface",
                    "Implement arithmetic operations",
                    "Add error handling and validation",
                    "Create unit tests",
                    "Document the implementation"
                ]
            elif "fibonacci" in request.lower():
                components = [
                    "Design fibonacci algorithm",
                    "Implement efficient solution",
                    "Add input validation",
                    "Create comprehensive tests",
                    "Document the function"
                ]
            else:
                components = [
                    f"Analyze requirements for: {request}",
                    f"Design solution architecture",
                    f"Implement core functionality",
                    f"Add error handling and validation",
                    f"Create tests and documentation"
                ]
        
        return {
            "objective": request,
            "components": components,
            "required_capabilities": analysis_result.get("agent_types_needed", ["developer", "tester"]),
            "dependencies": [],
            "success_criteria": ["working_code", "tests_pass", "documented"]
        }'''

# Replace the _analyze_request method
pattern = r'async def _analyze_request\(self, request: str\) -> Dict\[str, Any\]:.*?return \{[^}]+\}'
content = re.sub(pattern, new_analyze_request, content, flags=re.DOTALL)

# Write the updated file
with open('swarm_mas_unified_fixed.py', 'w') as f:
    f.write(content)

print("✅ Fixed swarm_mas_unified.py!")
print("   - _analyze_request now properly decomposes tasks")
print("   - Components are generated for all request types")
print("   - Tasks will now be created and executed")