# Agent Evaluation Specification: [AGENT NAME]

**Branch**: `[###-eval-pipeline]` | **Date**: [DATE]

**User Input**: "$ARGUMENTS"

**User Evaluation Requests**: [Parsed from user input - highest priority, or NA]

**Agent Path**: `[Path to agent code/repository, or No agent source code found]`

**Test Case Path**: `[Path to existing agent test cases, or No existing test cases found]`

**Trace Path**: `[Path to existing agent execution traces, or No existing traces found]`

**Design Path**: `[Path to evaluation design document]`


## Agent Analysis & Overview
<!--
  IMPORTANT: Agent analysis should be PRIORITIZED as evaluation areas ordered by importance.
  Each evaluation area must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable evaluation that delivers meaningful insights.
  
  Assign priorities (P1, P2, P3, etc.) to each area, where P1 is the most critical.
  Think of each area as a standalone slice of evaluation that can be:
  - Evaluated independently
  - Tested independently
  - Reported independently
-->

### Agent Architecture & Capabilities

**Agent Type**: [e.g., Conversational, RAG, Tool-using, Code generation]

**Input/Output Formats**: [Describe data types and interaction patterns]

**Key Functions**: [List primary capabilities and decision points]

**Available Tools**: [If applicable, list tools the agent can use]

**Technology Stack**: [Languages, frameworks, dependencies]

**Agent Workflow Diagram**:
```mermaid
flowchart TD
    A[User Input] --> B[Agent Processing]
    B --> C[Decision Point]
    C --> D[Tool Usage/Action]
    D --> E[Response Generation]
    E --> F[User Output]
    
    %% Add specific nodes for your agent:
    %% Example: C --> G[RAG Retrieval]
    %% Example: C --> H[Code Generation]
    %% Example: G --> I[Context Processing]
```
<!--
  ACTION REQUIRED: Replace the generic workflow above with your agent's specific flow, showing key decision points, tool usage, and data transformations.
-->

### Tracing Instrumentation and Assets Analysis

**Detected Instrumentation Status**: [Fully/Partially/Not Instrumented - tracing libraries found]

**Available Assets**: [Existing traces/test cases/source code only]

**Workflow Strategy**:
Based on the target agent's current state and available assets, the marked option determines which commands are needed in your evaluation workflow:
<!--
  ACTION REQUIRED: Select and mark with x, keep other unmarked there for reference
-->
- [ ] **Instrumented agent + existing traces** → `/evalkit.implement` only (fastest setup - analyze existing trace data)
- [ ] **Instrumented agent + test cases** → `/evalkit.implement` only (evaluate with existing tracing and test cases)
- [ ] **Instrumented agent only** → `/evalkit.data` → `/evalkit.implement` (generate test cases and evaluate with existing tracing)
- [ ] **Agent without instrumentation** → `/evalkit.trace` → `/evalkit.data` → `/evalkit.implement` (full workflow - add tracing, create tests, evaluate)
- [ ] **Traces only** → `/evalkit.implement` only (analyze existing traces without agent access)

### Tracing Configuration
<!--
  ACTION REQUIRED: Fill out if agent needs tracing instrumentation
-->

**Target Library**: [Traceloop (default)/OpenTelemetry/Custom - specify based on agent architecture]

**Instrumentation Points**: [Key functions/workflows to trace - e.g., main_execution, process_input, generate_response]

**Collection Method**: [Local OTEL collector (default)/Cloud service]

**Agent Integration Strategy**:
- **Default Traceloop Integration**: Use Traceloop decorators for evaluation-focused tracing
  - `@workflow`: Mark main agent execution flows for evaluation boundaries
  - `@task`: Mark individual reasoning/action steps for granular analysis
  - `@agent`: Mark agent decision points for performance measurement
- **Evaluation-Specific Naming**: Use descriptive span names that facilitate evaluation analysis
  - Example: `"agent_planning_phase"`, `"tool_execution_step"`, `"response_generation"`
- **Consistent App Naming**: Use format `"{agent-name}-eval-tracing"` for easy trace correlation

