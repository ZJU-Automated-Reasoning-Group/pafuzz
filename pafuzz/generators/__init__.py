"""
Fuzzlib Generators - Program generation utilities for fuzzing.

This module provides generators for creating test programs using various tools
like Csmith and YARPGen. The module has been reorganized for better structure:

- core: Main generators with unified interfaces
- legacy: Deprecated generators for backward compatibility
"""

# Import from the new core module
from .csmith import CsmithGenerator, generate_c_program
from .yarpgen import YarpgenGenerator, generate_cpp_program

# Import utilities and config
from pafuzz.generators.config import config, load_config
from pafuzz.generators.utils import run_cmd, sanitize_check, cleanup_tmp_files, check_undefined_behavior
from pafuzz.generators.genbc import generate_llvm_bitcode as generate_bitcode

__all__ = [
    # Core generators (recommended)
    'CsmithGenerator',
    'YarpgenGenerator',
    'generate_c_program',
    'generate_bitcode',
    'generate_cpp_program',
    # Utilities
    'config',
    'load_config',
    'run_cmd',
    'sanitize_check',
    'cleanup_tmp_files',
    'check_undefined_behavior'
]

__version__ = '0.0.1'
