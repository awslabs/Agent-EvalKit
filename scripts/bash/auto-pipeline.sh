#!/usr/bin/env bash

# Auto Pipeline Script for Agent EvalKit
# Runs the complete evaluation pipeline automatically using Claude CLI
# Usage: ./auto-pipeline.sh "your evaluation goal"

set -euo pipefail

GOAL="$1"

echo "Starting Agent EvalKit Auto Pipeline..."
echo "Goal: $GOAL"

claude -p "/evalkit.plan \"$GOAL\"" --output-format json --permission-mode acceptEdits
claude -p "/evalkit.data"           --output-format json --permission-mode acceptEdits
claude -p "/evalkit.trace"          --output-format json --permission-mode acceptEdits
claude -p "/evalkit.run_agent"      --output-format json --permission-mode acceptEdits
claude -p "/evalkit.eval"           --output-format json --permission-mode acceptEdits
claude -p "/evalkit.report"         --output-format json --permission-mode acceptEdits

echo "Pipeline complete!"
