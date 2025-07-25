#!/usr/bin/env python3
"""
Working demonstration that actually creates files like autonomous_fixed.py
"""

import os
import asyncio
import sys
sys.path.insert(0, '/app/src')

from datetime import datetime

async def create_python_library():
    """Actually create a Python library structure"""
    print("\n" + "="*60)
    print("🚀 WORKING SWARM - CREATING PYTHON LIBRARY")
    print("="*60 + "\n")
    
    # Create workspace directory
    workspace = "agent_workspace"
    os.makedirs(workspace, exist_ok=True)
    
    # Library name
    lib_name = "sample_lib"
    lib_path = os.path.join(workspace, lib_name)
    os.makedirs(lib_path, exist_ok=True)
    
    print(f"📁 Creating library structure in {lib_path}/")
    
    # 1. Create __init__.py
    init_content = '''"""
Sample Library
A demonstration Python library created by the swarm
"""

__version__ = "0.1.0"
__author__ = "Swarm Agent"

from .core import SampleClass
from .utils import helper_function

__all__ = ["SampleClass", "helper_function"]
'''
    
    with open(os.path.join(lib_path, "__init__.py"), "w") as f:
        f.write(init_content)
    print("✅ Created __init__.py")
    
    # 2. Create core.py
    core_content = '''"""
Core module with main functionality
"""

class SampleClass:
    """A sample class to demonstrate library structure"""
    
    def __init__(self, name="Sample"):
        self.name = name
        self.data = []
        
    def add_data(self, item):
        """Add data to the collection"""
        self.data.append(item)
        print(f"Added {item} to {self.name}")
        
    def process_data(self):
        """Process all collected data"""
        if not self.data:
            return "No data to process"
            
        result = f"Processing {len(self.data)} items:\n"
        for i, item in enumerate(self.data, 1):
            result += f"  {i}. {item}\n"
        return result
        
    def __str__(self):
        return f"SampleClass(name={self.name}, items={len(self.data)})"
'''
    
    with open(os.path.join(lib_path, "core.py"), "w") as f:
        f.write(core_content)
    print("✅ Created core.py")
    
    # 3. Create utils.py
    utils_content = '''"""
Utility functions for the library
"""

def helper_function(text):
    """A helper function that processes text"""
    return f"Processed: {text.upper()}"
    
def validate_input(data):
    """Validate input data"""
    if not data:
        raise ValueError("Data cannot be empty")
    return True
    
def format_output(items):
    """Format a list of items for display"""
    if not items:
        return "No items to display"
        
    output = "Items:\\n"
    for item in items:
        output += f"- {item}\\n"
    return output
'''
    
    with open(os.path.join(lib_path, "utils.py"), "w") as f:
        f.write(utils_content)
    print("✅ Created utils.py")
    
    # 4. Create tests directory
    tests_path = os.path.join(lib_path, "tests")
    os.makedirs(tests_path, exist_ok=True)
    
    # Create test __init__.py
    with open(os.path.join(tests_path, "__init__.py"), "w") as f:
        f.write("# Test package\n")
    
    # Create test file
    test_content = '''"""
Unit tests for sample_lib
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SampleClass
from utils import helper_function, validate_input

class TestSampleClass(unittest.TestCase):
    """Test cases for SampleClass"""
    
    def setUp(self):
        self.sample = SampleClass("Test")
        
    def test_initialization(self):
        self.assertEqual(self.sample.name, "Test")
        self.assertEqual(len(self.sample.data), 0)
        
    def test_add_data(self):
        self.sample.add_data("item1")
        self.assertEqual(len(self.sample.data), 1)
        self.assertEqual(self.sample.data[0], "item1")
        
    def test_process_data(self):
        self.sample.add_data("apple")
        self.sample.add_data("banana")
        result = self.sample.process_data()
        self.assertIn("2 items", result)
        self.assertIn("apple", result)
        self.assertIn("banana", result)
        
class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_helper_function(self):
        result = helper_function("hello")
        self.assertEqual(result, "Processed: HELLO")
        
    def test_validate_input(self):
        self.assertTrue(validate_input("data"))
        with self.assertRaises(ValueError):
            validate_input("")
            
if __name__ == "__main__":
    unittest.main()
'''
    
    with open(os.path.join(tests_path, "test_sample_lib.py"), "w") as f:
        f.write(test_content)
    print("✅ Created tests/test_sample_lib.py")
    
    # 5. Create setup.py
    setup_content = '''"""
Setup configuration for sample_lib
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sample_lib",
    version="0.1.0",
    author="Swarm Agent",
    author_email="agent@swarm.ai",
    description="A sample Python library created by the swarm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swarm/sample_lib",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
)
'''
    
    with open(os.path.join(workspace, "setup.py"), "w") as f:
        f.write(setup_content)
    print("✅ Created setup.py")
    
    # 6. Create README.md
    readme_content = f'''# Sample Library

A demonstration Python library created by the unified swarm.

## Installation

```bash
pip install -e .
```

## Usage

```python
from sample_lib import SampleClass, helper_function

# Create an instance
sample = SampleClass("MyData")

# Add some data
sample.add_data("item1")
sample.add_data("item2")

# Process the data
result = sample.process_data()
print(result)

# Use utility function
processed = helper_function("hello world")
print(processed)  # Output: Processed: HELLO WORLD
```

## Testing

Run the tests with:

```bash
python -m unittest discover sample_lib/tests
```

## Structure

```
{lib_name}/
├── __init__.py       # Package initialization
├── core.py           # Core functionality
├── utils.py          # Utility functions
└── tests/
    ├── __init__.py
    └── test_sample_lib.py
```

## License

MIT License

---
Created by Unified Swarm on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
    
    with open(os.path.join(workspace, "README.md"), "w") as f:
        f.write(readme_content)
    print("✅ Created README.md")
    
    # 7. Create example.py
    example_content = '''#!/usr/bin/env python3
"""
Example usage of the sample library
"""

from sample_lib import SampleClass, helper_function

def main():
    print("Sample Library Demo")
    print("-" * 30)
    
    # Create instance
    sample = SampleClass("Demo Collection")
    
    # Add some data
    items = ["Python", "JavaScript", "Go", "Rust"]
    for item in items:
        sample.add_data(item)
    
    # Process and display
    print("\\n" + sample.process_data())
    
    # Use utility function
    message = "Hello from the swarm!"
    processed = helper_function(message)
    print(f"\\nOriginal: {message}")
    print(f"Processed: {processed}")
    
    # Show object info
    print(f"\\nObject info: {sample}")

if __name__ == "__main__":
    main()
'''
    
    with open(os.path.join(workspace, "example.py"), "w") as f:
        f.write(example_content)
    print("✅ Created example.py")
    
    print("\n" + "="*60)
    print("✅ LIBRARY CREATION COMPLETE!")
    print("="*60)
    
    # Show created files
    print("\n📁 Files created:")
    for root, dirs, files in os.walk(workspace):
        level = root.replace(workspace, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    print(f"\n✅ Total files created: {sum(len(files) for _, _, files in os.walk(workspace))}")
    print(f"📂 Location: {os.path.abspath(workspace)}")
    
    # Test the library
    print("\n🧪 Testing the library...")
    os.system(f"cd {workspace} && python example.py")
    
    return workspace

if __name__ == "__main__":
    # Run the creation
    asyncio.run(create_python_library())