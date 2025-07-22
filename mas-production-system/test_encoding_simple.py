#!/usr/bin/env python3
"""Test script to verify Unicode encoding fixes - Standalone version"""

import json
import unicodedata
import re

def sanitize_unicode(text: str) -> str:
    """Sanitize Unicode text by removing surrogate characters and normalizing.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text safe for UTF-8 encoding
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove surrogate characters (U+D800 to U+DFFF)
    # These are invalid in UTF-8 and cause encoding errors
    text = re.sub(r'[\ud800-\udfff]', '', text)
    
    # Normalize Unicode to NFC (Canonical Decomposition, followed by Canonical Composition)
    text = unicodedata.normalize('NFC', text)
    
    # Replace any remaining problematic characters with their closest ASCII equivalent
    # or remove them if no equivalent exists
    cleaned = []
    for char in text:
        try:
            # Try to encode the character to UTF-8
            char.encode('utf-8')
            cleaned.append(char)
        except UnicodeEncodeError:
            # Try to get an ASCII representation
            ascii_repr = unicodedata.normalize('NFKD', char).encode('ascii', 'ignore').decode('ascii')
            if ascii_repr:
                cleaned.append(ascii_repr)
            else:
                # Skip the character if it can't be represented
                pass
    
    return ''.join(cleaned)

def safe_json_dumps(obj, **kwargs):
    """Safely convert object to JSON string with proper encoding.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with sanitized Unicode
    """
    # Ensure ensure_ascii is False to allow Unicode characters
    kwargs['ensure_ascii'] = False
    
    # Convert to JSON
    json_str = json.dumps(obj, **kwargs)
    
    # Sanitize the result
    return sanitize_unicode(json_str)

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
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        try:
            result = sanitize_unicode(input_text)
            status = "✓" if result == expected else "✗"
            if result == expected:
                passed += 1
            else:
                failed += 1
            print(f"{status} Input: {repr(input_text)}")
            print(f"  Output: {repr(result)}")
            if result != expected:
                print(f"  Expected: {repr(expected)}")
        except Exception as e:
            print(f"✗ Input: {repr(input_text)}")
            print(f"  Error: {e}")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return passed, failed

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
    
    passed = 0
    failed = 0
    
    for obj in test_objects:
        try:
            result = safe_json_dumps(obj, indent=2)
            print(f"✓ Input: {repr(obj)}")
            print(f"  Output JSON:")
            print("  " + "\n  ".join(result.split("\n")))
            
            # Try to encode to UTF-8 to verify it works
            result.encode('utf-8')
            print("  UTF-8 encoding: Success")
            passed += 1
            
        except Exception as e:
            print(f"✗ Input: {repr(obj)}")
            print(f"  Error: {e}")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return passed, failed

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
    
    passed = 0
    failed = 0
    
    # Test 1: Writing without sanitization (should fail)
    test_file1 = "/tmp/test_encoding_fail.txt"
    try:
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("✗ Writing unsanitized content: Unexpectedly succeeded")
        failed += 1
    except UnicodeEncodeError as e:
        print(f"✓ Writing unsanitized content: Failed as expected ({e})")
        passed += 1
    
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
        passed += 1
        
    except Exception as e:
        print(f"✗ Writing sanitized content: Failed ({e})")
        failed += 1
    
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
        passed += 1
        
    except Exception as e:
        print(f"✗ Writing with errors='replace': Failed ({e})")
        failed += 1
    
    print(f"Results: {passed} passed, {failed} failed")
    return passed, failed

if __name__ == "__main__":
    print("=" * 60)
    print("Unicode Encoding Fix Test Suite")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    p, f = test_sanitize_unicode()
    total_passed += p
    total_failed += f
    
    p, f = test_safe_json_dumps()
    total_passed += p
    total_failed += f
    
    p, f = test_file_writing()
    total_passed += p
    total_failed += f
    
    print("\n" + "=" * 60)
    print(f"Test suite completed! Total: {total_passed} passed, {total_failed} failed")
    print("=" * 60)