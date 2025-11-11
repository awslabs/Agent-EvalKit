---
description: Generate test cases for evaluation
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan --require-test-data-section
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.data` in the triggering message **is** additional context or specific test case requirements. This command generates comprehensive test cases based on the evaluation design and test scenarios.

Given that context, do this:

1. **Navigate to repository root**:
   
   First, find the repository root using git (preferred) or by locating the script:
   ```
   REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
   ```
   
   If that fails (not in a git repo), find the script and go up two directories:
   ```
   SCRIPT_PATH=$(find . -name "check-prerequisites.sh" | head -1)
   REPO_ROOT=$(cd "$(dirname "$SCRIPT_PATH")/../.." && pwd)
   ```
   
   Then change to the repository root:
   ```
   cd "$REPO_ROOT"
   ```

2. Run the script `{SCRIPT}` and parse its JSON output for BRANCH_NAME and PLAN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

3. Load the current evaluation plan (`eval/eval-plan.md`) to understand evaluation areas and test data generation requirements.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Validate evaluation plan exists and contains "Test Data Generation" section
    3. Generate proper test cases covering all scenarios and meeting all requirements
    4. Structure test cases in JSONL format
    5. Save test cases to `eval/test-cases.jsonl`


Report completion with test case count, coverage summary, and readiness for trace setup and collection (`/evalkit.trace`).