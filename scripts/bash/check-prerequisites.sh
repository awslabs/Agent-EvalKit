#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Agent Evaluation workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json                  Output in JSON format
#   --require-plan          Require eval-plan.md to exist
#   --require-tracing       Require tracing setup to be complete
#   --require-test-data-file Require test data file to be available
#   --require-processed-traces Require processed traces directory to exist and not be empty
#   --require-results       Require results directory to exist and not be empty
#   --include-plan          Include eval-plan.md in AVAILABLE_DOCS list
#   --paths-only            Only output path variables (no validation)
#   --help, -h              Show help message
#
# OUTPUTS:
#   JSON mode: {"EVALUATION_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: EVALUATION_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n EVALUATION_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_PLAN=false
REQUIRE_TEST_DATA_FILE=false
REQUIRE_TRACING=false
REQUIRE_PROCESSED_TRACES=false
REQUIRE_RESULTS=false
INCLUDE_PLAN=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-plan)
            REQUIRE_PLAN=true
            ;;
        --require-test-data-file)
            REQUIRE_TEST_DATA_FILE=true
            ;;
        --require-tracing)
            REQUIRE_TRACING=true
            ;;
        --require-processed-traces)
            REQUIRE_PROCESSED_TRACES=true
            ;;
        --require-results)
            REQUIRE_RESULTS=true
            ;;
        --include-plan)
            INCLUDE_PLAN=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for Agent Evaluation workflow.

OPTIONS:
  --json              Output in JSON format
  --require-plan      Require eval-plan.md to exist
  --require-test-data-file Require test data file to be available
  --require-processed-traces Require processed traces directory to exist and not be empty
  --require-results   Require results directory to exist and not be empty
  --include-plan      Include eval-plan.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check plan prerequisites (eval-plan.md required)
  ./check-prerequisites.sh --json --require-plan
  
  # Check implementation prerequisites (eval-plan.md required)
  ./check-prerequisites.sh --json --require-plan --include-plan
  
  # Get evaluation paths only (no validation)
  ./check-prerequisites.sh --paths-only
  
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Ensure we're running from repository root
ensure_repo_root

