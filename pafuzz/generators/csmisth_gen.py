"""Csmith-based C program generator with swarm testing support."""

import os
import random
import logging
from typing import Dict, List, Optional
from pafuzz.generators.utils import run_cmd
from pafuzz.generators.config import config

class CsmithGenerator:
    """Generate C programs using Csmith with swarm testing."""
    
    # Swarm testing features
    SWARM_FEATURES = [
        "arrays", "bitfields", "comma-operators", "compound-assignment",
        "consts", "divs", "jumps", "longlong", "muls", "pointers", 
        "structs", "unions", "volatiles", "inline-function"
    ]
    
    def __init__(self, csmith_bin: Optional[str] = None, 
                 csmith_runtime: Optional[str] = None):
        """Initialize generator with optional custom paths."""
        self.csmith_bin = csmith_bin or config.CSMITH
        self.csmith_runtime = csmith_runtime or config.CSMITH_HOME
        self._setup_environment()
    
    def _setup_environment(self):
        """Setup environment variables for Csmith."""
        if self.csmith_runtime:
            os.environ["CSMITH_HOME"] = os.path.dirname(self.csmith_bin)
            os.environ["CSMITH_RUNTIME"] = self.csmith_runtime
    
    def generate(self, output_file: str, seed: Optional[int] = None,
                functions: int = 5, swarm: bool = True,
                max_struct_fields: int = 6, max_block_depth: int = 5,
                max_array_dim: int = 3) -> bool:
        """Generate a C program using Csmith.
        
        Args:
            output_file: Output file path
            seed: Random seed (auto-generated if None)
            functions: Number of functions to generate
            swarm: Enable swarm testing
            max_struct_fields: Maximum struct fields
            max_block_depth: Maximum block depth
            max_array_dim: Maximum array dimensions
            
        Returns:
            True if generation successful, False otherwise
        """
        if seed is None:
            seed = random.randint(1, 100000)
        
        cmd = self._build_command(
            output_file, seed, functions, swarm,
            max_struct_fields, max_block_depth, max_array_dim
        )
        
        logging.info(f"Generating with seed {seed}: {' '.join(cmd)}")
        
        ret_code, stdout, stderr = run_cmd(cmd, config.CSMITH_TIMEOUT)
        
        if ret_code == 0:
            logging.info(f"Successfully generated: {output_file}")
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                logging.info(f"File size: {size} bytes")
            return True
        else:
            logging.error(f"Generation failed (code {ret_code}): {stderr}")
            return False
    
    def _build_command(self, output_file: str, seed: int, functions: int,
                      swarm: bool, max_struct_fields: int, 
                      max_block_depth: int, max_array_dim: int) -> List[str]:
        """Build the Csmith command."""
        cmd = [
            self.csmith_bin,
            "--seed", str(seed),
            "--output", output_file,
            "--max-funcs", str(functions),
            "--max-struct-fields", str(max_struct_fields),
            "--max-block-depth", str(max_block_depth),
            "--max-array-dim", str(max_array_dim)
        ]
        
        if swarm:
            cmd.extend(self._get_swarm_flags(seed))
        
        return cmd
    
    def _get_swarm_flags(self, seed: int) -> List[str]:
        """Generate swarm testing flags based on seed."""
        random.seed(seed)
        
        # Random enable/disable for each feature
        config_map = {
            feature: random.choice([True, False]) 
            for feature in self.SWARM_FEATURES
        }
        
        # Ensure at least 1/3 features are enabled
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
        
        logging.info(f"Swarm config: {config_map}")
        return flags

# Convenience function for backward compatibility
def generate_c_program(output_file: str, seed: Optional[int] = None,
                      functions: int = 5, swarm: bool = True) -> bool:
    """Generate a C program using default Csmith generator."""
    generator = CsmithGenerator()
    return generator.generate(output_file, seed, functions, swarm)


