import unittest

class TestExample(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(1 + 1, 2)
        
    def test_string(self):
        self.assertEqual("hello".upper(), "HELLO")
        
    def test_list(self):
        self.assertIn(1, [1, 2, 3])
        
if __name__ == '__main__':
    unittest.main()
