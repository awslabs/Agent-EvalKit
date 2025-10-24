#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Agent Evaluation workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-plan      Require plan.md to exist (for implementation phase)
#   --include-plan      Include plan.md in AVAILABLE_DOCS list
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"EVALUATION_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: EVALUATION_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n EVALUATION_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_PLAN=false
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
  --require-plan      Require plan.md to exist (for implementation phase)
  --include-plan      Include plan.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check design prerequisites (eval-design.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (plan.md required)
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

# Check for plan.md if required (for implementation phase)
if $REQUIRE_PLAN && [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $EVALUATION_DIR" >&2
    echo "Run /evalkit.plan first to create the implementation plan." >&2
    exit 1
fi

# Build list of available documents
docs=()

# Check results directory (only if it exists and has files)
if [[ -d "$RESULTS_DIR" ]] && [[ -n "$(ls -A "$RESULTS_DIR" 2>/dev/null)" ]]; then
    docs+=("results/")
fi

# Include plan.md if requested and it exists
if $INCLUDE_PLAN && [[ -f "$IMPL_PLAN" ]]; then
    docs+=("plan.md")
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
    
    if $INCLUDE_PLAN; then
        check_file "$IMPL_PLAN" "plan.md"
    fi
fi