#!/usr/bin/env python3
"""Example usage of fuzzlib generators."""

import logging
import tempfile
from pathlib import Path

from pafuzz.generators.csmisth_gen import CsmithGenerator
from pafuzz.generators.yarpgen_gen import YarpgenGenerator

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def demo_csmith():
    """Demonstrate Csmith generator usage."""
    print("\n=== Csmith Generator Demo ===")
    
    generator = CsmithGenerator()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "test.c"
        
        # Generate with swarm testing
        success = generator.generate(
            str(output_file),
            seed=12345,
            functions=3,
            swarm=True
        )
        
        if success:
            print(f"✓ Generated C program: {output_file}")
            print(f"  Size: {output_file.stat().st_size} bytes")
        else:
            print("✗ Failed to generate C program")

def demo_yarpgen():
    """Demonstrate YARPGen generator usage."""
    print("\n=== YARPGen Generator Demo ===")
    
    generator = YarpgenGenerator()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "yarpgen_output"
        
        # Generate C++ program
        success = generator.generate(
            str(output_dir),
            seed=54321,
            std="c++17",
            emit_pragmas=True
        )
        
        if success:
            print(f"✓ Generated C++ program in: {output_dir}")
            files = list(output_dir.glob("*.cpp")) + list(output_dir.glob("*.h"))
            for f in files:
                print(f"  {f.name}: {f.stat().st_size} bytes")
        else:
            print("✗ Failed to generate C++ program")

def main():
    """Run generator demonstrations."""
    setup_logging()
    
    print("Fuzzlib Generators Demo")
    print("=" * 30)
    
    try:
        demo_csmith()
        demo_yarpgen()
    except Exception as e:
        print(f"Demo failed: {e}")
        logging.exception("Demo error")

if __name__ == "__main__":
    main() 