# Get evaluation paths and validate branch
eval $(get_evaluation_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","EVALUATION_DIR":"%s","EVALUATION_PLAN":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$EVALUATION_DIR" "$EVALUATION_DIR/eval-plan.md"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "EVALUATION_DIR: $EVALUATION_DIR"
        echo "EVALUATION_PLAN: $EVALUATION_DIR/eval-plan.md"
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$EVALUATION_DIR" ]]; then
    echo "ERROR: Evaluation directory not found: $EVALUATION_DIR" >&2
    echo "Run /evalkit.plan first to create the evaluation structure." >&2
    exit 1
fi

# Check for eval-plan.md if required
if $REQUIRE_PLAN && [[ ! -f "$EVALUATION_DIR/eval-plan.md" ]]; then
    echo "ERROR: eval-plan.md not found in $EVALUATION_DIR" >&2
    echo "Run /evalkit.plan first to create the evaluation plan." >&2
    exit 1
fi

# Check for test data file if required
if $REQUIRE_TEST_DATA_FILE; then
    if [[ ! -f "$EVALUATION_DIR/test-cases.jsonl" ]]; then
        echo "ERROR: Test cases not found: $EVALUATION_DIR/test-cases.jsonl" >&2
        echo "Run /evalkit.data first to generate test cases." >&2
        exit 1
    fi
    
    # Validate test cases file is not empty
    if [[ ! -s "$EVALUATION_DIR/test-cases.jsonl" ]]; then
        echo "ERROR: Test cases file is empty: $EVALUATION_DIR/test-cases.jsonl" >&2
        echo "Run /evalkit.data to regenerate test cases." >&2
        exit 1
    fi
fi


# Check for tracing setup if required (for implementation phase)
if $REQUIRE_TRACING; then
    tracing_files_missing=()
    
    # Check for OTEL collector setup files in tracing subdirectory
    [[ ! -f "$EVALUATION_DIR/tracing/setup_otelcol.sh" ]] && tracing_files_missing+=("tracing/setup_otelcol.sh")
    [[ ! -f "$EVALUATION_DIR/tracing/run_otelcol.sh" ]] && tracing_files_missing+=("tracing/run_otelcol.sh")
    [[ ! -f "$EVALUATION_DIR/tracing/otel-config.yaml" ]] && tracing_files_missing+=("tracing/otel-config.yaml")
    
    if [[ ${#tracing_files_missing[@]} -gt 0 ]]; then
        echo "ERROR: Tracing setup incomplete. Missing files in $EVALUATION_DIR:" >&2
        printf "  - %s\n" "${tracing_files_missing[@]}" >&2
        echo "Run /evalkit.trace first to set up tracing instrumentation." >&2
        exit 1
    fi
    
    # Check if OTEL collector binary exists
    if [[ ! -f "$EVALUATION_DIR/tracing/otelcol-contrib" ]]; then
        echo "ERROR: OTEL collector binary not found in $EVALUATION_DIR/tracing/" >&2
        echo "Run ./tracing/setup_otelcol.sh in the evaluation directory to download the collector." >&2
        exit 1
    fi
fi

# Check for processed traces if required
if $REQUIRE_PROCESSED_TRACES; then
    if [[ ! -d "$EVALUATION_DIR/traces" ]]; then
        echo "ERROR: Processed traces directory not found: $EVALUATION_DIR/traces" >&2
        echo "Run /evalkit.trace first to generate and process traces." >&2
        exit 1
    fi
    
    # Check if traces directory is not empty
    if [[ -z "$(ls -A "$EVALUATION_DIR/traces" 2>/dev/null)" ]]; then
        echo "ERROR: Processed traces directory is empty: $EVALUATION_DIR/traces" >&2
        echo "Run /evalkit.trace to generate traces, then process them before running /evalkit.code." >&2
        exit 1
    fi
fi

# Check for results directory if required
if $REQUIRE_RESULTS; then
    if [[ ! -d "$RESULTS_DIR" ]]; then
        echo "ERROR: Results directory not found: $RESULTS_DIR" >&2
        echo "Run /evalkit.code first to execute evaluations and generate results." >&2
        exit 1
    fi
    
    # Check if results directory is not empty
    if [[ -z "$(ls -A "$RESULTS_DIR" 2>/dev/null)" ]]; then
        echo "ERROR: Results directory is empty: $RESULTS_DIR" >&2
        echo "Run /evalkit.code to execute evaluations before running /evalkit.report." >&2
        exit 1
    fi
fi


# Build list of available documents
docs=()

# Check results directory (only if it exists and has files)
if [[ -d "$RESULTS_DIR" ]] && [[ -n "$(ls -A "$RESULTS_DIR" 2>/dev/null)" ]]; then
    docs+=("results/")
fi

# Include eval-plan.md if it exists (automatic inclusion)
if [[ -f "$EVALUATION_DIR/eval-plan.md" ]]; then
    docs+=("eval-plan.md")
fi

# Include tracing files if they exist
if [[ -f "$EVALUATION_DIR/tracing/otel-config.yaml" ]]; then
    docs+=("tracing/otel-config.yaml")
fi
if [[ -f "$EVALUATION_DIR/tracing/otel-traces.jsonl" ]]; then
    docs+=("tracing/otel-traces.jsonl")
fi

# Include test case files if they exist
if [[ -f "$EVALUATION_DIR/test-cases.jsonl" ]]; then
    docs+=("test-cases.jsonl")
fi

# Include processed traces if they exist
if [[ -d "$EVALUATION_DIR/traces" ]] && [[ -n "$(ls -A "$EVALUATION_DIR/traces" 2>/dev/null)" ]]; then
    docs+=("traces/")
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of documents
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi
    
    printf '{"EVALUATION_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$EVALUATION_DIR" "$json_docs"
else
    # Text output
    echo "EVALUATION_DIR:$EVALUATION_DIR"
    echo "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    check_dir "$RESULTS_DIR" "results/"
    
    # Always show eval-plan.md status (automatic inclusion)
    check_file "$EVALUATION_DIR/eval-plan.md" "eval-plan.md"
    
    # Show tracing files status
    check_file "$EVALUATION_DIR/tracing/otel-config.yaml" "tracing/otel-config.yaml"
    check_file "$EVALUATION_DIR/tracing/otel-traces.jsonl" "tracing/otel-traces.jsonl"
    
    # Show test case files status
    check_file "$EVALUATION_DIR/test-cases.jsonl" "test-cases.jsonl"
    
    # Show processed traces status
    check_dir "$EVALUATION_DIR/traces" "traces/"
fi