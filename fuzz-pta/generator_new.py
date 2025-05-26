#!/usr/bin/env python3

import json
import logging
import random
import subprocess
from pathlib import Path
from typing import List, Optional
from pafuzz.generators.csmith import CsmithGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_llvm_bitcode(generator: CsmithGenerator, c_file: str, bc_file: str) -> bool:
    """
    Generate LLVM bitcode from a C source file.
    
    Args:
        generator: CSourceGenerator instance for paths
        c_file: Input C source file
        bc_file: Output LLVM bitcode file
        
    Returns:
        bool: True if generation successful, False otherwise
    """
    try:
        cmd = [
            generator.clang_path,
            "-emit-llvm", "-g",
            "-I", generator.csmith_runtime,
            "-o", bc_file,
            "-c", c_file
        ]

        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )

        if result.returncode != 0:
            logging.error(f"clang failed: {result.stderr}")
            return False

        return True

    except subprocess.TimeoutExpired:
        logging.error("clang timed out")
        return False
    except Exception as e:
        logging.error(f"Error generating bitcode: {str(e)}")
        return False


def main():
    """Example usage of the generator."""
    # Try to load from config file, fall back to defaults if not found
    generator = CsmithGenerator.from_config('generator_config.json')

    c_file = "output.c"
    bc_file = "output.bc"

    if generator.generate_source(c_file, check_ub=True):
        logging.info(f"Generated C source file: {c_file}")

        if generate_llvm_bitcode(generator, c_file, bc_file):
            logging.info(f"Generated LLVM bitcode: {bc_file}")
        else:
            logging.error("Failed to generate LLVM bitcode")
    else:
        logging.error("Failed to generate C source")


if __name__ == "__main__":
    main()
