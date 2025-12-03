#!/usr/bin/env bash
# .github/workflows/scripts/build-local-dev.sh
# Build local development packages without version tagging
# This script reuses the existing release build logic but for local development testing
#
# Usage: .github/workflows/scripts/build-local-dev.sh [agent] [script_type]
#   agent: kilocode, claude, or kiro (default: kilocode)
#   script_type: sh or ps (default: sh)
#
# Examples:
#   .github/workflows/scripts/build-local-dev.sh kilocode sh
#   .github/workflows/scripts/build-local-dev.sh claude sh
#   .github/workflows/scripts/build-local-dev.sh kiro sh

set -euo pipefail

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Parse arguments with defaults
AGENT="${1:-kilocode}"
SCRIPT="${2:-sh}"
VERSION="local-dev"

# Validate agent
case "$AGENT" in
    kilocode|claude|kiro) ;;
    *) echo "Error: Invalid agent '$AGENT'. Must be: kilocode, claude, or kiro" >&2; exit 1 ;;
esac

# Validate script type
case "$SCRIPT" in
    sh|ps) ;;
    *) echo "Error: Invalid script type '$SCRIPT'. Must be: sh or ps" >&2; exit 1 ;;
esac

echo "Building local development package for $AGENT ($SCRIPT)..."

# Use .genlocal instead of .genreleases to avoid conflicts with release builds
GENLOCAL_DIR="$REPO_ROOT/.genlocal"

# Clean and create local build directory
rm -rf "$GENLOCAL_DIR"
mkdir -p "$GENLOCAL_DIR"

# Change to repo root for build process
cd "$REPO_ROOT"

# Override GENRELEASES_DIR to use our local directory
export GENRELEASES_DIR="$GENLOCAL_DIR"

# Set NEW_VERSION for the sourced script (required by create-release-packages.sh)
export NEW_VERSION="$VERSION"

# Source only the functions we need from create-release-packages.sh
# We need to extract the functions without running the main script logic
{
    # Read the script and extract only the function definitions
    # Also patch the macOS cp --parents compatibility issue
    sed -n '/^rewrite_paths()/,/^}$/p; /^generate_commands()/,/^}$/p; /^build_variant()/,/^}$/p' \
        "$REPO_ROOT/.github/workflows/scripts/create-release-packages.sh" | \
    sed 's/cp --parents {} "$EVALKIT_DIR"\//cp {} "$EVALKIT_DIR\/templates\/"/'
} > "$GENLOCAL_DIR/functions.sh"

# Source the extracted functions
source "$GENLOCAL_DIR/functions.sh"

# Build the specific variant using the existing build_variant function
# This ensures we use the exact same transformation logic as releases
build_variant "$AGENT" "$SCRIPT"

# Clean up temporary function file
rm -f "$GENLOCAL_DIR/functions.sh"

echo "✓ Local development package built successfully"
echo "  Location: $GENLOCAL_DIR/evalkit-${AGENT}-package-${SCRIPT}/"
echo "  Archive: $GENLOCAL_DIR/evalkit-template-${AGENT}-${SCRIPT}-${VERSION}.zip"