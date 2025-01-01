import os

# Tool paths
parse_tool = '/home/code/ParseAst/tool_all'
parse_tool_clang = '/home/code/ParseAst/tool_clang'
YARPGEN = '/home/compiler/yarpgen/build/yarpgen'
CSMITH = '/home/software/csmith/bin/csmith'
CSMITH_HOME = '/home/compiler/csmith/runtime'
SAN_FILE = '/home/code/Artifact/san_check.sh'
YARP_SAN_FILE = '/home/code/Artifact/yarp_san_check.sh'
GCC = '/home/software/gcc-trunk-3aa004f/bin/gcc'
CLANG = 'clang'

# Timeouts
YARPGEN_TIMEOUT = 10
PARSE_TIMEOUT = 8
CSMITH_TIMEOUT = 15
SHELL_TIMEOUT = 300
COMPILE_TIMEOUT = 30
SAN_COMPILE_TIMEOUT = 30
RUN_TIMEOUT = 15

# Other constants
MIN_PROGRAM_SIZE = 20000