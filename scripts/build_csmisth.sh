#!/bin/bash

# Build script for csmith
set -e

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"

echo "Building csmith..."

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Download and build csmith
if [ ! -d "csmith" ]; then
    git clone https://github.com/csmith-project/csmith.git
else
    cd csmith && git pull && cd ..
fi

cd csmith

# Build csmith
CSMITH_INSTALL_DIR="$BUILD_DIR/csmith-install"
mkdir -p "$CSMITH_INSTALL_DIR"

# Clean previous build
rm -rf CMakeCache.txt CMakeFiles/

cmake -DCMAKE_INSTALL_PREFIX="$CSMITH_INSTALL_DIR" -DCMAKE_CXX_FLAGS="-Wno-enum-constexpr-conversion" .
make -j$(nproc)
make install

echo "csmith built successfully!"

# Create JSON config file
CONFIG_FILE="$PROJECT_ROOT/config.json"
CLANG_PATH=$(which clang 2>/dev/null || echo "clang")
GCC_PATH=$(which gcc 2>/dev/null || echo "gcc")

cat > "$CONFIG_FILE" << EOF
{
    "CSMITH": "$CSMITH_INSTALL_DIR/bin/csmith",
    "CSMITH_HOME": "$CSMITH_INSTALL_DIR/include",
    "CLANG": "$CLANG_PATH",
    "GCC": "$GCC_PATH"
}
EOF

echo "Configuration created at: $CONFIG_FILE"
echo "Build complete!"