"""
This file contains tests for the program generators.
"""

import unittest
import tempfile
import os
from pafuzz.generators.csmisth_gen import generate_c_program
from pafuzz.generators.yarpgen_gen import generate_cpp_program


class TestProgramGenerators(unittest.TestCase):
    def test_generate_c_program(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, "test_program.c")
            seed = 12345
            result = generate_c_program(output_file, seed)
            self.assertIsInstance(result, bool)

    def test_generate_cpp_program(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            seed = 12345
            result = generate_cpp_program(tmp_dir, seed)
            self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()