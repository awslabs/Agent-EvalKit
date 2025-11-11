---
description: Set up tracing instrumentation for target agent
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan --require-test-data-file
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.trace` in the triggering message **is** additional context or specific tracing requirements. This command sets up tracing instrumentation for the target agent based on the evaluation plan, creates scripts to run the instrumented agent on test cases to collect raw traces, and processes and simplifies the raw traces.

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

3. Load the current evaluation plan (`eval/eval-plan.md`) to understand tracing requirements and agent architecture.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Validate evaluation plan exists and `eval/test-cases.jsonl` exists
    3. Copy pre-built tracing artifacts to `eval/tracing/`
    4. Analyze agent code for supported frameworks and existing instrumentation
    5. Add minimal tracing instrumentation (only if needed)
    6. Create `eval/test_executor.py` for orchestrated test execution
    7. Set up OTEL collector and environment
    8. Run `eval/test_executor.py` on test cases to collect raw traces
    9. Run `eval/tracing/trace-processor.py` to simplify raw traces


## Technical Guidelines

### Pre-built Tracing Artifacts

Copy tracing infrastructure to evaluation workspace:

```bash
# Create tracing subdirectory
mkdir -p eval/tracing

# Copy OTEL templates from templates/tracing/
cp templates/tracing/setup-otelcol.sh eval/tracing/setup-otelcol.sh
cp templates/tracing/run-otelcol.sh eval/tracing/run-otelcol.sh
cp templates/tracing/otel-config.yaml eval/tracing/otel-config.yaml
cp templates/tracing/trace-processor.py eval/tracing/trace-processor.py

# Make scripts executable
chmod +x eval/tracing/setup-otelcol.sh
chmod +x eval/tracing/run-otelcol.sh
```

### Intelligent Instrumentation Detection

Analyze agent code for supported frameworks that provide automatic tracing via OpenLLMetry by Traceloop:

**LLM Foundation Models**:
- Azure OpenAI, Aleph Alpha, Anthropic, Amazon Bedrock, Amazon SageMaker
- Cohere, IBM watsonx, Google Gemini, Google VertexAI, Groq
- Mistral AI, Ollama, OpenAI, Replicate, together.ai
- HuggingFace Transformers, WRITER

**Vector Databases**:
- Chroma DB, Elasticsearch, LanceDB, Marqo, Milvus
- pgvector, Pinecone, Qdrant, Weaviate

**Frameworks**:
- Burr, CrewAI, Haystack by deepset, Langchain, LlamaIndex, OpenAI Agents

**Instrumentation Strategy**:
- **Supported frameworks** → Auto-instrumentation with minimal initialization:
  ```python
  from traceloop.sdk import Traceloop
  
  Traceloop.init(
      app_name="{agent-name}",
      disable_batch=True,
      api_endpoint="http://localhost:4318"
  )
  ```
- **Custom/unsupported code** → Add minimal Traceloop decorators

### Minimal Agent Instrumentation (If Needed)

For custom/unsupported code that requires manual instrumentation, add minimal decorators:

```python
# Import decorators for custom instrumentation
from traceloop.sdk.decorators import workflow, task, agent, tool

# Add minimal decorators only where needed
@workflow
def main_agent_workflow():
    """Main agent execution boundary"""
    pass

@task
def reasoning_step():
    """Individual reasoning/planning step"""
    pass

@agent
def main_agent():
    """Main agent instance"""
    pass

@tool
def custom_tool_usage():
    """Custom tool not auto-instrumented"""
    pass
```

**Note**: The `Traceloop.init()` initialization is still required regardless of instrumentation approach.

### Test Executor Implementation

Create `eval/test_executor.py` for orchestrated test execution:

```python
# Template for test_executor.py
import json
import os

def load_test_cases():
    """Load test cases from test-cases.jsonl"""
    with open('test-cases.jsonl', 'r') as f:
        return [json.loads(line) for line in f]

def execute_agent_on_test_case(test_case):
    """Execute instrumented agent on single test case"""
    # Import and run your instrumented agent here
    # The agent code should have Traceloop.init() and instrumentation
    # Return results
    pass

def main():
    test_cases = load_test_cases()
    for i, test_case in enumerate(test_cases):
        print(f"Executing test case {i+1}/{len(test_cases)}")
        result = execute_agent_on_test_case(test_case)
        # Results are automatically traced via OTEL

if __name__ == "__main__":
    main()
```

###  Set Up Environment

1. **Detect Existing Dependencies**: Check for existing dependency files in agent directory and repository root
   ```bash
   # Check for existing dependency files (in order of priority)
   find . -name "requirements.txt" -o -name "pyproject.toml" -o -name "setup.py" -o -name "Pipfile" -o -name "environment.yml"
   ```

2. **Consolidate Requirements**: Create unified `requirements.txt` at repository root
   ```bash
   # Merge agent dependencies with trace instrumentation dependencies
   # Include agent's existing requirements if found
   # Add trace instrumentation dependencies
   ```

3. **Create Virtual Environment**: Use `uv` to create `.venv` at repository root
   ```bash
   # Create virtual environment at repository root (not in eval/ directory)
   uv venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or .venv\Scripts\activate  # Windows
   ```

4. **Install Dependencies**: Use `uv pip install` for consistent dependency resolution
   ```bash
   uv pip install -r requirements.txt
   ```

#### Dependency Detection Priority

Check for existing dependency files in this order:
- `requirements.txt` (standard Python)
- `pyproject.toml` (modern Python projects)
- `setup.py` (legacy Python packages)
- `Pipfile` (pipenv projects)
- `environment.yml` (conda environments)

### OTEL Collector Setup & Execution

1. **Setup and Start Collector**:
   ```bash
   cd eval/tracing
   ./setup-otelcol.sh
   ./run-otelcol.sh &
   ```

2. **Execute Test Cases**:
   ```bash
   # Run instrumented agent on test cases
   python test_executor.py
   ```

3. **Process Raw Traces**:
   ```bash
   # Convert raw OTEL traces to evaluation-ready format
   python tracing/trace-processor.py
   ```

This creates:
- `eval/tracing/otel-traces.jsonl` (raw traces)
- `eval/traces/<traceId>.json` (processed individual traces)

## Instrumentation Guidelines

### Code Integration Principles

- **Evaluation-Focused**: Instrument specifically for agent evaluation analysis, not general monitoring
- **Meaningful Naming**: Use descriptive span names that facilitate evaluation insights
- **Minimal Invasiveness**: Add tracing with minimal changes to existing agent code
- **Graceful Degradation**: Agent should work even if tracing fails
- **Local-First**: Use local OTEL collector, avoid external dependencies

Report completion with tracing status, instrumentation details, trace collection results, and readiness for core evaluation implementation (`/evalkit.code`).

