# Indirect Call Instrumentation Test Suite

This directory contains test cases for the AFL indirect call tracking instrumentation module.

## Overview

The instrumentation module consists of:
- **`trace_icall.cpp`**: LLVM pass that instruments indirect function calls
- **`runtime.cpp`**: Runtime library that logs indirect call information
- **`test_indirect_calls.cpp`**: Comprehensive test cases

## Test Cases

The test suite includes 8 different scenarios:

1. **Simple indirect call** - Basic function pointer usage
2. **Function pointer array** - Array of function pointers
3. **Conditional indirect call** - Runtime function selection
4. **Returned function pointer** - Functions returning function pointers
5. **Nested indirect calls** - Callbacks and nested calls
6. **NULL pointer handling** - Edge case testing
7. **Function pointer in struct** - Structured data with function pointers
8. **Loop with indirect calls** - Multiple calls in iteration

## Building and Running

### Quick Start
```bash
./run_tests.sh
```

### Manual Build
```bash
# Build everything
make all

# Run tests
make test

# Clean build artifacts
make clean
```

### Requirements
- LLVM development tools (`llvm-config`, `opt`)
- Clang compiler
- Make

## Output

The instrumented test generates:
- **Console output**: Test execution results and debug information
- **`indirect_calls.log`**: Detailed log of all indirect calls with format:
  ```
  call_site_id|caller_info|target_ptr|target_name
  ```

## Example Log Entry
```
0|test_simple_indirect_call:test_indirect_calls.cpp:24:17|0x104567890|add
```

This shows:
- Call site ID: 0
- Caller: `test_simple_indirect_call` function at line 24, column 17
- Target pointer: 0x104567890
- Target function: `add`

## Integration

To use the instrumentation in your own code:

1. Compile your code to LLVM IR:
   ```bash
   clang -emit-llvm -S -o program.ll program.c
   ```

2. Apply the instrumentation pass:
   ```bash
   opt -load ./trace_icall.so -afl-indirect-call-tracker -S program.ll -o program_instrumented.ll
   ```

3. Compile with runtime library:
   ```bash
   clang -o program program_instrumented.ll ./runtime.so
   ```

4. Run with logging:
   ```bash
   AFL_INDIRECT_CALL_LOG=./calls.log ./program
   ``` 