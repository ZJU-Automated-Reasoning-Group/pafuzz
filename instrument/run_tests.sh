#!/bin/bash

# Test runner for indirect call instrumentation
set -e

echo "=== Indirect Call Instrumentation Test Suite ==="
echo ""

# Check dependencies
echo "Checking dependencies..."
if ! command -v llvm-config &> /dev/null; then
    echo "Error: llvm-config not found. Please install LLVM development tools."
    exit 1
fi

if ! command -v clang &> /dev/null; then
    echo "Error: clang not found. Please install clang."
    exit 1
fi

if ! command -v opt &> /dev/null; then
    echo "Error: opt not found. Please install LLVM tools."
    exit 1
fi

echo "Dependencies OK"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
make clean

# Build everything
echo "Building instrumentation pass and tests..."
make all

# Run tests
echo ""
echo "Running tests..."
make test

echo ""
echo "=== Test Summary ==="
echo "✓ LLVM pass compiled successfully"
echo "✓ Runtime library compiled successfully" 
echo "✓ Test cases executed"

if [ -f "indirect_calls.log" ]; then
    call_count=$(grep -c "^[0-9]" indirect_calls.log || echo "0")
    echo "✓ Logged $call_count indirect calls"
    echo ""
    echo "Sample log entries:"
    head -5 indirect_calls.log
else
    echo "⚠ No indirect call log generated"
fi

echo ""
echo "Test suite completed successfully!" 