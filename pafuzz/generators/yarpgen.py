"""YARPGen-based C++ program generator."""

import os
import random
import logging
from typing import Optional, List
from pafuzz.generators.utils import run_cmd
from pafuzz.generators.config import config

class YarpgenGenerator:
    """Generate C++ programs using YARPGen."""
    
    def __init__(self, yarpgen_bin: Optional[str] = None):
        """Initialize generator with optional custom path."""
        self.yarpgen_bin = yarpgen_bin or config.YARPGEN
    
    def generate(self, output_dir: str, seed: Optional[int] = None,
                std: str = "c++17", emit_pragmas: bool = True,
                emit_ub: bool = False, max_depth: int = 5) -> bool:
        """Generate a C++ program using YARPGen.
        
        Args:
            output_dir: Output directory for generated files
            seed: Random seed (auto-generated if None)
            std: C++ standard to target
            emit_pragmas: Whether to emit optimization pragmas
            emit_ub: Whether to emit undefined behavior
            max_depth: Maximum nesting depth
            
        Returns:
            True if generation successful, False otherwise
        """
        if seed is None:
            seed = random.randint(1, 100000)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = self._build_command(
            output_dir, seed, std, emit_pragmas, emit_ub, max_depth
        )
        
        logging.info(f"Generating with seed {seed}: {' '.join(cmd)}")
        
        ret_code, stdout, stderr = run_cmd(cmd, config.YARPGEN_TIMEOUT, output_dir)
        
        if ret_code == 0:
            logging.info(f"Successfully generated in: {output_dir}")
            self._log_generated_files(output_dir)
            return True
        else:
            logging.error(f"Generation failed (code {ret_code}): {stderr}")
            return False
    
    def _build_command(self, output_dir: str, seed: int, std: str,
                      emit_pragmas: bool, emit_ub: bool, max_depth: int) -> List[str]:
        """Build the YARPGen command."""
        cmd = [
            self.yarpgen_bin,
            "--seed", str(seed),
            "--std", std,
            "--max-depth", str(max_depth)
        ]
        
        if emit_pragmas:
            cmd.append("--emit-pragmas")
        
        if emit_ub:
            cmd.append("--emit-ub")
        
        return cmd
    
    def _log_generated_files(self, output_dir: str):
        """Log information about generated files."""
        try:
            files = [f for f in os.listdir(output_dir) 
                    if f.endswith(('.cpp', '.h'))]
            
            total_size = 0
            for filename in files:
                filepath = os.path.join(output_dir, filename)
                size = os.path.getsize(filepath)
                total_size += size
                logging.info(f"Generated {filename}: {size} bytes")
            
            logging.info(f"Total size: {total_size} bytes")
        except Exception as e:
            logging.warning(f"Could not analyze generated files: {e}")

# Convenience function for backward compatibility
def generate_cpp_program(output_dir: str, seed: Optional[int] = None,
                        std: str = "c++17") -> bool:
    """Generate a C++ program using default YARPGen generator."""
    generator = YarpgenGenerator()
    return generator.generate(output_dir, seed, std)
