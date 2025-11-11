---
description: Analyze your agent and design evaluation strategy
scripts:
  sh: scripts/bash/create-new-evaluation.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.plan` in the triggering message **is** the user evaluation requests or agent description. Assume you always have it available in this conversation even if it appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that user evaluation requests or agent description, do this:

1. **Navigate to repository root**:
   
   First, find the repository root using git (preferred) or by locating the script:
   ```
   REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
   ```
   
   If that fails (not in a git repo), find the script and go up two directories:
   ```
   SCRIPT_PATH=$(find . -name "create-new-evaluation.sh" | head -1)
   REPO_ROOT=$(cd "$(dirname "$SCRIPT_PATH")/../.." && pwd)
   ```
   
   Then change to the repository root:
   ```
   cd "$REPO_ROOT"
   ```

2. Run the script `{SCRIPT}` and parse its JSON output for BRANCH_NAME and PLAN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. For single quotes in args like "I'm analyzing", use escape syntax: e.g 'I'\''m analyzing' (or double-quote if possible: "I'm analyzing").

3. Load `templates/eval-plan-template.md` to understand required sections for evaluation plan.

4. Follow this execution flow:

    1. Parse user evaluation requests from input
       If empty: ERROR "No agent description or evaluation requests provided"
    2. Analyze agent and user requirements:
       - Parse specific evaluation requests, scenarios, and constraints from user input
       - Scan codebase for agent architecture and capabilities
       - Detect tracing instrumentation patterns (Traceloop, OpenTelemetry, etc.)
       - Check for existing test cases and trace files
    3. Design evaluation strategy:
       - Define evaluation areas and metrics (user-request-driven with agent-aware defaults)
       - Identify test scenarios and data requirements
       - Select technology stack and integration approach
    4. Create implementation plan:
       - Design evaluation pipeline architecture
       - Define file structure and implementation tasks
       - Choose configuration and execution approach
    5. Return: SUCCESS (evaluation plan ready for implementation)

5. Write the complete evaluation plan to PLAN_FILE (eval-plan.md) using the template structure, replacing placeholders with concrete details derived from the analysis while preserving section order and headings.

6. Report completion with branch name, evaluation plan file path, and readiness for following data generation (`/evalkit.data` if needed), trace setup and collection `/evalkit.trace`, and core evaluation implementation (`/evalkit.code`).


## General Guidelines

### Decision Guidelines

When creating evaluation plans from a user prompt:

1. **Prioritize user evaluation requests**: User input takes precedence over detected agent state - always honor specific user requirements and constraints
2. **Provide intelligent defaults**: When user input is minimal, use agent state analysis to suggest appropriate modules and implementation strategy
3. **Make informed guesses**: Use context, agent type patterns, and evaluation best practices to fill remaining gaps
4. **Enable design iteration**: Always include guidance for refining evaluation requests when defaults don't match user needs
5. **Think like an evaluator and architect**: Every requirement should be measurable and every technology choice should have clear rationale
6. **Make informed decisions**: Use context, agent type patterns, and evaluation best practices to make reasonable decisions without requiring user clarification

## Evaluation Planning Guidelines

### Design Principles

**High-Level Design (What & Why)**:
- Focus on **WHAT** to evaluate and **WHY** it matters for the agent
- Define evaluation areas and metrics that are measurable and verifiable
- Ensure requirements can be tested through actual agent execution

**Low-Level Implementation (How)**:
- Select appropriate technology stack and architecture
- Design practical file structure and execution approach
- Choose integration patterns and configuration methods

### Metrics Guidelines

Evaluation metrics must be:

1. **Measurable**: Define what will be measured
2. **Verifiable**: Can be measured through actual agent execution
3. **Implementation-ready**: Clear enough to guide technical implementation

### Architecture Principles

**Key Principles**:
- **Simple Structure**: Use the flat `eval/` directory structure
- **Configuration-Driven**: Externalize parameters in `eval/config.yaml`
- **Real Agent Focus**: Always use actual agent execution, never simulation or mock
- **Focused Implementation**: Avoid over-engineering, focus on core evaluation logic
- **Minimal Viable Implementation**: Start with essential components, add complexity incrementally
- **Framework-First**: Leverage existing evaluation frameworks before building custom solutions
- **Modular Design**: Create reusable components that can be easily tested and maintained

### Technology Selection Defaults

**Examples of reasonable defaults** (don't ask about these):

- **Tracing instrumentation**: Traceloop library
- **Evaluation frameworks**: DeepEval library
- **LLM calling service**: LiteLLM library
- **LLM provider**: Amazon Bedrock
- **Data processing**: JSON or JSONL
- **Agent integration**: Direct imports for Python agents
- **Configuration**: YAML files