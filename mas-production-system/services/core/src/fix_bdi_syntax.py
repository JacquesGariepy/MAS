#!/usr/bin/env python3
"""
Fix the syntax error in base_agent.py
"""

import os

def fix_syntax_error():
    """Fix the incorrectly placed code in base_agent.py"""
    
    file_path = '/app/src/core/agents/base_agent.py'
    
    print(f"🔧 Fixing syntax error in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find and remove the misplaced code (lines 197-211)
    # We need to move this code to after line 195 but properly indented
    
    # First, let's identify the misplaced code
    misplaced_start = None
    misplaced_end = None
    
    for i, line in enumerate(lines):
        if i >= 196 and "# Ensure actions is a list" in line and line.startswith('        '):
            misplaced_start = i
        if misplaced_start and i > misplaced_start and "actions = []" in line:
            misplaced_end = i + 1
            break
    
    if misplaced_start and misplaced_end:
        # Extract the misplaced code
        misplaced_code = lines[misplaced_start:misplaced_end]
        
        # Remove it from its current location
        del lines[misplaced_start:misplaced_end]
        
        # Find where to insert it (after "actions = await self.act()")
        for i, line in enumerate(lines):
            if "actions = await self.act()" in line:
                # Insert the code here, properly indented (add 4 more spaces)
                insert_index = i + 1
                for j, code_line in enumerate(misplaced_code):
                    # Add proper indentation
                    indented_line = '    ' + code_line
                    lines.insert(insert_index + j, indented_line)
                break
    
    # Write the fixed file
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Fixed syntax error")
    
    return file_path

if __name__ == "__main__":
    fix_syntax_error()
    print("\n✅ Syntax fix complete!")
    print("\nNow try running:")
    print("  docker exec mas-production-system-core-1 python /app/examples/autonomous_fixed.py")