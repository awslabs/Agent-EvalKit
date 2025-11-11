#!/usr/bin/env bash
# Common functions and variables for all scripts

# Ensure script runs from repository root directory
ensure_repo_root() {
    local repo_root=$(get_repo_root)
    if [[ "$(pwd)" != "$repo_root" ]]; then
        echo "[evalkit] Changing to repository root: $repo_root" >&2
        cd "$repo_root" || {
            echo "ERROR: Failed to change to repository root: $repo_root" >&2
            exit 1
        }
    fi
}

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if EVALKIT_FEATURE environment variable is set
    if [[ -n "${EVALKIT_FEATURE:-}" ]]; then
        echo "$EVALKIT_FEATURE"
        return
    fi
    
    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi
    
    # For non-git repos, we can't determine the branch name
    # Since we now use git branches for organization, fall back to a default
    
    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[evalkit] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi
    
    if [[ ! "$branch" =~ ^[0-9]{3}-eval-pipeline$ ]]; then
        echo "ERROR: Not on an evaluation branch. Current branch: $branch" >&2
        echo "Evaluation branches should be named like: 001-eval-pipeline" >&2
        return 1
    fi
    
    return 0
}

get_evaluation_dir() { echo "$1/eval"; }

get_evaluation_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"
    
    if has_git; then
        has_git_repo="true"
    fi
    
    local evaluation_dir=$(get_evaluation_dir "$repo_root")
    
    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
EVALUATION_DIR='$evaluation_dir'
EVALUATION_PLAN='$evaluation_dir/eval-plan.md'
RESULTS_DIR='$evaluation_dir/results'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
