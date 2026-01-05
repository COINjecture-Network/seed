#!/bin/bash
# Build script for liboqs (Open Quantum Safe library)
# This script downloads, builds, and installs liboqs for quantum-resistant cryptography

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
INSTALL_DIR="${SCRIPT_DIR}/liboqs-install"
LIBOQS_VERSION="0.10.1"

echo "=========================================="
echo "Building liboqs v${LIBOQS_VERSION}"
echo "=========================================="

# Clean previous builds
if [ -d "${BUILD_DIR}" ]; then
    echo "Cleaning previous build directory..."
    rm -rf "${BUILD_DIR}"
fi

# Create build directory
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Download liboqs
echo "Downloading liboqs v${LIBOQS_VERSION}..."
curl -L "https://github.com/open-quantum-safe/liboqs/archive/refs/tags/${LIBOQS_VERSION}.tar.gz" -o liboqs.tar.gz
tar -xzf liboqs.tar.gz
cd "liboqs-${LIBOQS_VERSION}"

# Configure with CMake
echo "Configuring liboqs with CMake..."
mkdir -p build
cd build
cmake -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
      -DBUILD_SHARED_LIBS=ON \
      -DCMAKE_BUILD_TYPE=Release \
      ..

# Build
echo "Building liboqs..."
make -j$(nproc)

# Install
echo "Installing liboqs to ${INSTALL_DIR}..."
make install

echo "=========================================="
echo "liboqs v${LIBOQS_VERSION} built successfully!"
echo "Installation directory: ${INSTALL_DIR}"
echo "=========================================="
echo ""
echo "To use liboqs in your projects:"
echo "  Include path: ${INSTALL_DIR}/include"
echo "  Library path: ${INSTALL_DIR}/lib"
echo ""
echo "Set environment variables:"
echo "  export LD_LIBRARY_PATH=${INSTALL_DIR}/lib:\$LD_LIBRARY_PATH"
echo "  export PKG_CONFIG_PATH=${INSTALL_DIR}/lib/pkgconfig:\$PKG_CONFIG_PATH"
