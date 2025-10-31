---
description: Set up tracing instrumentation for target agent
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-design --include-design 
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.trace` in the triggering message **is** additional context or specific tracing requirements. This command sets up tracing instrumentation for the target agent based on the evaluation design.

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

2. Run the script `{SCRIPT}` and parse its JSON output for BRANCH_NAME and DESIGN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

3. Load the current evaluation design (`eval/eval-design.md`) to understand tracing requirements and agent architecture.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Validate evaluation design exists and contains tracing requirements
    3. Analyze current agent instrumentation status
    4. Determine tracing strategy based on agent architecture and requirements
    5. Copy and configure OTEL templates to workspace
    6. Instrument target agent with selected tracing library
    7. Test tracing setup and validate trace collection

## Tracing Implementation Process

### Prerequisites Validation

Before proceeding, ensure:
- `eval/eval-design.md` exists and contains agent analysis
- Agent source code is accessible
- Tracing requirements are specified in the design

### Tracing Strategy Selection

Based on the evaluation design, determine the appropriate tracing approach:

#### Default: Traceloop Integration
For most Python agents, use Traceloop for lightweight instrumentation:

```python
# Traceloop imports
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, task, agent

# Initialize Traceloop for evaluation-focused tracing (local only)
Traceloop.init(
    app_name="{agent-name}-eval-tracing",
    disable_batch=True,
    api_endpoint="http://localhost:4318"
)
print("Traceloop initialized for agent evaluation tracing")

# Add evaluation-focused decorators to your agent
@workflow
def agent_main_execution():
    """Main agent workflow for evaluation boundary tracking"""
    # your agent code
    pass

@task
def agent_planning_phase():
    """Individual reasoning step for granular analysis"""
    # processing logic
    pass

@agent
def agent_decision_point():
    """Agent decision point for performance measurement"""
    # response generation
    pass
```

### OTEL Collector Setup

**Note**: Tracing templates are automatically copied by the design command when agent code is detected.

1. **Setup Collector Binary**:
   ```bash
   cd eval/tracing
   ./setup_otelcol.sh
   ```

2. **Test Collector**:
   ```bash
   # Start collector in background
   ./run_otelcol.sh &
   
   # Verify collector is running
   ps aux | grep otelcol
   ```

## Implementation Guidelines

### Code Integration Principles

- **Evaluation-Focused**: Instrument specifically for agent evaluation analysis, not general monitoring
- **Meaningful Naming**: Use descriptive span names that facilitate evaluation insights
- **Minimal Invasiveness**: Add tracing with minimal changes to existing agent code
- **Graceful Degradation**: Agent should work even if tracing fails
- **Performance Awareness**: Monitor and minimize tracing overhead
- **Local-First**: Use local OTEL collector, avoid external dependencies

Report completion with tracing status, instrumentation details, and readiness for test case generation (`/evalkit.data`) or implementation (`/evalkit.implement`).

