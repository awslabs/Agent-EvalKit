#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --help|-h) 
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0 
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_evaluation_paths)

# Check if we're on a proper evaluation branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure the evaluation directory exists
mkdir -p "$EVALUATION_DIR"

# Copy plan template if it exists
TEMPLATE="$REPO_ROOT/.evalkit/templates/plan-template.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$IMPL_PLAN"
    echo "Copied plan template to $IMPL_PLAN"
else
    echo "Warning: Plan template not found at $TEMPLATE"
    # Create a basic plan file if template doesn't exist
    touch "$IMPL_PLAN"
fi

# Output results
if $JSON_MODE; then
    printf '{"EVALUATION_SPEC":"%s","IMPL_PLAN":"%s","EVALS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
        "$EVALUATION_SPEC" "$IMPL_PLAN" "$EVALUATION_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
    echo "EVALUATION_SPEC: $EVALUATION_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "EVALS_DIR: $EVALUATION_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
