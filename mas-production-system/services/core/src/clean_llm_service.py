#!/usr/bin/env python3
"""
Clean up the corrupted llm_service.py file by removing orphaned code
"""

def clean_file():
    """Remove orphaned code from llm_service.py"""
    
    file_path = '/app/src/services/llm_service.py'
    
    print(f"🔧 Cleaning {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the orphaned code section (lines 428-499)
    # We want to remove everything from line 428 up to but not including line 501
    cleaned_lines = []
    skip_mode = False
    
    for i, line in enumerate(lines):
        line_num = i + 1  # 1-indexed
        
        # Start skipping at line 428
        if line_num == 428 and "# First attempt: direct JSON parsing" in line:
            skip_mode = True
            continue
            
        # Stop skipping at line 501
        if line_num >= 501 and "except Exception as e:" in line:
            skip_mode = False
            
        if not skip_mode:
            cleaned_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ Removed orphaned code")
    
    return file_path

if __name__ == "__main__":
    clean_file()
    print("\n✅ Cleanup complete!")
    print("\nNow try running:")
    print("  docker exec mas-production-system-core-1 python /app/examples/autonomous_fixed.py")