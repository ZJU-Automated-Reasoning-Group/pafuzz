#include <stdio.h>
#include <stdlib.h>

// Test functions for indirect calls
int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

int subtract(int a, int b) {
    return a - b;
}

// Function pointer types
typedef int (*BinaryOp)(int, int);
typedef void (*VoidFunc)();

// Test case 1: Simple function pointer call
void test_simple_indirect_call() {
    printf("=== Test 1: Simple indirect call ===\n");
    BinaryOp op = add;
    int result = op(5, 3);
    printf("Result: %d\n", result);
}

// Test case 2: Function pointer array
void test_function_array() {
    printf("=== Test 2: Function pointer array ===\n");
    BinaryOp ops[] = {add, multiply, subtract};
    
    for (int i = 0; i < 3; i++) {
        int result = ops[i](10, 2);
        printf("Operation %d result: %d\n", i, result);
    }
}

// Test case 3: Conditional function pointer
void test_conditional_call() {
    printf("=== Test 3: Conditional indirect call ===\n");
    BinaryOp op = (rand() % 2) ? add : multiply;
    int result = op(7, 4);
    printf("Conditional result: %d\n", result);
}

// Test case 4: Function returning function pointer
BinaryOp get_operation(int choice) {
    switch (choice) {
        case 0: return add;
        case 1: return multiply;
        case 2: return subtract;
        default: return add;
    }
}

void test_returned_function_pointer() {
    printf("=== Test 4: Returned function pointer ===\n");
    BinaryOp op = get_operation(1);
    int result = op(6, 3);
    printf("Returned function result: %d\n", result);
}

// Test case 5: Nested indirect calls
void callback_function() {
    printf("Callback executed\n");
}

void execute_callback(VoidFunc callback) {
    if (callback) {
        callback();
    }
}

void test_nested_calls() {
    printf("=== Test 5: Nested indirect calls ===\n");
    VoidFunc cb = callback_function;
    execute_callback(cb);
}

// Test case 6: NULL function pointer (edge case)
void test_null_pointer() {
    printf("=== Test 6: NULL pointer handling ===\n");
    BinaryOp op = NULL;
    if (op) {
        op(1, 2);
    } else {
        printf("NULL pointer detected\n");
    }
}

// Test case 7: Function pointer in struct
struct Calculator {
    BinaryOp operation;
    int operand1;
    int operand2;
};

void test_struct_function_pointer() {
    printf("=== Test 7: Function pointer in struct ===\n");
    struct Calculator calc = {multiply, 8, 7};
    int result = calc.operation(calc.operand1, calc.operand2);
    printf("Struct operation result: %d\n", result);
}

// Test case 8: Multiple indirect calls in loop
void test_loop_indirect_calls() {
    printf("=== Test 8: Loop with indirect calls ===\n");
    BinaryOp ops[] = {add, subtract, multiply};
    
    for (int i = 0; i < 5; i++) {
        BinaryOp selected = ops[i % 3];
        int result = selected(i + 1, 2);
        printf("Loop iteration %d result: %d\n", i, result);
    }
}

int main() {
    printf("Starting indirect call instrumentation tests...\n\n");
    
    // Run all test cases
    test_simple_indirect_call();
    test_function_array();
    test_conditional_call();
    test_returned_function_pointer();
    test_nested_calls();
    test_null_pointer();
    test_struct_function_pointer();
    test_loop_indirect_calls();
    
    printf("\nAll tests completed.\n");
    return 0;
} 