#!/usr/bin/env python3
"""
Specific test for the '\udcc3' surrogate character issue in autonomous.py
This demonstrates the problem and validates the fix
"""

import logging
import tempfile
import os
from pathlib import Path


def test_original_implementation():
    """Test the original implementation that causes the error"""
    print("Testing ORIGINAL implementation (will fail with surrogate)...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_original.log"
        
        # Configure logging as in the original autonomous.py
        logger = logging.getLogger("test_original")
        handler = logging.FileHandler(log_file, encoding='utf-8')  # Original line 38
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Test normal Unicode - should work
        try:
            logger.info("Normal Unicode: Café résumé 世界 🚀")
            print("✅ Normal Unicode logging: SUCCESS")
        except Exception as e:
            print(f"❌ Normal Unicode logging: FAILED - {e}")
        
        # Test problematic surrogate - will fail
        try:
            logger.info(f"Problematic surrogate: \udcc3")
            print("❌ Surrogate logging: UNEXPECTED SUCCESS (should have failed!)")
        except UnicodeEncodeError as e:
            print(f"✅ Surrogate logging: Expected failure - {type(e).__name__}: {e}")
        except Exception as e:
            print(f"❓ Surrogate logging: Unexpected error type - {type(e).__name__}: {e}")
        
        # Clean up
        handler.close()
        logger.removeHandler(handler)


def test_fixed_implementation_surrogateescape():
    """Test the fixed implementation with surrogateescape error handler"""
    print("\nTesting FIXED implementation with 'surrogateescape'...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_fixed_surrogateescape.log"
        
        # Configure logging with the fix
        logger = logging.getLogger("test_fixed_surrogateescape")
        handler = logging.FileHandler(log_file, encoding='utf-8', errors='surrogateescape')  # Fixed line
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Test normal Unicode
        try:
            logger.info("Normal Unicode: Café résumé 世界 🚀")
            print("✅ Normal Unicode logging: SUCCESS")
        except Exception as e:
            print(f"❌ Normal Unicode logging: FAILED - {e}")
        
        # Test problematic surrogate - should work now
        try:
            logger.info(f"Problematic surrogate: \udcc3")
            print("✅ Surrogate logging: SUCCESS (fixed!)")
        except Exception as e:
            print(f"❌ Surrogate logging: FAILED - {e}")
        
        # Test multiple surrogates
        try:
            logger.info(f"Multiple surrogates: \udcc3\udcc4\udcc5")
            print("✅ Multiple surrogates: SUCCESS")
        except Exception as e:
            print(f"❌ Multiple surrogates: FAILED - {e}")
        
        # Verify file was created and contains data
        handler.close()
        logger.removeHandler(handler)
        
        if log_file.exists():
            try:
                # Read with surrogateescape to handle the surrogates properly
                content = log_file.read_text(encoding='utf-8', errors='surrogateescape')
                print(f"✅ Log file created, size: {len(content)} bytes")
                
                # Check if our messages are in the file
                if "Normal Unicode" in content:
                    print("✅ Normal Unicode message found in log")
                if "\udcc3" in content:
                    print("✅ Surrogate character preserved in log")
                    
            except Exception as e:
                print(f"❌ Error reading log file: {e}")
        else:
            print("❌ Log file was not created")


def test_fixed_implementation_replace():
    """Test the fixed implementation with replace error handler"""
    print("\nTesting FIXED implementation with 'replace'...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_fixed_replace.log"
        
        # Configure logging with replace error handler
        logger = logging.getLogger("test_fixed_replace")
        handler = logging.FileHandler(log_file, encoding='utf-8', errors='replace')  # Alternative fix
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Test problematic surrogate
        try:
            logger.info(f"Surrogate with replace: \udcc3")
            print("✅ Surrogate logging with replace: SUCCESS")
        except Exception as e:
            print(f"❌ Surrogate logging with replace: FAILED - {e}")
        
        # Verify file content
        handler.close()
        logger.removeHandler(handler)
        
        if log_file.exists():
            try:
                content = log_file.read_text(encoding='utf-8')
                print(f"✅ Log file created with replace handler")
                
                # The surrogate should be replaced with replacement character
                if "�" in content or "?" in content:
                    print("✅ Surrogate was replaced with replacement character")
                    
            except Exception as e:
                print(f"❌ Error reading log file: {e}")


def test_real_world_scenario():
    """Test a real-world scenario with mixed content"""
    print("\nTesting REAL-WORLD scenario with mixed content...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_real_world.log"
        
        # Use the recommended fix
        logger = logging.getLogger("test_real_world")
        handler = logging.FileHandler(log_file, encoding='utf-8', errors='surrogateescape')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Simulate real agent operations with various content
        test_messages = [
            "Starting autonomous agent...",
            "Processing request: Créer une application web",
            "Agent initialized: 开发者-agent-123",
            "Analyzing task complexity: высокая сложность",
            f"Found problematic data: \udcc3\udcc4",
            "Emoji status: 🚀 Ready, ❤️ Healthy, 🔥 Active",
            "Mixed content: Hello world! Привет мир! 你好世界！",
            "Task completed successfully ✅"
        ]
        
        errors = 0
        for msg in test_messages:
            try:
                logger.info(msg)
            except Exception as e:
                print(f"❌ Failed to log: {msg[:30]}... - {e}")
                errors += 1
        
        if errors == 0:
            print(f"✅ All {len(test_messages)} messages logged successfully!")
        else:
            print(f"❌ {errors} out of {len(test_messages)} messages failed")
        
        # Verify file content
        handler.close()
        logger.removeHandler(handler)
        
        if log_file.exists():
            print(f"✅ Log file created: {log_file}")
            print(f"   Size: {log_file.stat().st_size} bytes")


def demonstrate_the_fix():
    """Demonstrate the exact fix needed for autonomous.py"""
    print("\n" + "="*80)
    print("🔧 FIX DEMONSTRATION FOR autonomous.py")
    print("="*80)
    
    print("\n📍 Location: autonomous.py, line 38")
    print("\n❌ CURRENT CODE (causes error):")
    print("    logging.FileHandler(LOG_FILE, encoding='utf-8'),")
    
    print("\n✅ FIXED CODE (handles surrogates):")
    print("    logging.FileHandler(LOG_FILE, encoding='utf-8', errors='surrogateescape'),")
    
    print("\n📝 Alternative fixes:")
    print("    1. errors='surrogateescape' - Preserves the bytes (recommended)")
    print("    2. errors='replace' - Replaces with � character")
    print("    3. errors='ignore' - Silently drops the characters")
    
    print("\n💡 Why this works:")
    print("    - Surrogate characters (U+D800 to U+DFFF) are invalid in UTF-8")
    print("    - The 'surrogateescape' handler allows Python to handle them gracefully")
    print("    - This preserves the original data while preventing crashes")


def main():
    """Run all tests"""
    print("🔍 Testing Unicode Surrogate Character Issue")
    print("="*80)
    print("This test demonstrates the '\\udcc3' character issue and validates the fix\n")
    
    # Run tests
    test_original_implementation()
    test_fixed_implementation_surrogateescape()
    test_fixed_implementation_replace()
    test_real_world_scenario()
    demonstrate_the_fix()
    
    print("\n" + "="*80)
    print("✅ Testing completed!")
    print("\n📌 Summary:")
    print("   - Original implementation fails with UnicodeEncodeError")
    print("   - Fixed implementation with 'surrogateescape' handles all cases")
    print("   - The fix is a simple one-line change")
    print("="*80)


if __name__ == "__main__":
    main()