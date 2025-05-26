"""LLVM bitcode generation utilities."""

import logging
from pathlib import Path
from typing import Optional

from pafuzz.generators.config import config
from pafuzz.generators.utils import run_cmd


def generate_llvm_bitcode(c_file: str, bc_file: str, 
                         clang_path: Optional[str] = None,
                         csmith_runtime: Optional[str] = None) -> bool:
    """
    Generate LLVM bitcode from a C source file.
    
    Args:
        c_file: Input C source file
        bc_file: Output LLVM bitcode file
        clang_path: Path to clang compiler (uses config default if None)
        csmith_runtime: Path to csmith runtime (uses config default if None)
        
    Returns:
        bool: True if generation successful, False otherwise
    """
    clang = clang_path or config.CLANG
    runtime = csmith_runtime or config.CSMITH_HOME
    
    if not clang:
        logging.error("Clang path not configured for bitcode generation")
        return False
        
    if not Path(clang).exists():
        logging.error(f"Clang not found at {clang}")
        return False
        
    try:
        cmd = [
            clang,
            "-emit-llvm", "-g",
            "-I", runtime,
            "-o", bc_file,
            "-c", c_file
        ]

        ret_code, stdout, stderr = run_cmd(cmd, config.COMPILE_TIMEOUT)

        if ret_code != 0:
            logging.error(f"Clang failed to generate bitcode: {stderr}")
            return False

        logging.info(f"Successfully generated bitcode: {bc_file}")
        return True

    except Exception as e:
        logging.error(f"Error generating bitcode: {str(e)}")
        return False 