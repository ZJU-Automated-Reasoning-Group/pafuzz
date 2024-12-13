#!/usr/bin/env python3

import json
import logging
import random
import subprocess
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CSourceGenerator:
    """Generator for C source files using csmith with configurable options."""

    # Default paths (can be overridden by config file)
    CSMITH_PATH = '/home/work/csmith/src/csmith'
    CLANG_PATH = '/usr/bin/clang'
    CSMITH_RUNTIME = '/home/work/csmith/runtime'

    # Options that can be randomly enabled/disabled for program diversity
    SWARM_OPTIONS = [
        "arrays", "checksum", "comma-operators", "compound-assignment",
        "consts", "divs", "embedded-assigns", "jumps", "longlong",
        "force-non-uniform-arrays", "math64", "builtins", "muls",
        "packed-struct", "paranoid", "structs", "volatiles",
        "volatile-pointers", "arg-structs", "dangling-global-pointers"
    ]

    # Default options that are always enabled
    BASE_OPTIONS = [
        "--pointers", "--no-unions", "--safe-math", "--no-argc",
        "--no-inline-function", "--no-bitfields", "--no-return-structs",
        "--quiet", "--concise", "--max-pointer-depth", "6"
    ]

    @classmethod
    def from_config(cls, config_file: str) -> 'CSourceGenerator':
        """Create a generator instance from a configuration file."""
        try:
            with open(config_file) as f:
                config = json.load(f)
                return cls(
                    csmith_path=config.get('CSMITH_PATH', cls.CSMITH_PATH),
                    clang_path=config.get('CLANG_PATH', cls.CLANG_PATH),
                    csmith_runtime=config.get('CSMITH_RUNTIME', cls.CSMITH_RUNTIME)
                )
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
            return cls()

    def __init__(self, csmith_path: Optional[str] = None,
                 clang_path: Optional[str] = None,
                 csmith_runtime: Optional[str] = None):
        """Initialize the generator with optional custom paths."""
        self.csmith_path = csmith_path or self.CSMITH_PATH
        self.clang_path = clang_path or self.CLANG_PATH
        self.csmith_runtime = csmith_runtime or self.CSMITH_RUNTIME

        if not Path(self.csmith_path).exists():
            raise FileNotFoundError(f"csmith not found at {self.csmith_path}")

    def check_undefined_behavior(self, cfilename: str) -> int:
        """
        Check whether the generated C program has undefined behavior.
        
        Returns:
            0: No undefined behavior detected
            1: Runtime error detected
            2: Compilation error
            3: Execution timeout
        """
        exe = f"{cfilename}exe-clang"
        out = f"{cfilename}out-clang"

        # Compile with UBSan
        compile_cmd = [
            "timeout", "30s",
            self.clang_path, "-msse4.2", "-m64",
            f"-I{self.csmith_runtime}",
            "-O0", "-fsanitize=undefined",
            "-c", cfilename, "-o", exe
        ]

        try:
            result = subprocess.run(compile_cmd,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                logging.error("Cannot compile program")
                return 2

            # Run the compiled program
            run_cmd = ["timeout", "30s", f"./{exe}"]
            with open(out, "w") as outf:
                result = subprocess.run(run_cmd,
                                        stdout=outf,
                                        stderr=subprocess.DEVNULL)
                if result.returncode != 0:
                    logging.error("Program execution timeout")
                    return 3

            # Check for runtime errors
            with open(out, "r") as outf:
                if any("runtime error" in line for line in outf):
                    logging.error("Runtime error detected")
                    return 1

            return 0

        finally:
            # Cleanup
            for file in [exe, out]:
                Path(file).unlink(missing_ok=True)

    def _generate_swarm_options(self) -> List[str]:
        """Generate random swarm testing options."""
        options = []
        for opt in self.SWARM_OPTIONS:
            prefix = "--" if random.random() < 0.5 else "--no-"
            options.append(f"{prefix}{opt}")
        return options

    def generate_source(self, output_file: str, check_ub: bool = False) -> bool:
        """
        Generate a C source file using csmith.
        
        Args:
            output_file: Path to save the generated C file
            check_ub: Whether to check for undefined behavior
            
        Returns:
            bool: True if generation successful, False otherwise
        """
        try:
            cmd = [self.csmith_path]
            cmd.extend(self._generate_swarm_options())
            cmd.extend(self.BASE_OPTIONS)

            logging.debug(f"Running command: {' '.join(cmd)}")

            with open(output_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    text=True
                )

            if result.returncode != 0:
                logging.error(f"csmith failed: {result.stderr}")
                return False

            if check_ub and self.check_undefined_behavior(output_file) != 0:
                return False

            return True

        except subprocess.TimeoutExpired:
            logging.error("csmith timed out")
            return False
        except Exception as e:
            logging.error(f"Error generating source: {str(e)}")
            return False


def generate_llvm_bitcode(generator: CSourceGenerator, c_file: str, bc_file: str) -> bool:
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
    generator = CSourceGenerator.from_config('generator_config.json')

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