## Evaluation Areas
<!--
  IMPORTANT: Focus on user evaluation requests. Do not over-complicate.
  - Prioritize what the user specifically asked for in their evaluation requests
  - Propose minimal evaluation areas that satisfy their needs
  - Avoid suggesting too many evaluation areas - keep it focused and achievable
  - Each area must be independently testable and deliver clear value
-->


### Evaluation Area 1 - [Brief Title] (Priority: P1)

[Describe this evaluation focus in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be evaluated independently - e.g., "Can be fully tested by [specific scenarios] and delivers [specific insights]"]

**Metrics**:
<!--
  IMPORTANT: Keep metrics minimal - 1-2 focused metrics maximum.
  Do not propose many metrics. Focus on what directly measures the evaluation area's core value.
-->
1. **Metric**: [specific measurement] | **Method**: [LLM-as-Judge or Code-based]

---
<!--
  IMPORTANT: Add more evaluation areas as needed, each with an assigned priority. Remember to keep minimal - only add if truly necessary for user's evaluation requests.
-->

### Key Test Scenarios
<!--
  ACTION REQUIRED: Fill out key test scenarios if evaluation involves specific test cases (content below represents placeholders), or remove this entire "Key Test Scenarios" section if existing test cases or traces are found.
-->

- **[Scenario Type 1]**: [What it tests, key characteristics without implementation]

### Test Case Requirements
<!--
  ACTION REQUIRED: Fill out if test cases need to be generated, or remove this entire "Test Case Requirements" section if existing test cases or traces are found.
-->

**Generation Strategy**: [Scenario-based (default)/Coverage-based/Hybrid]

**Test Case Format**: [JSONL with standardized schema (default)]

**Coverage Targets**: [Evaluation areas that need test cases - reference evaluation areas above]

**Expected Volume**: [Number of test cases needed - typically start with 5-10 based on evaluation scope]


## Implementation Plan
<!--
  IMPORTANT: This section defines the technical implementation approach for the evaluation infrastructure.
  Focus on practical decisions that enable trace-based evaluation of the agent.
-->

### Required Commands and Modules

Based on your evaluation requests, tracing instrumentation status, and available assets, the following commands and modules are suggested:
<!--
  ACTION REQUIRED: Select and mark with x based on 5-Command Workflow Strategy above
-->
- [ ] `/evalkit.trace` - Tracing instrumentation setup (if agent lacks tracing)
- [ ] `/evalkit.data` - Test case generation (if no test cases available/requested)
- [ ] `/evalkit.implement` - Core evaluation pipeline (always required)
- [ ] `/evalkit.insights` - Results analysis (optional after evaluation execution)

**Command Execution Order**: `design` → `trace` (if needed) → `data` (if needed) → `implement` → `insights` (if needed)

### Technical Stack

**Language/Version**: [e.g., Python 3.11, Node.js 18+]

**Tracing Libraries**: [e.g., Traceloop (default), OpenTelemetry]

**OTEL Infrastructure**: [Local collector with file export (default)]

**Evaluation Libraries**: [e.g., DeepEval (default), RAGAS, Custom]

**LLM Service**: [LiteLLM (default)]

**LLM Provider**: [Bedrock (default)]

**LLM Model**: [us.anthropic.claude-sonnet-4-20250514-v1:0 (default)]

**Agent Integration**: [e.g., Direct import, API]

**Results Storage**: [e.g., JSON files (default)]

### Core Architecture

**Evaluation Pipeline**: [e.g., Sequential processing vs parallel execution - approach and rationale]

**Trace-Based Evaluation**: [Decoupled architecture using `agent execution → otel-json traces → extraction → evaluation` (default)]
- **Primary Input**: [OTEL trace files (OTLP-JSON format) containing agent execution data (default)]
- **Extraction Layer**: [e.g., Parse traces to extract input/output pairs, history, retrieval context, tool related info, etc based on metric requirements]

**Configuration**: [e.g., YAML files for flexibility - configuration approach]

**Error Handling**: [e.g., Graceful degradation vs fail-fast - error strategy]


