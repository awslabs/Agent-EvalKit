#!/bin/bash

# Automated OpenTelemetry Collector Setup Script
# Downloads and sets up otelcol-contrib binary in .evalkit/tracing/
#
# Usage: .evalkit/tracing/setup-otelcol.sh
# Run from repository root directory

set -e

OTELCOL_VERSION="0.138.0"
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Map architecture names
case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    arm64)
        ARCH="arm64"
        ;;
    aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Map OS names
case $OS in
    darwin)
        OS="darwin"
        ;;
    linux)
        OS="linux"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

# Set up directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACING_DIR=".evalkit/tracing"
BINARY_PATH="${TRACING_DIR}/otelcol-contrib"

echo "🔧 Setting up OpenTelemetry Collector (Automated)"
echo "================================================="
echo "Version: ${OTELCOL_VERSION}"
echo "OS: ${OS}"
echo "Architecture: ${ARCH}"
echo "Binary will be saved to: ${BINARY_PATH}"
echo ""

# Create tracing directory if it doesn't exist
mkdir -p "${TRACING_DIR}"

# Check if binary already exists
if [ -f "${BINARY_PATH}" ]; then
    echo "✅ otelcol-contrib binary already exists at ${BINARY_PATH}"
    echo "   To re-download, delete ${BINARY_PATH} and run this script again"
    exit 0
fi

# Use the correct URL pattern from opentelemetry-collector-releases
BINARY_NAME="otelcol-contrib_${OTELCOL_VERSION}_${OS}_${ARCH}.tar.gz"
DOWNLOAD_URL="https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTELCOL_VERSION}/${BINARY_NAME}"

echo "📥 Downloading OpenTelemetry Collector binary..."
echo "   URL: ${DOWNLOAD_URL}"

# Download with better error handling
curl -L -f -o "${TRACING_DIR}/otelcol-contrib.tar.gz" "${DOWNLOAD_URL}"

if [ $? -ne 0 ]; then
    echo "❌ Download failed."
    echo ""
    echo "🔧 Manual setup required:"
    echo "   1. Visit: https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v${OTELCOL_VERSION}"
    echo "   2. Download: ${BINARY_NAME}"
    echo "   3. Extract: tar -xzf ${BINARY_NAME}"
    echo "   4. Rename to: otelcol-contrib"
    echo "   5. Make executable: chmod +x otelcol-contrib"
    exit 1
fi

# Check if download was successful (file size > 1KB)
if [ ! -f "${TRACING_DIR}/otelcol-contrib.tar.gz" ] || [ $(stat -f%z "${TRACING_DIR}/otelcol-contrib.tar.gz" 2>/dev/null || stat -c%s "${TRACING_DIR}/otelcol-contrib.tar.gz" 2>/dev/null || echo "0") -lt 1000 ]; then
    echo "❌ Downloaded file is too small or doesn't exist"
    rm -f "${TRACING_DIR}/otelcol-contrib.tar.gz"
    exit 1
fi

echo "📦 Extracting binary..."
cd "${TRACING_DIR}"
tar -xzf "otelcol-contrib.tar.gz"

# Find the binary in the extracted files
BINARY_FOUND=false

# Try different possible names
for possible_name in "otelcol-contrib" "otelcol-contrib_${OTELCOL_VERSION}_${OS}_${ARCH}" "otelcol-contrib_${OS}_${ARCH}"; do
    if [ -f "./${possible_name}" ]; then
        if [ "${possible_name}" != "otelcol-contrib" ]; then
            mv "./${possible_name}" "./otelcol-contrib"
        fi
        BINARY_FOUND=true
        break
    fi
done

# If not found, look for any otelcol* file
if [ "$BINARY_FOUND" = false ]; then
    FOUND_BINARY=$(find . -name "otelcol*" -type f | head -1)
    if [ -n "$FOUND_BINARY" ]; then
        mv "$FOUND_BINARY" "./otelcol-contrib"
        BINARY_FOUND=true
    fi
fi

if [ "$BINARY_FOUND" = false ]; then
    echo "❌ Could not find otelcol-contrib binary in extracted files"
    echo "   Contents of extracted archive:"
    ls -la
    exit 1
fi

# Make executable
chmod +x "./otelcol-contrib"

# Clean up
rm -f "otelcol-contrib.tar.gz"
# Remove any extra files that might have been extracted (like README.md)
rm -f README.md readme.md README.txt readme.txt LICENSE LICENSE.txt

# Test the binary
echo ""
echo "🎉 Setup complete!"
echo "   Binary location: ${BINARY_PATH}"

if ./otelcol-contrib --version >/dev/null 2>&1; then
    echo "   Version: $(./otelcol-contrib --version 2>/dev/null | head -1)"
else
    echo "   ⚠️  Version check failed, but binary exists"
fi

# Return to original directory
cd - > /dev/null