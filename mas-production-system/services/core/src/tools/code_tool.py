"""
Code Analysis and Generation Tool for MAS Agents
Provides code analysis, generation, and manipulation capabilities
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysis:
    """Results from code analysis"""
    language: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    complexity: int
    issues: List[str]
    suggestions: List[str]


class CodeTool(BaseTool):
    """Tool for code analysis and generation"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/app/agent_workspace"):
        super().__init__(
            name="CodeTool",
            description="Analyze, generate, and manipulate code",
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["analyze", "generate", "refactor", "test", "format", "lint"],
                    "description": "Action to perform"
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "typescript", "java", "go", "rust"],
                    "description": "Programming language"
                },
                "code": {
                    "type": "string",
                    "description": "Code to analyze or template for generation"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to code file"
                },
                "requirements": {
                    "type": "object",
                    "description": "Requirements for code generation"
                }
            },
            required=["action"]
        )
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root)
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute code tool action"""
        action = kwargs.get("action")
        
        try:
            if action == "analyze":
                return await self._analyze_code(kwargs)
            elif action == "generate":
                return await self._generate_code(kwargs)
            elif action == "refactor":
                return await self._refactor_code(kwargs)
            elif action == "test":
                return await self._generate_tests(kwargs)
            elif action == "format":
                return await self._format_code(kwargs)
            elif action == "lint":
                return await self._lint_code(kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            logger.error(f"Code tool error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
            
    async def _analyze_code(self, params: Dict[str, Any]) -> ToolResult:
        """Analyze code structure and quality"""
        code = params.get("code", "")
        file_path = params.get("file_path")
        language = params.get("language", "python")
        
        if file_path and not code:
            path = Path(file_path)
            if path.exists():
                code = path.read_text()
                
        if not code:
            return ToolResult(success=False, error="No code provided")
            
        analysis = CodeAnalysis(
            language=language,
            functions=[],
            classes=[],
            imports=[],
            complexity=0,
            issues=[],
            suggestions=[]
        )
        
        if language == "python":
            analysis = self._analyze_python(code)
        elif language in ["javascript", "typescript"]:
            analysis = self._analyze_javascript(code)
        else:
            analysis.issues.append(f"Analysis not implemented for {language}")
            
        return ToolResult(
            success=True,
            data={
                "analysis": {
                    "language": analysis.language,
                    "functions": analysis.functions,
                    "classes": analysis.classes,
                    "imports": analysis.imports,
                    "complexity": analysis.complexity,
                    "issues": analysis.issues,
                    "suggestions": analysis.suggestions
                }
            }
        )
        
    def _analyze_python(self, code: str) -> CodeAnalysis:
        """Analyze Python code"""
        analysis = CodeAnalysis(
            language="python",
            functions=[],
            classes=[],
            imports=[],
            complexity=0,
            issues=[],
            suggestions=[]
        )
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis.functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "lineno": node.lineno,
                        "docstring": ast.get_docstring(node)
                    })
                    analysis.complexity += self._calculate_complexity(node)
                    
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)
                    analysis.classes.append({
                        "name": node.name,
                        "methods": methods,
                        "lineno": node.lineno,
                        "docstring": ast.get_docstring(node)
                    })
                    
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis.imports.append(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis.imports.append(f"{module}.{alias.name}")
                        
            # Check for common issues
            if len(analysis.functions) > 20:
                analysis.issues.append("Module has many functions, consider splitting")
                
            if analysis.complexity > 10:
                analysis.issues.append("High complexity detected")
                
            # Add suggestions
            if not any(func["docstring"] for func in analysis.functions):
                analysis.suggestions.append("Add docstrings to functions")
                
        except SyntaxError as e:
            analysis.issues.append(f"Syntax error: {e}")
            
        return analysis
        
    def _analyze_javascript(self, code: str) -> CodeAnalysis:
        """Analyze JavaScript/TypeScript code"""
        analysis = CodeAnalysis(
            language="javascript",
            functions=[],
            classes=[],
            imports=[],
            complexity=0,
            issues=[],
            suggestions=[]
        )
        
        # Simple regex-based analysis
        function_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()'
        class_pattern = r'class\s+(\w+)'
        import_pattern = r'import\s+.*?from\s+[\'"](.+?)[\'"]'
        
        for match in re.finditer(function_pattern, code):
            name = match.group(1) or match.group(2)
            if name:
                analysis.functions.append({"name": name, "type": "function"})
                
        for match in re.finditer(class_pattern, code):
            analysis.classes.append({"name": match.group(1)})
            
        for match in re.finditer(import_pattern, code):
            analysis.imports.append(match.group(1))
            
        return analysis
        
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity
        
    async def _generate_code(self, params: Dict[str, Any]) -> ToolResult:
        """Generate code based on requirements"""
        language = params.get("language", "python")
        requirements = params.get("requirements", {})
        template = params.get("code", "")
        
        if language == "python":
            code = self._generate_python(requirements, template)
        elif language == "javascript":
            code = self._generate_javascript(requirements, template)
        else:
            return ToolResult(
                success=False,
                error=f"Code generation not implemented for {language}"
            )
            
        # Save generated code
        file_name = requirements.get("name", "generated")
        ext = {"python": ".py", "javascript": ".js"}.get(language, ".txt")
        output_path = self.workspace_root / f"{file_name}{ext}"
        
        output_path.write_text(code)
        
        return ToolResult(
            success=True,
            data={
                "generated_code": code,
                "file_path": str(output_path),
                "language": language
            }
        )
        
    def _generate_python(self, requirements: Dict[str, Any], template: str) -> str:
        """Generate Python code"""
        code_parts = []
        
        # Header
        code_parts.append('"""')
        code_parts.append(requirements.get("description", "Generated code"))
        code_parts.append('"""')
        code_parts.append("")
        
        # Imports
        imports = requirements.get("imports", [])
        for imp in imports:
            code_parts.append(f"import {imp}")
        if imports:
            code_parts.append("")
            
        # Classes
        classes = requirements.get("classes", [])
        for cls in classes:
            code_parts.append(f"class {cls['name']}:")
            code_parts.append(f'    """{cls.get("description", "")}"""')
            code_parts.append("    ")
            methods = cls.get("methods", [])
            if not methods:
                code_parts.append("    pass")
            else:
                for method in methods:
                    code_parts.append(f"    def {method['name']}(self):")
                    code_parts.append(f'        """{method.get("description", "")}"""')
                    code_parts.append("        pass")
                    code_parts.append("    ")
            code_parts.append("")
            
        # Functions
        functions = requirements.get("functions", [])
        for func in functions:
            args = ", ".join(func.get("args", []))
            code_parts.append(f"def {func['name']}({args}):")
            code_parts.append(f'    """{func.get("description", "")}"""')
            body = func.get("body", "pass")
            for line in body.split("\n"):
                code_parts.append(f"    {line}")
            code_parts.append("")
            
        # Main
        if requirements.get("main", False):
            code_parts.append('if __name__ == "__main__":')
            code_parts.append('    # Main execution')
            code_parts.append('    pass')
            
        return "\n".join(code_parts)
        
    def _generate_javascript(self, requirements: Dict[str, Any], template: str) -> str:
        """Generate JavaScript code"""
        code_parts = []
        
        # Header comment
        code_parts.append("/**")
        code_parts.append(f" * {requirements.get('description', 'Generated code')}")
        code_parts.append(" */")
        code_parts.append("")
        
        # Imports
        imports = requirements.get("imports", [])
        for imp in imports:
            code_parts.append(f"import {imp};")
        if imports:
            code_parts.append("")
            
        # Classes
        classes = requirements.get("classes", [])
        for cls in classes:
            code_parts.append(f"class {cls['name']} {{")
            methods = cls.get("methods", [])
            for method in methods:
                code_parts.append(f"  {method['name']}() {{")
                code_parts.append("    // Implementation")
                code_parts.append("  }")
                code_parts.append("")
            code_parts.append("}")
            code_parts.append("")
            
        # Functions
        functions = requirements.get("functions", [])
        for func in functions:
            args = ", ".join(func.get("args", []))
            code_parts.append(f"function {func['name']}({args}) {{")
            code_parts.append("  // Implementation")
            code_parts.append("}")
            code_parts.append("")
            
        return "\n".join(code_parts)
        
    async def _refactor_code(self, params: Dict[str, Any]) -> ToolResult:
        """Refactor code to improve quality"""
        code = params.get("code", "")
        language = params.get("language", "python")
        
        if language == "python":
            refactored = self._refactor_python(code)
        else:
            return ToolResult(
                success=False,
                error=f"Refactoring not implemented for {language}"
            )
            
        return ToolResult(
            success=True,
            data={
                "original": code,
                "refactored": refactored,
                "changes": self._diff_code(code, refactored)
            }
        )
        
    def _refactor_python(self, code: str) -> str:
        """Simple Python refactoring"""
        # Add imports optimization
        lines = code.split("\n")
        imports = []
        other_lines = []
        
        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)
            else:
                other_lines.append(line)
                
        # Sort imports
        imports.sort()
        
        # Combine
        refactored = []
        if imports:
            refactored.extend(imports)
            refactored.append("")
            
        refactored.extend(other_lines)
        
        return "\n".join(refactored)
        
    async def _generate_tests(self, params: Dict[str, Any]) -> ToolResult:
        """Generate unit tests for code"""
        code = params.get("code", "")
        language = params.get("language", "python")
        
        if language == "python":
            # Analyze code first
            analysis = self._analyze_python(code)
            tests = self._generate_python_tests(analysis)
        else:
            return ToolResult(
                success=False,
                error=f"Test generation not implemented for {language}"
            )
            
        return ToolResult(
            success=True,
            data={
                "tests": tests,
                "framework": "pytest" if language == "python" else "jest"
            }
        )
        
    def _generate_python_tests(self, analysis: CodeAnalysis) -> str:
        """Generate Python unit tests"""
        test_parts = []
        
        test_parts.append("import pytest")
        test_parts.append("")
        
        for func in analysis.functions:
            test_parts.append(f"def test_{func['name']}():")
            test_parts.append(f'    """Test {func["name"]} function"""')
            test_parts.append("    # TODO: Implement test")
            test_parts.append("    assert True")
            test_parts.append("")
            
        for cls in analysis.classes:
            test_parts.append(f"class Test{cls['name']}:")
            test_parts.append(f'    """Test {cls["name"]} class"""')
            test_parts.append("    ")
            for method in cls.get("methods", []):
                test_parts.append(f"    def test_{method}(self):")
                test_parts.append(f'        """Test {method} method"""')
                test_parts.append("        # TODO: Implement test")
                test_parts.append("        assert True")
                test_parts.append("    ")
            test_parts.append("")
            
        return "\n".join(test_parts)
        
    async def _format_code(self, params: Dict[str, Any]) -> ToolResult:
        """Format code using language-specific formatters"""
        code = params.get("code", "")
        language = params.get("language", "python")
        file_path = params.get("file_path")
        
        if file_path:
            path = Path(file_path)
            if path.exists():
                code = path.read_text()
                
        formatted = code
        
        if language == "python":
            # Use black if available
            try:
                import black
                formatted = black.format_str(code, mode=black.Mode())
            except ImportError:
                # Fallback to simple formatting
                formatted = self._simple_format_python(code)
        
        if file_path:
            Path(file_path).write_text(formatted)
            
        return ToolResult(
            success=True,
            data={
                "formatted": formatted,
                "changed": formatted != code
            }
        )
        
    def _simple_format_python(self, code: str) -> str:
        """Simple Python formatting without black"""
        # Basic formatting rules
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.endswith(":"):
                formatted_lines.append("    " * indent_level + stripped)
                indent_level += 1
            elif stripped in ["pass", "return", "break", "continue"]:
                formatted_lines.append("    " * indent_level + stripped)
                if indent_level > 0:
                    indent_level -= 1
            elif stripped:
                formatted_lines.append("    " * indent_level + stripped)
            else:
                formatted_lines.append("")
                
        return "\n".join(formatted_lines)
        
    async def _lint_code(self, params: Dict[str, Any]) -> ToolResult:
        """Lint code to find issues"""
        code = params.get("code", "")
        language = params.get("language", "python")
        params.get("file_path")
        
        issues = []
        
        if language == "python":
            # Basic Python linting
            lines = code.split("\n")
            for i, line in enumerate(lines, 1):
                # Line too long
                if len(line) > 88:
                    issues.append({
                        "line": i,
                        "level": "warning",
                        "message": f"Line too long ({len(line)} > 88 characters)"
                    })
                    
                # Missing spaces around operators
                if re.search(r'\w[=+\-*/]\w', line):
                    issues.append({
                        "line": i,
                        "level": "style",
                        "message": "Missing spaces around operator"
                    })
                    
                # TODO comments
                if "TODO" in line or "FIXME" in line:
                    issues.append({
                        "line": i,
                        "level": "info",
                        "message": "TODO/FIXME comment found"
                    })
                    
        return ToolResult(
            success=True,
            data={
                "issues": issues,
                "summary": {
                    "total": len(issues),
                    "errors": len([i for i in issues if i["level"] == "error"]),
                    "warnings": len([i for i in issues if i["level"] == "warning"]),
                    "info": len([i for i in issues if i["level"] == "info"])
                }
            }
        )
        
    def _diff_code(self, original: str, modified: str) -> List[Dict[str, Any]]:
        """Calculate differences between code versions"""
        changes = []
        original_lines = original.split("\n")
        modified_lines = modified.split("\n")
        
        # Simple line-by-line comparison
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines), 1):
            if orig != mod:
                changes.append({
                    "line": i,
                    "original": orig,
                    "modified": mod
                })
                
        return changes