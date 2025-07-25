"""
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
        
    output = f"Items ({len(items)} total):\n"
    for i, item in enumerate(items, 1):
        output += f"{i:3d}. {item}\n"
        
    return output
