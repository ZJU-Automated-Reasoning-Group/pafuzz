# Makefile for indirect call instrumentation tests

LLVM_CONFIG ?= llvm-config
CXX = clang++
CC = clang

# LLVM flags
LLVM_CXXFLAGS = $(shell $(LLVM_CONFIG) --cxxflags)
LLVM_LDFLAGS = $(shell $(LLVM_CONFIG) --ldflags)
LLVM_LIBS = $(shell $(LLVM_CONFIG) --libs)

# Compiler flags
CXXFLAGS = -fPIC -Wall -O2 $(LLVM_CXXFLAGS)
CFLAGS = -fPIC -Wall -O2

# Targets
PASS_SO = trace_icall.so
RUNTIME_SO = runtime.so
TEST_BINARY = test_indirect_calls
TEST_INSTRUMENTED = test_indirect_calls_instrumented

.PHONY: all clean test

all: $(PASS_SO) $(RUNTIME_SO) $(TEST_BINARY)

# Build the LLVM pass
$(PASS_SO): trace_icall.cpp
	$(CXX) $(CXXFLAGS) -shared -o $@ $< $(LLVM_LDFLAGS)

# Build the runtime library
$(RUNTIME_SO): runtime.cpp
	$(CXX) $(CFLAGS) -shared -o $@ $< -ldl

# Build test without instrumentation
$(TEST_BINARY): test_indirect_calls.cpp
	$(CC) -O1 -g -o $@ $<

# Build test with instrumentation
$(TEST_INSTRUMENTED): test_indirect_calls.cpp $(PASS_SO) $(RUNTIME_SO)
	$(CC) -O1 -g -emit-llvm -S -o test_indirect_calls.ll $<
	opt -load ./$(PASS_SO) -afl-indirect-call-tracker -S test_indirect_calls.ll -o test_indirect_calls_instrumented.ll
	$(CC) -O1 -g -o $@ test_indirect_calls_instrumented.ll ./$(RUNTIME_SO)

# Run tests
test: $(TEST_BINARY) $(TEST_INSTRUMENTED)
	@echo "=== Running uninstrumented test ==="
	./$(TEST_BINARY)
	@echo ""
	@echo "=== Running instrumented test ==="
	AFL_INDIRECT_CALL_LOG=./indirect_calls.log ./$(TEST_INSTRUMENTED)
	@echo ""
	@echo "=== Indirect call log ==="
	@cat indirect_calls.log || echo "No log file generated"

# Clean build artifacts
clean:
	rm -f $(PASS_SO) $(RUNTIME_SO) $(TEST_BINARY) $(TEST_INSTRUMENTED)
	rm -f *.ll *.log

# Help target
help:
	@echo "Available targets:"
	@echo "  all       - Build pass, runtime, and tests"
	@echo "  test      - Run both instrumented and uninstrumented tests"
	@echo "  clean     - Remove build artifacts"
	@echo "  help      - Show this help message" 