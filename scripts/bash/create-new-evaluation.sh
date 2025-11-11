#!/usr/bin/env bash

set -e

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json]"; exit 0 ;;
        *) echo "Error: Unknown argument '$arg'. Use --help for usage information." >&2; exit 1 ;;
    esac
done

# Function to find the repository root by searching for existing project markers
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.evalkit" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

EVAL_DIR="$REPO_ROOT/eval"

# Clean up existing eval directory to ensure fresh start
if [ -d "$EVAL_DIR" ]; then
    rm -rf "$EVAL_DIR"
fi

mkdir -p "$EVAL_DIR"

# Find the highest evaluation number from existing git branches
HIGHEST=0
if [ "$HAS_GIT" = true ]; then
    # Get all branch names and extract numbers from evaluation branches
    for branch in $(git branch -a | sed 's/^[* ] //' | sed 's/remotes\/origin\///' | sort -u); do
        # Extract number from branch names like "001-city-agent", "002-weather-app", etc.
        number=$(echo "$branch" | grep -o '^[0-9]\+' || echo "0")
        if [[ "$number" =~ ^[0-9]+$ ]]; then
            number=$((10#$number))
            if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
        fi
    done
fi

NEXT=$((HIGHEST + 1))
EVALUATION_NUM=$(printf "%03d" "$NEXT")

# Use fixed professional naming: 001-eval-pipeline, 002-eval-pipeline, etc.
BRANCH_NAME="${EVALUATION_NUM}-eval-pipeline"

if [ "$HAS_GIT" = true ]; then
    git checkout -b "$BRANCH_NAME"
else
    >&2 echo "[evalkit] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

# Use flat structure - files go directly in eval/ directory
TEMPLATE="$REPO_ROOT/.evalkit/templates/eval-plan-template.md"
PLAN_FILE="$EVAL_DIR/eval-plan.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$PLAN_FILE"; else touch "$PLAN_FILE"; fi

# Set the EVALKIT_FEATURE environment variable for the current session
export EVALKIT_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","PLAN_FILE":"%s","EVALUATION_NUM":"%s"}\n' "$BRANCH_NAME" "$PLAN_FILE" "$EVALUATION_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "PLAN_FILE: $PLAN_FILE"
    echo "EVALUATION_NUM: $EVALUATION_NUM"
    echo "EVALKIT_FEATURE environment variable set to: $BRANCH_NAME"
fi
