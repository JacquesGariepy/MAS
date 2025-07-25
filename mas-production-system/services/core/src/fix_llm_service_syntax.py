#!/usr/bin/env python3
"""
Quick fix for the syntax error in llm_service.py
"""

import os

def fix_syntax_error():
    """Fix the unterminated string literal error"""
    
    file_path = '/app/src/services/llm_service.py'
    
    print(f"🔧 Fixing syntax error in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 474 - the split('\n') is broken across lines
    if len(lines) > 474:
        # Lines are 0-indexed, so line 474 is at index 473
        if "lines = response_text.strip().split('" in lines[473]:
            lines[473] = "                        lines = response_text.strip().split('\\n')\n"
            # Remove the hanging quote on the next line if it exists
            if lines[474].strip() == "')":
                lines[474] = ""
    
    # Fix line 480 and 481 - malformed quotes
    if len(lines) > 480:
        if 'key.strip().strip(\'"' in lines[479]:
            lines[479] = '                                key = key.strip().strip(\'"\\\')\\n'
        if 'value.strip().strip(\'"' in lines[480]:
            lines[480] = '                                value = value.strip().strip(\'",\\\')\\n'
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Fixed syntax errors")
    
    return file_path

if __name__ == "__main__":
    fix_syntax_error()
    print("\n✅ Syntax fix complete!")
    print("\nNow try running:")
    print("  docker exec mas-production-system-core-1 python /app/examples/autonomous_fixed.py")