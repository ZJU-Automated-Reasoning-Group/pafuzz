"""Unified Csmith-based C program generator with comprehensive features."""

import json
import logging
import os
import random
import subprocess
from pathlib import Path
from typing import List, Optional

from pafuzz.generators.config import config
from pafuzz.generators.utils import check_undefined_behavior, cleanup_tmp_files


class CsmithGenerator:
    """Unified Csmith generator with swarm testing, UB checking, and LLVM bitcode support."""
    
    # Comprehensive swarm testing features (merged from both generators)
    SWARM_FEATURES = [
        "arrays", "bitfields", "checksum", "comma-operators", "compound-assignment",
        "consts", "divs", "embedded-assigns", "jumps", "longlong", "muls", 
        "pointers", "structs", "unions", "volatiles", "inline-function",
        "force-non-uniform-arrays", "math64", "builtins", "packed-struct", 
        "paranoid", "volatile-pointers", "arg-structs", "dangling-global-pointers"
    ]
    
    # Safe default options for reliable generation
    DEFAULT_OPTIONS = [
        "--safe-math", "--no-argc", "--no-return-structs",
        "--quiet", "--concise", "--max-pointer-depth", "6"
    ]
    
    def __init__(self, csmith_path: Optional[str] = None,
                 clang_path: Optional[str] = None,
                 csmith_runtime: Optional[str] = None):
        """Initialize generator with optional custom paths."""
        self.csmith_path = csmith_path or config.CSMITH
        self.clang_path = clang_path or config.CLANG
        self.csmith_runtime = csmith_runtime or config.CSMITH_HOME

    
    def generate(self, output_file: str, seed: Optional[int] = None,
                functions: int = 5, swarm: bool = True, check_ub: bool = False,
                max_struct_fields: int = 6, max_block_depth: int = 5,
                max_array_dim: int = 3, custom_options: Optional[List[str]] = None) -> bool:
        """Generate a C program using Csmith.
        
        Args:
            output_file: Output file path
            seed: Random seed (auto-generated if None)
            functions: Number of functions to generate
            swarm: Enable swarm testing
            check_ub: Check for undefined behavior
            max_struct_fields: Maximum struct fields
            max_block_depth: Maximum block depth
            max_array_dim: Maximum array dimensions
            custom_options: Additional custom Csmith options
            
        Returns:
            True if generation successful, False otherwise
        """
        try:
            
            if seed is None:
                seed = random.randint(1, 100000)
            
            cmd = self._build_command(
                output_file, seed, functions, swarm,
                max_struct_fields, max_block_depth, max_array_dim,
                custom_options or []
            )
            
            logging.info(f"Generating with seed {seed}: {' '.join(cmd)}")
            
            # Generate the C source
            with open(output_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=config.CSMITH_TIMEOUT,
                    text=True
                )
            
            if result.returncode != 0:
                logging.error(f"Csmith failed: {result.stderr}")
                return False
            
            # Check for undefined behavior if requested
            if check_ub and check_undefined_behavior(output_file, self.clang_path, self.csmith_runtime) != 0:
                logging.warning(f"Undefined behavior detected in {output_file}")
                return False
            
            logging.info(f"Successfully generated: {output_file}")
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                logging.info(f"File size: {size} bytes")
            
            return True
            
        except subprocess.TimeoutExpired:
            logging.error("Csmith generation timed out")
            return False
        except Exception as e:
            logging.error(f"Generation failed: {str(e)}")
            return False
    
    def _build_command(self, output_file: str, seed: int, functions: int,
                      swarm: bool, max_struct_fields: int, 
                      max_block_depth: int, max_array_dim: int,
                      custom_options: List[str]) -> List[str]:
        """Build the Csmith command."""
        cmd = [
            self.csmith_path,
            "--seed", str(seed),
            "--max-funcs", str(functions),
            "--max-struct-fields", str(max_struct_fields),
            "--max-block-depth", str(max_block_depth),
            "--max-array-dim", str(max_array_dim)
        ]
        
        # Add default safe options
        cmd.extend(self.DEFAULT_OPTIONS)
        
        # Add swarm testing flags
        if swarm:
            cmd.extend(self._get_swarm_flags(seed))
        
        # Add any custom options
        cmd.extend(custom_options)
        
        return cmd
    
    def _get_swarm_flags(self, seed: int) -> List[str]:
        """Generate swarm testing flags based on seed."""
        random.seed(seed)
        
        # Random enable/disable for each feature
        config_map = {
            feature: random.choice([True, False]) 
            for feature in self.SWARM_FEATURES
        }
        
        # Ensure at least 1/3 features are enabled for diversity
        enabled_count = sum(config_map.values())
        min_enabled = len(self.SWARM_FEATURES) // 3
        
        if enabled_count < min_enabled:
            disabled = [f for f, enabled in config_map.items() if not enabled]
            to_enable = random.sample(disabled, min_enabled - enabled_count)
            for feature in to_enable:
                config_map[feature] = True
        
        # Build flags
        flags = []
        for feature, enabled in config_map.items():
            flags.append(f"--{feature}" if enabled else f"--no-{feature}")
        
        logging.debug(f"Swarm config: {config_map}")
        return flags
    

# Convenience functions for backward compatibility
def generate_c_program(output_file: str, seed: Optional[int] = None,
                      functions: int = 5, swarm: bool = True, 
                      check_ub: bool = False) -> bool:
    """Generate a C program using default Csmith generator."""
    generator = CsmithGenerator()
    return generator.generate(output_file, seed, functions, swarm, check_ub)
