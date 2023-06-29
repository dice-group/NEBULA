import logging
import unittest

# Bring your packages onto the path
import sys
import os


# Get the directory path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory path
parent_dir = os.path.dirname(current_dir)

# Append the module's directory to the Python module search path
module_dir = os.path.join(parent_dir, 'nebula')
sys.path.append(module_dir)

import coreferenceresolution

class TestMyModule(unittest.TestCase):
    def test_add_numbers(self):
        text = "John went to the stadium. He enjoyed the game. The stadium was packed with fans."

        coreferences = coreferenceresolution.coref_resolution(text)
        resolved_text = coreferenceresolution.replace_coreferences(text, coreferences)
        self.assertEqual(resolved_text, "5")


if __name__ == '__main__':
    unittest.main()