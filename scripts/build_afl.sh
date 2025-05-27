#!/bin/bash

# Build script for AFL++
set -e

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"

echo "Building AFL++..."

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Download and build AFL++
if [ ! -d "AFLplusplus" ]; then
    git clone https://github.com/AFLplusplus/AFLplusplus.git
else
    cd AFLplusplus && git pull && cd ..
fi

cd AFLplusplus

# Build AFL++
AFL_INSTALL_DIR="$BUILD_DIR/afl-install"
mkdir -p "$AFL_INSTALL_DIR"

# Clean previous build
make clean || true

# Build AFL++ with all features
make all
make install PREFIX="$AFL_INSTALL_DIR"

echo "AFL++ built and configured successfully!"

# Update config
CONFIG_FILE="$PROJECT_ROOT/config.json"
python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
except:
    config = {}

config.update({
    'AFL_FUZZ': '$AFL_INSTALL_DIR/bin/afl-fuzz',
    'AFL_CC': '$AFL_INSTALL_DIR/bin/afl-clang-fast',
    'AFL_HOME': '$AFL_INSTALL_DIR'
})

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=4)
"

echo "AFL++ built and configured successfully!"

