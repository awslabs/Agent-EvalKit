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
#   --require-design        Require eval-design.md to exist (for implementation phase)
#   --require-tracing       Require tracing setup to be complete (for implementation phase)
#   --require-test-cases    Require test cases to be available (for implementation phase)
#   --require-test-scenarios Require test scenarios in design (for data generation phase)
#   --include-design        Include eval-design.md in AVAILABLE_DOCS list
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
REQUIRE_DESIGN=false
REQUIRE_TRACING=false
REQUIRE_TEST_CASES=false
REQUIRE_TEST_SCENARIOS=false
INCLUDE_DESIGN=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-design)
            REQUIRE_DESIGN=true
            ;;
        --require-tracing)
            REQUIRE_TRACING=true
            ;;
        --require-test-cases)
            REQUIRE_TEST_CASES=true
            ;;
        --require-test-scenarios)
            REQUIRE_TEST_SCENARIOS=true
            ;;
        --include-design)
            INCLUDE_DESIGN=true
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
  --require-design    Require eval-design.md to exist (for implementation phase)
  --include-design    Include eval-design.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check design prerequisites (eval-design.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (eval-design.md required)
  ./check-prerequisites.sh --json --require-design --include-design
  
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

# Get evaluation paths and validate branch
eval $(get_evaluation_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","EVALUATION_DIR":"%s","EVALUATION_SPEC":"%s","IMPL_PLAN":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$EVALUATION_DIR" "$EVALUATION_SPEC" "$IMPL_PLAN"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "EVALUATION_DIR: $EVALUATION_DIR"
        echo "EVALUATION_SPEC: $EVALUATION_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$EVALUATION_DIR" ]]; then
    echo "ERROR: Evaluation directory not found: $EVALUATION_DIR" >&2
    echo "Run /evalkit.design first to create the evaluation structure." >&2
    exit 1
fi

# Check for eval-design.md if required (for implementation phase)
if $REQUIRE_DESIGN && [[ ! -f "$EVALUATION_SPEC" ]]; then
    echo "ERROR: eval-design.md not found in $EVALUATION_DIR" >&2
    echo "Run /evalkit.design first to create the evaluation design." >&2
    exit 1
fi

# Check for tracing setup if required (for implementation phase)
if $REQUIRE_TRACING; then
    tracing_files_missing=()
    
    # Check for OTEL collector setup files
    [[ ! -f "$EVALUATION_DIR/setup_otelcol.sh" ]] && tracing_files_missing+=("setup_otelcol.sh")
    [[ ! -f "$EVALUATION_DIR/run_otelcol.sh" ]] && tracing_files_missing+=("run_otelcol.sh")
    [[ ! -f "$EVALUATION_DIR/otel-config.yaml" ]] && tracing_files_missing+=("otel-config.yaml")
    
    if [[ ${#tracing_files_missing[@]} -gt 0 ]]; then
        echo "ERROR: Tracing setup incomplete. Missing files in $EVALUATION_DIR:" >&2
        printf "  - %s\n" "${tracing_files_missing[@]}" >&2
        echo "Run /evalkit.trace first to set up tracing instrumentation." >&2
        exit 1
    fi
    
    # Check if OTEL collector binary exists
    if [[ ! -f "$EVALUATION_DIR/otelcol-contrib" ]]; then
        echo "ERROR: OTEL collector binary not found in $EVALUATION_DIR" >&2
        echo "Run ./setup_otelcol.sh in the evaluation directory to download the collector." >&2
        exit 1
    fi
fi

# Check for test cases if required (for implementation phase)
if $REQUIRE_TEST_CASES; then
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

# Check for test scenarios in design if required (for data generation phase)
if $REQUIRE_TEST_SCENARIOS; then
    if [[ ! -f "$EVALUATION_SPEC" ]]; then
        echo "ERROR: eval-design.md not found in $EVALUATION_DIR" >&2
        echo "Run /evalkit.design first to create the evaluation design." >&2
        exit 1
    fi
    
    # Check if design contains "Key Test Scenarios" section
        if ! grep -q "### Key Test Scenarios" "$EVALUATION_SPEC" 2>/dev/null; then
            echo "ERROR: eval-design.md missing 'Key Test Scenarios' section" >&2
            echo "Update eval-design.md to include test scenario specifications, or run /evalkit.design again." >&2
            exit 1
        fi
        
        # Check if test scenarios section has content (not just placeholders)
        scenarios_content=$(sed -n '/### Key Test Scenarios/,/###\|^$/p' "$EVALUATION_SPEC" | grep -v "^#" | grep -v "^<!--" | grep -v "^$" | wc -l)
        if [[ $scenarios_content -lt 3 ]]; then
            echo "ERROR: 'Key Test Scenarios' section appears to be empty or contains only placeholders" >&2
            echo "Please fill out the test scenarios in eval-design.md before running /evalkit.data." >&2
            exit 1
        fi
        
        # Check if design contains "Test Case Requirements" section
        if ! grep -q "### Test Case Requirements" "$EVALUATION_SPEC" 2>/dev/null; then
            echo "ERROR: eval-design.md missing 'Test Case Requirements' section" >&2
            echo "Update eval-design.md to include test case requirements, or run /evalkit.design again." >&2
            exit 1
        fi
fi

# Build list of available documents
docs=()

# Check results directory (only if it exists and has files)
if [[ -d "$RESULTS_DIR" ]] && [[ -n "$(ls -A "$RESULTS_DIR" 2>/dev/null)" ]]; then
    docs+=("results/")
fi

# Include eval-design.md if requested and it exists
if $INCLUDE_DESIGN && [[ -f "$EVALUATION_SPEC" ]]; then
    docs+=("eval-design.md")
fi

# Include tracing files if they exist
if [[ -f "$EVALUATION_DIR/otel-config.yaml" ]]; then
    docs+=("otel-config.yaml")
fi
if [[ -f "$EVALUATION_DIR/tracing-setup.md" ]]; then
    docs+=("tracing-setup.md")
fi

# Include test case files if they exist
if [[ -f "$EVALUATION_DIR/test-cases.jsonl" ]]; then
    docs+=("test-cases.jsonl")
fi
if [[ -f "$EVALUATION_DIR/test-cases-metadata.json" ]]; then
    docs+=("test-cases-metadata.json")
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
    
    if $INCLUDE_DESIGN; then
        check_file "$EVALUATION_SPEC" "eval-design.md"
    fi
    
    # Show tracing files status
    check_file "$EVALUATION_DIR/otel-config.yaml" "otel-config.yaml"
    check_file "$EVALUATION_DIR/tracing-setup.md" "tracing-setup.md"
    
    # Show test case files status
    check_file "$EVALUATION_DIR/test-cases.jsonl" "test-cases.jsonl"
    check_file "$EVALUATION_DIR/test-cases-metadata.json" "test-cases-metadata.json"
fi