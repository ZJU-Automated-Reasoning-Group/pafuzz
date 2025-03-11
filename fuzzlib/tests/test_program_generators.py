"""
This file contains tests for the program generators.
"""

import unittest
from generators.program_generation import generate_program, generate_program_yarpgen


class TestProgramGenerators(unittest.TestCase):
    def test_generate_program(self):
        tmp_dir = "test_tmp"
        seed = 12345
        result = generate_program(tmp_dir, "csmith", seed)
        self.assertIsNotNone(result)

    def test_generate_program_yarpgen(self):
        tmp_dir = "test_tmp"
        seed = 12345
        result = generate_program_yarpgen(tmp_dir, seed)
        self.assertIsNotNone(result)



if __name__ == "__main__":
    unittest.main()