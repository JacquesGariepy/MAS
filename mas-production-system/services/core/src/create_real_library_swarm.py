#!/usr/bin/env python3
"""
Demo showing how swarm_mas_unified.py SHOULD create real Python libraries
This demonstrates what the swarm needs to generate
"""

import os
import asyncio
import sys
sys.path.insert(0, '/app/src')

from datetime import datetime

async def demonstrate_real_library_creation():
    """Show what a real library creation looks like"""
    print("\n" + "="*80)
    print("🚀 DEMONSTRATING REAL LIBRARY CREATION")
    print("="*80 + "\n")
    
    workspace = "agent_workspace"
    os.makedirs(workspace, exist_ok=True)
    
    # This is what the swarm SHOULD create
    lib_name = "sample_lib"
    lib_path = os.path.join(workspace, lib_name)
    os.makedirs(lib_path, exist_ok=True)
    
    print(f"📁 Creating complete library structure in {lib_path}/")
    
    # 1. __init__.py
    init_content = '''"""
Sample Library - A Python library created by the MAS swarm
This library demonstrates real, functional code generation.
"""

__version__ = "0.1.0"
__author__ = "MAS Swarm"
__all__ = ["SampleClass", "helper_function", "validate_input"]

from .core import SampleClass
from .utils import helper_function, validate_input
'''
    
    with open(os.path.join(lib_path, "__init__.py"), 'w') as f:
        f.write(init_content)
    print("✅ Created __init__.py")
    
    # 2. core.py
    core_content = '''"""
Core module with main functionality
"""

class SampleClass:
    """A sample class to demonstrate library structure"""
    
    def __init__(self, name="Sample"):
        """Initialize the SampleClass
        
        Args:
            name (str): Name for this instance
        """
        self.name = name
        self.data = []
        self._config = {
            "verbose": False,
            "max_items": 1000
        }
        
    def add_data(self, item):
        """Add data to the collection
        
        Args:
            item: Item to add to the collection
            
        Returns:
            str: Confirmation message
        """
        if len(self.data) >= self._config["max_items"]:
            raise ValueError(f"Maximum items ({self._config['max_items']}) exceeded")
            
        self.data.append(item)
        message = f"Added {item} to {self.name}"
        
        if self._config["verbose"]:
            print(message)
            
        return message
        
    def process_data(self):
        """Process all collected data
        
        Returns:
            str: Processing result summary
        """
        if not self.data:
            return "No data to process"
            
        result = f"Processing {len(self.data)} items:\\n"
        
        # Group by type
        type_counts = {}
        for item in self.data:
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
        for item_type, count in type_counts.items():
            result += f"  - {item_type}: {count} items\\n"
            
        # List items
        for i, item in enumerate(self.data, 1):
            result += f"  {i}. {item}\\n"
            
        return result
        
    def clear_data(self):
        """Clear all data from the collection"""
        self.data.clear()
        return f"Cleared all data from {self.name}"
        
    def get_stats(self):
        """Get statistics about the data
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            "name": self.name,
            "count": len(self.data),
            "types": list(set(type(item).__name__ for item in self.data)),
            "config": self._config.copy()
        }
        
    def configure(self, **kwargs):
        """Update configuration settings
        
        Args:
            **kwargs: Configuration key-value pairs
        """
        self._config.update(kwargs)
        
    def __str__(self):
        return f"SampleClass(name={self.name}, items={len(self.data)})"
        
    def __repr__(self):
        return f"SampleClass('{self.name}')"
'''
    
    with open(os.path.join(lib_path, "core.py"), 'w') as f:
        f.write(core_content)
    print("✅ Created core.py")
    
    # 3. utils.py
    utils_content = '''"""
Utility functions for the library
"""

import re
from typing import List, Any, Optional

def helper_function(text: str) -> str:
    """A helper function that processes text
    
    Args:
        text (str): Input text to process
        
    Returns:
        str: Processed text in uppercase with prefix
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
        
    return f"Processed: {text.upper()}"
    
def validate_input(data: Any) -> bool:
    """Validate input data
    
    Args:
        data: Data to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If data is empty or None
    """
    if data is None:
        raise ValueError("Data cannot be None")
        
    if isinstance(data, str) and not data.strip():
        raise ValueError("Data cannot be empty")
        
    if isinstance(data, (list, dict, tuple)) and len(data) == 0:
        raise ValueError("Data cannot be empty")
        
    return True
    
def format_output(items: List[Any]) -> str:
    """Format a list of items for display
    
    Args:
        items (list): List of items to format
        
    Returns:
        str: Formatted string representation
    """
    if not items:
        return "No items to display"
        
    output = f"Items ({len(items)} total):\\n"
    for i, item in enumerate(items, 1):
        output += f"{i:3d}. {item}\\n"
        
    return output
'''
    
    with open(os.path.join(lib_path, "utils.py"), 'w') as f:
        f.write(utils_content)
    print("✅ Created utils.py")
    
    # 4. Create tests directory
    tests_path = os.path.join(workspace, "tests")
    os.makedirs(tests_path, exist_ok=True)
    
    with open(os.path.join(tests_path, "__init__.py"), 'w') as f:
        f.write('"""Test package"""\\n')
    
    # 5. Create test file
    test_content = '''"""
Unit tests for sample_lib
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_lib.core import SampleClass
from sample_lib.utils import helper_function, validate_input

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
    
    with open(os.path.join(tests_path, "test_sample_lib.py"), 'w') as f:
        f.write(test_content)
    print("✅ Created tests/test_sample_lib.py")
    
    # 6. Create setup.py
    setup_content = '''"""
Setup configuration for sample_lib
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sample_lib",
    version="0.1.0",
    author="MAS Swarm",
    author_email="swarm@mas-system.ai",
    description="A sample Python library created by the unified swarm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mas-swarm/sample_lib",
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
    
    with open(os.path.join(workspace, "setup.py"), 'w') as f:
        f.write(setup_content)
    print("✅ Created setup.py")
    
    # 7. Create README.md
    readme_content = f'''# Sample Library

A demonstration Python library created by the MAS unified swarm.

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

## Structure

```
sample_lib/
├── __init__.py       # Package initialization
├── core.py          # Core functionality
└── utils.py         # Utility functions

tests/
├── __init__.py
└── test_sample_lib.py
```

## Testing

```bash
python -m unittest discover tests
```

---
Created by MAS Unified Swarm on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
    
    with open(os.path.join(workspace, "README.md"), 'w') as f:
        f.write(readme_content)
    print("✅ Created README.md")
    
    # 8. Create example.py
    example_content = '''#!/usr/bin/env python3
"""
Example usage of the sample library
"""

from sample_lib import SampleClass, helper_function, validate_input

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
    
    with open(os.path.join(workspace, "example.py"), 'w') as f:
        f.write(example_content)
    print("✅ Created example.py")
    
    print("\n" + "="*60)
    print("✅ LIBRARY CREATION COMPLETE!")
    print("="*60)
    
    # Show created files
    print("\n📁 Files created:")
    created_files = []
    for root, dirs, files in os.walk(workspace):
        for file in files:
            filepath = os.path.join(root, file)
            created_files.append(filepath)
            rel_path = os.path.relpath(filepath, workspace)
            print(f"  - {rel_path}")
    
    print(f"\n✅ Total files created: {len(created_files)}")
    print(f"📂 Location: {os.path.abspath(workspace)}")
    
    # Test the library
    print("\n🧪 Testing the library...")
    os.system(f"cd {workspace} && python example.py")
    
    print("\n💡 This is what swarm_mas_unified.py SHOULD create!")
    print("   Not just simple generic files, but a complete, functional library.")
    
    return created_files

if __name__ == "__main__":
    # Create the demonstration
    asyncio.run(demonstrate_real_library_creation())