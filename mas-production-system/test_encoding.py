#!/usr/bin/env python3
"""Test script to verify Unicode encoding fixes"""

import sys
import os
sys.path.append('/app')

# Import the sanitize functions from autonomous_fixed
from examples.autonomous_fixed import sanitize_unicode, safe_json_dumps

def test_sanitize_unicode():
    """Test the sanitize_unicode function with problematic characters"""
    
    test_cases = [
        # Normal text
        ("Hello World", "Hello World"),
        
        # Text with accents
        ("Café résumé", "Café résumé"),
        
        # Surrogate characters (the problematic ones)
        ("Test \udcc3 with surrogate", "Test  with surrogate"),
        ("Multiple \ud800 surrogates \udfff here", "Multiple  surrogates  here"),
        
        # Mixed problematic content
        ("Résumé with \udcc3 surrogate", "Résumé with  surrogate"),
        
        # Emoji and special characters
        ("Hello 😊 World", "Hello 😊 World"),
        
        # Complex Unicode
        ("测试中文字符", "测试中文字符"),
        
        # None and non-string
        (None, "None"),
        (123, "123"),
        ({"key": "value"}, "{'key': 'value'}")
    ]
    
    print("Testing sanitize_unicode function:")
    print("-" * 50)
    
    for input_text, expected in test_cases:
        try:
            result = sanitize_unicode(input_text)
            status = "✓" if result == expected else "✗"
            print(f"{status} Input: {repr(input_text)}")
            print(f"  Output: {repr(result)}")
            if result != expected:
                print(f"  Expected: {repr(expected)}")
        except Exception as e:
            print(f"✗ Input: {repr(input_text)}")
            print(f"  Error: {e}")
        print()

def test_safe_json_dumps():
    """Test the safe_json_dumps function"""
    
    test_objects = [
        # Simple object
        {"name": "test", "value": 123},
        
        # Object with accents
        {"café": "résumé", "français": "oui"},
        
        # Object with problematic characters
        {"text": "Test \udcc3 with surrogate"},
        
        # Nested object with mixed content
        {
            "normal": "text",
            "accented": "café",
            "surrogate": "bad \udcc3 char",
            "nested": {
                "more": "surrogates \ud800 here"
            }
        },
        
        # List with problematic content
        ["normal", "café", "bad \udcc3 char"],
    ]
    
    print("\nTesting safe_json_dumps function:")
    print("-" * 50)
    
    for obj in test_objects:
        try:
            result = safe_json_dumps(obj, indent=2)
            print(f"✓ Input: {repr(obj)}")
            print(f"  Output JSON:")
            print("  " + "\n  ".join(result.split("\n")))
            
            # Try to encode to UTF-8 to verify it works
            result.encode('utf-8')
            print("  UTF-8 encoding: Success")
            
        except Exception as e:
            print(f"✗ Input: {repr(obj)}")
            print(f"  Error: {e}")
        print()

def test_file_writing():
    """Test writing files with problematic content"""
    
    test_content = """# Test Report
    
This report contains problematic characters:
- Normal text: Hello World
- Accented text: Café résumé
- Surrogate character: \udcc3
- Multiple surrogates: \ud800 and \udfff
- Mixed content: Résumé with \udcc3 surrogate

End of report.
"""
    
    print("\nTesting file writing with encoding:")
    print("-" * 50)
    
    # Test 1: Writing without sanitization (should fail)
    test_file1 = "/tmp/test_encoding_fail.txt"
    try:
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("✗ Writing unsanitized content: Unexpectedly succeeded")
    except UnicodeEncodeError as e:
        print(f"✓ Writing unsanitized content: Failed as expected ({e})")
    
    # Test 2: Writing with sanitization (should succeed)
    test_file2 = "/tmp/test_encoding_success.txt"
    try:
        sanitized_content = sanitize_unicode(test_content)
        with open(test_file2, 'w', encoding='utf-8') as f:
            f.write(sanitized_content)
        print("✓ Writing sanitized content: Success")
        
        # Read it back to verify
        with open(test_file2, 'r', encoding='utf-8') as f:
            read_content = f.read()
        print(f"  File size: {len(read_content)} chars")
        print(f"  Surrogates removed: {'\\udcc3' not in read_content}")
        
    except Exception as e:
        print(f"✗ Writing sanitized content: Failed ({e})")
    
    # Test 3: Writing with errors='replace' (fallback option)
    test_file3 = "/tmp/test_encoding_replace.txt"
    try:
        with open(test_file3, 'w', encoding='utf-8', errors='replace') as f:
            f.write(test_content)
        print("✓ Writing with errors='replace': Success")
        
        # Read it back to see what happened
        with open(test_file3, 'r', encoding='utf-8') as f:
            read_content = f.read()
        print(f"  File size: {len(read_content)} chars")
        
    except Exception as e:
        print(f"✗ Writing with errors='replace': Failed ({e})")

if __name__ == "__main__":
    print("=" * 60)
    print("Unicode Encoding Fix Test Suite")
    print("=" * 60)
    
    test_sanitize_unicode()
    test_safe_json_dumps()
    test_file_writing()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)