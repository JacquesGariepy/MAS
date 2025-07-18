#!/usr/bin/env python3
"""
Script to verify and apply the LLM JSON fix
"""

import os
import sys
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def verify_fix_applied(filepath):
    """Check if the fix has been applied"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for key indicators of the fix
    indicators = [
        "_extract_reasoning_content",
        "Response:",
        "delimiter_patterns",
        "extracted_from_reasoning"
    ]
    
    applied_count = sum(1 for indicator in indicators if indicator in content)
    return applied_count >= 3

def main():
    # Path to the LLM service file
    llm_service_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "services", "core", "src", "services", "llm_service.py"
    )
    
    print("🔍 LLM JSON Fix Verification Tool")
    print("=" * 50)
    
    if not os.path.exists(llm_service_path):
        print(f"❌ LLM service file not found at: {llm_service_path}")
        return 1
    
    print(f"📄 Checking file: {llm_service_path}")
    
    if verify_fix_applied(llm_service_path):
        print("✅ Fix is already applied!")
        print("\n🎯 The LLM service includes:")
        print("   - Enhanced JSON extraction for phi-4-mini-reasoning")
        print("   - Improved prompt format with Response: delimiter")
        print("   - Fallback content extraction mechanism")
        print("   - Better error handling for reasoning models")
    else:
        print("⚠️  Fix not fully applied or file has been modified")
        print("\n📝 To apply the fix manually:")
        print("   1. The fix adds better JSON extraction patterns")
        print("   2. Updates prompts to guide reasoning models")
        print("   3. Adds fallback content extraction")
        print("\n💡 Run the test script to verify functionality:")
        print("   python examples/test_llm_json_fix.py")
    
    # Check if running in Docker
    if os.path.exists("/.dockerenv"):
        print("\n🐳 Running inside Docker container")
        print("   Changes should be reflected immediately due to volume mount")
    else:
        print("\n💻 Running on host machine")
        print("   Make sure to restart Docker services if needed:")
        print("   docker-compose -f docker-compose.dev.yml restart core")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())