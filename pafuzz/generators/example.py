#!/usr/bin/env python3
"""Example usage of fuzzlib generators."""

import logging
import tempfile
from pathlib import Path


from pafuzz.generators.csmith import CsmithGenerator
from pafuzz.generators.yarpgen import YarpgenGenerator

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


def main():
    """Run generator demonstrations."""
    setup_logging()
    
    print("Fuzzlib Generators Demo")
    print("=" * 30)
    
    try:
        demo_csmith()
    except Exception as e:
        print(f"Demo failed: {e}")
        logging.exception("Demo error")

if __name__ == "__main__":
    main() 