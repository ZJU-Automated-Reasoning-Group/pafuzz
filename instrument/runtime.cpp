// runtime.cpp - Runtime support for the instrumentation pass
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <unordered_map>
#include <string>

extern "C" {

// Global data structures for tracking
static FILE *afl_log_file = nullptr;
static std::unordered_map<void*, std::string> function_name_cache;

// Initialize logging
__attribute__((constructor))
void __afl_init_logging() {
    const char *log_path = getenv("AFL_INDIRECT_CALL_LOG");
    if (!log_path) {
        log_path = "/tmp/afl_indirect_calls.log";
    }
    
    afl_log_file = fopen(log_path, "w");
    if (afl_log_file) {
        fprintf(afl_log_file, "# AFL Indirect Call Log\n");
        fprintf(afl_log_file, "# Format: call_site_id|caller_info|target_ptr|target_name\n");
        fflush(afl_log_file);
    }
}

// Cleanup logging
__attribute__((destructor))
void __afl_cleanup_logging() {
    if (afl_log_file) {
        fclose(afl_log_file);
    }
}

// Resolve function name from pointer
char* __afl_resolve_function_name(void* func_ptr) {
    static char unknown[] = "unknown";
    
    if (!func_ptr) {
        return unknown;
    }
    
    // Check cache first
    auto it = function_name_cache.find(func_ptr);
    if (it != function_name_cache.end()) {
        return const_cast<char*>(it->second.c_str());
    }
    
    // Try to resolve using dladdr
    Dl_info info;
    if (dladdr(func_ptr, &info) && info.dli_sname) {
        std::string name = info.dli_sname;
        function_name_cache[func_ptr] = name;
        return const_cast<char*>(function_name_cache[func_ptr].c_str());
    }
    
    // Try to get symbol info using backtrace_symbols
    char **symbols = backtrace_symbols(&func_ptr, 1);
    if (symbols && symbols[0]) {
        std::string symbol_info = symbols[0];
        free(symbols);
        
        // Extract function name from symbol info
        size_t start = symbol_info.find('(');
        size_t end = symbol_info.find('+');
        if (start != std::string::npos && end != std::string::npos && start < end) {
            std::string name = symbol_info.substr(start + 1, end - start - 1);
            if (!name.empty()) {
                function_name_cache[func_ptr] = name;
                return const_cast<char*>(function_name_cache[func_ptr].c_str());
            }
        }
    }
    
    // Fallback: use hex address
    char addr_str[32];
    snprintf(addr_str, sizeof(addr_str), "func_%p", func_ptr);
    function_name_cache[func_ptr] = addr_str;
    return const_cast<char*>(function_name_cache[func_ptr].c_str());
}

// Log indirect call
void __afl_log_indirect_call(int call_site_id, void* target_func, 
                           char* caller_info, char* target_name) {
    if (afl_log_file) {
        fprintf(afl_log_file, "%d|%s|%p|%s\n", 
                call_site_id, caller_info, target_func, target_name);
        fflush(afl_log_file);
    }
    
    // Also print to stderr for debugging
    fprintf(stderr, "[AFL] Indirect call %d: %s -> %s (%p)\n",
            call_site_id, caller_info, target_name, target_func);
}

} // extern "C"