### File Structure
<!--
  ACTION REQUIRED: Adjust based on Required Implementation Modules
-->

```
./                           # Repository root directory
├── requirements.txt         # Consolidated dependencies (created by /evalkit.implement)
├── .venv/                   # Python virtual environment (created by uv)
│
└── eval/                    # Evaluation workspace
    ├── README.md            # Running instructions and usage examples (always present)
    ├── config.yaml          # Configuration for evaluation framework (always present)
    ├── trace_extractor.py   # Trace extraction layer (always present for trace-based evaluation)
    ├── evaluators.py        # Core evaluation pipeline (always present)
    ├── run_evaluation.py    # Main orchestration script (always present)
    ├── results/             # Evaluation outputs (always present)
    ├── eval-design.md       # This evaluation specification and plan (always present)
    ├── test-cases.jsonl     # Generated test cases (from /evalkit.data)
    │
    └── tracing/             # Tracing instrumentation files (from /evalkit.trace)
        ├── setup_otelcol.sh    # OTEL collector setup script
        ├── run_otelcol.sh      # OTEL collector runner script
        ├── otel-config.yaml    # OTEL collector configuration
        ├── otelcol-contrib      # OTEL collector binary (downloaded by setup)
        ├── otel-traces.jsonl    # Collected traces output (primary evaluation input)
        └── normalized-traces.jsonl # Processed traces in NormalizedTrace format (generated by trace_extractor.py)
```

### Implementation Tasks
<!--
  ACTION REQUIRED: Adjust based on Required Commands and Modules above
-->

#### Tracing Setup Tasks (use `/evalkit.trace`)
<!--
  ACTION REQUIRED: Keep - only if agent lacks tracing instrumentation, otherwise remove
-->
- [ ] Create tracing subdirectory (`eval/tracing/`)
- [ ] Copy OTEL templates to tracing directory (`eval/tracing/setup_otelcol.sh`, `eval/tracing/run_otelcol.sh`, `eval/tracing/otel-config.yaml`)
- [ ] Download and setup OTEL collector binary in tracing directory
- [ ] Instrument agent code with selected tracing library (Traceloop default)

#### Test Case Generation Tasks (use `/evalkit.data`)
<!--
  ACTION REQUIRED: Keep - only if no existing test cases available, otherwise remove
-->
- [ ] Parse evaluation design for test scenario requirements
- [ ] Generate minimal test cases in JSONL format (`eval/test-cases.jsonl`)

#### Core Evaluation Tasks (use `/evalkit.implement`)
<!--
  ACTION REQUIRED: Keep - always required
-->
- [ ] Set up Python environment and dependency management (first step)
- [ ] Create evaluation project structure based on the decided file structure
- [ ] **Implement trace extraction layer in `eval/trace_extractor.py` (critical first step)**
- [ ] **Validate trace extraction can provide all required evaluation data**
- [ ] Implement all evaluation area evaluators in `eval/evaluators.py` (using extracted trace data as primary input)
- [ ] Build main evaluation orchestration in `eval/run_evaluation.py` (trace-based evaluation flow)
- [ ] Add configuration management in `eval/config.yaml` (include trace input sources and extraction settings)
- [ ] Create comprehensive `eval/README.md` with clear running instructions and usage examples
- [ ] Conduct code review to identify critical issues and fix


## Evaluation Design Iteration Guide

If the above design doesn't match your evaluation needs, try to re-design with more specific requests:

**Example 1 - Analyze unknown traces:**
`/evalkit.design I have trace files but need to understand what agent capabilities they represent and evaluate them`

**Example 2 - Custom evaluation focus:**
`/evalkit.design I want to focus specifically on [accuracy/performance/safety/tool usage/reasoning] evaluation`

**Refine current design:**
You can manually edit this `eval-design.md` file to add/remove/modify specific content as needed.

---

**Note**: Running `/evalkit.design` again will create a new evaluation branch and automatically remove the current `eval/` directory to start fresh. This allows you to iterate on your evaluation design with different approaches while preserving your work in separate branches.

