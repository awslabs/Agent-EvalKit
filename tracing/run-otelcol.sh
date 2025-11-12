#!/bin/bash

# OpenTelemetry Collector Runner Script
# Starts the otelcol-contrib binary with local configuration
#
# Usage examples:
# Run in foreground: .evalkit/tracing/run-otelcol.sh
# Run in background: .evalkit/tracing/run-otelcol.sh &
# Quick test (start & stop after 3s): .evalkit/tracing/run-otelcol.sh & sleep 3 && pkill -f otelcol-contrib

# Set up directory paths
TRACING_DIR=".evalkit/tracing"
BINARY_PATH="${TRACING_DIR}/otelcol-contrib"
CONFIG_PATH="${TRACING_DIR}/otel-config.yaml"

echo "🚀 Starting OpenTelemetry Collector"
echo "============================================="

# Check if binary exists
if [ ! -f "${BINARY_PATH}" ]; then
    echo "❌ otelcol-contrib binary not found at ${BINARY_PATH}!"
    echo "   Run .evalkit/tracing/setup-otelcol.sh first to download the binary"
    exit 1
fi

# Check if config exists
if [ ! -f "${CONFIG_PATH}" ]; then
    echo "❌ otel-config.yaml not found at ${CONFIG_PATH}!"
    exit 1
fi

echo "📁 Configuration: ${CONFIG_PATH}"
echo "📊 Traces will be written to: eval/otel-traces.jsonl"
echo "🌐 OTLP endpoint: http://localhost:4318"
echo ""
echo "ℹ️  Note: Run this script from the repository root directory"
echo ""

# Create eval directory (traces file will be created by otelcol-contrib)
mkdir -p eval

echo "▶️  Starting collector..."
echo "   Press Ctrl+C to stop"
echo ""

# Run the collector
"${BINARY_PATH}" --config="${CONFIG_PATH}"