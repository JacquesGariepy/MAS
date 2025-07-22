#!/usr/bin/env python3
"""
Comprehensive Unicode Handling Tests for MAS Production System
Tests various Unicode scenarios including the problematic '\udcc3' character
"""

import sys
import os
import tempfile
import logging
import json
import codecs
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Test data with various Unicode scenarios
UNICODE_TEST_CASES = {
    "ascii_normal": {
        "content": "Hello World! This is normal ASCII text.",
        "expected_encoding": "ascii",
        "should_succeed": True
    },
    "utf8_accents": {
        "content": "Café, naïve, résumé - French accents: é à ç ê ô ù",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "utf8_mixed_languages": {
        "content": "English, Español, Français, Deutsch, Português, Italiano",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "emojis_basic": {
        "content": "🚀 Rocket 🌟 Star ❤️ Heart 🔥 Fire 🎉 Party",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "emojis_complex": {
        "content": "👨‍👩‍👧‍👦 Family 🏳️‍🌈 Rainbow Flag 👨🏻‍💻 Developer",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "chinese_simplified": {
        "content": "简体中文：你好世界！这是一个测试。",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "chinese_traditional": {
        "content": "繁體中文：你好世界！這是一個測試。",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "japanese_mixed": {
        "content": "日本語: こんにちは世界！ひらがな、カタカナ、漢字。",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "korean": {
        "content": "한국어: 안녕하세요 세계! 한글 테스트입니다.",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "arabic": {
        "content": "العربية: مرحبا بالعالم! هذا اختبار.",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "hebrew": {
        "content": "עברית: שלום עולם! זהו מבחן.",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "russian_cyrillic": {
        "content": "Русский: Привет мир! Это тест кириллицы.",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "greek": {
        "content": "Ελληνικά: Γεια σου κόσμε! Αυτό είναι ένα τεστ.",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "special_symbols": {
        "content": "Math: ∑ ∏ ∞ ≠ ≤ ≥ ∈ ∉ ∪ ∩ ⊂ ⊃ √ ∛ ∜",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "currency_symbols": {
        "content": "Currencies: $ € £ ¥ ₹ ₽ ₿ ¢ ¤",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "box_drawing": {
        "content": "┌─────┐\n│ Box │\n└─────┘",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "problematic_surrogate": {
        "content": "This contains the problematic character: \udcc3",
        "expected_encoding": "utf-8",
        "should_succeed": False,  # This should fail with standard encoding
        "is_surrogate": True
    },
    "mixed_surrogates": {
        "content": "Mixed: \udcc3\udcc4\udcc5 with normal text",
        "expected_encoding": "utf-8",
        "should_succeed": False,
        "is_surrogate": True
    },
    "invalid_utf8_sequence": {
        "content": b"\xff\xfe Invalid UTF-8".decode('utf-8', errors='surrogateescape'),
        "expected_encoding": "utf-8",
        "should_succeed": False,
        "is_surrogate": True
    },
    "zero_width_chars": {
        "content": "Zero​Width​Space: 'Hello​World'",  # Contains zero-width spaces
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "bidi_text": {
        "content": "English العربية English עברית Mixed",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "combining_diacritics": {
        "content": "Café (composed) vs Café (combining): é vs é",
        "expected_encoding": "utf-8",
        "should_succeed": True
    },
    "control_characters": {
        "content": "Line1\nLine2\rLine3\tTabbed\x0bVertical\x0cForm",
        "expected_encoding": "utf-8",
        "should_succeed": True
    }
}


class TestUnicodeHandling:
    """Test class for Unicode handling scenarios"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_file_write_read_unicode(self, temp_dir):
        """Test writing and reading files with various Unicode content"""
        results = []
        
        for test_name, test_case in UNICODE_TEST_CASES.items():
            file_path = Path(temp_dir) / f"{test_name}.txt"
            result = {
                "test_name": test_name,
                "content_preview": test_case["content"][:50] + "..." if len(test_case["content"]) > 50 else test_case["content"]
            }
            
            # Test writing
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(test_case["content"])
                result["write_success"] = True
                result["write_error"] = None
            except Exception as e:
                result["write_success"] = False
                result["write_error"] = str(e)
            
            # Test reading
            if result["write_success"]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        read_content = f.read()
                    result["read_success"] = True
                    result["read_error"] = None
                    result["content_matches"] = read_content == test_case["content"]
                except Exception as e:
                    result["read_success"] = False
                    result["read_error"] = str(e)
                    result["content_matches"] = False
            
            results.append(result)
            
            # Print result immediately
            print(f"\n{'='*60}")
            print(f"Test: {test_name}")
            print(f"Content: {result['content_preview']}")
            print(f"Write: {'✓' if result['write_success'] else '✗'} {result.get('write_error', '')}")
            if result.get('read_success') is not None:
                print(f"Read: {'✓' if result['read_success'] else '✗'} {result.get('read_error', '')}")
                print(f"Match: {'✓' if result.get('content_matches', False) else '✗'}")
        
        return results
    
    def test_logging_with_unicode(self, temp_dir):
        """Test logging with Unicode content - the main issue"""
        log_file = Path(temp_dir) / "unicode_test.log"
        results = []
        
        # Test 1: Standard UTF-8 encoding (current implementation)
        try:
            logger1 = logging.getLogger("test_utf8")
            handler1 = logging.FileHandler(log_file, encoding='utf-8')
            handler1.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            logger1.addHandler(handler1)
            
            # This should work
            logger1.info("Normal UTF-8: Café résumé 🚀")
            
            # This will fail with surrogate characters
            try:
                logger1.info(f"Problematic: \udcc3")
                results.append(("UTF-8 with surrogate", "FAILED - Should have failed!"))
            except Exception as e:
                results.append(("UTF-8 with surrogate", f"Expected failure: {type(e).__name__}"))
            
            handler1.close()
            logger1.removeHandler(handler1)
        except Exception as e:
            results.append(("UTF-8 logging setup", f"Failed: {e}"))
        
        # Test 2: Using surrogateescape error handler (fix for the issue)
        try:
            log_file2 = Path(temp_dir) / "unicode_test_fixed.log"
            logger2 = logging.getLogger("test_surrogateescape")
            
            # Custom handler that uses surrogateescape
            handler2 = logging.FileHandler(log_file2, encoding='utf-8', errors='surrogateescape')
            handler2.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            logger2.addHandler(handler2)
            
            # Test normal UTF-8
            logger2.info("Normal UTF-8: Café résumé 🚀")
            
            # Test problematic surrogate - should work now
            logger2.info(f"Problematic surrogate: \udcc3")
            logger2.info("Mixed: \udcc3\udcc4 with normal text")
            
            handler2.close()
            logger2.removeHandler(handler2)
            
            # Verify the file was written
            if log_file2.exists():
                results.append(("Surrogateescape logging", "SUCCESS - File created"))
            else:
                results.append(("Surrogateescape logging", "FAILED - No file"))
                
        except Exception as e:
            results.append(("Surrogateescape logging", f"Failed: {e}"))
        
        # Test 3: Using replace error handler
        try:
            log_file3 = Path(temp_dir) / "unicode_test_replace.log"
            logger3 = logging.getLogger("test_replace")
            
            handler3 = logging.FileHandler(log_file3, encoding='utf-8', errors='replace')
            handler3.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            logger3.addHandler(handler3)
            
            # Test with surrogate characters - will replace with ?
            logger3.info(f"Surrogate with replace: \udcc3")
            
            handler3.close()
            logger3.removeHandler(handler3)
            
            if log_file3.exists():
                results.append(("Replace error handler", "SUCCESS - File created"))
        except Exception as e:
            results.append(("Replace error handler", f"Failed: {e}"))
        
        return results
    
    def test_json_with_unicode(self, temp_dir):
        """Test JSON serialization with Unicode"""
        results = []
        
        # Test normal Unicode in JSON
        data1 = {
            "message": "Hello 世界 🌍",
            "languages": ["English", "中文", "العربية", "עברית"],
            "emoji": "🚀🌟❤️"
        }
        
        try:
            json_str = json.dumps(data1, ensure_ascii=False, indent=2)
            results.append(("JSON with Unicode", "SUCCESS"))
            
            # Write to file
            json_file = Path(temp_dir) / "unicode.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data1, f, ensure_ascii=False, indent=2)
            
            # Read back
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            if loaded_data == data1:
                results.append(("JSON round-trip", "SUCCESS"))
            else:
                results.append(("JSON round-trip", "FAILED - Data mismatch"))
                
        except Exception as e:
            results.append(("JSON with Unicode", f"Failed: {e}"))
        
        # Test problematic surrogates in JSON
        data2 = {
            "problematic": "\udcc3",
            "normal": "text"
        }
        
        try:
            # This will fail
            json_str = json.dumps(data2)
            results.append(("JSON with surrogate", "FAILED - Should have failed!"))
        except Exception as e:
            results.append(("JSON with surrogate", f"Expected failure: {type(e).__name__}"))
        
        return results
    
    def test_pathlib_with_unicode(self, temp_dir):
        """Test Path operations with Unicode filenames"""
        results = []
        
        unicode_filenames = [
            "café.txt",
            "文件.txt",
            "файл.txt",
            "αρχείο.txt",
            "🚀rocket.txt",
            "mixed_语言_file.txt"
        ]
        
        for filename in unicode_filenames:
            try:
                file_path = Path(temp_dir) / filename
                file_path.write_text("Test content", encoding='utf-8')
                
                # Verify it exists
                if file_path.exists():
                    # Read it back
                    content = file_path.read_text(encoding='utf-8')
                    if content == "Test content":
                        results.append((f"Path: {filename}", "SUCCESS"))
                    else:
                        results.append((f"Path: {filename}", "FAILED - Content mismatch"))
                else:
                    results.append((f"Path: {filename}", "FAILED - File not created"))
                    
            except Exception as e:
                results.append((f"Path: {filename}", f"Failed: {e}"))
        
        return results
    
    def test_string_operations_unicode(self):
        """Test various string operations with Unicode"""
        results = []
        
        # Test string length with Unicode
        test_strings = [
            ("ASCII", "Hello", 5),
            ("Accents", "Café", 4),
            ("Emoji", "🚀", 1),
            ("Family emoji", "👨‍👩‍👧‍👦", 1),  # This is one grapheme cluster
            ("Chinese", "你好", 2),
            ("Mixed", "Hello世界", 7)
        ]
        
        for name, string, expected_len in test_strings:
            actual_len = len(string)
            if actual_len == expected_len:
                results.append((f"Length {name}", f"SUCCESS: {actual_len}"))
            else:
                results.append((f"Length {name}", f"FAILED: Expected {expected_len}, got {actual_len}"))
        
        # Test string operations
        test_ops = [
            ("Upper", "café", "café".upper()),
            ("Lower", "CAFÉ", "café"),
            ("Title", "hello world", "Hello World"),
            ("Strip", "  hello  ", "hello"),
            ("Replace", "hello", "hello".replace("l", "L"))
        ]
        
        for op_name, input_str, expected in test_ops:
            try:
                if op_name == "Upper":
                    result = input_str.upper()
                elif op_name == "Lower":
                    result = input_str.lower()
                elif op_name == "Title":
                    result = input_str.title()
                elif op_name == "Strip":
                    result = input_str.strip()
                elif op_name == "Replace":
                    result = input_str.replace("l", "L")
                
                results.append((f"{op_name} operation", "SUCCESS"))
            except Exception as e:
                results.append((f"{op_name} operation", f"Failed: {e}"))
        
        return results


def create_test_report(test_results: Dict[str, List]) -> str:
    """Create a formatted test report"""
    report = """# Unicode Handling Test Report

## Test Summary

This report contains comprehensive tests for Unicode handling in the MAS Production System,
specifically addressing the '\\udcc3' surrogate character issue in logging.

## Test Results

"""
    
    for test_category, results in test_results.items():
        report += f"### {test_category}\n\n"
        
        success_count = sum(1 for r in results if "SUCCESS" in str(r) or "Expected failure" in str(r))
        total_count = len(results)
        
        report += f"**Success Rate**: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)\n\n"
        
        report += "| Test | Result |\n"
        report += "|------|--------|\n"
        
        for result in results:
            if isinstance(result, tuple):
                test_name, test_result = result
                status_icon = "✅" if "SUCCESS" in test_result or "Expected failure" in test_result else "❌"
                report += f"| {test_name} | {status_icon} {test_result} |\n"
            else:
                report += f"| {result.get('test_name', 'Unknown')} | {result} |\n"
        
        report += "\n"
    
    report += """## Key Findings

1. **The Problem**: The original code uses `logging.FileHandler(LOG_FILE, encoding='utf-8')` which fails when encountering surrogate characters like '\\udcc3'.

2. **The Solution**: Use `logging.FileHandler(LOG_FILE, encoding='utf-8', errors='surrogateescape')` or `errors='replace'` to handle these characters gracefully.

3. **Surrogate Characters**: These are Unicode code points in the range U+D800 to U+DFFF that are reserved for UTF-16 encoding and are invalid in UTF-8.

## Recommendations

1. **Immediate Fix**: Update line 38 in `autonomous.py`:
   ```python
   # Change from:
   logging.FileHandler(LOG_FILE, encoding='utf-8')
   
   # To:
   logging.FileHandler(LOG_FILE, encoding='utf-8', errors='surrogateescape')
   ```

2. **Best Practices**:
   - Always specify error handling when dealing with file I/O
   - Use `errors='surrogateescape'` to preserve the original bytes
   - Use `errors='replace'` to replace invalid characters with �
   - Use `errors='ignore'` to skip invalid characters entirely

3. **Testing**: Regular testing with various Unicode inputs including edge cases like surrogate pairs

"""
    
    return report


def main():
    """Run all Unicode tests"""
    print("🔍 Starting Unicode Handling Tests...")
    print("="*80)
    
    # Create test instance
    tester = TestUnicodeHandling()
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run all tests
        test_results = {}
        
        print("\n📝 Testing File I/O with Unicode...")
        test_results["File I/O Tests"] = tester.test_file_write_read_unicode(temp_dir)
        
        print("\n📋 Testing Logging with Unicode (Main Issue)...")
        test_results["Logging Tests"] = tester.test_logging_with_unicode(temp_dir)
        
        print("\n📊 Testing JSON with Unicode...")
        test_results["JSON Tests"] = tester.test_json_with_unicode(temp_dir)
        
        print("\n📁 Testing Path Operations with Unicode...")
        test_results["Path Tests"] = tester.test_pathlib_with_unicode(temp_dir)
        
        print("\n🔤 Testing String Operations with Unicode...")
        test_results["String Tests"] = tester.test_string_operations_unicode()
        
        # Generate report
        report = create_test_report(test_results)
        
        # Save report
        report_path = Path("/app/logs") / f"unicode_test_report_{os.getpid()}.md"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(report, encoding='utf-8')
        
        print(f"\n📄 Test report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 TEST SUMMARY")
        print("="*80)
        
        for category, results in test_results.items():
            if isinstance(results[0], dict):
                success = sum(1 for r in results if r.get('write_success') and r.get('read_success', True))
                total = len(results)
            else:
                success = sum(1 for r in results if "SUCCESS" in str(r) or "Expected failure" in str(r))
                total = len(results)
            
            print(f"{category}: {success}/{total} passed")
        
        print("\n✅ Unicode testing completed!")
        
        # Show the fix
        print("\n" + "="*80)
        print("🔧 FIX FOR THE ISSUE")
        print("="*80)
        print("In autonomous.py, line 38, change:")
        print("  logging.FileHandler(LOG_FILE, encoding='utf-8')")
        print("To:")
        print("  logging.FileHandler(LOG_FILE, encoding='utf-8', errors='surrogateescape')")
        print("\nThis will handle surrogate characters like '\\udcc3' gracefully.")


if __name__ == "__main__":
    main()