---
description: Analyze user agent source code and design comprehensive evaluation specification with implementation plan
scripts:
  sh: scripts/bash/create-new-evaluation.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.design` in the triggering message **is** the user evaluation requests or agent description. Assume you always have it available in this conversation even if it appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that user evaluation requests or agent description, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and DESIGN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. For single quotes in args like "I'm analyzing", use escape syntax: e.g 'I'\''m analyzing' (or double-quote if possible: "I'm analyzing").

2. Load `templates/eval-design-template.md` to understand required sections for both specification and implementation plan.

3. Follow this execution flow:

    1. Parse user evaluation requests from Input
       If empty: ERROR "No agent description or evaluation requests provided"
    2. Analyze agent state and user evaluation requests:
       a. **Priority 1 - User Input Analysis**: Parse specific evaluation requests, scenarios, and constraints from user input
       b. **Priority 2 - Agent State Detection**:
          - Scan codebase for tracing instrumentation patterns (Traceloop, OpenTelemetry, custom tracing, agent SDK native tracing support, etc)
          - Check for existing trace files/directories in project
          - Identify existing test case files and formats
          - Determine default implementation scenario:
            • Instrumented agent + existing traces → Core evaluation pipeline only
            • Instrumented agent + test cases → Trace collection + core evaluation pipeline
            • Instrumented agent only → Test generation + trace collection + core evaluation pipeline
            • Agent without instrumentation → Instrumentation guidance + full pipeline
            • Traces only → Trace analysis + core evaluation pipeline
       c. **Priority 3 - Module Selection**: Choose required modules based on user requests OR default scenario
    3. Design evaluation strategy and metrics (user-request-driven with agent-state-aware defaults)
       If no clear evaluation approach: ERROR "Cannot determine evaluation strategy"
    4. Generate evaluation requirements
       Each requirement must be measurable and testable
    5. Identify test scenarios and data requirements
    6. Design technical implementation plan:
       - Select appropriate technology stack based on evaluation requirements and agent architecture
       - Design evaluation pipeline architecture (test case generation, trace collection, core evaluation pipeline)
       - Define file structure and implementation tasks
       - Choose integration patterns and configuration approach
    7. **For any unclear aspects during design**: Mark with [NEEDS CLARIFICATION: specific question] if:
       - The choice significantly impacts evaluation scope, metrics, or technical architecture
       - Multiple reasonable evaluation approaches exist with different implications
       - No reasonable default evaluation strategy or technology stack exists
       - **LIMIT: Maximum 5 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: evaluation scope > metrics > technical architecture > implementation details
    8. Return: SUCCESS (evaluation design and implementation plan ready for implementation)

4. Write the complete evaluation specification AND implementation plan to DESIGN_FILE (eval-design.md) using the template structure, replacing placeholders with concrete details derived from the agent analysis while preserving section order and headings.

5. **Copy tracing templates if target agent code exists**:
   
   If target agent code was found during analysis (regardless of instrumentation status):
   ```bash
   # Create tracing subdirectory
   mkdir -p eval/tracing
   
   # Copy OTEL templates from templates/tracing/
   cp templates/tracing/setup-otelcol-template.sh eval/tracing/setup_otelcol.sh
   cp templates/tracing/run-otelcol-template.sh eval/tracing/run_otelcol.sh
   cp templates/tracing/otel-config-template.yaml eval/tracing/otel-config.yaml
   
   # Make scripts executable
   chmod +x eval/tracing/setup_otelcol.sh
   chmod +x eval/tracing/run_otelcol.sh
   ```
   
   This ensures tracing infrastructure is available for later commands, even when `/evalkit.trace` is skipped for already-instrumented agents.

6. **Handle [NEEDS CLARIFICATION] markers** (if any remain):
   
   1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
   2. **LIMIT CHECK**: If more than 5 markers exist, keep only the 5 most critical (by evaluation impact) and make informed guesses for the rest
   3. For each clarification needed (max 5), present options to user in this format:
   
      ```markdown
      ## Question [N]: [Topic]
      
      **Context**: [Quote relevant spec section]
      
      **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
      
      **Suggested Answers**:
      
      | Option | Answer | Implications |
      |--------|--------|--------------|
      | A      | [First suggested answer] | [What this means for the evaluation] |
      | B      | [Second suggested answer] | [What this means for the evaluation] |
      | C      | [Third suggested answer] | [What this means for the evaluation] |
      | Custom | Provide your own answer | [Explain how to provide custom input] |
      
      **Your choice**: _[Wait for user response]_
      ```
   
   4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted with consistent spacing
   5. Number questions sequentially (Q1, Q2, Q3 - max 5 total)
   6. Present all questions together before waiting for responses
   7. Wait for user to respond with their choices for all questions
   8. Update the eval-design.md by replacing each [NEEDS CLARIFICATION] marker with the user's answer
   9. If no clarifications needed, proceed directly to step 6

7. Report completion with branch name, evaluation design file path, and readiness for implementation (`/evalkit.implement`).


## General Guidelines

### Design Decision Guidelines

When creating evaluation specifications and implementation plans from a user prompt:

1. **Prioritize user evaluation requests**: User input takes precedence over detected agent state - always honor specific user requirements and constraints
2. **Provide intelligent defaults**: When user input is minimal, use agent state analysis to suggest appropriate modules and implementation strategy
3. **Make informed guesses**: Use context, agent type patterns, and evaluation best practices to fill remaining gaps
4. **Enable design iteration**: Always include guidance for refining evaluation requests when defaults don't match user needs
5. **Think like an evaluator and architect**: Every requirement should be measurable and every technology choice should have clear rationale
6. **Ask clarification questions**: Use [NEEDS CLARIFICATION: specific question] markers sparingly (max 5 total) for critical decisions that significantly impact evaluation scope or technical architecture

## Evaluation Specification Phase Guidelines

### Design Principles

- Focus on **WHAT** to evaluate and **WHY** it matters for the agent.
- Avoid HOW to implement evaluation (no specific frameworks, file structures, code architecture).
- DO NOT create any checklists that are embedded in this phase.

### Metrics Guidelines

Metrics must be:

1. **Measurable**: Define what will be measured
2. **Framework-agnostic**: No mention of specific evaluation tools, libraries, or implementations
3. **Verifiable**: Can be measured through actual agent execution


## Implementation Planning Phase Guidelines

### Architecture Principles

**Key Principles**:
- **Simple Structure**: Use the flat `eval/` directory structure
- **Configuration-Driven**: Externalize parameters in `config.yaml`
- **Real Agent Focus**: Always use actual agent execution, never simulation
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
- **Visualization**: Streamlit for interactive dashboards
- **Configuration**: YAML files