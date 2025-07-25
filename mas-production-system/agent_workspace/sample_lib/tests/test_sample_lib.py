"""
Unit tests for sample_lib
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SampleClass
from utils import helper_function, validate_input

class TestSampleClass(unittest.TestCase):
    """Test cases for SampleClass"""
    
    def setUp(self):
        self.sample = SampleClass("Test")
        
    def test_initialization(self):
        self.assertEqual(self.sample.name, "Test")
        self.assertEqual(len(self.sample.data), 0)
        
    def test_add_data(self):
        self.sample.add_data("item1")
        self.assertEqual(len(self.sample.data), 1)
        self.assertEqual(self.sample.data[0], "item1")
        
    def test_process_data(self):
        self.sample.add_data("apple")
        self.sample.add_data("banana")
        result = self.sample.process_data()
        self.assertIn("2 items", result)
        self.assertIn("apple", result)
        self.assertIn("banana", result)
        
class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_helper_function(self):
        result = helper_function("hello")
        self.assertEqual(result, "Processed: HELLO")
        
    def test_validate_input(self):
        self.assertTrue(validate_input("data"))
        with self.assertRaises(ValueError):
            validate_input("")
            
if __name__ == "__main__":
    unittest.main()
