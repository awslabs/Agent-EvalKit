---
description: Run instrumented agent and collect traces
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan --require-test-data-file
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.run_agent` in the triggering message **is** additional context or specific execution requirements. This command runs the instrumented agent and collects traces.

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
    2. Review evaluation plan to understand requirements; update the evaluation plan if it does not align with the user's input (if provided); add entry to User Requirements Log in eval-plan.md
    3. Execute trace generation and processing pipeline:
       **IMPORTANT**: Always navigate to repository root before any operation in the following process to avoid path errors.
       - **Create requirements.txt**: Detect existing dependencies and consolidate into unified `requirements.txt` at repository root
       - **Set up environment**: Use `uv` to create virtual environment, activate it, and install `requirements.txt`
       - **Clean up existing OTEL collectors**: Use `pkill -f otelcol-contrib` to terminate any running OTEL collector processes before starting new ones
       - **Set up local OTEL collector**: Run `tracing/setup-otelcol.sh` and `tracing/run-otelcol.sh &` to ensure `eval/otel-traces.jsonl` is created
       - **Create agent runner**: Create a script (e.g., `eval/agent_runner.py`) to run instrumented agent on test cases (`eval/test-cases.jsonl`), then execute it (e.g., `python eval/agent_runner.py --input eval/test-cases.jsonl`) to ensure it exports raw OTEL traces directly to `eval/otel-traces.jsonl` (do not allow custom output paths)
       - **Process raw OTEL traces**: Run `python tracing/trace-processor.py --input eval/otel-traces.jsonl --output-dir eval/traces/ --pretty` to process and simplify the raw OTEL traces
       - **Terminate OTEL collector**: Stop any running OTEL collector processes in the background
    4. Confirm `eval/traces/` directory exists and contains processed trace files
    5. Update Evaluation Progress section in eval-plan.md with completion status

5. Report completion with trace generation status and readiness for the next phase (`/evalkit.eval`) for evaluation implementation.

## Implementation Guidelines

**CRITICAL: Always Create Minimal Working Version**: Implement the most basic version that works

### Environment Setup Guidelines

#### Update Existing Requirements

1. **Check Existing Requirements**: Verify requirements.txt exists in repository root
   ```bash
   # Check if requirements.txt exists
   ls requirements.txt
   ```

2. **Create Unified Requirements**: Detect existing dependencies and consolidate into unified `requirements.txt`
   ```bash
   # Check for existing dependency files (in order of priority)
   find . -name "requirements.txt" -o -name "pyproject.toml" -o -name "setup.py" -o -name "Pipfile" -o -name "environment.yml"
   
   # Merge agent dependencies with trace instrumentation and execution dependencies
   # Include agent's existing requirements if found
   # Add trace instrumentation dependencies:
   echo "traceloop-sdk>=0.0.75" >> requirements.txt
   echo "opentelemetry-api>=1.20.0" >> requirements.txt
   echo "opentelemetry-sdk>=1.20.0" >> requirements.txt
   echo "opentelemetry-exporter-otlp>=1.20.0" >> requirements.txt
   echo "opentelemetry-instrumentation>=0.41b0" >> requirements.txt
   # Add other dependencies as needed based on evaluation plan
   ```

#### Dependency Detection Priority

Check for existing dependency files in this order:
- `requirements.txt` (standard Python)
- `pyproject.toml` (modern Python projects)
- `setup.py` (legacy Python packages)
- `Pipfile` (pipenv projects)
- `environment.yml` (conda environments)

3. **Installation**: Use `uv` for dependency management
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```


## Common Pitfalls to Avoid

- **Forgetting to terminate OTEL collector**: Always stop background processes
- **Not verifying trace output**: Confirm traces are actually generated before proceeding
- **Ignoring test case failures**: Handle individual failures without stopping the entire pipeline
- **Over-Engineering**: Don't add complexity before the basic version works
- **Ignoring the Plan**: Follow the established evaluation plan structure and requirements