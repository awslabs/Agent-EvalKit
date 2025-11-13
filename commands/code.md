---
description: Implement trace-based evaluation pipeline
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan --require-test-data-file
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.code` in the triggering message **is** additional context or specific implementation requirements. This command conducts the evaluation pipeline implementation.

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
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. If any error occurs, stop the process immediately and provide solving instructions for users.

3. Load the current evaluation plan (`eval/eval-plan.md`) to understand the task structure and requirements.

4. Follow this execution flow:

    1. Parse user context from user input (if provided)
    2. Review evaluation plan to understand requirements; update the evaluation plan if it does not align with the user's input (if provided); add entry to Appendix > User Input Tracker in eval-plan.md:
       - `/evalkit.code`: [User input from $ARGUMENTS, or "Not found"]
    3. Conduct evaluation pipeline implementation:
       **IMPORTANT**: Always navigate to repository root before any operation in the following process to avoid path errors.
       - **Set up environment**: Use `uv` to create virtual environment, activate it, and install `requirements.txt`
       - **Set up local OTEL collector**: Run `tracing/setup-otelcol.sh` and `tracing/run-otelcol.sh &` to ensure `eval/otel-traces.jsonl` is created
       - **Create test executor**: Create a script (e.g., `eval/test_executor.py`) to run instrumented agent on test cases (`eval/test-cases.jsonl`), then execute it (e.g., `python eval/test_executor.py --input eval/test-cases.jsonl`) to export raw OTEL traces into `eval/otel-traces.jsonl`
       - **Process raw OTEL traces**: Run `python tracing/trace-processor.py --input eval/otel-traces.jsonl --output-dir eval/traces/ --pretty` to process and simplify the raw OTEL traces
       - **Implement metrics** (critical step): Evaluation input will be the processed traces from `eval/traces/<traceId>.json` files. The script (e.g., `eval/metrics.py`) should include both metric classes and necessary extraction functions to extract evaluation-required information from processed traces. **MUST** examine processed trace structure by loading a trace file before implementing
       - **Build evaluation main entry function**: Create `eval/run_evaluation.py` to coordinate the pipeline. Ensure evaluation results are saved to `eval/results/`.
       - **Code review**: Identify and fix critical issues
       - **Update requirements and environment**: Add additional pipeline dependencies to `requirements.txt` and reinstall
       - **Create documentation**: Create `eval/README.md` with running instructions including OTEL collector setup, environment setup, pipeline execution, etc.
    4. Instruct user to follow `eval/README.md` to run evaluation

5. Terminate any running OTEL collector processes in the background

6. Report completion with implementation status and readiness for execution and the optional next phase (`/evalkit.report`) after execution.


## Implementation Guidelines

**CRITICAL: Always Create Minimal Working Version**: Implement the most basic version that works

### Context7 Validation

**MANDATORY**: Before implementing functionality from any publicly available evaluation library, validate its current API usage with Context7 MCP:

- "What's the current DeepEval LLMTestCase constructor signature and parameters?"
- "Show me the latest DeepEval BaseMetric implementation patterns"
- "What are the current built-in metrics available in DeepEval?"

This ensures production-ready code that follows current best practices and avoids deprecated patterns.

### Code Patterns/Examples
- If using DeepEval, please refer to `reference/deepeval/` for implementation patterns and examples.
- If using Strands Evals SDK, please refer to `reference/strands/` for implementation patterns and examples.


## Environment Setup Guidelines

### Update Existing Requirements

1. **Check Existing Requirements**: Verify requirements.txt exists in repository root
   ```bash
   # Check if requirements.txt exists
   ls requirements.txt
   ```

2. **Add Evaluation Dependencies**: Update requirements.txt with additional evaluation pipeline dependencies, for example
   ```bash
   # Add evaluation framework dependencies (if not already present)
   echo "boto3>=1.35.0" >> requirements.txt
   echo "litellm>=1.0.0" >> requirements.txt
   echo "deepeval>=0.21.0" >> requirements.txt
   # Add other dependencies as needed based on evaluation plan
   ```

3. **Installation**: Use `uv` for dependency management
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```


## Common Pitfalls to Avoid

- **Over-Engineering**: Don't add complexity before the basic version works
- **Ignoring Reference Implementation**: Always use specified reference during development
- **Ignoring the Plan**: Follow the established evaluation plan structure and requirements