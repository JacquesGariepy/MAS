#!/usr/bin/env python3
"""
Test autonomous_fixed.py with a calculator request
"""

import subprocess
import sys

def test_autonomous_agent():
    """Test the autonomous agent with a calculator request"""
    
    print("🧪 Testing autonomous_fixed.py with calculator request...")
    print("="*60)
    
    # The request to send
    request = "create a simple python calculator with basic operations (add, subtract, multiply, divide)"
    
    # Run the autonomous agent with the request
    process = subprocess.Popen(
        ['python', '/app/examples/autonomous_fixed.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send the request and quit
    stdout, stderr = process.communicate(input=f"{request}\nquit\n")
    
    # Print the output
    print("STDOUT:")
    print(stdout)
    
    if stderr:
        print("\nSTDERR:")
        print(stderr)
    
    # Check if any files were created
    import os
    workspace = "/app/outputs"
    if os.path.exists(workspace):
        print(f"\n📁 Files created in {workspace}:")
        for root, dirs, files in os.walk(workspace):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, workspace)
                print(f"  - {rel_path}")
                
                # Show content of calculator files
                if "calculator" in file.lower() or "calc" in file.lower():
                    print(f"\n📄 Content of {rel_path}:")
                    with open(filepath, 'r') as f:
                        content = f.read()
                        # Show first 500 chars
                        print(content[:500] + ("..." if len(content) > 500 else ""))
    
    return process.returncode == 0

if __name__ == "__main__":
    success = test_autonomous_agent()
    sys.exit(0 if success else 1)