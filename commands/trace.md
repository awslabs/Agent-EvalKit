---
description: Set up tracing instrumentation 
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.trace` in the triggering message **is** additional context or specific tracing requirements. This command sets up tracing instrumentation for the target agent based on the evaluation plan.

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

3. Load the current evaluation plan (`eval/eval-plan.md`) to understand tracing requirements and agent architecture.

4. Follow this execution flow:

    1. Parse user context from user input (if provided)
    2. Review the evaluation plan to understand requirements; update the evaluation plan if it does not align with the user's input (if provided); add entry to Appendix > User Input Tracker in eval-plan.md:
       - `/evalkit.trace`: [User input from $ARGUMENTS, or "Not found"]
    3. Analyze agent code for supported frameworks and existing instrumentation
    4. Add minimal tracing instrumentation to the original agent code (if needed)
    5. Create `requirements.txt` in repository root

5. Report completion with tracing status, instrumentation details, requirements.txt creation, and readiness for evaluation pipeline implementation (`/evalkit.code`).


## Technical Guidelines

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

**Note**: The `Traceloop.init()` initialization is still required regardless of instrumentation approach. Does instrumention by directly modifying the original agent code (do not create new agent files).

### Strands Framework
If the agent is built on the Strands framework, note that **Strands is not supported by Traceloop's auto-instrumentation**. For Strands-based agents, you must implement custom instrumentation using separate approaches. Please check the Strands-specific instrumentation reference in `reference/strands` for detailed implementation guidance.

###  Create requirements.txt

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

#### Dependency Detection Priority

Check for existing dependency files in this order:
- `requirements.txt` (standard Python)
- `pyproject.toml` (modern Python projects)
- `setup.py` (legacy Python packages)
- `Pipfile` (pipenv projects)
- `environment.yml` (conda environments)


## Instrumentation Guidelines

### Code Integration Principles

- **Evaluation-Focused**: Instrument specifically for agent evaluation analysis, not general monitoring
- **Meaningful Naming**: Use descriptive span names that facilitate evaluation insights
- **Minimal Invasiveness**: Add tracing with minimal changes to existing agent code