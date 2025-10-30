#!/bin/bash

# OpenTelemetry Collector Runner Script
# Starts the otelcol-contrib binary with local configuration

echo "🚀 Starting OpenTelemetry Collector"
echo "============================================="

# Check if binary exists
if [ ! -f "./otelcol-contrib" ]; then
    echo "❌ otelcol-contrib binary not found!"
    echo "   Run ./setup_otelcol.sh first to download the binary"
    exit 1
fi

# Check if config exists
if [ ! -f "./otel-config.yaml" ]; then
    echo "❌ otel-config.yaml not found!"
    exit 1
fi

echo "📁 Configuration: ./otel-config.yaml"
echo "📊 Traces will be written to: ./otel-traces.jsonl"
echo "🌐 OTLP endpoint: http://localhost:4318"
echo ""

# Create traces file if it doesn't exist
touch ./otel-traces.jsonl

echo "▶️  Starting collector..."
echo "   Press Ctrl+C to stop"
echo ""

# Run the collector
./otelcol-contrib --config=./otel-config.yaml