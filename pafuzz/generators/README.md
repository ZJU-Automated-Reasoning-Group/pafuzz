# Fuzzlib Generators

A concise and modular program generation library for fuzzing, supporting Csmith and YARPGen.

## Features

- **Class-based generators** with consistent interfaces
- **Configurable parameters** via JSON config files
- **Swarm testing support** for Csmith
- **Undefined behavior checking** with sanitizers
- **LLVM bitcode generation** support
- **Type hints** and comprehensive error handling
- **Utility functions** for command execution and sanitizer checks

## Quick Start

```python
from pafuzz.generators import CsmithGenerator, YarpgenGenerator, CSourceGenerator

# Generate C program with Csmith (original)
csmith = CsmithGenerator()
csmith.generate("test.c", seed=12345, functions=5, swarm=True)

# Generate C program with enhanced CSourceGenerator
csource = CSourceGenerator()
csource.generate_source("enhanced.c", check_ub=True, seed=12345)
csource.generate_llvm_bitcode("enhanced.c", "enhanced.bc")

# Generate C++ program with YARPGen  
yarpgen = YarpgenGenerator()
yarpgen.generate("output_dir", seed=54321, std="c++17")
```

## Configuration

Create `~/.pafuzz/config.json`:

```json
{
    "CSMITH": "/path/to/csmith",
    "YARPGEN": "/path/to/yarpgen", 
    "CSMITH_HOME": "/path/to/csmith/runtime",
    "CSMITH_TIMEOUT": 15,
    "YARPGEN_TIMEOUT": 10
}
```

## API Reference

### CsmithGenerator

- `generate(output_file, seed=None, functions=5, swarm=True, ...)` - Generate C program
- Supports swarm testing with automatic feature selection
- Configurable struct fields, block depth, array dimensions

### CSourceGenerator

- `generate_source(output_file, check_ub=False, seed=None)` - Generate C program with UB checking
- `generate_llvm_bitcode(c_file, bc_file)` - Generate LLVM bitcode from C source
- `check_undefined_behavior(cfilename)` - Check for undefined behavior using sanitizers
- Enhanced swarm testing with extended option set
- Built-in undefined behavior detection and filtering

### YarpgenGenerator  

- `generate(output_dir, seed=None, std="c++17", emit_pragmas=True, ...)` - Generate C++ program
- Supports different C++ standards
- Optional pragma and undefined behavior emission

### Utilities

- `run_cmd(cmd, timeout, work_dir=None)` - Execute commands with timeout
- `sanitize_check(src_file, include_path, tmp_dir)` - Run sanitizer checks
- `cleanup_tmp_files(tmp_dir, keep_source=False)` - Clean temporary files

## Examples

- See `example.py` for complete usage demonstrations
- See `csource_example.py` for CSourceGenerator usage examples 